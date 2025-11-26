from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from src.services.azure_sql_service import AzureSQLService
from src.services.cache_service import cache_service
from src.utils.fiscal_year import get_fiscal_year_months

logger = logging.getLogger(__name__)

dashboard_optimized_bp = Blueprint('dashboard_optimized', __name__)

# GL Account Mappings by Department (Source: Softbase P&L)
GL_ACCOUNTS = {
    'new_equipment': {
        'dept_code': 10,
        'dept_name': 'New Equipment',
        'revenue': ['410001', '412001', '413001', '414001', '421001', '426001', '431001', '434001'],
        'cogs': ['510001', '513001', '514001', '521001', '525001', '526001', '531001', '534001', '534013', '538000']
    },
    'used_equipment': {
        'dept_code': 20,
        'dept_name': 'Used Equipment',
        'revenue': ['410002', '412002', '413002', '414002', '421002', '426002', '431002', '434002', '436001'],
        'cogs': ['510002', '512002', '513002', '514002', '521002', '525002', '526002', '531002', '534002', '536001']
    },
    'parts': {
        'dept_code': 30,
        'dept_name': 'Parts',
        'revenue': ['410003', '410012', '410014', '410015', '421003', '424000', '429001', '430000', '433000', '434003', '436002', '439000'],
        'cogs': ['510003', '510012', '510013', '510014', '510015', '521003', '522001', '524000', '529002', '530000', '533000', '534003', '536002', '542000', '543000', '544000']
    },
    'service': {
        'dept_code': 40,
        'dept_name': 'Service',
        'revenue': ['410004', '410005', '410007', '410016', '421004', '421005', '421006', '421007', '423000', '425000', '428000', '429002', '432000', '435000', '435001', '435002', '435003', '435004'],
        'cogs': ['510004', '510005', '510007', '512001', '521004', '521005', '521006', '521007', '522000', '523000', '528000', '529001', '534015', '535001', '535002', '535003', '535004', '535005']
    },
    'rental': {
        'dept_code': 60,
        'dept_name': 'Rental',
        'revenue': ['410008', '411001', '419000', '420000', '421000', '434012'],
        'cogs': ['510008', '511001', '519000', '520000', '521008', '534014', '537001', '539000', '545000']
    },
    'transportation': {
        'dept_code': 80,
        'dept_name': 'Transportation',
        'revenue': ['410010', '421010', '434010', '434013'],
        'cogs': ['510010', '521010', '534010', '534012']
    },
    'administrative': {
        'dept_code': 90,
        'dept_name': 'Administrative',
        'revenue': ['410011', '421011', '422100', '427000', '434011'],
        'cogs': ['510011', '521011', '522100', '525000', '527000', '532000', '534011', '540000', '541000']
    }
}

# Other Income/Contra-Revenue Accounts (7xxxxx series)
# Note: 706000 (ADMINISTRATIVE FUND EXPENSE) is NOT included - it's an expense account
OTHER_INCOME_ACCOUNTS = ['701000', '702000', '703000', '704000', '705000']

