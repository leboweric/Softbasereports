"""
GL Account Auto-Discovery ETL
Discovers all GL accounts from the Softbase GL table and populates
the tenant_gl_accounts mapping table in PostgreSQL.

Account number patterns:
  Bennett (ben002): 6-digit (e.g., 411010)
    - Digit 1: Type (4=Revenue, 5=COGS, 6=Expense, 7=Other Income)
    - Digits 2-3: Account subcategory
    - Digits 4-5: Department code (10=New Equip, 20=Used, 30=Parts, 40=Service, 60=Rental, 80=Transport)
    - Digit 6: Location/branch
    
  IPS (ind004): 7-digit (e.g., 4110501)
    - Digit 1: Type (4=Revenue, 5=COGS, 6=Expense, 7=Other Income)
    - Digits 2-3: Account subcategory
    - Digits 4-5: Department code
    - Digits 6-7: Location/branch
"""

import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Default department code mappings (can be overridden per tenant via admin UI)
DEFAULT_DEPT_MAPPINGS = {
    '10': 'New Equipment',
    '20': 'Used Equipment',
    '30': 'Parts',          # Bennett uses 30 for Parts
    '40': 'Service',
    '50': 'Parts',          # IPS uses 50 for Parts
    '60': 'Rental',
    '70': 'Allied Sales',
    '74': 'Allied Rental',
    '75': 'Allied Service',
    '80': 'Transportation',
    '90': 'Rental',         # Some tenants use 90 for Rental
    '01': 'Admin/Overhead',
    '02': 'Allied',
    '03': 'Other',
}

# Default expense category mappings based on account subcategory (digits 2-3)
DEFAULT_EXPENSE_CATEGORIES = {
    '01': 'salaries_wages',
    '02': 'vehicle_equipment',
    '03': 'bad_debt',
    '04': 'bank_charges',
    '05': 'office_admin',
    '06': 'charitable',
    '07': 'office_admin',
    '08': 'payroll_benefits',
    '09': 'payroll_benefits',
    '10': 'payroll_benefits',
    '11': 'office_admin',
    '12': 'office_admin',
    '13': 'insurance',
    '14': 'insurance',
    '15': 'insurance',
    '16': 'insurance',
    '17': 'insurance',
    '20': 'marketing',
    '21': 'marketing',
    '22': 'marketing',
    '30': 'depreciation',
    '31': 'vehicle_equipment',
    '32': 'office_admin',
    '33': 'vehicle_equipment',
    '34': 'office_admin',
    '35': 'office_admin',
    '40': 'office_admin',
    '41': 'office_admin',
    '42': 'interest_finance',
    '43': 'interest_finance',
    '44': 'other_expenses',
    '45': 'other_expenses',
    '46': 'other_expenses',
    '47': 'other_expenses',
    '48': 'other_expenses',
    '49': 'other_expenses',
    '50': 'office_admin',
    '51': 'office_admin',
    '52': 'professional_fees',
    '53': 'professional_fees',
    '54': 'professional_fees',
    '55': 'professional_fees',
    '60': 'rent_facilities',
    '61': 'rent_facilities',
    '62': 'rent_facilities',
    '70': 'payroll_benefits',
    '71': 'payroll_benefits',
    '72': 'payroll_benefits',
    '73': 'payroll_benefits',
    '74': 'utilities',
    '75': 'utilities',
    '80': 'office_admin',
    '81': 'office_admin',
    '82': 'vehicle_equipment',
    '83': 'office_admin',
    '84': 'office_admin',
    '85': 'office_admin',
    '90': 'other_expenses',
    '91': 'other_expenses',
    '92': 'utilities',
    '93': 'other_expenses',
    '94': 'other_expenses',
    '95': 'other_expenses',
    '96': 'other_expenses',
    '97': 'other_expenses',
    '98': 'other_expenses',
    '99': 'other_expenses',
}

EXPENSE_CATEGORY_NAMES = {
    'salaries_wages': 'Salaries & Wages',
    'payroll_benefits': 'Payroll & Benefits',
    'insurance': 'Insurance',
    'rent_facilities': 'Rent & Facilities',
    'depreciation': 'Depreciation',
    'marketing': 'Marketing',
    'professional_fees': 'Professional Fees',
    'office_admin': 'Office & Admin',
    'vehicle_equipment': 'Vehicle & Equipment',
    'utilities': 'Utilities',
    'interest_finance': 'Interest & Finance',
    'other_expenses': 'Other Expenses',
    'bad_debt': 'Bad Debt',
    'charitable': 'Charitable Contributions',
    'bank_charges': 'Bank Charges',
}


