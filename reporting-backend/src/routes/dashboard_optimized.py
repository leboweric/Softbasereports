from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from src.services.azure_sql_service import AzureSQLService

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
    
    def get_monthly_sales(self):
        """Get monthly sales for last 12 months"""
        try:
            query = f"""
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                SUM(GrandTotal) as amount
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{self.twelve_months_ago}'
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
            
            # Pad with zeros for missing months
            if len(monthly_sales) < 12:
                all_months = []
                for i in range(11, -1, -1):
                    month_date = self.current_date - timedelta(days=i*30)
                    all_months.append(month_date.strftime("%b"))
                
                existing_data = {item['month']: item['amount'] for item in monthly_sales}
                monthly_sales = [{'month': month, 'amount': existing_data.get(month, 0)} for month in all_months]
            
            return monthly_sales
        except Exception as e:
            logger.error(f"Monthly sales query failed: {str(e)}")
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
        """Get monthly quotes since March"""
        try:
            query = """
            SELECT 
                YEAR(CreationTime) as year,
                MONTH(CreationTime) as month,
                SUM(Amount) as amount
            FROM ben002.WOQuote
            WHERE CreationTime >= '2025-03-01'
            AND Amount > 0
            GROUP BY YEAR(CreationTime), MONTH(CreationTime)
            ORDER BY YEAR(CreationTime), MONTH(CreationTime)
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
                    top_customers.append({
                        'rank': i + 1,
                        'name': customer['customer_name'],
                        'sales': float(customer['total_sales']),
                        'invoice_count': int(customer['invoice_count'])
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
            query = f"""
            SELECT 
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                -- Parts calculations
                SUM(CASE WHEN SaleCode IN ('PARTS', 'PARTSNT', 'FREIGHT', 'SHOPSP') 
                    THEN GrandTotal ELSE 0 END) as parts_sales,
                SUM(CASE WHEN SaleCode IN ('PARTS', 'PARTSNT', 'FREIGHT', 'SHOPSP') 
                    THEN ISNULL(PartsCost, 0) ELSE 0 END) as parts_cost,
                -- Labor calculations  
                SUM(CASE WHEN SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                    'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                    'RENTR', 'RENT-DEL', 'MO-RENT')
                    THEN GrandTotal ELSE 0 END) as labor_sales,
                SUM(CASE WHEN SaleCode IN ('RDCST', 'SHPCST', 'FMROAD', 'FMSHOP', 'PM', 'PM-FM', 'EDCO', 
                    'RENTPM', 'NEWEQP-R', 'SERVP-A', 'SERVP-A-S', 'NEQPREP', 'USEDEQP',
                    'RENTR', 'RENT-DEL', 'MO-RENT')
                    THEN ISNULL(LaborCost, 0) ELSE 0 END) as labor_cost,
                -- Equipment calculations
                SUM(CASE WHEN SaleCode IN ('USEDEQ', 'RTLEQP', 'ALLIEDE', 'NEWEQP') 
                    THEN GrandTotal ELSE 0 END) as equipment_sales,
                SUM(CASE WHEN SaleCode IN ('USEDEQ', 'RTLEQP', 'ALLIEDE', 'NEWEQP') 
                    THEN ISNULL(EquipmentCost, 0) ELSE 0 END) as equipment_cost,
                -- Rental calculations
                SUM(CASE WHEN SaleCode IN ('RENT', 'DLVPKUP', 'DAMAGE', 'DAMAGE-', 'STRENT', 'HRENT', 'LIFTTRK', 'STRENT+') 
                    THEN GrandTotal ELSE 0 END) as rental_sales,
                SUM(CASE WHEN SaleCode IN ('RENT', 'DLVPKUP', 'DAMAGE', 'DAMAGE-', 'STRENT', 'HRENT', 'LIFTTRK', 'STRENT+') 
                    THEN ISNULL(RentalCost, 0) ELSE 0 END) as rental_cost
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
                    
                    # Calculate margins
                    parts_margin = 0
                    if row['parts_sales'] > 0:
                        parts_margin = ((row['parts_sales'] - row['parts_cost']) / row['parts_sales']) * 100
                    
                    labor_margin = 0
                    if row['labor_sales'] > 0:
                        labor_margin = ((row['labor_sales'] - row['labor_cost']) / row['labor_sales']) * 100
                    
                    equipment_margin = 0
                    if row['equipment_sales'] > 0:
                        equipment_margin = ((row['equipment_sales'] - row['equipment_cost']) / row['equipment_sales']) * 100
                    
                    rental_margin = 0
                    if row['rental_sales'] > 0:
                        rental_margin = ((row['rental_sales'] - row['rental_cost']) / row['rental_sales']) * 100
                    
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


@dashboard_optimized_bp.route('/api/reports/dashboard/summary-optimized', methods=['GET'])
@jwt_required()
def get_dashboard_summary_optimized():
    """Optimized dashboard endpoint using parallel query execution"""
    start_time = time.time()
    
    try:
        db = AzureSQLService()
        queries = DashboardQueries(db)
        
        # Define all query tasks
        query_tasks = {
            'total_sales': queries.get_current_month_sales,
            'inventory_count': queries.get_inventory_count,
            'active_customers': queries.get_active_customers,
            'monthly_sales': queries.get_monthly_sales,
            'uninvoiced': queries.get_uninvoiced_work_orders,
            'monthly_quotes': queries.get_monthly_quotes,
            'work_order_types': queries.get_work_order_types,
            'top_customers': queries.get_top_customers,
            'monthly_work_orders': queries.get_monthly_work_orders_by_type,
            'department_margins': queries.get_department_margins
        }
        
        # Execute queries in parallel
        results = {}
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
            'uninvoiced_work_orders': int(uninvoiced_data['value']),
            'uninvoiced_count': uninvoiced_data['count'],
            'open_work_orders_value': int(wo_types_data['total_value']),
            'open_work_orders_count': wo_types_data['total_count'],
            'work_order_types': wo_types_data['types'],
            'monthly_sales': results.get('monthly_sales', []),
            'monthly_quotes': results.get('monthly_quotes', []),
            'top_customers': results.get('top_customers', []),
            'monthly_work_orders_by_type': results.get('monthly_work_orders', []),
            'department_margins': results.get('department_margins', []),
            'period': datetime.now().strftime('%B %Y'),
            'last_updated': datetime.now().isoformat(),
            'query_time': round(time.time() - start_time, 2)
        }
        
        logger.info(f"Optimized dashboard loaded in {response_data['query_time']} seconds")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in optimized dashboard: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Failed to load dashboard data',
            'message': str(e)
        }), 500