class DashboardQueries:
    """Encapsulate all dashboard queries for parallel execution"""
    
    def __init__(self, db):
        self.db = db
        self.current_date = datetime.now()
        self.month_start = self.current_date.replace(day=1).strftime('%Y-%m-%d')
        self.thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        self.twelve_months_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        
        # Fiscal year start (November 1st)
        if self.current_date.month >= 11:
            self.fiscal_year_start = datetime(self.current_date.year, 11, 1).strftime('%Y-%m-%d')
        else:
            self.fiscal_year_start = datetime(self.current_date.year - 1, 11, 1).strftime('%Y-%m-%d')
    
    def get_current_month_sales(self):
        """Get current month's total sales using GLDetail (matches Monthly Sales chart)"""
        try:
            # Collect all revenue accounts from all departments
            all_revenue_accounts = []
            for dept in GL_ACCOUNTS.values():
                all_revenue_accounts.extend(dept['revenue'])
            
            # Add Other Income accounts
            all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)
            
            # Format for SQL IN clause
            revenue_list = "', '".join(all_revenue_accounts)
            
            # Get current month's revenue from GLDetail
            query = f"""
            SELECT -SUM(Amount) as total_sales
            FROM ben002.GLDetail
            WHERE AccountNo IN ('{revenue_list}')
                AND MONTH(EffectiveDate) = {self.current_date.month}
                AND YEAR(EffectiveDate) = {self.current_date.year}
                AND Posted = 1
            """
            result = self.db.execute_query(query)
            return int(float(result[0]['total_sales'] or 0)) if result else 0
        except Exception as e:
            logger.error(f"Current month sales query failed: {str(e)}")
            return 0
    
    
    def get_ytd_sales(self):
        """Get fiscal year-to-date sales using GLDetail (matches Monthly Sales chart)"""
        try:
            # Collect all revenue accounts from all departments
            all_revenue_accounts = []
            for dept in GL_ACCOUNTS.values():
                all_revenue_accounts.extend(dept['revenue'])
            
            # Add Other Income accounts
            all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)
            
            # Format for SQL IN clause
            revenue_list = "', '".join(all_revenue_accounts)
            
            # Get YTD revenue from GLDetail
            query = f"""
            SELECT -SUM(Amount) as ytd_sales
            FROM ben002.GLDetail
            WHERE AccountNo IN ('{revenue_list}')
                AND EffectiveDate >= '{self.fiscal_year_start}'
                AND EffectiveDate < DATEADD(DAY, 1, GETDATE())
                AND Posted = 1
            """
            result = self.db.execute_query(query)
            return int(float(result[0]['ytd_sales'] or 0)) if result else 0
        except Exception as e:
            logger.error(f"YTD sales query failed: {str(e)}")
            return 0
    
    def get_inventory_count(self):
        """Get count of equipment ready to rent"""
        try:
            query = """
            SELECT COUNT(*) as inventory_count
            FROM ben002.Equipment
            WHERE RentalStatus = 'Ready To Rent'
            """
            result = self.db.execute_query(query)
            return int(result[0]['inventory_count']) if result else 0
        except Exception as e:
            logger.error(f"Inventory query failed: {str(e)}")
            return 0
    
    def get_active_customers(self):
        """Get count of active customers in last 30 days with previous month comparison"""
        try:
            # Calculate previous month period
            sixty_days_ago = (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d')
            
            query = f"""
            SELECT 
                COUNT(DISTINCT CASE 
                    WHEN InvoiceDate >= '{self.thirty_days_ago}' 
                    THEN CASE 
                        WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                        WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                        ELSE BillToName
                    END
                    ELSE NULL 
                END) as active_customers,
                COUNT(DISTINCT CASE 
                    WHEN InvoiceDate >= '{sixty_days_ago}' AND InvoiceDate < '{self.thirty_days_ago}' 
                    THEN CASE 
                        WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                        WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                        ELSE BillToName
                    END
                    ELSE NULL 
                END) as previous_month_customers
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{sixty_days_ago}'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            AND BillToName NOT LIKE '%Wells Fargo%'
            AND BillToName NOT LIKE '%Maintenance contract%'
            AND BillToName NOT LIKE '%Rental Fleet%'
            """
            result = self.db.execute_query(query)
            if result:
                current = int(result[0]['active_customers'])
                previous = int(result[0]['previous_month_customers'])
                return {
                    'current': current,
                    'previous': previous,
                    'change': current - previous,
                    'change_percent': ((current - previous) / previous * 100) if previous > 0 else 0
                }
            return {'current': 0, 'previous': 0, 'change': 0, 'change_percent': 0}
        except Exception as e:
            logger.error(f"Active customers query failed: {str(e)}")
            return {'current': 0, 'previous': 0, 'change': 0, 'change_percent': 0}
    
    def get_total_customers(self):
        """Get total number of customers in the system"""
        try:
            # First try without WHERE clause to see if we get any customers
            query = """
            SELECT COUNT(*) as total_customers
            FROM ben002.Customer
            """
            result = self.db.execute_query(query)
            return int(result[0]['total_customers']) if result else 0
        except Exception as e:
            logger.error(f"Total customers query failed: {str(e)}")
            # If Customer table doesn't exist, try counting unique customers from invoices
            try:
                query = """
                SELECT COUNT(DISTINCT CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END) as total_customers
                FROM ben002.InvoiceReg
                WHERE BillToName IS NOT NULL
                AND BillToName != ''
                AND BillToName NOT LIKE '%Wells Fargo%'
                AND BillToName NOT LIKE '%Maintenance contract%'
                AND BillToName NOT LIKE '%Rental Fleet%'
                """
                result = self.db.execute_query(query)
                return int(result[0]['total_customers']) if result else 0
            except Exception as e2:
                logger.error(f"Fallback total customers query failed: {str(e2)}")
                return 0
    
    def get_monthly_sales(self):
        """Get monthly sales with trailing 13 months using GLDetail (All Departments)"""
        try:
            # Collect all revenue and cost accounts from all departments
            all_revenue_accounts = []
            all_cost_accounts = []
            
            for dept in GL_ACCOUNTS.values():
                all_revenue_accounts.extend(dept['revenue'])
                all_cost_accounts.extend(dept['cogs'])
            
            # Add Other Income accounts to revenue
            all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)
            
            # Format for SQL IN clause
            revenue_list = "', '".join(all_revenue_accounts)
            cost_list = "', '".join(all_cost_accounts)
            all_accounts_list = "', '".join(all_revenue_accounts + all_cost_accounts)
            
            query = f"""
            SELECT 
                YEAR(EffectiveDate) as year,
                MONTH(EffectiveDate) as month,
                -- Revenue (Credit accounts, so negate sum)
                -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as total_revenue,
                -- Cost (Debit accounts, so positive sum)
                SUM(CASE WHEN AccountNo IN ('{cost_list}') THEN Amount ELSE 0 END) as total_cost
            FROM ben002.GLDetail
            WHERE AccountNo IN ('{all_accounts_list}')
                AND EffectiveDate >= DATEADD(month, -13, GETDATE())
                AND Posted = 1
            GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            """
            
            results = self.db.execute_query(query)
            
            # Create a dictionary to store data by year-month key
            revenue_by_month = {}
            for row in results:
                year_month_key = (row['year'], row['month'])
                revenue_by_month[year_month_key] = row
            
            # Get fiscal year months (trailing 13 months)
            fiscal_year_months = get_fiscal_year_months()
            
            monthly_sales = []
            for year, month in fiscal_year_months:
                month_date = datetime(year, month, 1)
                # Include year in label if spanning multiple calendar years
                if fiscal_year_months[0][0] != fiscal_year_months[-1][0]:
                    month_str = month_date.strftime("%b '%y")
                else:
                    month_str = month_date.strftime("%b")
                
                year_month_key = (year, month)
                prior_year_key = (year - 1, month)
                
                # Get current year data
                row = revenue_by_month.get(year_month_key)
                prior_row = revenue_by_month.get(prior_year_key)
                
                if row:
                    total_revenue = float(row['total_revenue'] or 0)
                    total_cost = float(row['total_cost'] or 0)
                    
                    # Calculate gross margin percentage
                    margin = None
                    if total_revenue > 0:
                        margin = round(((total_revenue - total_cost) / total_revenue) * 100, 1)
                else:
                    total_revenue = 0
                    margin = None
                
                # Get prior year data for comparison
                prior_total = 0
                prior_margin = None
                if prior_row:
                    prior_total = float(prior_row['total_revenue'] or 0)
                    prior_cost = float(prior_row['total_cost'] or 0)
                    if prior_total > 0:
                        prior_margin = round(((prior_total - prior_cost) / prior_total) * 100, 1)

                monthly_sales.append({
                    'month': month_str,
                    'year': year,
                    'amount': total_revenue,
                    'margin': margin,
                    'prior_year_amount': prior_total,
                    'prior_year_margin': prior_margin
                })
            
            return monthly_sales
        except Exception as e:
            logger.error(f"Monthly sales query failed: {str(e)}")
            return []
    
    def get_monthly_sales_excluding_equipment(self):
        """Get monthly sales with trailing 13 months excluding equipment (Service + Parts + Rental + Trans + Admin + Other)"""
        try:
            # Collect all revenue and cost accounts from non-equipment departments
            all_revenue_accounts = []
            all_cost_accounts = []
            
            # Departments to include
            include_depts = ['service', 'parts', 'rental', 'transportation', 'administrative']
            
            for dept_key in include_depts:
                if dept_key in GL_ACCOUNTS:
                    dept = GL_ACCOUNTS[dept_key]
                    all_revenue_accounts.extend(dept['revenue'])
                    all_cost_accounts.extend(dept['cogs'])
            
            # Add Other Income accounts to revenue
            all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)
            
            # Format for SQL IN clause
            revenue_list = "', '".join(all_revenue_accounts)
            cost_list = "', '".join(all_cost_accounts)
            all_accounts_list = "', '".join(all_revenue_accounts + all_cost_accounts)
            
            query = f"""
            SELECT 
                YEAR(EffectiveDate) as year,
                MONTH(EffectiveDate) as month,
                -- Revenue (Credit accounts, so negate sum)
                -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as total_revenue,
                -- Cost (Debit accounts, so positive sum)
                SUM(CASE WHEN AccountNo IN ('{cost_list}') THEN Amount ELSE 0 END) as total_cost
            FROM ben002.GLDetail
            WHERE AccountNo IN ('{all_accounts_list}')
                AND EffectiveDate >= DATEADD(month, -13, GETDATE())
                AND Posted = 1
            GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            """
            
            results = self.db.execute_query(query)
            
            # Create a dictionary to store data by year-month key
            revenue_by_month = {}
            for row in results:
                year_month_key = (row['year'], row['month'])
                revenue_by_month[year_month_key] = row
            
            # Get fiscal year months (trailing 13 months)
            fiscal_year_months = get_fiscal_year_months()
            
            monthly_sales = []
            for year, month in fiscal_year_months:
                month_date = datetime(year, month, 1)
                # Include year in label if spanning multiple calendar years
                if fiscal_year_months[0][0] != fiscal_year_months[-1][0]:
                    month_str = month_date.strftime("%b '%y")
                else:
                    month_str = month_date.strftime("%b")
                
                year_month_key = (year, month)
                prior_year_key = (year - 1, month)
                
                # Get current year data
                row = revenue_by_month.get(year_month_key)
                prior_row = revenue_by_month.get(prior_year_key)
                
                if row:
                    total_revenue = float(row['total_revenue'] or 0)
                    total_cost = float(row['total_cost'] or 0)
                    
                    # Calculate gross margin percentage
                    margin = None
                    if total_revenue > 0:
                        margin = round(((total_revenue - total_cost) / total_revenue) * 100, 1)
                else:
                    total_revenue = 0
                    margin = None
                
                # Get prior year data for comparison
                prior_total = 0
                prior_margin = None
                if prior_row:
                    prior_total = float(prior_row['total_revenue'] or 0)
                    prior_cost = float(prior_row['total_cost'] or 0)
                    if prior_total > 0:
                        prior_margin = round(((prior_total - prior_cost) / prior_total) * 100, 1)

                monthly_sales.append({
                    'month': month_str,
                    'year': year,
                    'amount': total_revenue,
                    'margin': margin,
                    'prior_year_amount': prior_total,
                    'prior_year_margin': prior_margin
                })

            return monthly_sales
        except Exception as e:
            logger.error(f"Monthly sales excluding equipment query failed: {str(e)}")
            return []
    
    def get_monthly_sales_by_stream(self):
        """Get monthly sales by revenue stream with trailing 13 months using GLDetail"""
        try:
            # Get account lists from GL_ACCOUNTS
            service_rev = GL_ACCOUNTS['service']['revenue']
            service_cost = GL_ACCOUNTS['service']['cogs']
            
            parts_rev = GL_ACCOUNTS['parts']['revenue']
            parts_cost = GL_ACCOUNTS['parts']['cogs']
            
            rental_rev = GL_ACCOUNTS['rental']['revenue']
            rental_cost = GL_ACCOUNTS['rental']['cogs']
            
            # Format for SQL IN clause
            service_rev_list = "', '".join(service_rev)
            service_cost_list = "', '".join(service_cost)
            
            parts_rev_list = "', '".join(parts_rev)
            parts_cost_list = "', '".join(parts_cost)
            
            rental_rev_list = "', '".join(rental_rev)
            rental_cost_list = "', '".join(rental_cost)
            
            all_accounts = service_rev + service_cost + parts_rev + parts_cost + rental_rev + rental_cost
            all_accounts_list = "', '".join(all_accounts)
            
            query = f"""
            SELECT 
                YEAR(EffectiveDate) as year,
                MONTH(EffectiveDate) as month,
                -- Service (Labor) Revenue and Cost
                -SUM(CASE WHEN AccountNo IN ('{service_rev_list}') THEN Amount ELSE 0 END) as labor_revenue,
                SUM(CASE WHEN AccountNo IN ('{service_cost_list}') THEN Amount ELSE 0 END) as labor_cost,
                -- Parts Revenue and Cost
                -SUM(CASE WHEN AccountNo IN ('{parts_rev_list}') THEN Amount ELSE 0 END) as parts_revenue,
                SUM(CASE WHEN AccountNo IN ('{parts_cost_list}') THEN Amount ELSE 0 END) as parts_cost,
                -- Rental Revenue and Cost
                -SUM(CASE WHEN AccountNo IN ('{rental_rev_list}') THEN Amount ELSE 0 END) as rental_revenue,
                SUM(CASE WHEN AccountNo IN ('{rental_cost_list}') THEN Amount ELSE 0 END) as rental_cost
            FROM ben002.GLDetail
            WHERE AccountNo IN ('{all_accounts_list}')
                AND EffectiveDate >= DATEADD(month, -13, GETDATE())
                AND Posted = 1
            GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            """
            
            results = self.db.execute_query(query)
            
            # Create a dictionary to store data by year-month key
            revenue_by_month = {}
            for row in results:
                year_month_key = (row['year'], row['month'])
                revenue_by_month[year_month_key] = row
            
            # Get fiscal year months (trailing 13 months)
            fiscal_year_months = get_fiscal_year_months()
            
            monthly_data = []
            for year, month in fiscal_year_months:
                month_date = datetime(year, month, 1)
                # Include year in label if spanning multiple calendar years
                if fiscal_year_months[0][0] != fiscal_year_months[-1][0]:
                    month_str = month_date.strftime("%b '%y")
                else:
                    month_str = month_date.strftime("%b")
                
                year_month_key = (year, month)
                prior_year_key = (year - 1, month)
                
                # Get current year data
                row = revenue_by_month.get(year_month_key)
                prior_row = revenue_by_month.get(prior_year_key)
                
                if row:
                    # Calculate margins for each department
                    parts_revenue = float(row['parts_revenue'] or 0)
                    parts_cost = float(row['parts_cost'] or 0)
                    parts_margin = round(((parts_revenue - parts_cost) / parts_revenue) * 100, 1) if parts_revenue > 0 else None
                    
                    labor_revenue = float(row['labor_revenue'] or 0)
                    labor_cost = float(row['labor_cost'] or 0)
                    labor_margin = round(((labor_revenue - labor_cost) / labor_revenue) * 100, 1) if labor_revenue > 0 else None
                    
                    rental_revenue = float(row['rental_revenue'] or 0)
                    rental_cost = float(row['rental_cost'] or 0)
                    rental_margin = round(((rental_revenue - rental_cost) / rental_revenue) * 100, 1) if rental_revenue > 0 else None
                else:
                    parts_revenue = 0
                    parts_margin = None
                    labor_revenue = 0
                    labor_margin = None
                    rental_revenue = 0
                    rental_margin = None
                
                # Get prior year data for comparison
                if prior_row:
                    prior_parts = float(prior_row['parts_revenue'] or 0)
                    prior_labor = float(prior_row['labor_revenue'] or 0)
                    prior_rental = float(prior_row['rental_revenue'] or 0)
                else:
                    prior_parts = 0
                    prior_labor = 0
                    prior_rental = 0
                
                monthly_data.append({
                    'month': month_str,
                    'year': year,
                    'parts': parts_revenue,
                    'labor': labor_revenue,
                    'rental': rental_revenue,
                    'parts_margin': parts_margin,
                    'labor_margin': labor_margin,
                    'rental_margin': rental_margin,
                    # Prior year comparison
                    'prior_parts': prior_parts,
                    'prior_labor': prior_labor,
                    'prior_rental': prior_rental
                })
            
            return monthly_data
        except Exception as e:
            logger.error(f"Monthly sales by stream query failed: {str(e)}")
            return []
    
    def get_uninvoiced_work_orders(self):
        """Get uninvoiced work orders value and count"""
        try:
            # Try WO table approach with a single optimized query
            query = """
            SELECT 
                COUNT(*) as count,
                COALESCE(SUM(
                    COALESCE(l.labor_total, 0) + 
                    COALESCE(p.parts_total, 0) + 
                    COALESCE(m.misc_total, 0)
                ), 0) as total_value
            FROM ben002.WO w
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as labor_total 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ) l ON w.WONo = l.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell * Qty) as parts_total 
                FROM ben002.WOParts 
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_total 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            WHERE w.CompletedDate IS NOT NULL
            AND w.InvoiceDate IS NULL
            """
            
            result = self.db.execute_query(query)
            if result:
                return {
                    'value': float(result[0]['total_value']),
                    'count': int(result[0]['count'])
                }
            return {'value': 0, 'count': 0}
        except Exception as e:
            logger.error(f"Uninvoiced work orders query failed: {str(e)}")
            # Fallback to simple count
            try:
                simple_query = """
                SELECT COUNT(*) as count
                FROM ben002.WO
                WHERE CompletedDate IS NOT NULL
                AND InvoiceDate IS NULL
                """
                result = self.db.execute_query(simple_query)
                count = int(result[0]['count']) if result else 0
                return {'value': count * 500, 'count': count}  # Estimate value
            except:
                return {'value': 0, 'count': 0}
    
    def get_monthly_equipment_sales(self):
        """Get monthly Linde new truck sales with trailing 13 months using GLDetail (GL account 413001) and unit counts"""
        try:
            # 1. Get Revenue/Cost from GLDetail
            # Use GLDetail for Linde new truck sales only (GL account 413001 revenue, 513001 cost)
            gl_query = """
            SELECT 
                YEAR(EffectiveDate) as year,
                MONTH(EffectiveDate) as month,
                ABS(SUM(CASE WHEN AccountNo = '413001' THEN Amount ELSE 0 END)) as equipment_revenue,
                ABS(SUM(CASE WHEN AccountNo = '513001' THEN Amount ELSE 0 END)) as equipment_cost
            FROM ben002.GLDetail
            WHERE AccountNo IN ('413001', '513001')  -- Linde new truck sales only
                AND EffectiveDate >= DATEADD(month, -13, GETDATE())
                AND Posted = 1
            GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            """
            
            gl_results = self.db.execute_query(gl_query)
            
            # 2. Get Unit Counts from InvoiceReg
            # Count invoices with SaleCode LINDEN only (per user request)
            unit_query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                COUNT(*) as unit_count
            FROM ben002.InvoiceReg
            WHERE SaleCode = 'LINDEN'
                AND InvoiceDate >= DATEADD(month, -13, GETDATE())
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            unit_results = self.db.execute_query(unit_query)
            
            # Create dictionaries for easy lookup
            revenue_by_month = {}
            for row in gl_results:
                year_month_key = (row['year'], row['month'])
                revenue_by_month[year_month_key] = row
                
            units_by_month = {}
            for row in unit_results:
                year_month_key = (row['year'], row['month'])
                units_by_month[year_month_key] = row['unit_count']
            
            # Get fiscal year months (trailing 13 months)
            fiscal_year_months = get_fiscal_year_months()
            
            monthly_sales = []
            for year, month in fiscal_year_months:
                month_date = datetime(year, month, 1)
                # Include year in label if spanning multiple calendar years
                if fiscal_year_months[0][0] != fiscal_year_months[-1][0]:
                    month_str = month_date.strftime("%b '%y")
                else:
                    month_str = month_date.strftime("%b")
                
                year_month_key = (year, month)
                prior_year_key = (year - 1, month)
                
                # Get current year data
                row = revenue_by_month.get(year_month_key)
                prior_row = revenue_by_month.get(prior_year_key)
                unit_count = units_by_month.get(year_month_key, 0)
                
                if row:
                    revenue = float(row['equipment_revenue'] or 0)
                    cost = float(row['equipment_cost'] or 0)
                    
                    # Calculate gross margin percentage
                    margin = None
                    if revenue > 0:
                        margin = round(((revenue - cost) / revenue) * 100, 1)
                else:
                    revenue = 0
                    margin = None
                
                # Get prior year data for comparison
                prior_revenue = 0
                prior_margin = None
                if prior_row:
                    prior_revenue = float(prior_row['equipment_revenue'] or 0)
                    prior_cost = float(prior_row['equipment_cost'] or 0)
                    if prior_revenue > 0:
                        prior_margin = round(((prior_revenue - prior_cost) / prior_revenue) * 100, 1)

                monthly_sales.append({
                    'month': month_str,
                    'month_number': month,
                    'year': year,
                    'amount': revenue,
                    'margin': margin,
                    'prior_year_amount': prior_revenue,
                    'prior_year_margin': prior_margin,
                    'unit_count': unit_count
                })
            
            return monthly_sales
        except Exception as e:
            logger.error(f"Monthly equipment sales query failed: {str(e)}")
            return []
    
    def get_monthly_quotes(self):
        """Get monthly quotes since March - latest quote per work order"""
        try:
            # Use only the latest quote per WO per month
            query = """
            WITH LatestQuotes AS (
                -- First, get the latest quote date for each WO per month
                SELECT 
                    YEAR(CreationTime) as year,
                    MONTH(CreationTime) as month,
                    WONo,
                    MAX(CAST(CreationTime AS DATE)) as latest_quote_date
                FROM ben002.WOQuote
                WHERE CreationTime >= '2025-03-01'
                AND Amount > 0
                GROUP BY YEAR(CreationTime), MONTH(CreationTime), WONo
            ),
            QuoteTotals AS (
                -- Then sum all line items for each WO on its latest quote date
                SELECT 
                    lq.year,
                    lq.month,
                    lq.WONo,
                    SUM(wq.Amount) as wo_total
                FROM LatestQuotes lq
                INNER JOIN ben002.WOQuote wq
                    ON lq.WONo = wq.WONo
                    AND lq.year = YEAR(wq.CreationTime)
                    AND lq.month = MONTH(wq.CreationTime)
                    AND CAST(wq.CreationTime AS DATE) = lq.latest_quote_date
                WHERE wq.Amount > 0
                GROUP BY lq.year, lq.month, lq.WONo
            )
            SELECT 
                year,
                month,
                SUM(wo_total) as amount
            FROM QuoteTotals
            GROUP BY year, month
            ORDER BY year, month
            """
            
            results = self.db.execute_query(query)
            monthly_quotes = []
            
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_quotes.append({
                        'month': month_date.strftime("%b"),
                        'year': row['year'],
                        'amount': float(row['amount'])
                    })
            
            # Pad missing months
            start_date = datetime(2025, 3, 1)
            all_months = []
            date = start_date
            while date <= self.current_date:
                all_months.append({'month': date.strftime("%b"), 'year': date.year})
                if date.month == 12:
                    date = date.replace(year=date.year + 1, month=1)
                else:
                    date = date.replace(month=date.month + 1)
            
            existing_quotes = {f"{item['year']}-{item['month']}": item for item in monthly_quotes}
            monthly_quotes = []
            for month_info in all_months:
                key = f"{month_info['year']}-{month_info['month']}"
                if key in existing_quotes:
                    monthly_quotes.append(existing_quotes[key])
                else:
                    monthly_quotes.append({
                        'month': month_info['month'],
                        'year': month_info['year'],
                        'amount': 0
                    })
            
            return monthly_quotes
        except Exception as e:
            logger.error(f"Monthly quotes query failed: {str(e)}")
            return []
    
    def get_work_order_types(self):
        """Get work order types breakdown with month-over-month comparison"""
        try:
            # Calculate previous month END date for proper comparison
            current_date = datetime.now()
            # Get first day of current month
            first_of_month = current_date.replace(day=1)
            # Get last day of previous month
            previous_month_end = first_of_month - timedelta(days=1)
            previous_month_end_str = previous_month_end.strftime('%Y-%m-%d')
            
            # Current open work orders query - OPTIMIZED with CTEs
            query = """
            WITH LaborTotals AS (
                SELECT WONo, SUM(Sell) as labor_total 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ),
            PartsTotals AS (
                SELECT WONo, SUM(Sell * Qty) as parts_total 
                FROM ben002.WOParts 
                GROUP BY WONo
            ),
            MiscTotals AS (
                SELECT WONo, SUM(Sell) as misc_total 
                FROM ben002.WOMisc 
                GROUP BY WONo
            )
            SELECT 
                CASE 
                    WHEN w.Type = 'S' THEN 'Service'
                    WHEN w.Type = 'R' THEN 'Rental'
                    WHEN w.Type = 'P' THEN 'Parts'
                    WHEN w.Type = 'PM' THEN 'Preventive Maintenance'
                    WHEN w.Type = 'SH' THEN 'Shop'
                    WHEN w.Type = 'E' THEN 'Equipment'
                    WHEN w.Type IS NULL THEN 'Unspecified'
                    ELSE w.Type
                END as type_name,
                COUNT(*) as count,
                SUM(
                    COALESCE(l.labor_total, 0) + 
                    COALESCE(p.parts_total, 0) + 
                    COALESCE(m.misc_total, 0)
                ) as total_value
            FROM ben002.WO w
            LEFT JOIN LaborTotals l ON w.WONo = l.WONo
            LEFT JOIN PartsTotals p ON w.WONo = p.WONo
            LEFT JOIN MiscTotals m ON w.WONo = m.WONo
            WHERE w.CompletedDate IS NULL
            AND w.ClosedDate IS NULL
            GROUP BY w.Type
            ORDER BY total_value DESC
            """
            
            # Previous month open work orders value query - OPTIMIZED with CTEs
            previous_query = f"""
            WITH LaborTotals AS (
                SELECT WONo, SUM(Sell) as labor_total 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ),
            PartsTotals AS (
                SELECT WONo, SUM(Sell * Qty) as parts_total 
                FROM ben002.WOParts 
                GROUP BY WONo
            ),
            MiscTotals AS (
                SELECT WONo, SUM(Sell) as misc_total 
                FROM ben002.WOMisc 
                GROUP BY WONo
            )
            SELECT SUM(
                COALESCE(l.labor_total, 0) + 
                COALESCE(p.parts_total, 0) + 
                COALESCE(m.misc_total, 0)
            ) as previous_total_value
            FROM ben002.WO w
            LEFT JOIN LaborTotals l ON w.WONo = l.WONo
            LEFT JOIN PartsTotals p ON w.WONo = p.WONo
            LEFT JOIN MiscTotals m ON w.WONo = m.WONo
            WHERE w.OpenDate <= '{previous_month_end_str}'
            AND (w.CompletedDate IS NULL OR w.CompletedDate > '{previous_month_end_str}')
            AND (w.ClosedDate IS NULL OR w.ClosedDate > '{previous_month_end_str}')
            """
            
            results = self.db.execute_query(query)
            work_order_types = []
            total_value = 0
            total_count = 0
            
            if results:
                for row in results:
                    work_order_types.append({
                        'type': row['type_name'],
                        'count': int(row['count']),
                        'value': float(row['total_value'])
                    })
                    total_value += float(row['total_value'])
                    total_count += int(row['count'])
            
            # Get previous month value
            previous_result = self.db.execute_query(previous_query)
            previous_value = 0
            if previous_result and previous_result[0]['previous_total_value']:
                previous_value = float(previous_result[0]['previous_total_value'])
            
            # Calculate change
            change = total_value - previous_value
            change_percent = ((total_value - previous_value) / previous_value * 100) if previous_value > 0 else 0
            
            # Debug logging
            logger.info(f"Open WO Debug - Current: ${total_value:,.0f}, Previous (end of {previous_month_end.strftime('%B')}): ${previous_value:,.0f}, Change: ${change:,.0f} ({change_percent:.1f}%)")
            
            return {
                'types': work_order_types,
                'total_value': total_value,
                'total_count': total_count,
                'previous_value': previous_value,
                'change': change,
                'change_percent': change_percent
            }
        except Exception as e:
            logger.error(f"Work order types query failed: {str(e)}")
            return {'types': [], 'total_value': 0, 'total_count': 0, 'previous_value': 0, 'change': 0, 'change_percent': 0}
    
    def get_awaiting_invoice_work_orders(self):
        """Get completed SERVICE, SHOP, and PM work orders awaiting invoice"""
        try:
            query = """
            WITH LaborTotals AS (
                SELECT WONo, SUM(Sell) as labor_sell 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ),
            LaborQuotes AS (
                SELECT WONo, SUM(Amount) as quote_amount 
                FROM ben002.WOQuote 
                WHERE Type = 'L'
                GROUP BY WONo
            ),
            PartsTotals AS (
                SELECT WONo, SUM(Sell * Qty) as parts_sell 
                FROM ben002.WOParts 
                GROUP BY WONo
            ),
            MiscTotals AS (
                SELECT WONo, SUM(Sell) as misc_sell 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ),
            CompletedWOs AS (
                SELECT 
                    w.WONo,
                    w.Type,
                    w.CompletedDate,
                    w.BillTo,
                    DATEDIFF(day, w.CompletedDate, GETDATE()) as DaysSinceCompleted,
                    COALESCE(l.labor_sell, 0) + COALESCE(lq.quote_amount, 0) as labor_total,
                    COALESCE(p.parts_sell, 0) as parts_total,
                    COALESCE(m.misc_sell, 0) as misc_total
                FROM ben002.WO w
                LEFT JOIN LaborTotals l ON w.WONo = l.WONo
                LEFT JOIN LaborQuotes lq ON w.WONo = lq.WONo
                LEFT JOIN PartsTotals p ON w.WONo = p.WONo
                LEFT JOIN MiscTotals m ON w.WONo = m.WONo
                LEFT JOIN ben002.Customer c ON w.BillTo = c.Number
                WHERE w.CompletedDate IS NOT NULL
                  AND w.ClosedDate IS NULL
                  AND w.InvoiceDate IS NULL
                  AND w.DeletionTime IS NULL
                  AND w.Type IN ('S', 'SH', 'PM')  -- Service, Shop, and PM work orders
                  AND c.Name NOT IN (
                    'NEW EQUIP PREP - EXPENSE',
                    'RENTAL FLEET - EXPENSE', 
                    'USED EQUIP. PREP-EXPENSE',
                    'SVC REWORK/SVC WARRANTY',
                    'NEW EQ. INTNL RNTL/DEMO'
                  )  -- Exclude internal expense accounts
            )
            SELECT 
                COUNT(*) as count,
                SUM(labor_total + parts_total + misc_total) as total_value,
                AVG(DaysSinceCompleted) as avg_days_waiting,
                COUNT(CASE WHEN DaysSinceCompleted > 3 THEN 1 END) as over_three_days,
                COUNT(CASE WHEN DaysSinceCompleted > 5 THEN 1 END) as over_five_days,
                COUNT(CASE WHEN DaysSinceCompleted > 7 THEN 1 END) as over_seven_days
            FROM CompletedWOs
            """
            
            result = self.db.execute_query(query)
            
            if result and result[0]['count']:
                return {
                    'count': int(result[0]['count']) if result[0]['count'] else 0,
                    'total_value': float(result[0]['total_value']) if result[0]['total_value'] else 0,
                    'avg_days_waiting': float(result[0]['avg_days_waiting']) if result[0]['avg_days_waiting'] else 0,
                    'over_three_days': int(result[0]['over_three_days']) if result[0]['over_three_days'] else 0,
                    'over_five_days': int(result[0]['over_five_days']) if result[0]['over_five_days'] else 0,
                    'over_seven_days': int(result[0]['over_seven_days']) if result[0]['over_seven_days'] else 0
                }
            else:
                return {
                    'count': 0,
                    'total_value': 0,
                    'avg_days_waiting': 0,
                    'over_three_days': 0,
                    'over_five_days': 0,
                    'over_seven_days': 0
                }
        except Exception as e:
            logger.error(f"Awaiting invoice work orders query failed: {str(e)}")
            return {
                'count': 0,
                'total_value': 0,
                'avg_days_waiting': 0,
                'over_three_days': 0,
                'over_five_days': 0,
                'over_seven_days': 0
            }
    
    def get_open_parts_work_orders(self):
        """Get open PARTS work orders (not yet invoiced)"""
        try:
            query = """
            WITH OpenPartsWOs AS (
                SELECT 
                    w.WONo,
                    w.OpenDate,
                    DATEDIFF(day, w.OpenDate, GETDATE()) as DaysSinceOpened,
                    COALESCE(p.parts_total, 0) as parts_total,
                    COALESCE(m.misc_total, 0) as misc_total
                FROM ben002.WO w
                LEFT JOIN (
                    SELECT WONo, SUM(Sell * Qty) as parts_total 
                    FROM ben002.WOParts 
                    GROUP BY WONo
                ) p ON w.WONo = p.WONo
                LEFT JOIN (
                    SELECT WONo, SUM(Sell) as misc_total 
                    FROM ben002.WOMisc 
                    GROUP BY WONo
                ) m ON w.WONo = m.WONo
                WHERE w.ClosedDate IS NULL
                  AND w.DeletionTime IS NULL
                  AND w.Type = 'P'  -- Parts work orders only
                  AND w.WONo NOT LIKE '91%'  -- Exclude quotes (quotes start with 91)
            )
            SELECT 
                COUNT(*) as count,
                SUM(parts_total + misc_total) as total_value,
                AVG(DaysSinceOpened) as avg_days_open
            FROM OpenPartsWOs
            """
            
            result = self.db.execute_query(query)
            
            if result and result[0]['count']:
                return {
                    'count': int(result[0]['count']) if result[0]['count'] else 0,
                    'total_value': float(result[0]['total_value']) if result[0]['total_value'] else 0,
                    'avg_days_open': float(result[0]['avg_days_open']) if result[0]['avg_days_open'] else 0
                }
            
            return {
                'count': 0,
                'total_value': 0,
                'avg_days_open': 0
            }
            
        except Exception as e:
            self.logger.error(f"Error in get_open_parts_work_orders: {str(e)}")
            return {
                'count': 0,
                'total_value': 0,
                'avg_days_open': 0
            }
    
    def get_parts_awaiting_invoice_work_orders(self):
        """Get completed PARTS work orders awaiting invoice"""
        try:
            query = """
            WITH CompletedWOs AS (
                SELECT 
                    w.WONo,
                    w.Type,
                    w.CompletedDate,
                    w.BillTo,
                    DATEDIFF(day, w.CompletedDate, GETDATE()) as DaysSinceCompleted,
                    COALESCE(p.parts_sell, 0) as parts_total,
                    COALESCE(m.misc_sell, 0) as misc_total
                FROM ben002.WO w
                LEFT JOIN (
                    SELECT WONo, SUM(Sell * Qty) as parts_sell 
                    FROM ben002.WOParts 
                    GROUP BY WONo
                ) p ON w.WONo = p.WONo
                LEFT JOIN (
                    SELECT WONo, SUM(Sell) as misc_sell 
                    FROM ben002.WOMisc 
                    GROUP BY WONo
                ) m ON w.WONo = m.WONo
                WHERE w.CompletedDate IS NOT NULL
                  AND w.ClosedDate IS NULL
                  AND w.InvoiceDate IS NULL
                  AND w.DeletionTime IS NULL
                  AND w.Type = 'P'  -- Parts work orders only
                  AND w.WONo NOT LIKE '91%'  -- Exclude quotes (quotes start with 91)
            )
            SELECT 
                COUNT(*) as count,
                SUM(parts_total + misc_total) as total_value,
                AVG(DaysSinceCompleted) as avg_days_waiting,
                COUNT(CASE WHEN DaysSinceCompleted > 3 THEN 1 END) as over_three_days,
                COUNT(CASE WHEN DaysSinceCompleted > 5 THEN 1 END) as over_five_days,
                COUNT(CASE WHEN DaysSinceCompleted > 7 THEN 1 END) as over_seven_days
            FROM CompletedWOs
            """
            
            result = self.db.execute_query(query)
            
            if result and result[0]['count']:
                return {
                    'count': int(result[0]['count']) if result[0]['count'] else 0,
                    'total_value': float(result[0]['total_value']) if result[0]['total_value'] else 0,
                    'avg_days_waiting': float(result[0]['avg_days_waiting']) if result[0]['avg_days_waiting'] else 0,
                    'over_three_days': int(result[0]['over_three_days']) if result[0]['over_three_days'] else 0,
                    'over_five_days': int(result[0]['over_five_days']) if result[0]['over_five_days'] else 0,
                    'over_seven_days': int(result[0]['over_seven_days']) if result[0]['over_seven_days'] else 0
                }
            else:
                return {
                    'count': 0,
                    'total_value': 0,
                    'avg_days_waiting': 0,
                    'over_three_days': 0,
                    'over_five_days': 0,
                    'over_seven_days': 0
                }
        except Exception as e:
            logger.error(f"Parts awaiting invoice work orders query failed: {str(e)}")
            return {
                'count': 0,
                'total_value': 0,
                'avg_days_waiting': 0,
                'over_three_days': 0,
                'over_five_days': 0,
                'over_seven_days': 0
            }
    
    def get_monthly_invoice_delay_avg(self):
        """Get average days waiting for invoice at month end for Service, Shop, and PM work orders"""
        try:
            query = """
            WITH MonthEnds AS (
                SELECT DISTINCT 
                    YEAR(CompletedDate) as year,
                    MONTH(CompletedDate) as month,
                    EOMONTH(CompletedDate) as month_end
                FROM ben002.WO
                WHERE CompletedDate >= '2025-03-01'
                    AND CompletedDate <= GETDATE()
                    AND Type IN ('S', 'SH', 'PM')  -- Service, Shop, and PM work orders
            ),
            MonthlyDelays AS (
                SELECT 
                    me.year,
                    me.month,
                    me.month_end,
                    w.WONo,
                    w.CompletedDate,
                    COALESCE(w.InvoiceDate, w.ClosedDate) as InvoicedDate,
                    CASE 
                        -- If invoiced in same month or before month end, calculate actual days
                        WHEN COALESCE(w.InvoiceDate, w.ClosedDate) <= me.month_end 
                        THEN DATEDIFF(day, w.CompletedDate, COALESCE(w.InvoiceDate, w.ClosedDate))
                        -- If not invoiced by month end, calculate days to month end
                        ELSE DATEDIFF(day, w.CompletedDate, me.month_end)
                    END as DaysWaiting
                FROM MonthEnds me
                INNER JOIN ben002.WO w 
                    ON YEAR(w.CompletedDate) = me.year 
                    AND MONTH(w.CompletedDate) = me.month
                WHERE w.CompletedDate IS NOT NULL
                    AND w.Type IN ('S', 'SH', 'PM')  -- Service, Shop, and PM work orders
            )
            SELECT 
                year,
                month,
                COUNT(*) as completed_count,
                AVG(CAST(DaysWaiting as FLOAT)) as avg_days_waiting,
                COUNT(CASE WHEN DaysWaiting > 3 THEN 1 END) as over_three_days,
                COUNT(CASE WHEN DaysWaiting > 7 THEN 1 END) as over_seven_days
            FROM MonthlyDelays
            GROUP BY year, month
            ORDER BY year, month
            """
            
            results = self.db.execute_query(query)
            monthly_delays = []
            
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_delays.append({
                        'month': month_date.strftime("%b"),
                        'year': row['year'],
                        'avg_days': round(float(row['avg_days_waiting']), 1),
                        'completed_count': int(row['completed_count']),
                        'over_three_days': int(row['over_three_days']),
                        'over_seven_days': int(row['over_seven_days'])
                    })
            
            return monthly_delays
        except Exception as e:
            logger.error(f"Monthly invoice delay query failed: {str(e)}")
            return []
    
    def get_top_customers(self):
        """Get top 10 customers by YTD sales since March 2025"""
        try:
            # Data starts from March 2025 (Softbase migration)
            ytd_start = '2025-03-01'
            
            # First get total sales since March 2025 (excluding non-customers)
            total_sales_query = f"""
            SELECT SUM(GrandTotal) as total_sales
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{ytd_start}'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            AND BillToName NOT LIKE '%Wells Fargo%'
            AND BillToName NOT LIKE '%Maintenance contract%'
            AND BillToName NOT LIKE '%Rental Fleet%'
            """
            total_result = self.db.execute_query(total_sales_query)
            total_fiscal_sales = float(total_result[0]['total_sales']) if total_result and total_result[0]['total_sales'] else 0
            
            # Calculate date ranges for risk analysis
            recent_90_start = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
            recent_30_start = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            
            query = f"""
            WITH NormalizedInvoices AS (
                SELECT 
                    InvoiceNo,
                    InvoiceDate,
                    GrandTotal,
                    CASE 
                        WHEN BillToName IN ('Polaris Industries', 'Polaris', 'Polaris Monticello, Co.') THEN 'Polaris Industries'
                        WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                        ELSE BillToName
                    END as customer_name
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= '{ytd_start}'
                AND BillToName IS NOT NULL
                AND BillToName != ''
                AND BillToName NOT LIKE '%Wells Fargo%'
                AND BillToName NOT LIKE '%Maintenance contract%'
                AND BillToName NOT LIKE '%Rental Fleet%'
            )
            SELECT TOP 10
                customer_name as customer_id,
                customer_name,
                COUNT(DISTINCT InvoiceNo) as invoice_count,
                SUM(GrandTotal) as total_sales,
                MAX(InvoiceDate) as last_invoice_date,
                MIN(InvoiceDate) as first_invoice_date,
                DATEDIFF(day, MAX(InvoiceDate), GETDATE()) as days_since_last_invoice,
                DATEDIFF(day, MIN(InvoiceDate), MAX(InvoiceDate)) as customer_lifespan_days,
                -- Recent activity metrics for risk analysis
                SUM(CASE WHEN InvoiceDate >= '{recent_30_start}' THEN GrandTotal ELSE 0 END) as recent_30_sales,
                COUNT(CASE WHEN InvoiceDate >= '{recent_30_start}' THEN 1 ELSE NULL END) as recent_30_invoices,
                SUM(CASE WHEN InvoiceDate >= '{recent_90_start}' THEN GrandTotal ELSE 0 END) as recent_90_sales,
                COUNT(CASE WHEN InvoiceDate >= '{recent_90_start}' THEN 1 ELSE NULL END) as recent_90_invoices
            FROM NormalizedInvoices
            GROUP BY customer_name
            ORDER BY SUM(GrandTotal) DESC
            """
            
            results = self.db.execute_query(query)
            top_customers = []
            
            if results:
                for i, customer in enumerate(results):
                    customer_sales = float(customer['total_sales'])
                    percentage = (customer_sales / total_fiscal_sales * 100) if total_fiscal_sales > 0 else 0
                    
                    # Calculate risk metrics
                    customer_lifespan_days = int(customer['customer_lifespan_days']) or 1
                    customer_lifespan_months = max(customer_lifespan_days / 30.0, 1)
                    expected_monthly_sales = customer_sales / customer_lifespan_months
                    expected_monthly_invoices = int(customer['invoice_count']) / customer_lifespan_months
                    
                    recent_30_sales = float(customer['recent_30_sales'])
                    recent_30_invoices = int(customer['recent_30_invoices'])
                    recent_90_sales = float(customer['recent_90_sales'])
                    days_since_last_invoice = int(customer['days_since_last_invoice']) if customer.get('days_since_last_invoice') else 0
                    
                    # Determine risk level and factors
                    risk_factors = []
                    risk_level = 'none'
                    
                    if days_since_last_invoice > 90:
                        risk_factors.append(f"No activity for {days_since_last_invoice} days")
                        risk_level = 'high'
                    elif days_since_last_invoice > 60:
                        risk_factors.append(f"No activity for {days_since_last_invoice} days")
                        risk_level = 'medium'
                    
                    if recent_30_invoices == 0 and expected_monthly_invoices > 1:
                        risk_factors.append("No invoices in last 30 days (usually active monthly)")
                        if risk_level == 'none':
                            risk_level = 'medium'
                    
                    if recent_30_sales < (expected_monthly_sales * 0.5) and expected_monthly_sales > 1000:
                        decline_pct = ((expected_monthly_sales - recent_30_sales) / expected_monthly_sales * 100)
                        risk_factors.append(f"Sales dropped {decline_pct:.0f}% below normal")
                        risk_level = 'high'
                    
                    top_customers.append({
                        'rank': i + 1,
                        'customer_id': customer['customer_id'],
                        'name': customer['customer_name'],
                        'sales': customer_sales,
                        'invoice_count': int(customer['invoice_count']),
                        'percentage': round(percentage, 1),
                        'last_invoice_date': customer['last_invoice_date'].strftime('%Y-%m-%d') if customer.get('last_invoice_date') else None,
                        'days_since_last_invoice': days_since_last_invoice,
                        # Risk analysis data
                        'risk_level': risk_level,
                        'risk_factors': risk_factors,
                        'recent_30_sales': recent_30_sales,
                        'recent_90_sales': recent_90_sales,
                        'expected_monthly_sales': expected_monthly_sales
                    })
            
            return top_customers
        except Exception as e:
            logger.error(f"Top customers query failed: {str(e)}")
            return []
    
    def get_monthly_work_orders_by_type(self):
        """Get monthly work orders by type since March"""
        try:
            query = """
            WITH LaborTotals AS (
                SELECT WONo, SUM(Sell) as labor_total 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ),
            PartsTotals AS (
                SELECT WONo, SUM(Sell * Qty) as parts_total 
                FROM ben002.WOParts 
                GROUP BY WONo
            ),
            MiscTotals AS (
                SELECT WONo, SUM(Sell) as misc_total 
                FROM ben002.WOMisc 
                GROUP BY WONo
            )
            SELECT 
                YEAR(w.OpenDate) as year,
                MONTH(w.OpenDate) as month,
                w.Type,
                COUNT(*) as count,
                SUM(
                    COALESCE(l.labor_total, 0) + 
                    COALESCE(p.parts_total, 0) + 
                    COALESCE(m.misc_total, 0)
                ) as total_value
            FROM ben002.WO w
            LEFT JOIN LaborTotals l ON w.WONo = l.WONo
            LEFT JOIN PartsTotals p ON w.WONo = p.WONo
            LEFT JOIN MiscTotals m ON w.WONo = m.WONo
            WHERE w.OpenDate >= '2025-03-01'
            AND w.OpenDate IS NOT NULL
            GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate), w.Type
            ORDER BY YEAR(w.OpenDate), MONTH(w.OpenDate)
            """
            
            results = self.db.execute_query(query)
            months_data = {}
            
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    month_key = month_date.strftime("%b")
                    
                    if month_key not in months_data:
                        months_data[month_key] = {
                            'month': month_key,
                            'service_value': 0,
                            'rental_value': 0,
                            'parts_value': 0,
                            'pm_value': 0,
                            'shop_value': 0,
                            'equipment_value': 0
                        }
                    
                    # Map work order types to categories
                    wo_type = row['Type']
                    value = float(row['total_value'])
                    
                    if wo_type == 'S':
                        months_data[month_key]['service_value'] += value
                    elif wo_type == 'R':
                        months_data[month_key]['rental_value'] += value
                    elif wo_type == 'P':
                        months_data[month_key]['parts_value'] += value
                    elif wo_type == 'PM':
                        months_data[month_key]['pm_value'] += value
                    elif wo_type == 'SH':
                        months_data[month_key]['shop_value'] += value
                    elif wo_type == 'E':
                        months_data[month_key]['equipment_value'] += value
            
            # Convert to list and ensure all months are present
            start_date = datetime(2025, 3, 1)
            monthly_data = []
            date = start_date
            
            while date <= self.current_date:
                month_key = date.strftime("%b")
                if month_key in months_data:
                    monthly_data.append(months_data[month_key])
                else:
                    monthly_data.append({
                        'month': month_key,
                        'service_value': 0,
                        'rental_value': 0,
                        'parts_value': 0,
                        'pm_value': 0,
                        'shop_value': 0,
                        'equipment_value': 0
                    })
                
                if date.month == 12:
                    date = date.replace(year=date.year + 1, month=1)
                else:
                    date = date.replace(month=date.month + 1)
            
            return monthly_data
        except Exception as e:
            logger.error(f"Monthly work orders by type query failed: {str(e)}")
            return []
    
    def get_department_margins(self):
        """Get department gross margin percentages by month"""
        try:
            # Use the same calculation as the original dashboard - sum the taxable/nontax fields
            query = f"""
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                -- Parts margin
                SUM(PartsTaxable + PartsNonTax) as parts_revenue,
                SUM(PartsCost) as parts_cost,
                -- Labor margin
                SUM(LaborTaxable + LaborNonTax) as labor_revenue,
                SUM(LaborCost) as labor_cost,
                -- Equipment margin
                SUM(EquipmentTaxable + EquipmentNonTax) as equipment_revenue,
                SUM(EquipmentCost) as equipment_cost,
                -- Rental margin
                SUM(RentalTaxable + RentalNonTax) as rental_revenue,
                SUM(RentalCost) as rental_cost
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{self.twelve_months_ago}'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            results = self.db.execute_query(query)
            department_margins = []
            
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    
                    # Calculate margins - handle nulls and division by zero
                    parts_revenue = float(row.get('parts_revenue') or 0)
                    parts_cost = float(row.get('parts_cost') or 0)
                    parts_margin = 0
                    if parts_revenue > 0:
                        parts_margin = ((parts_revenue - parts_cost) / parts_revenue) * 100
                    
                    labor_revenue = float(row.get('labor_revenue') or 0)
                    labor_cost = float(row.get('labor_cost') or 0)
                    labor_margin = 0
                    if labor_revenue > 0:
                        labor_margin = ((labor_revenue - labor_cost) / labor_revenue) * 100
                    
                    equipment_revenue = float(row.get('equipment_revenue') or 0)
                    equipment_cost = float(row.get('equipment_cost') or 0)
                    equipment_margin = 0
                    if equipment_revenue > 0:
                        equipment_margin = ((equipment_revenue - equipment_cost) / equipment_revenue) * 100
                    
                    rental_revenue = float(row.get('rental_revenue') or 0)
                    rental_cost = float(row.get('rental_cost') or 0)
                    rental_margin = 0
                    if rental_revenue > 0:
                        rental_margin = ((rental_revenue - rental_cost) / rental_revenue) * 100
                    
                    department_margins.append({
                        'month': month_date.strftime("%b"),
                        'parts_margin': round(parts_margin, 1),
                        'labor_margin': round(labor_margin, 1),
                        'equipment_margin': round(equipment_margin, 1),
                        'rental_margin': round(rental_margin, 1)
                    })
            
            return department_margins
        except Exception as e:
            logger.error(f"Department margins query failed: {str(e)}")
            return []
    
    def get_monthly_active_customers(self):
        """Get monthly active customers count since March 2025"""
        try:
            query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                COUNT(DISTINCT CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                    ELSE BillToName
                END) as active_customers
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '2025-03-01'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            AND BillToName NOT LIKE '%Wells Fargo%'
            AND BillToName NOT LIKE '%Maintenance contract%'
            AND BillToName NOT LIKE '%Rental Fleet%'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            results = self.db.execute_query(query)
            monthly_customers = []
            
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_customers.append({
                        'month': month_date.strftime("%b"),
                        'customers': int(row['active_customers'])
                    })
            
            # Pad missing months from March onwards
            start_date = datetime(2025, 3, 1)
            all_months = []
            date = start_date
            while date <= self.current_date:
                all_months.append(date.strftime("%b"))
                if date.month == 12:
                    date = date.replace(year=date.year + 1, month=1)
                else:
                    date = date.replace(month=date.month + 1)
            
            existing_data = {item['month']: item['customers'] for item in monthly_customers}
            monthly_customers = [{'month': month, 'customers': existing_data.get(month, 0)} for month in all_months]
            
            return monthly_customers
        except Exception as e:
            logger.error(f"Monthly active customers query failed: {str(e)}")
            return []
    
    def get_monthly_open_work_orders(self):
        """Get monthly open work orders value since March 2025"""
        try:
            # Get snapshot of open work orders value at the end of each month (completed months only)
            query = """
            WITH MonthEnds AS (
                SELECT DISTINCT 
                    YEAR(OpenDate) as year,
                    MONTH(OpenDate) as month,
                    EOMONTH(OpenDate) as month_end
                FROM ben002.WO
                WHERE OpenDate >= '2025-03-01'
                AND EOMONTH(OpenDate) < EOMONTH(GETDATE())  -- Only include completed months
            )
            SELECT 
                me.year,
                me.month,
                SUM(
                    CASE 
                        WHEN w.OpenDate <= me.month_end 
                        AND (w.ClosedDate IS NULL OR w.ClosedDate > me.month_end)
                        AND (w.InvoiceDate IS NULL OR w.InvoiceDate > me.month_end)
                        THEN COALESCE(l.labor_total, 0) + COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0)
                        ELSE 0
                    END
                ) as open_value
            FROM MonthEnds me
            CROSS JOIN ben002.WO w
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as labor_total 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ) l ON w.WONo = l.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell * Qty) as parts_total 
                FROM ben002.WOParts 
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_total 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            GROUP BY me.year, me.month, me.month_end
            ORDER BY me.year, me.month
            """
            
            results = self.db.execute_query(query)
            monthly_work_orders = []
            
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_work_orders.append({
                        'month': month_date.strftime("%b"),
                        'value': float(row['open_value'] or 0)
                    })
            
            # Pad missing months from March onwards (completed months only)
            start_date = datetime(2025, 3, 1)
            # Get the end of the previous month (last completed month)
            current_date = datetime.now()
            if current_date.day == 1:
                # If it's the 1st, use previous month
                last_completed_month = current_date.replace(day=1) - timedelta(days=1)
            else:
                # Use the 1st of current month - 1 day to get last day of previous month
                last_completed_month = current_date.replace(day=1) - timedelta(days=1)
            
            all_months = []
            date = start_date
            while date <= last_completed_month.replace(day=1):  # Compare to first day of last completed month
                all_months.append(date.strftime("%b"))
                if date.month == 12:
                    date = date.replace(year=date.year + 1, month=1)
                else:
                    date = date.replace(month=date.month + 1)
            
            existing_data = {item['month']: item['value'] for item in monthly_work_orders}
            return monthly_work_orders
        except Exception as e:
            logger.error(f"Monthly open work orders query failed: {str(e)}")
            return []

    @dashboard_optimized_bp.route('/api/dashboard/diagnostic/invoice-detail', methods=['GET'])
    @jwt_required()
    def diagnose_invoice_detail():
        """Diagnostic endpoint to explore InvoiceDetail table structure"""
        try:
            db = AzureSQLService() # Changed from get_db() to AzureSQLService() to match surrounding code's pattern
            
            # 1. Check if InvoiceDetail table exists and get its columns
            columns_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
                AND TABLE_NAME = 'InvoiceDetail'
            ORDER BY ORDINAL_POSITION
            """
            
            columns = db.execute_query(columns_query)
            
            if not columns:
                return jsonify({
                    'error': 'InvoiceDetail table not found',
                    'suggestion': 'Table may not exist or may have a different name'
                }), 404
            
            # 2. Get sample records from InvoiceDetail for LINDEN invoices
            sample_query = """
            SELECT TOP 10
                id.*
            FROM ben002.InvoiceDetail id
            INNER JOIN ben002.InvoiceReg ir ON id.InvoiceNo = ir.InvoiceNo
            WHERE ir.SaleCode = 'LINDEN'
                AND ir.InvoiceDate >= DATEADD(month, -3, GETDATE())
            ORDER BY ir.InvoiceDate DESC
            """
            
            try:
                samples = db.execute_query(sample_query)
            except Exception as e:
                samples = []
                sample_error = str(e)
            
            # 3. Try to find quantity-related columns
            qty_columns = [col for col in columns if 'qty' in col['COLUMN_NAME'].lower() or 'quantity' in col['COLUMN_NAME'].lower()]
            
            return jsonify({
                'table_exists': True,
                'total_columns': len(columns),
                'all_columns': [{'name': col['COLUMN_NAME'], 'type': col['DATA_TYPE']} for col in columns],
                'quantity_columns': [col['COLUMN_NAME'] for col in qty_columns],
                'sample_records': [dict(row) for row in samples] if samples else [],
                'sample_error': sample_error if 'sample_error' in locals() else None,
                'recommendation': 'Check quantity_columns and sample_records to determine how to count units'
            }), 200
            
        except Exception as e:
            logger.error(f"InvoiceDetail diagnostic failed: {str(e)}")
            return jsonify({'error': str(e)}), 500


