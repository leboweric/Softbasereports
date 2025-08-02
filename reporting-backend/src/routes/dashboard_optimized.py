from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from src.services.azure_sql_service import AzureSQLService
from src.services.cache_service import cache_service

logger = logging.getLogger(__name__)

dashboard_optimized_bp = Blueprint('dashboard_optimized', __name__)

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
        """Get current month's total sales"""
        try:
            query = f"""
            SELECT COALESCE(SUM(GrandTotal), 0) as total_sales
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{self.month_start}'
            AND MONTH(InvoiceDate) = {self.current_date.month}
            AND YEAR(InvoiceDate) = {self.current_date.year}
            """
            result = self.db.execute_query(query)
            return int(float(result[0]['total_sales'])) if result else 0
        except Exception as e:
            logger.error(f"Current month sales query failed: {str(e)}")
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
        """Get count of active customers in last 30 days"""
        try:
            query = f"""
            SELECT COUNT(DISTINCT BillToName) as active_customers
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{self.thirty_days_ago}'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            """
            result = self.db.execute_query(query)
            return int(result[0]['active_customers']) if result else 0
        except Exception as e:
            logger.error(f"Active customers query failed: {str(e)}")
            return 0
    
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
                SELECT COUNT(DISTINCT BillToName) as total_customers
                FROM ben002.InvoiceReg
                WHERE BillToName IS NOT NULL
                AND BillToName != ''
                """
                result = self.db.execute_query(query)
                return int(result[0]['total_customers']) if result else 0
            except Exception as e2:
                logger.error(f"Fallback total customers query failed: {str(e2)}")
                return 0
    
    def get_monthly_sales(self):
        """Get monthly sales since March 2025"""
        try:
            query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(GrandTotal) as amount
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '2025-03-01'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            results = self.db.execute_query(query)
            
            monthly_sales = []
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_sales.append({
                        'month': month_date.strftime("%b"),
                        'amount': float(row['amount'])
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
            
            existing_data = {item['month']: item['amount'] for item in monthly_sales}
            monthly_sales = [{'month': month, 'amount': existing_data.get(month, 0)} for month in all_months]
            
            return monthly_sales
        except Exception as e:
            logger.error(f"Monthly sales query failed: {str(e)}")
            return []
    
    def get_monthly_sales_excluding_equipment(self):
        """Get monthly sales since March 2025 excluding equipment sales"""
        try:
            query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(GrandTotal - COALESCE(EquipmentTaxable, 0) - COALESCE(EquipmentNonTax, 0)) as amount
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '2025-03-01'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            results = self.db.execute_query(query)
            
            monthly_sales = []
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_sales.append({
                        'month': month_date.strftime("%b"),
                        'amount': float(row['amount'])
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
            
            existing_data = {item['month']: item['amount'] for item in monthly_sales}
            monthly_sales = [{'month': month, 'amount': existing_data.get(month, 0)} for month in all_months]
            
            return monthly_sales
        except Exception as e:
            logger.error(f"Monthly sales excluding equipment query failed: {str(e)}")
            return []
    
    def get_monthly_sales_by_stream(self):
        """Get monthly sales by revenue stream since March 2025"""
        try:
            query = """
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue,
                SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as labor_revenue,
                SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as rental_revenue,
                SUM(COALESCE(MiscTaxable, 0) + COALESCE(MiscNonTax, 0)) as misc_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '2025-03-01'
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            results = self.db.execute_query(query)
            
            monthly_data = []
            if results:
                for row in results:
                    month_date = datetime(row['year'], row['month'], 1)
                    monthly_data.append({
                        'month': month_date.strftime("%b"),
                        'parts': float(row['parts_revenue'] or 0),
                        'labor': float(row['labor_revenue'] or 0),
                        'rental': float(row['rental_revenue'] or 0),
                        'misc': float(row['misc_revenue'] or 0)
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
            
            existing_months = [item['month'] for item in monthly_data]
            existing_data = {item['month']: item for item in monthly_data}
            
            monthly_data = []
            for month in all_months:
                if month in existing_data:
                    monthly_data.append(existing_data[month])
                else:
                    monthly_data.append({
                        'month': month, 
                        'parts': 0,
                        'labor': 0,
                        'rental': 0,
                        'misc': 0
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
                SELECT WONo, SUM(Sell) as parts_total 
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
                        'amount': float(row['amount'])
                    })
            
            # Pad missing months
            start_date = datetime(2025, 3, 1)
            all_months = []
            date = start_date
            while date <= self.current_date:
                all_months.append(date.strftime("%b"))
                if date.month == 12:
                    date = date.replace(year=date.year + 1, month=1)
                else:
                    date = date.replace(month=date.month + 1)
            
            existing_quotes = {item['month']: item['amount'] for item in monthly_quotes}
            monthly_quotes = [{'month': month, 'amount': existing_quotes.get(month, 0)} for month in all_months]
            
            return monthly_quotes
        except Exception as e:
            logger.error(f"Monthly quotes query failed: {str(e)}")
            return []
    
    def get_work_order_types(self):
        """Get work order types breakdown"""
        try:
            query = """
            SELECT 
                CASE 
                    WHEN Type = 'S' THEN 'Service'
                    WHEN Type = 'R' THEN 'Rental'
                    WHEN Type = 'P' THEN 'Parts'
                    WHEN Type = 'PM' THEN 'Preventive Maintenance'
                    WHEN Type = 'SH' THEN 'Shop'
                    WHEN Type = 'E' THEN 'Equipment'
                    WHEN Type IS NULL THEN 'Unspecified'
                    ELSE Type
                END as type_name,
                COUNT(*) as count,
                SUM(
                    COALESCE(l.labor_total, 0) + 
                    COALESCE(p.parts_total, 0) + 
                    COALESCE(m.misc_total, 0)
                ) as total_value
            FROM ben002.WO w
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as labor_total 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ) l ON w.WONo = l.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as parts_total 
                FROM ben002.WOParts 
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_total 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            WHERE w.CompletedDate IS NULL
            AND w.ClosedDate IS NULL
            GROUP BY Type
            ORDER BY total_value DESC
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
            
            return {
                'types': work_order_types,
                'total_value': total_value,
                'total_count': total_count
            }
        except Exception as e:
            logger.error(f"Work order types query failed: {str(e)}")
            return {'types': [], 'total_value': 0, 'total_count': 0}
    
    def get_top_customers(self):
        """Get top 10 customers by fiscal YTD sales"""
        try:
            # First get total sales for the fiscal year
            total_sales_query = f"""
            SELECT SUM(GrandTotal) as total_sales
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{self.fiscal_year_start}'
            """
            total_result = self.db.execute_query(total_sales_query)
            total_fiscal_sales = float(total_result[0]['total_sales']) if total_result and total_result[0]['total_sales'] else 0
            
            query = f"""
            SELECT TOP 10
                CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    ELSE BillToName
                END as customer_name,
                COUNT(DISTINCT InvoiceNo) as invoice_count,
                SUM(GrandTotal) as total_sales
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{self.fiscal_year_start}'
            AND BillToName IS NOT NULL
            AND BillToName != ''
            GROUP BY 
                CASE 
                    WHEN BillToName IN ('Polaris Industries', 'Polaris') THEN 'Polaris Industries'
                    ELSE BillToName
                END
            ORDER BY SUM(GrandTotal) DESC
            """
            
            results = self.db.execute_query(query)
            top_customers = []
            
            if results:
                for i, customer in enumerate(results):
                    customer_sales = float(customer['total_sales'])
                    percentage = (customer_sales / total_fiscal_sales * 100) if total_fiscal_sales > 0 else 0
                    top_customers.append({
                        'rank': i + 1,
                        'name': customer['customer_name'],
                        'sales': customer_sales,
                        'invoice_count': int(customer['invoice_count']),
                        'percentage': round(percentage, 1)
                    })
            
            return top_customers
        except Exception as e:
            logger.error(f"Top customers query failed: {str(e)}")
            return []
    
    def get_monthly_work_orders_by_type(self):
        """Get monthly work orders by type since March"""
        try:
            query = """
            SELECT 
                YEAR(OpenDate) as year,
                MONTH(OpenDate) as month,
                Type,
                COUNT(*) as count,
                SUM(
                    COALESCE(l.labor_total, 0) + 
                    COALESCE(p.parts_total, 0) + 
                    COALESCE(m.misc_total, 0)
                ) as total_value
            FROM ben002.WO w
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as labor_total 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ) l ON w.WONo = l.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as parts_total 
                FROM ben002.WOParts 
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_total 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            WHERE w.OpenDate >= '2025-03-01'
            AND w.OpenDate IS NOT NULL
            GROUP BY YEAR(OpenDate), MONTH(OpenDate), Type
            ORDER BY YEAR(OpenDate), MONTH(OpenDate)
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
                COUNT(DISTINCT BillToName) as active_customers
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '2025-03-01'
            AND BillToName IS NOT NULL
            AND BillToName != ''
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


@dashboard_optimized_bp.route('/api/reports/dashboard/summary-optimized', methods=['GET'])
@jwt_required()
def get_dashboard_summary_optimized():
    """Optimized dashboard endpoint using parallel query execution and caching"""
    start_time = time.time()
    
    # Check for cache refresh parameter
    force_refresh = request.args.get('refresh', '').lower() == 'true'
    
    try:
        db = AzureSQLService()
        queries = DashboardQueries(db)
        
        # Cache TTL settings (in seconds)
        cache_ttl = {
            'total_sales': 300,  # 5 minutes - changes frequently
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
            'inventory_count': lambda: cached_query('inventory_count', queries.get_inventory_count, cache_ttl['inventory_count']),
            'active_customers': lambda: cached_query('active_customers', queries.get_active_customers, cache_ttl['active_customers']),
            'total_customers': lambda: cached_query('total_customers', queries.get_total_customers, cache_ttl['active_customers']),
            'monthly_sales': lambda: cached_query('monthly_sales', queries.get_monthly_sales, cache_ttl['monthly_sales']),
            'monthly_sales_no_equipment': lambda: cached_query('monthly_sales_no_equipment', queries.get_monthly_sales_excluding_equipment, cache_ttl['monthly_sales']),
            'monthly_sales_by_stream': lambda: cached_query('monthly_sales_by_stream', queries.get_monthly_sales_by_stream, cache_ttl['monthly_sales']),
            'uninvoiced': lambda: cached_query('uninvoiced', queries.get_uninvoiced_work_orders, cache_ttl['uninvoiced']),
            'monthly_quotes': lambda: cached_query('monthly_quotes', queries.get_monthly_quotes, cache_ttl['monthly_quotes']),
            'work_order_types': lambda: cached_query('work_order_types', queries.get_work_order_types, cache_ttl['work_order_types']),
            'top_customers': lambda: cached_query('top_customers', queries.get_top_customers, cache_ttl['top_customers']),
            'monthly_work_orders': lambda: cached_query('monthly_work_orders', queries.get_monthly_work_orders_by_type, cache_ttl['monthly_work_orders']),
            'department_margins': lambda: cached_query('department_margins', queries.get_department_margins, cache_ttl['department_margins']),
            'monthly_active_customers': lambda: cached_query('monthly_active_customers', queries.get_monthly_active_customers, cache_ttl['active_customers'])
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
        wo_types_data = results.get('work_order_types', {'types': [], 'total_value': 0, 'total_count': 0})
        
        response_data = {
            'total_sales': results.get('total_sales', 0),
            'inventory_count': results.get('inventory_count', 0),
            'active_customers': results.get('active_customers', 0),
            'total_customers': results.get('total_customers', 0),
            'uninvoiced_work_orders': int(uninvoiced_data['value']),
            'uninvoiced_count': uninvoiced_data['count'],
            'open_work_orders_value': int(wo_types_data['total_value']),
            'open_work_orders_count': wo_types_data['total_count'],
            'work_order_types': wo_types_data['types'],
            'monthly_sales': results.get('monthly_sales', []),
            'monthly_sales_no_equipment': results.get('monthly_sales_no_equipment', []),
            'monthly_sales_by_stream': results.get('monthly_sales_by_stream', []),
            'monthly_quotes': results.get('monthly_quotes', []),
            'top_customers': results.get('top_customers', []),
            'monthly_work_orders_by_type': results.get('monthly_work_orders', []),
            'department_margins': results.get('department_margins', []),
            'monthly_active_customers': results.get('monthly_active_customers', []),
            'period': datetime.now().strftime('%B %Y'),
            'last_updated': datetime.now().isoformat(),
            'query_time': round(time.time() - start_time, 2),
            'cache_enabled': cache_service.enabled,
            'from_cache': not force_refresh and cache_service.enabled
        }
        
        logger.info(f"Optimized dashboard loaded in {response_data['query_time']} seconds (cache: {response_data['from_cache']})")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in optimized dashboard: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to load dashboard data',
            'message': str(e)
        }), 500


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