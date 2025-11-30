"""
Softbase Evolution ERP Adapter

Extracts financial data from Softbase Evolution SQL Server databases.
Based on the proven queries from the existing Currie Report implementation.
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import date, datetime
import pymssql

from .base_adapter import BaseERPAdapter

logger = logging.getLogger(__name__)


class SoftbaseEvolutionAdapter(BaseERPAdapter):
    """
    Adapter for Softbase Evolution dealer management system.
    Connects to Azure SQL Server databases.
    """

    # GL Account mappings for Currie Financial Model
    # Organized by report section for exact replication
    GL_ACCOUNTS = {
        # New Equipment Sales Section
        'new_lift_truck_primary': {
            'revenue': ['413001'],
            'cost': ['513001']
        },
        'new_lift_truck_other': {
            'revenue': ['426001'],
            'cost': ['526001']
        },
        'new_allied': {
            'revenue': ['412001'],
            'cost': ['512001']
        },
        'batteries': {
            'revenue': ['414001'],
            'cost': ['514001']
        },
        # Used Equipment
        'used_equipment': {
            'revenue': ['412002', '413002', '414002', '426002', '431002', '410002'],
            'cost': ['512002', '513002', '514002', '526002', '531002', '510002']
        },
        # Rental - Consolidated
        'rental': {
            'revenue': ['411001', '419000', '420000', '421000', '434012', '410008'],
            'cost': ['510008', '511001', '519000', '520000', '521008', '537001', '539000', '534014', '545000']
        },
        # Service - Broken down by category
        'service_customer_labor': {
            'revenue': ['410004', '410005', '410007'],
            'cost': ['510004', '510005', '510007']
        },
        'service_internal_labor': {
            'revenue': ['423000', '425000'],
            'cost': ['523000']
        },
        'service_warranty_labor': {
            'revenue': ['435000', '435001', '435002', '435003', '435004'],
            'cost': ['535001', '535002', '535003', '535004', '535005']
        },
        'service_sublet': {
            'revenue': ['432000'],
            'cost': ['532000']
        },
        'service_other': {
            'revenue': ['428000', '429002'],
            'cost': ['528000', '529001']
        },
        # Parts - Broken down by category
        'parts_counter_primary': {
            'revenue': ['410003'],
            'cost': ['510003']
        },
        'parts_ro_primary': {
            'revenue': ['410012'],
            'cost': ['510012']
        },
        'parts_internal': {
            'revenue': ['424000'],
            'cost': ['524000']
        },
        'parts_warranty': {
            'revenue': ['410014'],
            'cost': ['510014']
        },
        # Trucking
        'trucking': {
            'revenue': ['410010', '421010', '434001', '434002', '434003', '434010', '434011', '434012', '434013'],
            'cost': ['510010', '521010', '534001', '534002', '534003', '534010', '534011', '534012', '534013', '534014', '534015']
        }
    }

    # Expense GL Account Mappings
    EXPENSE_ACCOUNTS = {
        'personnel': {
            'salaries': ('610100', '610199'),
            'commissions': ('610200', '610299'),
            'benefits': ('620100', '629999'),
            'payroll_taxes': ('630100', '639999')
        },
        'operating': {
            'advertising': ('710100', '719999'),
            'professional_fees': ('720100', '729999'),
            'supplies': ('730100', '739999'),
            'insurance': ('740100', '749999'),
            'travel': ('750100', '759999'),
            'other': ('760100', '799999')
        },
        'occupancy': {
            'rent': ('810100', '819999'),
            'utilities': ('820100', '829999'),
            'repairs': ('830100', '839999'),
            'depreciation': ('840100', '849999'),
            'other': ('850100', '899999')
        }
    }

    # Default department allocation percentages (can be overridden per dealer)
    DEFAULT_ALLOCATIONS = {
        'new': 0.47517,
        'used': 0.03209,
        'rental': 0.20694,
        'parts': 0.13121,
        'service': 0.14953,
        'trucking': 0.00507
    }

    @property
    def erp_type(self) -> str:
        return 'softbase_evolution'

    def __init__(self, connection_config: Dict[str, Any]):
        """
        Initialize with database connection details.

        Args:
            connection_config: Dict with keys:
                - server: Azure SQL server hostname
                - database: Database name
                - username: SQL username
                - password: SQL password
                - schema: Schema name (default: 'ben002')
        """
        super().__init__(connection_config)
        self.schema = connection_config.get('schema', 'ben002')
        self._connection = None

    def _get_connection(self):
        """Get or create database connection."""
        if self._connection is None:
            self._connection = pymssql.connect(
                server=self.config['server'],
                user=self.config['username'],
                password=self.config['password'],
                database=self.config['database']
            )
        return self._connection

    def test_connection(self) -> Dict[str, Any]:
        """Test database connectivity."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            cursor.close()
            return {'success': True, 'message': 'Connection successful'}
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {'success': False, 'message': str(e)}

    def _execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a SQL query and return results as list of dicts."""
        conn = self._get_connection()
        cursor = conn.cursor(as_dict=True)
        cursor.execute(query, params)
        results = cursor.fetchall()
        cursor.close()
        return results

    # ==========================================
    # CURRIE FINANCIAL MODEL - Main Entry Point
    # ==========================================

    def get_currie_financial_model(
        self,
        start_date: date,
        end_date: date,
        dealer_name: str = 'Dealer',
        num_locations: int = 1
    ) -> Dict[str, Any]:
        """
        Get complete Currie Financial Model data.
        This is the main method that replicates the full report.
        """
        # Calculate number of months
        months_diff = (end_date.year - start_date.year) * 12 + end_date.month - start_date.month + 1

        data = {
            'dealership_info': {
                'name': dealer_name,
                'date': datetime.now().strftime('%Y-%m-%d'),
                'num_locations': num_locations,
                'num_months': months_diff,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            },
            'new_equipment': self._get_new_equipment_sales(start_date, end_date),
            'rental': self._get_rental_revenue(start_date, end_date),
            'service': self._get_service_revenue(start_date, end_date),
            'parts': self._get_parts_revenue(start_date, end_date),
            'trucking': self._get_trucking_revenue(start_date, end_date)
        }

        # Calculate totals
        data['totals'] = self._calculate_totals(data, months_diff)

        # Get expenses
        expenses = self._get_gl_expenses(start_date, end_date)
        data['expenses'] = expenses

        # Get other income and interest
        other_income = self._get_other_income_and_interest(start_date, end_date)
        data['other_income'] = other_income.get('other_income', 0)
        data['interest_expense'] = other_income.get('interest_expense', 0)
        data['fi_income'] = other_income.get('fi_income', 0)

        # Calculate bottom summary totals
        total_operating_profit = (
            data['totals']['total_company']['gross_profit'] -
            expenses['grand_total'] +
            data['other_income'] +
            data['interest_expense']
        )
        data['total_operating_profit'] = total_operating_profit
        data['pre_tax_income'] = total_operating_profit + data['fi_income']

        # Add department-allocated expenses
        data['department_expenses'] = self._calculate_department_expenses(expenses)

        # Add AR Aging
        data['ar_aging'] = self._get_ar_aging()

        # Add Balance Sheet data
        data['balance_sheet'] = self._get_balance_sheet_data(end_date)

        return data

    # ==========================================
    # Revenue by Department
    # ==========================================

    def _get_new_equipment_sales(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get new equipment sales broken down by category."""
        categories = {
            'new_lift_truck_primary': {'sales': 0, 'cogs': 0},
            'new_lift_truck_other': {'sales': 0, 'cogs': 0},
            'new_allied': {'sales': 0, 'cogs': 0},
            'other_new_equipment': {'sales': 0, 'cogs': 0},
            'operator_training': {'sales': 0, 'cogs': 0},
            'used_equipment': {'sales': 0, 'cogs': 0},
            'ecommerce': {'sales': 0, 'cogs': 0},
            'systems': {'sales': 0, 'cogs': 0},
            'batteries': {'sales': 0, 'cogs': 0}
        }

        # Collect all relevant accounts
        all_accounts = []
        for key in ['new_lift_truck_primary', 'new_lift_truck_other', 'new_allied', 'batteries', 'used_equipment']:
            if key in self.GL_ACCOUNTS:
                all_accounts.extend(self.GL_ACCOUNTS[key]['revenue'])
                all_accounts.extend(self.GL_ACCOUNTS[key]['cost'])

        if not all_accounts:
            return categories

        placeholders = ','.join(['%s'] * len(all_accounts))
        query = f"""
        SELECT
            AccountNo,
            SUM(Amount) as total_amount
        FROM {self.schema}.GLDetail
        WHERE EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN ({placeholders})
        GROUP BY AccountNo
        """

        params = (start_date, end_date) + tuple(all_accounts)
        results = self._execute_query(query, params)

        # Map results to categories
        for row in results:
            account = row['AccountNo']
            amount = float(row['total_amount'] or 0)

            # New Lift Truck - Primary Brand
            if account in self.GL_ACCOUNTS['new_lift_truck_primary']['revenue']:
                categories['new_lift_truck_primary']['sales'] += -amount
            elif account in self.GL_ACCOUNTS['new_lift_truck_primary']['cost']:
                categories['new_lift_truck_primary']['cogs'] += amount

            # New Lift Truck - Other Brands
            elif account in self.GL_ACCOUNTS['new_lift_truck_other']['revenue']:
                categories['new_lift_truck_other']['sales'] += -amount
            elif account in self.GL_ACCOUNTS['new_lift_truck_other']['cost']:
                categories['new_lift_truck_other']['cogs'] += amount

            # New Allied Equipment
            elif account in self.GL_ACCOUNTS['new_allied']['revenue']:
                categories['new_allied']['sales'] += -amount
            elif account in self.GL_ACCOUNTS['new_allied']['cost']:
                categories['new_allied']['cogs'] += amount

            # Batteries
            elif account in self.GL_ACCOUNTS['batteries']['revenue']:
                categories['batteries']['sales'] += -amount
            elif account in self.GL_ACCOUNTS['batteries']['cost']:
                categories['batteries']['cogs'] += amount

            # Used Equipment
            elif account in self.GL_ACCOUNTS['used_equipment']['revenue']:
                categories['used_equipment']['sales'] += -amount
            elif account in self.GL_ACCOUNTS['used_equipment']['cost']:
                categories['used_equipment']['cogs'] += amount

        # Calculate gross profit
        for category in categories.values():
            category['gross_profit'] = category['sales'] - category['cogs']

        return categories

    def _get_rental_revenue(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get rental revenue as consolidated category."""
        rental_data = {'sales': 0, 'cogs': 0, 'gross_profit': 0}

        revenue_accounts = self.GL_ACCOUNTS['rental']['revenue']
        cost_accounts = self.GL_ACCOUNTS['rental']['cost']
        all_accounts = revenue_accounts + cost_accounts

        placeholders = ','.join(['%s'] * len(all_accounts))
        query = f"""
        SELECT
            AccountNo,
            SUM(Amount) as total_amount
        FROM {self.schema}.GLDetail
        WHERE EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN ({placeholders})
        GROUP BY AccountNo
        """

        params = (start_date, end_date) + tuple(all_accounts)
        results = self._execute_query(query, params)

        for row in results:
            account = row['AccountNo']
            amount = float(row['total_amount'] or 0)

            if account in revenue_accounts:
                rental_data['sales'] += -amount
            elif account in cost_accounts:
                rental_data['cogs'] += amount

        rental_data['gross_profit'] = rental_data['sales'] - rental_data['cogs']
        return rental_data

    def _get_service_revenue(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get service revenue broken down by customer, internal, warranty, sublet."""
        service_data = {
            'customer_labor': {'sales': 0, 'cogs': 0},
            'internal_labor': {'sales': 0, 'cogs': 0},
            'warranty_labor': {'sales': 0, 'cogs': 0},
            'sublet': {'sales': 0, 'cogs': 0},
            'other': {'sales': 0, 'cogs': 0}
        }

        # Map service categories to GL accounts
        category_mapping = {
            'customer_labor': 'service_customer_labor',
            'internal_labor': 'service_internal_labor',
            'warranty_labor': 'service_warranty_labor',
            'sublet': 'service_sublet',
            'other': 'service_other'
        }

        # Collect all accounts
        all_accounts = []
        for gl_key in category_mapping.values():
            if gl_key in self.GL_ACCOUNTS:
                all_accounts.extend(self.GL_ACCOUNTS[gl_key]['revenue'])
                all_accounts.extend(self.GL_ACCOUNTS[gl_key]['cost'])

        if not all_accounts:
            return service_data

        placeholders = ','.join(['%s'] * len(all_accounts))
        query = f"""
        SELECT
            AccountNo,
            SUM(Amount) as total_amount
        FROM {self.schema}.GLDetail
        WHERE EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN ({placeholders})
        GROUP BY AccountNo
        """

        params = (start_date, end_date) + tuple(all_accounts)
        results = self._execute_query(query, params)

        for row in results:
            account = row['AccountNo']
            amount = float(row['total_amount'] or 0)

            for cat_name, gl_key in category_mapping.items():
                if gl_key in self.GL_ACCOUNTS:
                    if account in self.GL_ACCOUNTS[gl_key]['revenue']:
                        service_data[cat_name]['sales'] += -amount
                    elif account in self.GL_ACCOUNTS[gl_key]['cost']:
                        service_data[cat_name]['cogs'] += amount

        # Calculate gross profit
        for category in service_data.values():
            category['gross_profit'] = category['sales'] - category['cogs']

        return service_data

    def _get_parts_revenue(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get parts revenue broken down by counter, RO, internal, warranty."""
        parts_data = {
            'counter_primary': {'sales': 0, 'cogs': 0},
            'counter_other': {'sales': 0, 'cogs': 0},
            'ro_primary': {'sales': 0, 'cogs': 0},
            'ro_other': {'sales': 0, 'cogs': 0},
            'internal': {'sales': 0, 'cogs': 0},
            'warranty': {'sales': 0, 'cogs': 0},
            'ecommerce': {'sales': 0, 'cogs': 0}
        }

        category_mapping = {
            'counter_primary': 'parts_counter_primary',
            'ro_primary': 'parts_ro_primary',
            'internal': 'parts_internal',
            'warranty': 'parts_warranty'
        }

        # Collect all accounts
        all_accounts = []
        for gl_key in category_mapping.values():
            if gl_key in self.GL_ACCOUNTS:
                all_accounts.extend(self.GL_ACCOUNTS[gl_key]['revenue'])
                all_accounts.extend(self.GL_ACCOUNTS[gl_key]['cost'])

        if not all_accounts:
            return parts_data

        placeholders = ','.join(['%s'] * len(all_accounts))
        query = f"""
        SELECT
            AccountNo,
            SUM(Amount) as total_amount
        FROM {self.schema}.GLDetail
        WHERE EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN ({placeholders})
        GROUP BY AccountNo
        """

        params = (start_date, end_date) + tuple(all_accounts)
        results = self._execute_query(query, params)

        for row in results:
            account = row['AccountNo']
            amount = float(row['total_amount'] or 0)

            for cat_name, gl_key in category_mapping.items():
                if gl_key in self.GL_ACCOUNTS:
                    if account in self.GL_ACCOUNTS[gl_key]['revenue']:
                        parts_data[cat_name]['sales'] += -amount
                    elif account in self.GL_ACCOUNTS[gl_key]['cost']:
                        parts_data[cat_name]['cogs'] += amount

        # Calculate gross profit
        for category in parts_data.values():
            category['gross_profit'] = category['sales'] - category['cogs']

        return parts_data

    def _get_trucking_revenue(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get trucking/delivery revenue."""
        trucking_data = {'sales': 0, 'cogs': 0, 'gross_profit': 0}

        revenue_accounts = self.GL_ACCOUNTS['trucking']['revenue']
        cost_accounts = self.GL_ACCOUNTS['trucking']['cost']
        all_accounts = revenue_accounts + cost_accounts

        placeholders = ','.join(['%s'] * len(all_accounts))
        query = f"""
        SELECT
            AccountNo,
            SUM(Amount) as total_amount
        FROM {self.schema}.GLDetail
        WHERE EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN ({placeholders})
        GROUP BY AccountNo
        """

        params = (start_date, end_date) + tuple(all_accounts)
        results = self._execute_query(query, params)

        for row in results:
            account = row['AccountNo']
            amount = float(row['total_amount'] or 0)

            if account in revenue_accounts:
                trucking_data['sales'] += -amount
            elif account in cost_accounts:
                trucking_data['cogs'] += amount

        trucking_data['gross_profit'] = trucking_data['sales'] - trucking_data['cogs']
        return trucking_data

    # ==========================================
    # Totals Calculation
    # ==========================================

    def _calculate_totals(self, data: Dict[str, Any], num_months: int) -> Dict[str, Any]:
        """Calculate total sales, COGS, and GP across all categories."""

        # Total New Equipment = first 4 items
        total_new_equipment = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
        if 'new_equipment' in data:
            new_eq_categories = ['new_lift_truck_primary', 'new_lift_truck_other', 'new_allied', 'other_new_equipment']
            for cat in new_eq_categories:
                if cat in data['new_equipment']:
                    total_new_equipment['sales'] += data['new_equipment'][cat].get('sales', 0)
                    total_new_equipment['cogs'] += data['new_equipment'][cat].get('cogs', 0)
            total_new_equipment['gross_profit'] = total_new_equipment['sales'] - total_new_equipment['cogs']

        # Total Sales Dept = all equipment items
        total_sales_dept = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
        if 'new_equipment' in data:
            for category in data['new_equipment'].values():
                total_sales_dept['sales'] += category.get('sales', 0)
                total_sales_dept['cogs'] += category.get('cogs', 0)
            total_sales_dept['gross_profit'] = total_sales_dept['sales'] - total_sales_dept['cogs']

        # Total Rental
        total_rental = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
        if 'rental' in data:
            total_rental['sales'] = data['rental'].get('sales', 0)
            total_rental['cogs'] = data['rental'].get('cogs', 0)
            total_rental['gross_profit'] = total_rental['sales'] - total_rental['cogs']

        # Total Service
        total_service = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
        if 'service' in data:
            for category in data['service'].values():
                total_service['sales'] += category.get('sales', 0)
                total_service['cogs'] += category.get('cogs', 0)
            total_service['gross_profit'] = total_service['sales'] - total_service['cogs']

        # Total Parts
        total_parts = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
        if 'parts' in data:
            for category in data['parts'].values():
                total_parts['sales'] += category.get('sales', 0)
                total_parts['cogs'] += category.get('cogs', 0)
            total_parts['gross_profit'] = total_parts['sales'] - total_parts['cogs']

        # Total Aftermarket
        total_aftermarket = {
            'sales': total_service['sales'] + total_parts['sales'],
            'cogs': total_service['cogs'] + total_parts['cogs'],
            'gross_profit': 0
        }
        total_aftermarket['gross_profit'] = total_aftermarket['sales'] - total_aftermarket['cogs']

        # Grand Total
        grand_total = {
            'sales': total_sales_dept['sales'] + total_rental['sales'] + total_service['sales'] + total_parts['sales'],
            'cogs': total_sales_dept['cogs'] + total_rental['cogs'] + total_service['cogs'] + total_parts['cogs'],
            'gross_profit': 0
        }

        # Add trucking
        if 'trucking' in data:
            grand_total['sales'] += data['trucking'].get('sales', 0)
            grand_total['cogs'] += data['trucking'].get('cogs', 0)

        grand_total['gross_profit'] = grand_total['sales'] - grand_total['cogs']

        avg_monthly = grand_total['sales'] / num_months if num_months > 0 else 0

        return {
            'total_new_equipment': total_new_equipment,
            'total_sales_dept': total_sales_dept,
            'total_rental': total_rental,
            'total_service': total_service,
            'total_parts': total_parts,
            'total_aftermarket': total_aftermarket,
            'grand_total': grand_total,
            'total_company': grand_total,
            'avg_monthly_sales_gp': avg_monthly
        }

    # ==========================================
    # Expenses
    # ==========================================

    def _get_gl_expenses(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get expenses from GL accounts by category."""
        expenses = {
            'personnel': {'total': 0, 'details': {}},
            'operating': {'total': 0, 'details': {}},
            'occupancy': {'total': 0, 'details': {}},
            'grand_total': 0
        }

        for category, subcategories in self.EXPENSE_ACCOUNTS.items():
            category_total = 0
            for subcat, (start_acct, end_acct) in subcategories.items():
                query = f"""
                SELECT SUM(Amount) as total_amount
                FROM {self.schema}.GLDetail
                WHERE EffectiveDate >= %s
                  AND EffectiveDate <= %s
                  AND Posted = 1
                  AND AccountNo >= %s
                  AND AccountNo <= %s
                """
                results = self._execute_query(query, (start_date, end_date, start_acct, end_acct))
                amount = float(results[0]['total_amount'] or 0) if results else 0
                expenses[category]['details'][subcat] = amount
                category_total += amount

            expenses[category]['total'] = category_total

        expenses['grand_total'] = (
            expenses['personnel']['total'] +
            expenses['operating']['total'] +
            expenses['occupancy']['total']
        )

        return expenses

    def _calculate_department_expenses(self, expenses: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate department-allocated expenses using allocation percentages."""
        allocations = self.DEFAULT_ALLOCATIONS

        personnel_total = expenses.get('personnel', {}).get('total', 0)
        operating_total = expenses.get('operating', {}).get('total', 0)
        occupancy_total = expenses.get('occupancy', {}).get('total', 0)

        # Calculate G&A allocation (remainder)
        ga_allocation = 1 - sum(allocations.values())

        dept_expenses = {
            'personnel': {},
            'operating': {},
            'occupancy': {},
            'total': {}
        }

        for dept, pct in allocations.items():
            dept_expenses['personnel'][dept] = personnel_total * pct
            dept_expenses['operating'][dept] = operating_total * pct
            dept_expenses['occupancy'][dept] = occupancy_total * pct
            dept_expenses['total'][dept] = (
                dept_expenses['personnel'][dept] +
                dept_expenses['operating'][dept] +
                dept_expenses['occupancy'][dept]
            )

        # G&A
        dept_expenses['personnel']['ga'] = personnel_total * ga_allocation
        dept_expenses['operating']['ga'] = operating_total * ga_allocation
        dept_expenses['occupancy']['ga'] = occupancy_total * ga_allocation
        dept_expenses['total']['ga'] = (
            dept_expenses['personnel']['ga'] +
            dept_expenses['operating']['ga'] +
            dept_expenses['occupancy']['ga']
        )

        # Totals
        dept_expenses['personnel']['total'] = personnel_total
        dept_expenses['operating']['total'] = operating_total
        dept_expenses['occupancy']['total'] = occupancy_total
        dept_expenses['total']['total'] = personnel_total + operating_total + occupancy_total

        return dept_expenses

    def _get_other_income_and_interest(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get other income and interest expense."""
        # Other Income accounts (800xxx range typically)
        # Interest Expense accounts
        # F&I Income accounts

        query = f"""
        SELECT
            -SUM(CASE WHEN AccountNo BETWEEN '800000' AND '849999' THEN Amount ELSE 0 END) as other_income,
            SUM(CASE WHEN AccountNo BETWEEN '850000' AND '859999' THEN Amount ELSE 0 END) as interest_expense,
            -SUM(CASE WHEN AccountNo BETWEEN '860000' AND '869999' THEN Amount ELSE 0 END) as fi_income
        FROM {self.schema}.GLDetail
        WHERE EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 1
        """

        results = self._execute_query(query, (start_date, end_date))

        if results:
            row = results[0]
            return {
                'other_income': float(row['other_income'] or 0),
                'interest_expense': float(row['interest_expense'] or 0),
                'fi_income': float(row['fi_income'] or 0)
            }

        return {'other_income': 0, 'interest_expense': 0, 'fi_income': 0}

    # ==========================================
    # AR Aging
    # ==========================================

    def _get_ar_aging(self) -> Dict[str, Any]:
        """Get AR aging buckets."""
        try:
            # Get total AR
            total_query = f"""
            SELECT SUM(Amount) as total_ar
            FROM {self.schema}.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            total_result = self._execute_query(total_query)
            total_ar = float(total_result[0]['total_ar']) if total_result and total_result[0]['total_ar'] else 0

            # Get aging buckets
            aging_query = f"""
            WITH InvoiceBalances AS (
                SELECT
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM {self.schema}.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT
                CASE
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) < 30 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 30 AND 59 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 60 AND 89 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) >= 90 THEN '90+'
                END as AgingBucket,
                SUM(NetBalance) as TotalAmount
            FROM InvoiceBalances
            GROUP BY
                CASE
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) < 30 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 30 AND 59 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 60 AND 89 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) >= 90 THEN '90+'
                END
            """

            ar_results = self._execute_query(aging_query)

            ar_aging = {
                'current': 0,
                'days_31_60': 0,
                'days_61_90': 0,
                'days_91_plus': 0,
                'total': total_ar
            }

            for row in ar_results:
                bucket = row['AgingBucket']
                amount = float(row['TotalAmount'] or 0)

                if bucket == 'Current':
                    ar_aging['current'] = amount
                elif bucket == '30-60':
                    ar_aging['days_31_60'] = amount
                elif bucket == '60-90':
                    ar_aging['days_61_90'] = amount
                elif bucket == '90+':
                    ar_aging['days_91_plus'] = amount

            return ar_aging

        except Exception as e:
            logger.error(f"Error fetching AR aging: {str(e)}")
            return {}

    # ==========================================
    # Balance Sheet
    # ==========================================

    def _get_balance_sheet_data(self, as_of_date: date) -> Dict[str, Any]:
        """Get balance sheet data as of a specific date."""
        try:
            query = f"""
            SELECT
                -- Cash and equivalents
                -SUM(CASE WHEN AccountNo BETWEEN '100000' AND '109999' THEN Amount ELSE 0 END) as cash,
                -- Accounts Receivable
                -SUM(CASE WHEN AccountNo BETWEEN '110000' AND '119999' THEN Amount ELSE 0 END) as accounts_receivable,
                -- Inventory
                -SUM(CASE WHEN AccountNo BETWEEN '120000' AND '149999' THEN Amount ELSE 0 END) as inventory,
                -- Fixed Assets
                -SUM(CASE WHEN AccountNo BETWEEN '150000' AND '199999' THEN Amount ELSE 0 END) as fixed_assets,
                -- Accounts Payable
                SUM(CASE WHEN AccountNo BETWEEN '200000' AND '209999' THEN Amount ELSE 0 END) as accounts_payable,
                -- Other Current Liabilities
                SUM(CASE WHEN AccountNo BETWEEN '210000' AND '249999' THEN Amount ELSE 0 END) as other_current_liabilities,
                -- Long Term Debt
                SUM(CASE WHEN AccountNo BETWEEN '250000' AND '299999' THEN Amount ELSE 0 END) as long_term_debt,
                -- Equity
                SUM(CASE WHEN AccountNo BETWEEN '300000' AND '399999' THEN Amount ELSE 0 END) as equity
            FROM {self.schema}.GLDetail
            WHERE EffectiveDate <= %s
              AND Posted = 1
            """

            results = self._execute_query(query, (as_of_date,))

            if results:
                row = results[0]
                return {
                    'cash': float(row['cash'] or 0),
                    'accounts_receivable': float(row['accounts_receivable'] or 0),
                    'inventory': float(row['inventory'] or 0),
                    'fixed_assets': float(row['fixed_assets'] or 0),
                    'accounts_payable': float(row['accounts_payable'] or 0),
                    'other_current_liabilities': float(row['other_current_liabilities'] or 0),
                    'long_term_debt': float(row['long_term_debt'] or 0),
                    'equity': float(row['equity'] or 0)
                }

            return {}

        except Exception as e:
            logger.error(f"Error fetching balance sheet: {str(e)}")
            return {}

    # ==========================================
    # Metrics
    # ==========================================

    def get_currie_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Get operational metrics for Currie Financial Model."""
        num_days = (end_date - start_date).days + 1

        metrics = {
            'ar_aging': self._get_ar_aging(),
            'service_calls_per_day': self._get_service_calls_per_day(start_date, end_date, num_days),
            'technician_count': self._get_technician_count(),
            'labor_metrics': self._get_labor_metrics(start_date, end_date),
            'absorption_rate': self._calculate_absorption_rate(start_date, end_date)
        }

        return metrics

    def _get_service_calls_per_day(self, start_date: date, end_date: date, num_days: int) -> Dict[str, Any]:
        """Calculate average service calls per day."""
        try:
            query = f"""
            SELECT COUNT(*) as total_service_calls
            FROM {self.schema}.WO
            WHERE OpenDate >= %s
              AND OpenDate <= %s
              AND SaleDept IN ('40', '45', '47')
            """

            results = self._execute_query(query, (start_date, end_date))
            total_calls = int(results[0]['total_service_calls']) if results else 0
            calls_per_day = total_calls / num_days if num_days > 0 else 0

            return {
                'total_service_calls': total_calls,
                'calls_per_day': round(calls_per_day, 1),
                'num_days': num_days
            }
        except Exception as e:
            logger.error(f"Error getting service calls: {str(e)}")
            return {'total_service_calls': 0, 'calls_per_day': 0, 'num_days': num_days}

    def _get_technician_count(self) -> int:
        """Get current technician headcount."""
        try:
            query = f"""
            SELECT COUNT(*) as tech_count
            FROM {self.schema}.Employee
            WHERE Department IN ('40', '45', '47')
              AND (TerminateDate IS NULL OR TerminateDate > GETDATE())
            """
            results = self._execute_query(query)
            return int(results[0]['tech_count']) if results else 0
        except Exception as e:
            logger.error(f"Error getting technician count: {str(e)}")
            return 0

    def _get_labor_metrics(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get labor productivity metrics."""
        try:
            query = f"""
            SELECT
                SUM(BilledHours) as billed_hours,
                SUM(ActualHours) as actual_hours
            FROM {self.schema}.WOLabor
            WHERE PostDate >= %s AND PostDate <= %s
            """
            results = self._execute_query(query, (start_date, end_date))

            if results and results[0]['billed_hours']:
                billed = float(results[0]['billed_hours'] or 0)
                actual = float(results[0]['actual_hours'] or 0)
                efficiency = (billed / actual * 100) if actual > 0 else 0

                return {
                    'billed_hours': billed,
                    'actual_hours': actual,
                    'efficiency': round(efficiency, 1)
                }

            return {'billed_hours': 0, 'actual_hours': 0, 'efficiency': 0}
        except Exception as e:
            logger.error(f"Error getting labor metrics: {str(e)}")
            return {'billed_hours': 0, 'actual_hours': 0, 'efficiency': 0}

    def _calculate_absorption_rate(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Calculate absorption rate (aftermarket GP / total expenses)."""
        try:
            # Get revenue data
            rental = self._get_rental_revenue(start_date, end_date)
            service = self._get_service_revenue(start_date, end_date)
            parts = self._get_parts_revenue(start_date, end_date)

            # Calculate aftermarket GP
            service_gp = sum(cat.get('gross_profit', 0) for cat in service.values())
            parts_gp = sum(cat.get('gross_profit', 0) for cat in parts.values())
            rental_gp = rental.get('gross_profit', 0)
            total_aftermarket_gp = service_gp + parts_gp + rental_gp

            # Get expenses
            expenses = self._get_gl_expenses(start_date, end_date)
            total_expenses = expenses.get('grand_total', 0)

            absorption_rate = (total_aftermarket_gp / total_expenses * 100) if total_expenses > 0 else 0

            return {
                'rate': round(absorption_rate, 1),
                'aftermarket_gp': round(total_aftermarket_gp, 2),
                'total_expenses': round(total_expenses, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating absorption rate: {str(e)}")
            return {'rate': 0, 'aftermarket_gp': 0, 'total_expenses': 0}

    # ==========================================
    # Base Adapter Interface Methods
    # ==========================================

    def get_department_financials(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Extract financial data by department - wrapper for base interface."""
        model = self.get_currie_financial_model(start_date, end_date)

        results = []
        for dept in ['new_equipment', 'rental', 'service', 'parts', 'trucking']:
            if dept in model:
                if dept == 'new_equipment':
                    # Sum all equipment categories
                    sales = sum(cat.get('sales', 0) for cat in model[dept].values())
                    cogs = sum(cat.get('cogs', 0) for cat in model[dept].values())
                elif dept in ('service', 'parts'):
                    sales = sum(cat.get('sales', 0) for cat in model[dept].values())
                    cogs = sum(cat.get('cogs', 0) for cat in model[dept].values())
                else:
                    sales = model[dept].get('sales', 0)
                    cogs = model[dept].get('cogs', 0)

                results.append({
                    'department': dept,
                    'gross_sales': sales,
                    'discounts': 0,
                    'cost_of_goods_sold': cogs
                })

        return results

    def get_expense_allocations(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Extract expense data - wrapper for base interface."""
        expenses = self._get_gl_expenses(start_date, end_date)

        results = []
        for category in ['personnel', 'operating', 'occupancy']:
            results.append({
                'expense_category': category,
                'department': None,
                'amount': expenses.get(category, {}).get('total', 0),
                'allocation_method': 'pending_allocation'
            })

        return results

    def get_operational_metrics(
        self,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """Extract operational KPIs - wrapper for base interface."""
        metrics = self.get_currie_metrics(start_date, end_date)

        results = []

        # AR Aging
        ar = metrics.get('ar_aging', {})
        for bucket, value in ar.items():
            results.append({
                'metric_name': f'ar_{bucket}',
                'metric_category': 'ar',
                'metric_value': value,
                'metric_unit': 'dollars'
            })

        # Service metrics
        svc = metrics.get('service_calls_per_day', {})
        results.append({
            'metric_name': 'service_calls_per_day',
            'metric_category': 'service',
            'metric_value': svc.get('calls_per_day', 0),
            'metric_unit': 'count'
        })

        results.append({
            'metric_name': 'technician_count',
            'metric_category': 'service',
            'metric_value': metrics.get('technician_count', 0),
            'metric_unit': 'count'
        })

        # Absorption rate
        absorption = metrics.get('absorption_rate', {})
        results.append({
            'metric_name': 'absorption_rate',
            'metric_category': 'financial',
            'metric_value': absorption.get('rate', 0),
            'metric_unit': 'percent'
        })

        return results

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None
        self.connected = False