@dashboard_optimized_bp.route('/api/reports/dashboard/summary-optimized', methods=['GET'])
@jwt_required()
def get_dashboard_summary_optimized():
    """Optimized dashboard endpoint using parallel query execution and caching"""
    start_time = time.time()
    
    # Check for cache refresh parameter
    force_refresh = request.args.get('refresh', '').lower() == 'true'
    
    # Log cache status
    logger.info(f"Dashboard request - force_refresh: {force_refresh}, cache_enabled: {cache_service.enabled}")
    
    try:
        db = AzureSQLService()
        queries = DashboardQueries(db)
        
        # Cache TTL settings (in seconds)
        cache_ttl = {
            'total_sales': 300,  # 5 minutes - changes frequently
            'ytd_sales': 300,  # 5 minutes - changes frequently
            'inventory_count': 600,  # 10 minutes - changes moderately
            'active_customers': 900,  # 15 minutes - changes slowly
            'monthly_sales': 1800,  # 30 minutes - historical data
            'uninvoiced': 300,  # 5 minutes - important to keep fresh
            'monthly_quotes': 900,  # 15 minutes
            'work_order_types': 300,  # 5 minutes - changes frequently
            'top_customers': 1800,  # 30 minutes - changes slowly
            'monthly_work_orders': 900,  # 15 minutes
            'department_margins': 1800  # 30 minutes - historical data
        }
        
        # Define all query tasks with caching
        def cached_query(key, func, ttl):
            cache_key = f"dashboard:{key}:{datetime.now().strftime('%Y-%m')}"
            return cache_service.cache_query(cache_key, func, ttl, force_refresh)
        
        query_tasks = {
            'total_sales': lambda: cached_query('total_sales', queries.get_current_month_sales, cache_ttl['total_sales']),
            'ytd_sales': lambda: cached_query('ytd_sales', queries.get_ytd_sales, cache_ttl['ytd_sales']),
            'inventory_count': lambda: cached_query('inventory_count', queries.get_inventory_count, cache_ttl['inventory_count']),
            'active_customers': lambda: cached_query('active_customers', queries.get_active_customers, cache_ttl['active_customers']),
            'total_customers': lambda: cached_query('total_customers', queries.get_total_customers, cache_ttl['active_customers']),
            'monthly_sales': lambda: cached_query('monthly_sales', queries.get_monthly_sales, cache_ttl['monthly_sales']),
            'monthly_sales_no_equipment': lambda: cached_query('monthly_sales_no_equipment', queries.get_monthly_sales_excluding_equipment, cache_ttl['monthly_sales']),
            'monthly_equipment_sales': lambda: cached_query('monthly_equipment_sales', queries.get_monthly_equipment_sales, cache_ttl['monthly_sales']),
            'monthly_sales_by_stream': lambda: cached_query('monthly_sales_by_stream', queries.get_monthly_sales_by_stream, cache_ttl['monthly_sales']),
            'uninvoiced': lambda: cached_query('uninvoiced', queries.get_uninvoiced_work_orders, cache_ttl['uninvoiced']),
            'monthly_quotes': lambda: cached_query('monthly_quotes', queries.get_monthly_quotes, cache_ttl['monthly_quotes']),
            'work_order_types': lambda: cached_query('work_order_types', queries.get_work_order_types, cache_ttl['work_order_types']),
            'top_customers': lambda: cached_query('top_customers', queries.get_top_customers, cache_ttl['top_customers']),
            'monthly_work_orders': lambda: cached_query('monthly_work_orders', queries.get_monthly_work_orders_by_type, cache_ttl['monthly_work_orders']),
            'department_margins': lambda: cached_query('department_margins', queries.get_department_margins, cache_ttl['department_margins']),
            'monthly_active_customers': lambda: cached_query('monthly_active_customers', queries.get_monthly_active_customers, cache_ttl['active_customers']),
            'monthly_open_work_orders': lambda: cached_query('monthly_open_work_orders', queries.get_monthly_open_work_orders, cache_ttl['work_order_types']),
            'awaiting_invoice': lambda: cached_query('awaiting_invoice', queries.get_awaiting_invoice_work_orders, cache_ttl['uninvoiced']),
            'monthly_invoice_delays': lambda: cached_query('monthly_invoice_delays', queries.get_monthly_invoice_delay_avg, cache_ttl['work_order_types'])
        }
        
        # Execute queries in parallel
        results = {}
        cache_hits = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all tasks
            future_to_key = {executor.submit(func): key for key, func in query_tasks.items()}
            
            # Collect results as they complete
            for future in as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    logger.error(f"Query {key} failed: {str(e)}")
                    results[key] = None
        
        # Process results
        uninvoiced_data = results.get('uninvoiced', {'value': 0, 'count': 0})
        wo_types_data = results.get('work_order_types', {'types': [], 'total_value': 0, 'total_count': 0, 'previous_value': 0, 'change': 0, 'change_percent': 0})
        awaiting_invoice_data = results.get('awaiting_invoice', {
            'count': 0,
            'total_value': 0,
            'avg_days_waiting': 0,
            'over_three_days': 0,
            'over_five_days': 0,
            'over_seven_days': 0
        })
        
        # Handle active customers data (could be int or dict)
        active_customers_data = results.get('active_customers', 0)
        if isinstance(active_customers_data, dict):
            active_customers_info = active_customers_data
        else:
            # Fallback for old format
            active_customers_info = {
                'current': active_customers_data,
                'previous': 0,
                'change': 0,
                'change_percent': 0
            }
        
        response_data = {
            'total_sales': results.get('total_sales', 0),
            'ytd_sales': results.get('ytd_sales', 0),
            'inventory_count': results.get('inventory_count', 0),
            'active_customers': active_customers_info['current'],
            'active_customers_change': active_customers_info['change'],
            'active_customers_change_percent': active_customers_info['change_percent'],
            'active_customers_previous': active_customers_info['previous'],
            'total_customers': results.get('total_customers', 0),
            'uninvoiced_work_orders': int(uninvoiced_data['value']),
            'uninvoiced_count': uninvoiced_data['count'],
            'open_work_orders_value': int(wo_types_data['total_value']),
            'open_work_orders_count': wo_types_data['total_count'],
            'open_work_orders_change': int(wo_types_data['change']),
            'open_work_orders_change_percent': wo_types_data['change_percent'],
            'open_work_orders_previous': int(wo_types_data['previous_value']),
            'work_order_types': wo_types_data['types'],
            'monthly_sales': results.get('monthly_sales', []),
            'monthly_sales_no_equipment': results.get('monthly_sales_no_equipment', []),
            'monthly_equipment_sales': results.get('monthly_equipment_sales', []),
            'monthly_sales_by_stream': results.get('monthly_sales_by_stream', []),
            'monthly_quotes': results.get('monthly_quotes', []),
            'top_customers': results.get('top_customers', []),
            'monthly_work_orders_by_type': results.get('monthly_work_orders', []),
            'department_margins': results.get('department_margins', []),
            'monthly_active_customers': results.get('monthly_active_customers', []),
            'monthly_open_work_orders': results.get('monthly_open_work_orders', []),
            # Awaiting invoice data
            'awaiting_invoice_count': awaiting_invoice_data['count'],
            'awaiting_invoice_value': int(awaiting_invoice_data['total_value']),
            'awaiting_invoice_avg_days': awaiting_invoice_data['avg_days_waiting'],
            'awaiting_invoice_over_three': awaiting_invoice_data['over_three_days'],
            'awaiting_invoice_over_five': awaiting_invoice_data['over_five_days'],
            'awaiting_invoice_over_seven': awaiting_invoice_data['over_seven_days'],
            # Monthly invoice delay trends
            'monthly_invoice_delays': results.get('monthly_invoice_delays', []),
            'period': datetime.now().strftime('%B %Y'),
            'last_updated': datetime.now().isoformat(),
            'query_time': round(time.time() - start_time, 2),
            'cache_enabled': cache_service.enabled,
            'from_cache': not force_refresh and cache_service.enabled
        }
        
        logger.info(f"✅ Dashboard loaded in {response_data['query_time']} seconds (from_cache: {response_data['from_cache']})")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in optimized dashboard: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to load dashboard data',
            'message': str(e)
        }), 500