class GLDiscoveryETL:
    """Auto-discovers GL accounts from Softbase and populates PostgreSQL mapping table."""
    
    def __init__(self, org_id, schema, azure_sql=None, pg=None):
        self.org_id = org_id
        self.schema = schema
        self.azure_sql = azure_sql
        self.pg = pg
    
    def classify_account(self, account_no):
        """
        Classify a GL account number into type, department, and expense category.
        
        Returns dict with: account_type, department_code, department_name, expense_category
        """
        account_str = str(account_no).strip()
        
        if not account_str or not account_str[0].isdigit():
            return {
                'account_type': 'other',
                'department_code': None,
                'department_name': None,
                'expense_category': None,
            }
        
        first_digit = account_str[0]
        
        # Determine account type from first digit
        type_map = {
            '4': 'revenue',
            '5': 'cogs',
            '6': 'expense',
            '7': 'other_income',
        }
        account_type = type_map.get(first_digit, 'other')
        
        # Extract department code (digits 4-5 for both 6-digit and 7-digit accounts)
        dept_code = None
        dept_name = None
        if len(account_str) >= 5:
            dept_code = account_str[3:5]
            dept_name = DEFAULT_DEPT_MAPPINGS.get(dept_code, f'Department {dept_code}')
        
        # Extract expense category for 6xxxxx accounts
        expense_category = None
        if account_type == 'expense' and len(account_str) >= 3:
            subcategory = account_str[1:3]
            expense_category = DEFAULT_EXPENSE_CATEGORIES.get(subcategory, 'other_expenses')
        
        return {
            'account_type': account_type,
            'department_code': dept_code,
            'department_name': dept_name,
            'expense_category': expense_category,
        }
    
    def discover_accounts(self):
        """
        Query all distinct GL accounts from the Softbase GL table
        and upsert them into the PostgreSQL mapping table.
        """
        logger.info(f"[GL Discovery] Starting for org_id={self.org_id}, schema={self.schema}")
        
        started_at = datetime.now()
        accounts_found = 0
        accounts_new = 0
        accounts_updated = 0
        
        try:
            # Step 1: Query all distinct accounts from GL table with their descriptions
            query = f"""
                SELECT DISTINCT 
                    g.AccountNo,
                    COALESCE(c.Description, '') as Description
                FROM {self.schema}.GL g
                LEFT JOIN {self.schema}.ChartOfAccounts c ON g.AccountNo = c.AccountNo
                WHERE g.AccountNo IS NOT NULL
                AND LEN(LTRIM(RTRIM(g.AccountNo))) >= 5
                ORDER BY g.AccountNo
            """
            
            try:
                rows = self.azure_sql.execute_query(query)
            except Exception as e:
                # ChartOfAccounts might not exist — try without it
                logger.warning(f"[GL Discovery] ChartOfAccounts join failed, trying without: {e}")
                query = f"""
                    SELECT DISTINCT AccountNo, '' as Description
                    FROM {self.schema}.GL
                    WHERE AccountNo IS NOT NULL
                    AND LEN(LTRIM(RTRIM(AccountNo))) >= 5
                    ORDER BY AccountNo
                """
                rows = self.azure_sql.execute_query(query)
            
            accounts_found = len(rows)
            logger.info(f"[GL Discovery] Found {accounts_found} distinct accounts in {self.schema}.GL")
            
            if accounts_found == 0:
                logger.warning(f"[GL Discovery] No accounts found for {self.schema}")
                self._log_discovery(started_at, accounts_found, 0, 0, 'warning', 'No accounts found')
                return
            
            # Step 2: Get existing mappings from PostgreSQL
            existing_query = """
                SELECT account_no, is_auto_discovered 
                FROM tenant_gl_accounts 
                WHERE organization_id = %s
            """
            existing = self.pg.execute_query(existing_query, (self.org_id,))
            existing_map = {r['account_no']: r['is_auto_discovered'] for r in existing}
            
            # Step 3: Upsert each account
            upsert_query = """
                INSERT INTO tenant_gl_accounts 
                    (organization_id, account_no, account_type, department_code, department_name, 
                     expense_category, description, is_active, is_auto_discovered, last_seen_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, TRUE, CURRENT_TIMESTAMP)
                ON CONFLICT (organization_id, account_no) 
                DO UPDATE SET 
                    last_seen_date = CURRENT_TIMESTAMP,
                    description = CASE 
                        WHEN tenant_gl_accounts.is_auto_discovered = TRUE 
                        THEN EXCLUDED.description 
                        ELSE tenant_gl_accounts.description 
                    END,
                    account_type = CASE 
                        WHEN tenant_gl_accounts.is_auto_discovered = TRUE 
                        THEN EXCLUDED.account_type 
                        ELSE tenant_gl_accounts.account_type 
                    END,
                    department_code = CASE 
                        WHEN tenant_gl_accounts.is_auto_discovered = TRUE 
                        THEN EXCLUDED.department_code 
                        ELSE tenant_gl_accounts.department_code 
                    END,
                    department_name = CASE 
                        WHEN tenant_gl_accounts.is_auto_discovered = TRUE 
                        THEN EXCLUDED.department_name 
                        ELSE tenant_gl_accounts.department_name 
                    END,
                    expense_category = CASE 
                        WHEN tenant_gl_accounts.is_auto_discovered = TRUE 
                        THEN EXCLUDED.expense_category 
                        ELSE tenant_gl_accounts.expense_category 
                    END,
                    updated_at = CURRENT_TIMESTAMP
            """
            
            with self.pg.get_connection() as conn:
                with conn.cursor() as cursor:
                    for row in rows:
                        account_no = str(row['AccountNo']).strip()
                        description = str(row.get('Description', '')).strip()
                        
                        classification = self.classify_account(account_no)
                        
                        cursor.execute(upsert_query, (
                            self.org_id,
                            account_no,
                            classification['account_type'],
                            classification['department_code'],
                            classification['department_name'],
                            classification['expense_category'],
                            description,
                        ))
                        
                        if account_no not in existing_map:
                            accounts_new += 1
                        else:
                            accounts_updated += 1
                    
                    conn.commit()
            
            logger.info(f"[GL Discovery] Completed: {accounts_found} found, {accounts_new} new, {accounts_updated} updated")
            
            # Step 4: Populate department and expense category tables
            self._populate_departments()
            self._populate_expense_categories()
            
            # Step 5: Log the discovery
            self._log_discovery(started_at, accounts_found, accounts_new, accounts_updated, 'success')
            
        except Exception as e:
            logger.error(f"[GL Discovery] Error for org_id={self.org_id}: {str(e)}")
            self._log_discovery(started_at, accounts_found, accounts_new, accounts_updated, 'error', str(e))
            raise
    
    def _populate_departments(self):
        """Populate the tenant_departments table from discovered accounts."""
        query = """
            SELECT DISTINCT department_code, department_name
            FROM tenant_gl_accounts
            WHERE organization_id = %s
            AND department_code IS NOT NULL
            AND is_active = TRUE
            ORDER BY department_code
        """
        depts = self.pg.execute_query(query, (self.org_id,))
        
        upsert = """
            INSERT INTO tenant_departments (organization_id, dept_code, dept_name, display_order)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (organization_id, dept_code)
            DO UPDATE SET dept_name = EXCLUDED.dept_name, updated_at = CURRENT_TIMESTAMP
        """
        
        with self.pg.get_connection() as conn:
            with conn.cursor() as cursor:
                for i, dept in enumerate(depts):
                    cursor.execute(upsert, (
                        self.org_id,
                        dept['department_code'],
                        dept['department_name'],
                        i * 10,
                    ))
                conn.commit()
        
        logger.info(f"[GL Discovery] Populated {len(depts)} departments for org_id={self.org_id}")
    
    def _populate_expense_categories(self):
        """Populate the tenant_expense_categories table from discovered accounts."""
        query = """
            SELECT DISTINCT expense_category
            FROM tenant_gl_accounts
            WHERE organization_id = %s
            AND expense_category IS NOT NULL
            AND account_type = 'expense'
            AND is_active = TRUE
            ORDER BY expense_category
        """
        cats = self.pg.execute_query(query, (self.org_id,))
        
        upsert = """
            INSERT INTO tenant_expense_categories (organization_id, category_key, category_name, display_order)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (organization_id, category_key)
            DO UPDATE SET category_name = EXCLUDED.category_name, updated_at = CURRENT_TIMESTAMP
        """
        
        with self.pg.get_connection() as conn:
            with conn.cursor() as cursor:
                for i, cat in enumerate(cats):
                    key = cat['expense_category']
                    name = EXPENSE_CATEGORY_NAMES.get(key, key.replace('_', ' ').title())
                    cursor.execute(upsert, (self.org_id, key, name, i * 10))
                conn.commit()
        
        logger.info(f"[GL Discovery] Populated {len(cats)} expense categories for org_id={self.org_id}")
    
    def _log_discovery(self, started_at, found, new, updated, status, error_msg=None):
        """Log the discovery run."""
        try:
            query = """
                INSERT INTO gl_discovery_log 
                    (organization_id, discovery_type, accounts_found, accounts_new, accounts_updated, 
                     status, error_message, started_at, completed_at)
                VALUES (%s, 'full', %s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
            """
            with self.pg.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, (self.org_id, found, new, updated, status, error_msg, started_at))
                conn.commit()
        except Exception as e:
            logger.error(f"[GL Discovery] Failed to log discovery: {e}")


def run_gl_discovery_etl(org_id=None, schema=None):
    """
    Run GL account discovery for a specific tenant or all tenants.
    """
    from src.etl.tenant_discovery import run_etl_for_all_tenants
    from src.services.postgres_service import PostgreSQLService
    
    pg = PostgreSQLService()
    
    if org_id and schema:
        from src.etl.tenant_discovery import create_tenant_azure_sql
        azure_sql = create_tenant_azure_sql(org_id)
        if azure_sql:
            etl = GLDiscoveryETL(org_id, schema, azure_sql, pg)
            etl.discover_accounts()
        else:
            logger.error(f"[GL Discovery] Could not create Azure SQL connection for org_id={org_id}")
    else:
        def _run_for_tenant(tenant_org_id, tenant_schema, azure_sql):
            etl = GLDiscoveryETL(tenant_org_id, tenant_schema, azure_sql, pg)
            etl.discover_accounts()
        
        run_etl_for_all_tenants('GL Discovery', _run_for_tenant)