@dashboard_optimized_bp.route('/api/dashboard/active-customers-export', methods=['GET'])
@jwt_required()
def export_active_customers():
    """Export detailed active customers list for CSV download"""
    try:
        db = AzureSQLService()
        
        # Get current month period or custom period if specified
        period = request.args.get('period', 'current')  # 'current', 'last30', or 'YYYY-MM'
        
        if period == 'current':
            # Current month
            current_date = datetime.now()
            start_date = current_date.replace(day=1).strftime('%Y-%m-%d')
            end_date = current_date.strftime('%Y-%m-%d')
            period_label = current_date.strftime('%B %Y')
        elif period == 'last30':
            # Last 30 days
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
            period_label = 'Last 30 Days'
        else:
            # Specific month (format: YYYY-MM)
            try:
                year, month = period.split('-')
                month_date = datetime(int(year), int(month), 1)
                start_date = month_date.strftime('%Y-%m-%d')
                # Get last day of month
                if month_date.month == 12:
                    next_month = month_date.replace(year=month_date.year + 1, month=1)
                else:
                    next_month = month_date.replace(month=month_date.month + 1)
                end_date = (next_month - timedelta(days=1)).strftime('%Y-%m-%d')
                period_label = month_date.strftime('%B %Y')
            except:
                return jsonify({'error': 'Invalid period format. Use YYYY-MM'}), 400
        
        # Query to get detailed active customers with their activity
        query = f"""
        SELECT 
            CASE 
                WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END as customer_name,
            COUNT(DISTINCT InvoiceNo) as invoice_count,
            MIN(InvoiceDate) as first_invoice_date,
            MAX(InvoiceDate) as last_invoice_date,
            SUM(GrandTotal) as total_sales,
            AVG(GrandTotal) as avg_invoice_value
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '{start_date}'
            AND InvoiceDate <= '{end_date}'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            AND BillToName NOT LIKE '%Wells Fargo%'
            AND BillToName NOT LIKE '%Maintenance contract%'
            AND BillToName NOT LIKE '%Rental Fleet%'
            AND GrandTotal > 0
        GROUP BY 
            CASE 
                WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END
        ORDER BY total_sales DESC
        """
        
        results = db.execute_query(query)
        customers = []
        
        if results:
            for row in results:
                customers.append({
                    'customer_name': row['customer_name'],
                    'invoice_count': int(row['invoice_count']),
                    'first_invoice_date': row['first_invoice_date'].strftime('%Y-%m-%d') if row['first_invoice_date'] else '',
                    'last_invoice_date': row['last_invoice_date'].strftime('%Y-%m-%d') if row['last_invoice_date'] else '',
                    'total_sales': float(row['total_sales']),
                    'avg_invoice_value': float(row['avg_invoice_value'])
                })
        
        return jsonify({
            'customers': customers,
            'period': period_label,
            'total_customers': len(customers),
            'total_sales': sum(c['total_sales'] for c in customers),
            'date_range': f"{start_date} to {end_date}"
        })
        
    except Exception as e:
        logger.error(f"Error exporting active customers: {str(e)}")
        return jsonify({
            'error': 'Failed to export active customers',
            'message': str(e)
        }), 500

@dashboard_optimized_bp.route('/api/dashboard/customer-risk-analysis', methods=['GET'])
@jwt_required()
def analyze_customer_risk():
    """Analyze top customers for behavioral changes and risk factors"""
    try:
        db = AzureSQLService()
        
        # Current fiscal year dates
        current_date = datetime.now()
        if current_date.month >= 11:
            fiscal_year_start = datetime(current_date.year, 11, 1)
        else:
            fiscal_year_start = datetime(current_date.year - 1, 11, 1)
        
        fiscal_year_start_str = fiscal_year_start.strftime('%Y-%m-%d')
        
        # Get last 90 days for recent activity analysis
        recent_start = (current_date - timedelta(days=90)).strftime('%Y-%m-%d')
        very_recent_start = (current_date - timedelta(days=30)).strftime('%Y-%m-%d')
        
        # Simplified query to avoid compatibility issues
        risk_analysis_query = f"""
        SELECT TOP 10
            CASE 
                WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END as customer_name,
            COUNT(DISTINCT InvoiceNo) as total_invoices,
            SUM(GrandTotal) as total_sales,
            AVG(GrandTotal) as avg_invoice_value,
            MIN(InvoiceDate) as first_invoice,
            MAX(InvoiceDate) as last_invoice,
            DATEDIFF(day, MIN(InvoiceDate), MAX(InvoiceDate)) as customer_lifespan_days,
            SUM(CASE WHEN InvoiceDate >= '{recent_start}' THEN GrandTotal ELSE 0 END) as recent_90_sales,
            COUNT(CASE WHEN InvoiceDate >= '{recent_start}' THEN 1 ELSE NULL END) as recent_90_invoices,
            SUM(CASE WHEN InvoiceDate >= '{very_recent_start}' THEN GrandTotal ELSE 0 END) as recent_30_sales,
            COUNT(CASE WHEN InvoiceDate >= '{very_recent_start}' THEN 1 ELSE NULL END) as recent_30_invoices,
            DATEDIFF(day, MAX(InvoiceDate), GETDATE()) as days_since_last_invoice
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '{fiscal_year_start_str}'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            AND BillToName NOT LIKE '%Wells Fargo%'
            AND BillToName NOT LIKE '%Maintenance contract%'
            AND BillToName NOT LIKE '%Rental Fleet%'
            AND GrandTotal > 0
        GROUP BY 
            CASE 
                WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                WHEN BillToName IN ('Tinnacity', 'Tinnacity Inc') THEN 'Tinnacity'
                ELSE BillToName
            END
        ORDER BY SUM(GrandTotal) DESC
        """
        
        results = db.execute_query(risk_analysis_query)
        customers_risk = []
        
        if results:
            for row in results:
                # Calculate expected monthly values based on historical data
                total_sales = float(row['total_sales'])
                total_invoices = int(row['total_invoices'])
                customer_lifespan_days = int(row['customer_lifespan_days']) or 1
                
                # Calculate expected monthly averages
                customer_lifespan_months = max(customer_lifespan_days / 30.0, 1)
                expected_monthly_sales = total_sales / customer_lifespan_months
                expected_monthly_invoices = total_invoices / customer_lifespan_months
                
                # Get recent activity
                recent_30_sales = float(row['recent_30_sales'])
                recent_30_invoices = int(row['recent_30_invoices'])
                recent_90_sales = float(row['recent_90_sales'])
                recent_90_invoices = int(row['recent_90_invoices'])
                days_since_last_invoice = int(row['days_since_last_invoice'])
                
                # Determine risk factors
                risk_factors = []
                risk_level = 'none'  # Default to no risk
                
                if days_since_last_invoice > 90:
                    risk_factors.append(f"No activity for {days_since_last_invoice} days")
                    risk_level = 'high'
                elif days_since_last_invoice > 60:
                    risk_factors.append(f"No activity for {days_since_last_invoice} days")
                    risk_level = 'medium'
                
                if recent_30_invoices == 0 and expected_monthly_invoices > 1:
                    risk_factors.append("No invoices in last 30 days (usually active monthly)")
                    if risk_level == 'none':
                        risk_level = 'medium'
                
                if recent_30_sales < (expected_monthly_sales * 0.5) and expected_monthly_sales > 1000:
                    actual = recent_30_sales
                    expected = expected_monthly_sales
                    risk_factors.append(f"Sales dropped {((expected - actual) / expected * 100):.0f}% below normal")
                    risk_level = 'high'
                
                if recent_90_invoices < (expected_monthly_invoices * 2) and expected_monthly_invoices > 0.5:
                    risk_factors.append("Invoice frequency has decreased significantly")
                    if risk_level == 'none':
                        risk_level = 'medium'
                
                # Calculate trends
                recent_90_avg = recent_90_sales / 3.0 if recent_90_sales > 0 else 0  # 3-month average
                
                customers_risk.append({
                    'customer_name': row['customer_name'],
                    'total_sales': total_sales,
                    'risk_level': risk_level,
                    'risk_factors': risk_factors,
                    'days_since_last_invoice': days_since_last_invoice,
                    'recent_30_sales': recent_30_sales,
                    'recent_90_sales': recent_90_sales,
                    'expected_monthly_sales': expected_monthly_sales,
                    'trend_analysis': {
                        'recent_vs_expected': ((recent_90_avg / expected_monthly_sales - 1) * 100) if expected_monthly_sales > 0 else 0,
                        'activity_status': 'declining' if recent_90_avg < expected_monthly_sales * 0.8 else 'stable'
                    }
                })
        
        return jsonify({
            'customers': customers_risk,
            'analysis_date': current_date.isoformat(),
            'period_analyzed': f"Fiscal YTD since {fiscal_year_start_str}"
        })
        
    except Exception as e:
        logger.error(f"Error in customer risk analysis: {str(e)}")
        return jsonify({
            'error': 'Failed to analyze customer risk',
            'message': str(e)
        }), 500


@dashboard_optimized_bp.route('/api/dashboard/invoice-delay-analysis', methods=['GET'])
@jwt_required()
def analyze_invoice_delays():
    """Analyze invoice delays by department type"""
    try:
        db = AzureSQLService()
        
        # Get breakdown by work order type
        query = """
        WITH CompletedWOs AS (
            SELECT 
                w.WONo,
                w.Type,
                CASE 
                    WHEN w.Type = 'S' THEN 'Service'
                    WHEN w.Type = 'R' THEN 'Rental'
                    WHEN w.Type = 'P' THEN 'Parts'
                    WHEN w.Type = 'PM' THEN 'Preventive Maintenance'
                    WHEN w.Type = 'I' THEN 'Internal'
                    WHEN w.Type = 'E' THEN 'Equipment'
                    WHEN w.Type IS NULL THEN 'Unspecified'
                    ELSE w.Type
                END as TypeName,
                w.CompletedDate,
                w.BillTo,
                DATEDIFF(day, w.CompletedDate, GETDATE()) as DaysSinceCompleted,
                -- Include labor quotes for flat rate labor
                COALESCE(l.labor_sell, 0) + COALESCE(lq.quote_amount, 0) as labor_total,
                COALESCE(p.parts_sell, 0) as parts_total,
                COALESCE(m.misc_sell, 0) as misc_total
            FROM ben002.WO w
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as labor_sell 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ) l ON w.WONo = l.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Amount) as quote_amount 
                FROM ben002.WOQuote 
                WHERE Type = 'L'
                GROUP BY WONo
            ) lq ON w.WONo = lq.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell * Qty) as parts_sell 
                FROM ben002.WOParts 
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_sell 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            WHERE w.CompletedDate IS NOT NULL
              AND w.ClosedDate IS NULL
              AND w.InvoiceDate IS NULL
              AND w.DeletionTime IS NULL
        )
        SELECT 
            TypeName,
            COUNT(*) as count,
            SUM(labor_total + parts_total + misc_total) as total_value,
            AVG(CAST(DaysSinceCompleted as FLOAT)) as avg_days_waiting,
            MIN(DaysSinceCompleted) as min_days,
            MAX(DaysSinceCompleted) as max_days,
            COUNT(CASE WHEN DaysSinceCompleted <= 3 THEN 1 END) as within_target,
            COUNT(CASE WHEN DaysSinceCompleted > 3 THEN 1 END) as over_three_days,
            COUNT(CASE WHEN DaysSinceCompleted > 7 THEN 1 END) as over_seven_days,
            COUNT(CASE WHEN DaysSinceCompleted > 14 THEN 1 END) as over_fourteen_days,
            COUNT(CASE WHEN DaysSinceCompleted > 30 THEN 1 END) as over_thirty_days
        FROM CompletedWOs
        GROUP BY TypeName
        ORDER BY total_value DESC
        """
        
        results = db.execute_query(query)
        
        departments = []
        total_all = {
            'count': 0,
            'value': 0,
            'within_target': 0,
            'over_three': 0,
            'over_seven': 0,
            'over_fourteen': 0,
            'over_thirty': 0
        }
        
        if results:
            for row in results:
                dept_data = {
                    'department': row['TypeName'],
                    'count': int(row['count']),
                    'value': float(row['total_value']),
                    'avg_days': round(float(row['avg_days_waiting']), 1),
                    'min_days': int(row['min_days']),
                    'max_days': int(row['max_days']),
                    'within_target': int(row['within_target']),
                    'within_target_pct': round((int(row['within_target']) / int(row['count'])) * 100, 1),
                    'over_three': int(row['over_three_days']),
                    'over_three_pct': round((int(row['over_three_days']) / int(row['count'])) * 100, 1),
                    'over_seven': int(row['over_seven_days']),
                    'over_seven_pct': round((int(row['over_seven_days']) / int(row['count'])) * 100, 1),
                    'over_fourteen': int(row['over_fourteen_days']),
                    'over_fourteen_pct': round((int(row['over_fourteen_days']) / int(row['count'])) * 100, 1),
                    'over_thirty': int(row['over_thirty_days']),
                    'over_thirty_pct': round((int(row['over_thirty_days']) / int(row['count'])) * 100, 1)
                }
                departments.append(dept_data)
                
                # Add to totals
                total_all['count'] += dept_data['count']
                total_all['value'] += dept_data['value']
                total_all['within_target'] += dept_data['within_target']
                total_all['over_three'] += dept_data['over_three']
                total_all['over_seven'] += dept_data['over_seven']
                total_all['over_fourteen'] += dept_data['over_fourteen']
                total_all['over_thirty'] += dept_data['over_thirty']
        
        # Get detailed work orders for worst performers
        detail_query = """
        SELECT TOP 20
            w.WONo,
            CASE 
                WHEN w.Type = 'S' THEN 'Service'
                WHEN w.Type = 'R' THEN 'Rental'
                WHEN w.Type = 'P' THEN 'Parts'
                WHEN w.Type = 'PM' THEN 'Preventive Maintenance'
                WHEN w.Type = 'I' THEN 'Internal'
                WHEN w.Type = 'E' THEN 'Equipment'
                ELSE COALESCE(w.Type, 'Unspecified')
            END as TypeName,
            w.BillTo,
            c.Name as CustomerName,
            w.CompletedDate,
            DATEDIFF(day, w.CompletedDate, GETDATE()) as DaysWaiting,
            COALESCE(l.labor_sell, 0) + COALESCE(lq.quote_amount, 0) + 
            COALESCE(p.parts_sell, 0) + COALESCE(m.misc_sell, 0) as TotalValue
        FROM ben002.WO w
        LEFT JOIN ben002.Customer c ON w.BillTo = c.Number
        LEFT JOIN (
            SELECT WONo, SUM(Sell) as labor_sell FROM ben002.WOLabor GROUP BY WONo
        ) l ON w.WONo = l.WONo
        LEFT JOIN (
            SELECT WONo, SUM(Amount) as quote_amount FROM ben002.WOQuote WHERE Type = 'L' GROUP BY WONo
        ) lq ON w.WONo = lq.WONo
        LEFT JOIN (
            SELECT WONo, SUM(Sell * Qty) as parts_sell FROM ben002.WOParts GROUP BY WONo
        ) p ON w.WONo = p.WONo
        LEFT JOIN (
            SELECT WONo, SUM(Sell) as misc_sell FROM ben002.WOMisc GROUP BY WONo
        ) m ON w.WONo = m.WONo
        WHERE w.CompletedDate IS NOT NULL
          AND w.ClosedDate IS NULL
          AND w.InvoiceDate IS NULL
          AND w.DeletionTime IS NULL
        ORDER BY DATEDIFF(day, w.CompletedDate, GETDATE()) DESC
        """
        
        detail_results = db.execute_query(detail_query)
        worst_offenders = []
        
        if detail_results:
            for row in detail_results:
                worst_offenders.append({
                    'wo_number': row['WONo'],
                    'type': row['TypeName'],
                    'customer': row['CustomerName'] or row['BillTo'],
                    'completed_date': row['CompletedDate'].strftime('%Y-%m-%d') if row['CompletedDate'] else None,
                    'days_waiting': int(row['DaysWaiting']),
                    'value': float(row['TotalValue'])
                })
        
        return jsonify({
            'departments': departments,
            'totals': {
                'count': total_all['count'],
                'value': total_all['value'],
                'avg_days': round(sum(d['avg_days'] * d['count'] for d in departments) / total_all['count'], 1) if total_all['count'] > 0 else 0,
                'within_target_pct': round((total_all['within_target'] / total_all['count']) * 100, 1) if total_all['count'] > 0 else 0,
                'over_three_pct': round((total_all['over_three'] / total_all['count']) * 100, 1) if total_all['count'] > 0 else 0,
                'over_seven_pct': round((total_all['over_seven'] / total_all['count']) * 100, 1) if total_all['count'] > 0 else 0,
                'over_fourteen_pct': round((total_all['over_fourteen'] / total_all['count']) * 100, 1) if total_all['count'] > 0 else 0,
                'over_thirty_pct': round((total_all['over_thirty'] / total_all['count']) * 100, 1) if total_all['count'] > 0 else 0
            },
            'worst_offenders': worst_offenders,
            'analysis_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in invoice delay analysis: {str(e)}")
        return jsonify({
            'error': 'Failed to analyze invoice delays',
            'message': str(e)
        }), 500

@dashboard_optimized_bp.route('/api/dashboard-optimized/debug-no-equipment', methods=['GET'])
@jwt_required()
def debug_no_equipment_sales():
    """Debug endpoint to check Monthly Sales (No Equipment) data"""
    try:
        queries = DashboardQueries()
        data = queries.get_monthly_sales_excluding_equipment()
        
        return jsonify({
            'monthly_sales_no_equipment': data,
            'count': len(data),
            'message': 'Data for Monthly Sales (No Equipment) card'
        })
        
    except Exception as e:
        logger.error(f"Debug no equipment error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_optimized_bp.route('/api/dashboard-optimized/equipment-salecodes', methods=['GET'])
@jwt_required()
def check_equipment_sale_codes():
    """Check what equipment sale codes actually exist in the database"""
    try:
        db = DatabaseService()
        
        # Get all sale codes that have equipment revenue for July 2025 specifically
        query = """
        SELECT 
            SaleCode,
            SaleDept,
            COUNT(*) as invoice_count,
            SUM(COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0)) as total_revenue,
            MIN(InvoiceDate) as first_invoice,
            MAX(InvoiceDate) as last_invoice
        FROM ben002.InvoiceReg
        WHERE YEAR(InvoiceDate) = 2025 AND MONTH(InvoiceDate) = 7
            AND (EquipmentTaxable > 0 OR EquipmentNonTax > 0)
        GROUP BY SaleCode, SaleDept
        ORDER BY total_revenue DESC
        """
        
        results = db.execute_query(query)
        
        # Also check if our specific codes exist at all (even before March)
        check_query = """
        SELECT 
            'LINDE' as code, COUNT(*) as count 
        FROM ben002.InvoiceReg 
        WHERE SaleCode = 'LINDE'
        UNION ALL
        SELECT 
            'LINDEN' as code, COUNT(*) as count 
        FROM ben002.InvoiceReg 
        WHERE SaleCode = 'LINDEN'
        UNION ALL
        SELECT 
            'NEWEQ' as code, COUNT(*) as count 
        FROM ben002.InvoiceReg 
        WHERE SaleCode = 'NEWEQ'
        UNION ALL
        SELECT 
            'KOM' as code, COUNT(*) as count 
        FROM ben002.InvoiceReg 
        WHERE SaleCode = 'KOM'
        """
        
        code_check = db.execute_query(check_query)
        
        return jsonify({
            'equipment_sale_codes': [dict(row) for row in results] if results else [],
            'target_codes_check': [dict(row) for row in code_check] if code_check else [],
            'message': 'These are all the sale codes with equipment revenue since March 2025'
        })
        
    except Exception as e:
        logger.error(f"Sale codes check error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_optimized_bp.route('/api/dashboard-optimized/equipment-debug', methods=['GET'])
@jwt_required()
def debug_equipment_sales():
    """Debug endpoint for equipment sales data"""
    try:
        db = DatabaseService()
        result = {}
        
        # Test 1: Check if we have any equipment sales
        test1_query = """
        SELECT TOP 10
            InvoiceNo,
            InvoiceDate,
            SaleCode,
            EquipmentTaxable,
            EquipmentNonTax,
            EquipmentCost
        FROM ben002.InvoiceReg
        WHERE SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'KOM')
            AND InvoiceDate >= '2025-03-01'
        ORDER BY InvoiceDate DESC
        """
        
        try:
            invoices = db.execute_query(test1_query)
            result['invoice_samples'] = [dict(row) for row in invoices] if invoices else []
            result['invoice_count'] = len(invoices) if invoices else 0
        except Exception as e:
            result['invoice_samples'] = []
            result['invoice_error'] = str(e)
        
        # Test 2: Check ALL sale codes that have equipment revenue
        test2_query = """
        SELECT DISTINCT SaleCode, COUNT(*) as count
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '2025-03-01'
            AND (EquipmentTaxable > 0 OR EquipmentNonTax > 0)
        GROUP BY SaleCode
        ORDER BY count DESC
        """
        
        try:
            all_codes = db.execute_query(test2_query)
            result['all_equipment_sale_codes'] = [dict(row) for row in all_codes] if all_codes else []
        except Exception as e:
            result['sale_codes_error'] = str(e)
        
        # Test 3: Check if InvoiceSales table exists
        test3_query = """
        SELECT COUNT(*) as total_count
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'InvoiceSales'
        """
        
        try:
            table_exists = db.execute_query(test3_query)
            result['invoice_sales_exists'] = bool(table_exists and table_exists[0]['total_count'] > 0)
        except Exception as e:
            result['invoice_sales_exists'] = False
            result['table_check_error'] = str(e)
        
        # Test 4: Monthly aggregation without InvoiceSales
        test4_query = """
        SELECT 
            YEAR(InvoiceDate) as year,
            MONTH(InvoiceDate) as month,
            COUNT(*) as invoice_count,
            SUM(CASE 
                WHEN SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'KOM')
                THEN COALESCE(EquipmentTaxable, 0) + COALESCE(EquipmentNonTax, 0)
                ELSE 0
            END) as equipment_revenue
        FROM ben002.InvoiceReg
        WHERE InvoiceDate >= '2025-03-01'
            AND SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'KOM')
        GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
        ORDER BY year, month
        """
        
        try:
            monthly_data = db.execute_query(test4_query)
            result['monthly_aggregation'] = [dict(row) for row in monthly_data] if monthly_data else []
        except Exception as e:
            result['monthly_error'] = str(e)
        
        # If InvoiceSales exists, try to query it
        if result.get('invoice_sales_exists'):
            test5_query = """
            SELECT TOP 5
                InvoiceNo,
                SaleCode,
                Qty,
                SerialNo,
                UnitNo,
                Description
            FROM ben002.InvoiceSales
            WHERE SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'KOM')
            """
            try:
                sales_sample = db.execute_query(test5_query)
                result['invoice_sales_samples'] = [dict(row) for row in sales_sample] if sales_sample else []
            except Exception as e:
                result['invoice_sales_error'] = str(e)
        
        result['message'] = 'Debug data for equipment sales'
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Equipment sales debug error: {str(e)}")
        return jsonify({'error': str(e), 'message': 'Failed to run debug'}), 500

@dashboard_optimized_bp.route('/api/dashboard-optimized/equipment-sales-details', methods=['GET'])
@jwt_required()
def get_equipment_sales_details_endpoint():
    """Get detailed equipment sales information with unit counts"""
    try:
        db = get_db_connection()
        
        # Get date range from query params
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date:
            start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # For now, get equipment sales summary from InvoiceReg
        # We can't get individual unit details without proper table relationships
        query = f"""
        SELECT 
            ir.InvoiceNo,
            ir.InvoiceDate,
            ir.BillTo as CustomerNo,
            ir.BillToName as CustomerName,
            ir.SaleCode,
            ir.Salesman1,
            ir.EquipmentTaxable + COALESCE(ir.EquipmentNonTax, 0) as SellPrice,
            ir.EquipmentCost as CostPrice,
            ir.WONo
        FROM ben002.InvoiceReg ir
        WHERE ir.InvoiceDate >= '{start_date}'
            AND ir.InvoiceDate <= '{end_date}'
            AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
        ORDER BY ir.InvoiceDate DESC
        """
        
        results = db.execute_query(query)
        
        equipment_sales = []
        total_revenue = 0
        total_cost = 0
        sale_code_summary = {}
        
        if results:
            for row in results:
                sell_price = float(row['SellPrice'] or 0)
                cost_price = float(row['CostPrice'] or 0)
                gp_percent = 0
                if sell_price > 0:
                    gp_percent = round(((sell_price - cost_price) / sell_price) * 100, 1)
                
                equipment_sales.append({
                    'invoice_no': row['InvoiceNo'],
                    'invoice_date': row['InvoiceDate'].strftime('%Y-%m-%d') if row['InvoiceDate'] else None,
                    'customer_no': row['CustomerNo'],
                    'customer_name': row['CustomerName'],
                    'sell_price': sell_price,
                    'cost_price': cost_price,
                    'gp_amount': sell_price - cost_price,
                    'gp_percent': gp_percent,
                    'sale_code': row['SaleCode'],
                    'salesman': row['Salesman1'],
                    'wo_no': row['WONo']
                })
                
                total_revenue += sell_price
                total_cost += cost_price
                
                # Track by sale code instead of model
                sale_code = row['SaleCode'] or 'Unknown'
                if sale_code not in sale_code_summary:
                    sale_code_summary[sale_code] = {'qty': 0, 'revenue': 0, 'cost': 0}
                sale_code_summary[sale_code]['qty'] += 1
                sale_code_summary[sale_code]['revenue'] += sell_price
                sale_code_summary[sale_code]['cost'] += cost_price
        
        # Format sale code summary
        code_summary = []
        for code, data in sale_code_summary.items():
            gp = 0
            if data['revenue'] > 0:
                gp = round(((data['revenue'] - data['cost']) / data['revenue']) * 100, 1)
            code_summary.append({
                'sale_code': code,
                'qty': data['qty'],
                'total_sales': data['revenue'],
                'gp_percent': gp
            })
        
        return jsonify({
            'details': equipment_sales,
            'summary': {
                'total_units': len(equipment_sales),
                'total_revenue': total_revenue,
                'total_cost': total_cost,
                'total_gp': total_revenue - total_cost,
                'overall_gp_percent': round(((total_revenue - total_cost) / total_revenue) * 100, 1) if total_revenue > 0 else 0
            },
            'by_sale_code': code_summary,
            'date_range': {
                'start': start_date,
                'end': end_date
            }
        })
        
    except Exception as e:
        logger.error(f"Failed to get equipment sales details: {str(e)}")
        return jsonify({'error': str(e)}), 500

@dashboard_optimized_bp.route('/api/reports/dashboard/invalidate-cache', methods=['POST'])
@jwt_required()
def invalidate_dashboard_cache():
    """Invalidate dashboard cache - useful after data updates"""
    try:
        cache_service.invalidate_dashboard()
        return jsonify({
            'success': True,
            'message': 'Dashboard cache invalidated'
        })
    except Exception as e:
        logger.error(f"Failed to invalidate cache: {str(e)}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500