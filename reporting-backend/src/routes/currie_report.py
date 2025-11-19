"""
Currie Financial Model Report API
Automates quarterly Currie reporting by extracting data from Softbase
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.azure_sql_service import AzureSQLService
from datetime import datetime, timedelta
import logging
import calendar

logger = logging.getLogger(__name__)

currie_bp = Blueprint('currie', __name__)
sql_service = AzureSQLService()

@currie_bp.route('/api/currie/sales-cogs-gp', methods=['GET'])
@jwt_required()
def get_sales_cogs_gp():
    """
    Get Sales, COGS, and Gross Profit data for Currie Financial Model
    Query params: start_date, end_date
    """
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Calculate number of months
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        months_diff = (end.year - start.year) * 12 + end.month - start.month + 1
        
        # Get all revenue and COGS data
        data = {
            'dealership_info': {
                'name': 'Bennett Material Handling',  # TODO: Make configurable
                'submitted_by': get_jwt_identity(),
                'date': datetime.now().strftime('%Y-%m-%d'),
                'num_locations': 1,  # TODO: Make configurable
                'num_months': months_diff,
                'start_date': start_date,
                'end_date': end_date
            },
            'new_equipment': get_new_equipment_sales(start_date, end_date),
            'rental': get_rental_revenue(start_date, end_date),
            'service': get_service_revenue(start_date, end_date),
            'parts': get_parts_revenue(start_date, end_date),
            'trucking': get_trucking_revenue(start_date, end_date)
        }
        
        # Calculate totals
        data['totals'] = calculate_totals(data, months_diff)
        
        # Get expenses for bottom summary section
        expenses = get_gl_expenses(start_date, end_date)
        data['expenses'] = expenses
        
        # Get other income and interest
        other_income_interest = get_other_income_and_interest(start_date, end_date)
        data['other_income'] = other_income_interest.get('other_income', 0)
        data['interest_expense'] = other_income_interest.get('interest_expense', 0)
        data['fi_income'] = other_income_interest.get('fi_income', 0)
        
        # Calculate bottom summary totals
        total_operating_profit = data['totals']['total_company']['gross_profit'] - expenses['grand_total'] + data['other_income'] + data['interest_expense']
        data['total_operating_profit'] = total_operating_profit
        data['pre_tax_income'] = total_operating_profit + data['fi_income']
        
        return jsonify(data), 200
        
    except Exception as e:
        logger.error(f"Error fetching Currie sales data: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_new_equipment_sales(start_date, end_date):
    """Get new equipment sales broken down by category using GLDetail table"""
    try:
        # Query for equipment sales and costs from GLDetail using approved GL accounts
        query = """
        SELECT 
            AccountNo,
            SUM(Amount) as total_amount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN (
            -- New Equipment Revenue
            '413001', '426001', '412001', '414001',
            -- New Equipment Cost
            '513001', '526001', '512001', '514001',
            -- Used Equipment Revenue
            '412002', '413002', '414002', '426002', '431002', '410002',
            -- Used Equipment Cost
            '512002', '513002', '514002', '526002', '531002', '510002'
          )
        GROUP BY AccountNo
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        # Initialize categories
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
        
        # Map GL accounts to categories
        for row in results:
            account = row['AccountNo']
            amount = float(row['total_amount'] or 0)
            
            # New Lift Truck - Primary Brand (LINDE)
            if account == '413001':
                categories['new_lift_truck_primary']['sales'] += -amount  # Revenue is credit (negative)
            elif account == '513001':
                categories['new_lift_truck_primary']['cogs'] += amount  # COGS is debit (positive)
            
            # New Lift Truck - Other Brands (KOMATSU)
            elif account == '426001':
                categories['new_lift_truck_other']['sales'] += -amount
            elif account == '526001':
                categories['new_lift_truck_other']['cogs'] += amount
            
            # New Allied Equipment
            elif account == '412001':
                categories['new_allied']['sales'] += -amount
            elif account == '512001':
                categories['new_allied']['cogs'] += amount
            
            # Batteries
            elif account == '414001':
                categories['batteries']['sales'] += -amount
            elif account == '514001':
                categories['batteries']['cogs'] += amount
            
            # Used Equipment (aggregate all used accounts)
            elif account in ('412002', '413002', '414002', '426002', '431002', '410002'):
                categories['used_equipment']['sales'] += -amount  # Revenue is credit (negative)
            elif account in ('512002', '513002', '514002', '526002', '531002', '510002'):
                categories['used_equipment']['cogs'] += amount  # COGS is debit (positive)
        
        # Calculate gross profit for each category
        for category in categories.values():
            category['gross_profit'] = category['sales'] - category['cogs']
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching new equipment sales: {str(e)}")
        return {}


def get_rental_revenue(start_date, end_date):
    """Get rental revenue as a single consolidated category using GLDetail"""
    try:
        # Query rental revenue and costs from GLDetail using approved GL accounts
        query = """
        SELECT 
            AccountNo,
            SUM(Amount) as total_amount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN (
            -- Rental Revenue
            '411001', '419000', '420000', '421000', '434012', '410008',
            -- Rental Cost
            '510008', '511001', '519000', '520000', '521008', '537001', '539000', '534014', '545000'
          )
        GROUP BY AccountNo
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        rental_data = {
            'sales': 0,
            'cogs': 0,
            'gross_profit': 0
        }
        
        # Revenue accounts
        revenue_accounts = ['411001', '419000', '420000', '421000', '434012', '410008']
        # Cost accounts
        cost_accounts = ['510008', '511001', '519000', '520000', '521008', '537001', '539000', '534014', '545000']
        
        for row in results:
            account = row['AccountNo']
            amount = float(row['total_amount'] or 0)
            
            if account in revenue_accounts:
                rental_data['sales'] += -amount  # Revenue is credit (negative)
            elif account in cost_accounts:
                rental_data['cogs'] += amount  # COGS is debit (positive)
        
        rental_data['gross_profit'] = rental_data['sales'] - rental_data['cogs']
        
        return rental_data
        
    except Exception as e:
        logger.error(f"Error fetching rental revenue: {str(e)}")
        return {}


def get_service_revenue(start_date, end_date):
    """Get service revenue broken down by customer, internal, warranty, sublet using GLDetail"""
    try:
        # Query service revenue from GLDetail table with exact GL accounts
        query = """
        SELECT 
            -- Customer Labor: Field (410004) + Shop (410005) + Full Maint (410007)
            -SUM(CASE WHEN AccountNo IN ('410004', '410005', '410007') THEN Amount ELSE 0 END) as customer_sales,
            SUM(CASE WHEN AccountNo IN ('510004', '510005', '510007') THEN Amount ELSE 0 END) as customer_cogs,
            
            -- Internal Labor (Field GM, Shop GM)
            -SUM(CASE WHEN AccountNo IN ('423000', '425000') THEN Amount ELSE 0 END) as internal_sales,
            SUM(CASE WHEN AccountNo = '523000' THEN Amount ELSE 0 END) as internal_cogs,
            
            -- Warranty Labor
            -SUM(CASE WHEN AccountNo IN ('435000', '435001', '435002', '435003', '435004') THEN Amount ELSE 0 END) as warranty_sales,
            SUM(CASE WHEN AccountNo IN ('535001', '535002', '535003', '535004', '535005') THEN Amount ELSE 0 END) as warranty_cogs,
            
            -- Sublet Sales
            -SUM(CASE WHEN AccountNo = '432000' THEN Amount ELSE 0 END) as sublet_sales,
            SUM(CASE WHEN AccountNo = '532000' THEN Amount ELSE 0 END) as sublet_cogs,
            
            -- Other Service Sales (PM Contracts, etc)
            -SUM(CASE WHEN AccountNo IN ('428000', '429002') THEN Amount ELSE 0 END) as other_sales,
            SUM(CASE WHEN AccountNo IN ('528000', '529001') THEN Amount ELSE 0 END) as other_cogs
        FROM ben002.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN (
              -- Customer Labor
              '410004', '410005', '410007', '510004', '510005', '510007',
              -- Internal Labor
              '423000', '425000', '523000',
              -- Warranty Labor
              '435000', '435001', '435002', '435003', '435004',
              '535001', '535002', '535003', '535004', '535005',
              -- Sublet
              '432000', '532000',
              -- Other Service
              '428000', '429002', '528000', '529001'
          )
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        service_data = {
            'customer_labor': {'sales': 0, 'cogs': 0},
            'internal_labor': {'sales': 0, 'cogs': 0},
            'warranty_labor': {'sales': 0, 'cogs': 0},
            'sublet': {'sales': 0, 'cogs': 0},
            'other': {'sales': 0, 'cogs': 0}
        }
        
        # Map query results to service_data
        if results and len(results) > 0:
            row = results[0]
            service_data['customer_labor']['sales'] = float(row['customer_sales'] or 0)
            service_data['customer_labor']['cogs'] = float(row['customer_cogs'] or 0)
            service_data['internal_labor']['sales'] = float(row['internal_sales'] or 0)
            service_data['internal_labor']['cogs'] = float(row['internal_cogs'] or 0)
            service_data['warranty_labor']['sales'] = float(row['warranty_sales'] or 0)
            service_data['warranty_labor']['cogs'] = float(row['warranty_cogs'] or 0)
            service_data['sublet']['sales'] = float(row['sublet_sales'] or 0)
            service_data['sublet']['cogs'] = float(row['sublet_cogs'] or 0)
            service_data['other']['sales'] = float(row['other_sales'] or 0)
            service_data['other']['cogs'] = float(row['other_cogs'] or 0)
        
        # Calculate gross profit
        for category in service_data.values():
            category['gross_profit'] = category['sales'] - category['cogs']
        
        return service_data
        
    except Exception as e:
        logger.error(f"Error fetching service revenue: {str(e)}")
        return {}


def get_parts_revenue(start_date, end_date):
    """Get parts revenue broken down by counter, RO, internal, warranty using GLDetail"""
    try:
        # Query parts sales and costs from GLDetail using approved GL accounts
        query = """
        SELECT 
            AccountNo,
            SUM(Amount) as total_amount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN (
            -- Counter Parts (Primary Brand - all counter goes here)
            '410003', '510003',
            -- RO Parts (Primary Brand - all RO goes here)
            '410012', '510012',
            -- Internal Parts
            '424000', '524000',
            -- Warranty Parts
            '410014', '510014'
          )
        GROUP BY AccountNo
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        parts_data = {
            'counter_primary': {'sales': 0, 'cogs': 0},
            'counter_other': {'sales': 0, 'cogs': 0},
            'ro_primary': {'sales': 0, 'cogs': 0},
            'ro_other': {'sales': 0, 'cogs': 0},
            'internal': {'sales': 0, 'cogs': 0},
            'warranty': {'sales': 0, 'cogs': 0},
            'ecommerce': {'sales': 0, 'cogs': 0}
        }
        
        # Map GL accounts to categories
        for row in results:
            account = row['AccountNo']
            amount = float(row['total_amount'] or 0)
            
            # Counter Primary Brand (all counter sales)
            if account == '410003':
                parts_data['counter_primary']['sales'] += -amount  # Revenue is credit (negative)
            elif account == '510003':
                parts_data['counter_primary']['cogs'] += amount  # COGS is debit (positive)
            
            # RO Primary Brand (all RO sales)
            elif account == '410012':
                parts_data['ro_primary']['sales'] += -amount
            elif account == '510012':
                parts_data['ro_primary']['cogs'] += amount
            
            # Internal Parts
            elif account == '424000':
                parts_data['internal']['sales'] += -amount
            elif account == '524000':
                parts_data['internal']['cogs'] += amount
            
            # Warranty Parts
            elif account == '410014':
                parts_data['warranty']['sales'] += -amount
            elif account == '510014':
                parts_data['warranty']['cogs'] += amount
        
        # Counter Other, RO Other, and E-commerce remain at $0
        
        # Calculate gross profit
        for category in parts_data.values():
            category['gross_profit'] = category['sales'] - category['cogs']
        
        return parts_data
        
    except Exception as e:
        logger.error(f"Error fetching parts revenue: {str(e)}")
        return {}


def get_trucking_revenue(start_date, end_date):
    """Get trucking/delivery revenue using GLDetail with all trucking GL accounts"""
    try:
        # Query trucking revenue from GLDetail table with exact GL accounts
        query = """
        SELECT 
            -- All Trucking Revenue Accounts
            -SUM(CASE WHEN AccountNo IN (
                '410010',  -- Sales - Trucking
                '421010',  -- SALES - FREIGHT - Trucking
                '434001',  -- SALES - TRUCKING/DELIVERY - New Equip
                '434002',  -- SALES - TRUCKING/DELIVERY - Used Equip
                '434003',  -- SALES - TRUCKING/DELIVERY - Parts
                '434010',  -- SALES - TRUCKING/DELIVERY - Trucking
                '434011',  -- SALES - TRUCKING/DELIVERY - G&A
                '434012',  -- SALES - TRUCKING/DELIVERY - RENTAL
                '434013'   -- SALES - TRUCKING/DELIVERY - SERVICE
            ) THEN Amount ELSE 0 END) as sales,
            
            -- All Trucking Cost Accounts
            SUM(CASE WHEN AccountNo IN (
                '510010',  -- COS - Trucking
                '521010',  -- COS - FREIGHT - Trucking
                '534001',  -- COS - TRUCKING/DELIVERY - New Equip
                '534002',  -- COS - TRUCKING/DELIVERY - Used Equip
                '534003',  -- COS - TRUCKING/DELIVERY - Parts
                '534010',  -- COS - TRUCKING/DELIVERY - Trucking
                '534011',  -- COS - TRUCKING/DELIVERY - G&A
                '534012',  -- COS - TRUCKING/DELIVERY - Customer
                '534013',  -- COS - TRUCKING/DELIVERY - New Equipment Demo
                '534014',  -- COS - TRUCKING/DELIVERY - Rental
                '534015'   -- COS - TRUCKING/DELIVERY - Service
            ) THEN Amount ELSE 0 END) as cogs
        FROM ben002.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN (
              -- Revenue accounts
              '410010', '421010', '434001', '434002', '434003', 
              '434010', '434011', '434012', '434013',
              -- Cost accounts
              '510010', '521010', '534001', '534002', '534003', 
              '534010', '534011', '534012', '534013', '534014', '534015'
          )
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        trucking_data = {
            'sales': 0,
            'cogs': 0,
            'gross_profit': 0
        }
        
        if results and len(results) > 0:
            row = results[0]
            trucking_data['sales'] = float(row['sales'] or 0)
            trucking_data['cogs'] = float(row['cogs'] or 0)
            trucking_data['gross_profit'] = trucking_data['sales'] - trucking_data['cogs']
        
        return trucking_data
        
    except Exception as e:
        logger.error(f"Error fetching trucking revenue: {str(e)}")
        return {}


def calculate_totals(data, num_months):
    """Calculate total sales, COGS, and GP across all categories with subtotals"""
    
    # Calculate subtotals for each section
    # TOTAL NEW EQUIPMENT = only first 4 items (matches Excel row 14)
    total_new_equipment = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
    if 'new_equipment' in data:
        # Only sum the first 4 equipment categories for TOTAL NEW EQUIPMENT subtotal
        new_eq_categories = ['new_lift_truck_primary', 'new_lift_truck_other', 'new_allied', 'other_new_equipment']
        for cat in new_eq_categories:
            if cat in data['new_equipment']:
                total_new_equipment['sales'] += data['new_equipment'][cat].get('sales', 0)
                total_new_equipment['cogs'] += data['new_equipment'][cat].get('cogs', 0)
        total_new_equipment['gross_profit'] = total_new_equipment['sales'] - total_new_equipment['cogs']
    
    # TOTAL SALES DEPT = all equipment items (matches Excel row 20)
    total_sales_dept = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
    if 'new_equipment' in data:
        for category in data['new_equipment'].values():
            total_sales_dept['sales'] += category.get('sales', 0)
            total_sales_dept['cogs'] += category.get('cogs', 0)
        total_sales_dept['gross_profit'] = total_sales_dept['sales'] - total_sales_dept['cogs']
    
    total_rental = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
    if 'rental' in data:
        # Rental is now a single object, not a dict of categories
        total_rental['sales'] = data['rental'].get('sales', 0)
        total_rental['cogs'] = data['rental'].get('cogs', 0)
        total_rental['gross_profit'] = total_rental['sales'] - total_rental['cogs']
    
    total_service = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
    if 'service' in data:
        for category in data['service'].values():
            total_service['sales'] += category.get('sales', 0)
            total_service['cogs'] += category.get('cogs', 0)
        total_service['gross_profit'] = total_service['sales'] - total_service['cogs']
    
    total_parts = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
    if 'parts' in data:
        for category in data['parts'].values():
            total_parts['sales'] += category.get('sales', 0)
            total_parts['cogs'] += category.get('cogs', 0)
        total_parts['gross_profit'] = total_parts['sales'] - total_parts['cogs']
    
    # Calculate combined totals
    total_aftermarket = {
        'sales': total_service['sales'] + total_parts['sales'],
        'cogs': total_service['cogs'] + total_parts['cogs'],
        'gross_profit': 0
    }
    total_aftermarket['gross_profit'] = total_aftermarket['sales'] - total_aftermarket['cogs']
    
    # Grand total uses total_sales_dept (all equipment) not just total_new_equipment (first 4)
    grand_total = {
        'sales': total_sales_dept['sales'] + total_rental['sales'] + total_service['sales'] + total_parts['sales'],
        'cogs': total_sales_dept['cogs'] + total_rental['cogs'] + total_service['cogs'] + total_parts['cogs'],
        'gross_profit': 0
    }
    
    # Add trucking to grand total
    if 'trucking' in data:
        grand_total['sales'] += data['trucking'].get('sales', 0)
        grand_total['cogs'] += data['trucking'].get('cogs', 0)
    
    grand_total['gross_profit'] = grand_total['sales'] - grand_total['cogs']
    
    # Calculate average monthly sales & GP
    avg_monthly_sales_gp = grand_total['sales'] / num_months if num_months > 0 else 0
    
    return {
        'total_new_equipment': total_new_equipment,  # Subtotal for first 4 items only (Excel row 14)
        'total_sales_dept': total_sales_dept,        # Grand total for all equipment (Excel row 20)
        'total_rental': total_rental,
        'total_service': total_service,
        'total_parts': total_parts,
        'total_aftermarket': total_aftermarket,
        'total_net_sales_gp': grand_total,  # Same as total_company but matches Excel naming
        'grand_total': grand_total,
        'total_company': grand_total,  # Alias for grand_total
        'avg_monthly_sales_gp': avg_monthly_sales_gp,
        # Keep legacy format for backward compatibility
        'sales': grand_total['sales'],
        'cogs': grand_total['cogs'],
        'gross_profit': grand_total['gross_profit']
    }


@currie_bp.route('/api/currie/metrics', methods=['GET'])
@jwt_required()
def get_currie_metrics():
    """Get metrics for Currie Financial Model"""
    try:
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Calculate number of days in period
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        num_days = (end - start).days + 1
        
        metrics = {}
        
        # 1. AR Aging
        metrics['ar_aging'] = get_ar_aging()
        
        # 2. Service Calls Per Day
        metrics['service_calls_per_day'] = get_service_calls_per_day(start_date, end_date, num_days)
        
        # 3. Technician Count
        metrics['technician_count'] = get_technician_count(start_date, end_date)
        
        # 4. Labor Metrics
        metrics['labor_metrics'] = get_labor_metrics(start_date, end_date)
        
        # 5. Parts Inventory Metrics
        metrics['parts_inventory'] = get_parts_inventory_metrics(start_date, end_date)
        
        # 6. Absorption Rate
        # Get revenue and expense data to calculate absorption rate
        num_months = (end - start).days / 30.44  # Average days per month
        data = {
            'rental': get_rental_revenue(start_date, end_date),
            'service': get_service_revenue(start_date, end_date),
            'parts': get_parts_revenue(start_date, end_date)
        }
        totals = calculate_totals(data, max(1, int(num_months)))
        expenses = get_gl_expenses(start_date, end_date)
        
        # Absorption Rate = (Aftermarket GP / Total Expenses) × 100
        aftermarket_gp = totals.get('total_aftermarket', {}).get('gross_profit', 0)
        rental_gp = totals.get('total_rental', {}).get('gross_profit', 0)
        total_aftermarket_gp = aftermarket_gp + rental_gp
        
        total_expenses = (
            expenses.get('personnel', {}).get('total', 0) +
            expenses.get('operating', {}).get('total', 0) +
            expenses.get('occupancy', {}).get('total', 0)
        )
        
        absorption_rate = (total_aftermarket_gp / total_expenses * 100) if total_expenses > 0 else 0
        
        metrics['absorption_rate'] = {
            'rate': round(absorption_rate, 1),
            'aftermarket_gp': round(total_aftermarket_gp, 2),
            'total_expenses': round(total_expenses, 2)
        }
        
        return jsonify({
            'metrics': metrics,
            'date_range': {
                'start_date': start_date,
                'end_date': end_date,
                'num_days': num_days
            },
            'generated_at': datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching Currie metrics: {str(e)}")
        return jsonify({'error': 'Failed to fetch metrics', 'message': str(e)}), 500


def get_ar_aging():
    """Get AR aging buckets (reusing logic from department_reports)"""
    try:
        # Get total AR
        total_ar_query = """
        SELECT SUM(Amount) as total_ar
        FROM ben002.ARDetail
        WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
            AND DeletionTime IS NULL
        """
        total_ar_result = sql_service.execute_query(total_ar_query, [])
        total_ar = float(total_ar_result[0]['total_ar']) if total_ar_result and total_ar_result[0]['total_ar'] else 0
        
        # Get AR aging buckets
        ar_query = """
        WITH InvoiceBalances AS (
            SELECT 
                ar.InvoiceNo,
                ar.CustomerNo,
                MIN(ar.Due) as Due,
                SUM(ar.Amount) as NetBalance
            FROM ben002.ARDetail ar
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
        
        ar_results = sql_service.execute_query(ar_query, [])
        
        # Format results for Currie (Current, 31-60, 61-90, 91+)
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


def get_service_calls_per_day(start_date, end_date, num_days):
    """Calculate average service calls per day"""
    try:
        query = """
        SELECT COUNT(*) as total_service_calls
        FROM ben002.WO
        WHERE OpenDate >= %s 
          AND OpenDate <= %s
          AND SaleDept IN ('40', '45', '47')  -- Field Service (40), Shop Service (45), PM (47)
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        total_calls = int(results[0]['total_service_calls']) if results and results[0]['total_service_calls'] else 0
        calls_per_day = total_calls / num_days if num_days > 0 else 0
        
        return {
            'total_service_calls': total_calls,
            'calls_per_day': round(calls_per_day, 2),
            'num_days': num_days
        }
        
    except Exception as e:
        logger.error(f"Error calculating service calls per day: {str(e)}")
        return {}


def get_technician_count(start_date, end_date):
    """Count unique technicians who worked during the period"""
    try:
        query = """
        SELECT COUNT(DISTINCT Technician) as technician_count
        FROM ben002.WO
        WHERE OpenDate >= %s 
          AND OpenDate <= %s
          AND Technician IS NOT NULL
          AND Technician != ''
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        count = int(results[0]['technician_count']) if results and results[0]['technician_count'] else 0
        
        return {
            'active_technicians': count
        }
        
    except Exception as e:
        logger.error(f"Error counting technicians: {str(e)}")
        return {}


def get_parts_inventory_metrics(start_date, end_date):
    """Get parts inventory metrics: fill rate, turnover, aging"""
    try:
        # Calculate days in period
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days_in_period = (end - start).days + 1
        
        # 1. Fill Rate - percentage of orders filled from stock
        fill_rate_query = f"""
        WITH PartsOrders AS (
            SELECT 
                wp.PartNo,
                wp.BOQty as BackorderQty,
                COALESCE(p.OnHand, 0) as CurrentStock,
                CASE 
                    WHEN wp.BOQty > 0 THEN 'Backordered'
                    WHEN p.OnHand IS NULL OR p.OnHand = 0 THEN 'Out of Stock'
                    WHEN p.OnHand < wp.Qty THEN 'Partial Stock'
                    ELSE 'In Stock'
                END as StockStatus
            FROM ben002.WOParts wp
            INNER JOIN ben002.WO w ON wp.WONo = w.WONo
            LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
            WHERE w.OpenDate >= %s AND w.OpenDate <= %s
        )
        SELECT 
            COUNT(*) as TotalOrders,
            SUM(CASE WHEN StockStatus = 'In Stock' THEN 1 ELSE 0 END) as FilledOrders
        FROM PartsOrders
        """
        
        fill_rate_result = sql_service.execute_query(fill_rate_query, [start_date, end_date])
        
        total_orders = int(fill_rate_result[0]['TotalOrders'] or 0) if fill_rate_result else 0
        filled_orders = int(fill_rate_result[0]['FilledOrders'] or 0) if fill_rate_result else 0
        fill_rate = (filled_orders / total_orders * 100) if total_orders > 0 else 0
        
        # 2. Inventory Value - TOTAL current inventory (not period-specific)
        inventory_query = """
        SELECT SUM(OnHand * Cost) as TotalInventoryValue
        FROM ben002.Parts
        WHERE OnHand > 0 AND Cost > 0
        """
        
        inventory_result = sql_service.execute_query(inventory_query, [])
        inventory_value = float(inventory_result[0]['TotalInventoryValue'] or 0) if inventory_result else 0
        
        # 3. Inventory Turnover - annualized based on period movement
        turnover_query = """
        SELECT 
            SUM(wp.Qty * p.Cost) as TotalCOGS
        FROM ben002.WOParts wp
        INNER JOIN ben002.WO w ON wp.WONo = w.WONo
        LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
        WHERE w.OpenDate >= %s AND w.OpenDate <= %s
        """
        
        turnover_result = sql_service.execute_query(turnover_query, [start_date, end_date])
        cogs = float(turnover_result[0]['TotalCOGS'] or 0) if turnover_result else 0
        
        # Annualize the turnover (COGS for period / avg inventory) * (365 / days in period)
        turnover_rate = (cogs / inventory_value * (365 / days_in_period)) if (inventory_value > 0 and days_in_period > 0) else 0
        
        # 4. Inventory Aging - parts with no movement in 90+ days
        aging_query = f"""
        WITH PartMovement AS (
            SELECT 
                p.PartNo,
                MAX(p.OnHand) as CurrentStock,
                MAX(p.Cost) as Cost,
                MAX(w.OpenDate) as LastMovementDate
            FROM ben002.Parts p
            LEFT JOIN ben002.WOParts wp ON p.PartNo = wp.PartNo
            LEFT JOIN ben002.WO w ON wp.WONo = w.WONo
            WHERE p.OnHand > 0
            GROUP BY p.PartNo
        )
        SELECT 
            COUNT(CASE WHEN DATEDIFF(day, LastMovementDate, GETDATE()) > 365 OR LastMovementDate IS NULL THEN 1 END) as Obsolete,
            COUNT(CASE WHEN DATEDIFF(day, LastMovementDate, GETDATE()) BETWEEN 181 AND 365 THEN 1 END) as Slow,
            COUNT(CASE WHEN DATEDIFF(day, LastMovementDate, GETDATE()) BETWEEN 91 AND 180 THEN 1 END) as Medium,
            COUNT(CASE WHEN DATEDIFF(day, LastMovementDate, GETDATE()) <= 90 THEN 1 END) as Fast,
            SUM(CASE WHEN DATEDIFF(day, LastMovementDate, GETDATE()) > 365 OR LastMovementDate IS NULL THEN CurrentStock * Cost ELSE 0 END) as ObsoleteValue
        FROM PartMovement
        """
        
        aging_result = sql_service.execute_query(aging_query, [])
        
        if aging_result and len(aging_result) > 0:
            aging = aging_result[0]
            return {
                'fill_rate': round(fill_rate, 1),
                'total_orders': total_orders,
                'filled_orders': filled_orders,
                'inventory_turnover': round(turnover_rate, 2),
                'inventory_value': round(inventory_value, 2),
                'aging': {
                    'obsolete_count': int(aging.get('Obsolete', 0)),
                    'slow_count': int(aging.get('Slow', 0)),
                    'medium_count': int(aging.get('Medium', 0)),
                    'fast_count': int(aging.get('Fast', 0)),
                    'obsolete_value': round(float(aging.get('ObsoleteValue', 0)), 2)
                }
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Error fetching parts inventory metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}


def get_labor_metrics(start_date, end_date):
    """Get labor productivity metrics from WOLabor"""
    try:
        # Use the same pattern as other successful queries: SUM(Sell) for labor value
        query = """
        SELECT 
            COUNT(DISTINCT l.WONo) as wo_count,
            SUM(l.Hours) as total_hours,
            CASE 
                WHEN SUM(l.Hours) > 0 THEN SUM(l.Sell) / SUM(l.Hours)
                ELSE 0 
            END as avg_rate,
            SUM(l.Sell) as total_labor_value
        FROM ben002.WOLabor l
        INNER JOIN ben002.WO w ON l.WONo = w.WONo
        WHERE w.OpenDate >= %s 
          AND w.OpenDate <= %s
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        if results and len(results) > 0:
            row = results[0]
            return {
                'work_orders_with_labor': int(row['wo_count'] or 0),
                'total_billed_hours': float(row['total_hours'] or 0),
                'average_labor_rate': float(row['avg_rate'] or 0),
                'total_labor_value': float(row['total_labor_value'] or 0)
            }
        
        return {}
        
    except Exception as e:
        logger.error(f"Error fetching labor metrics: {str(e)}")
        return {}


@currie_bp.route('/api/currie/export-excel', methods=['GET'])
@jwt_required()
def export_currie_excel():
    """Export Currie Financial Model to Excel using template"""
    try:
        import openpyxl
        from openpyxl.utils import get_column_letter
        from flask import send_file
        import os
        from datetime import datetime
        import io
        
        # Get date range from query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Calculate number of months and days
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        months_diff = (end.year - start.year) * 12 + (end.month - start.month) + 1
        num_days = (end - start).days + 1
        
        # Get all the data
        new_equipment = get_new_equipment_sales(start_date, end_date)
        rental = get_rental_revenue(start_date, end_date)
        service = get_service_revenue(start_date, end_date)
        parts = get_parts_revenue(start_date, end_date)
        trucking = get_trucking_revenue(start_date, end_date)
        expenses = get_gl_expenses(start_date, end_date)
        ar_aging = get_ar_aging()
        service_calls_per_day = get_service_calls_per_day(start_date, end_date, num_days)
        
        # Build data structure for calculate_totals
        data = {
            'new_equipment': new_equipment,
            'rental': rental,
            'service': service,
            'parts': parts,
            'trucking': trucking
        }
        
        # Calculate totals
        totals = calculate_totals(data, months_diff)
        
        # Load template
        template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'currie_template.xlsx')
        wb = openpyxl.load_workbook(template_path)
        
        # Delete "New TB" sheet since we're writing actual calculated values now
        if 'New TB' in wb.sheetnames:
            del wb['New TB']
        
        # Get the Sales, COGS, GP sheet
        ws = wb['Sales, COGS, GP']
        
        # Update dealership info
        ws['B3'] = 'Bennett Material Handling'  # Dealership name
        ws['B5'] = datetime.now().strftime('%m/%d/%Y')  # Date
        ws['B7'] = months_diff  # Number of months
        
        # Helper function to write sales/cogs/gp data
        def write_row(row, data):
            ws[f'B{row}'] = data.get('sales', 0)
            ws[f'C{row}'] = data.get('cogs', 0)
            ws[f'D{row}'] = data.get('gross_profit', 0)
        
        # Write Equipment Sales (rows 10-19)
        write_row(10, new_equipment.get('new_lift_truck_primary', {}))
        write_row(11, new_equipment.get('new_lift_truck_other', {}))
        write_row(12, new_equipment.get('new_allied', {}))
        write_row(13, new_equipment.get('other_new_equipment', {}))
        write_row(15, new_equipment.get('operator_training', {}))
        write_row(16, new_equipment.get('used_equipment', {}))
        write_row(17, new_equipment.get('ecommerce', {}))
        write_row(18, new_equipment.get('systems', {}))
        write_row(19, new_equipment.get('batteries', {}))
        
        # Write Rental (rows 21-23) - we only have consolidated rental
        write_row(21, rental)  # rental is already the data dict with sales/cogs/gp
        write_row(22, {'sales': 0, 'cogs': 0, 'gross_profit': 0})  # Long term
        write_row(23, {'sales': 0, 'cogs': 0, 'gross_profit': 0})  # Re-rent
        
        # Write Service (rows 24-28)
        write_row(24, service.get('customer_labor', {}))
        write_row(25, service.get('internal_labor', {}))
        write_row(26, service.get('warranty_labor', {}))
        write_row(27, service.get('sublet', {}))
        write_row(28, service.get('other', {}))  # Fixed: function returns 'other' not 'other_service'
        
        # Write Parts (rows 30-36)
        write_row(30, parts.get('counter_primary', {}))
        write_row(31, parts.get('counter_other', {}))
        write_row(32, parts.get('ro_primary', {}))
        write_row(33, parts.get('ro_other', {}))
        write_row(34, parts.get('internal', {}))  # Fixed: function returns 'internal' not 'internal_parts'
        write_row(35, parts.get('warranty', {}))  # Fixed: function returns 'warranty' not 'warranty_parts'
        write_row(36, parts.get('ecommerce_parts', {}))
        
        # Write Trucking (row 38)
        write_row(38, trucking)
        
        # Get other income/interest data for bottom section
        other_income_interest = get_other_income_and_interest(start_date, end_date)
        
        # Calculate and write bottom section values (rows 40-47)
        # Row 40: Total Aftermarket Sales, COGS & GP
        total_aftermarket = totals['total_aftermarket']
        ws['B40'] = total_aftermarket['sales']
        ws['C40'] = total_aftermarket['cogs']
        ws['D40'] = total_aftermarket['gross_profit']
        
        # Row 41: Total Net Sales & GP
        total_net_sales = totals['total_net_sales_gp']
        ws['B41'] = total_net_sales['sales']
        ws['C41'] = total_net_sales['cogs']
        ws['D41'] = total_net_sales['gross_profit']
        
        # Row 42: Total Company Expenses (write to column B, not D)
        ws['B42'] = expenses['grand_total']
        
        # Row 43: Other Income (Expenses) - negative because it's an expense (write to column B)
        ws['B43'] = other_income_interest.get('other_income', 0)
        
        # Row 44: Interest (Expense) - negative because it's an expense (write to column B)
        ws['B44'] = other_income_interest.get('interest_expense', 0)
        
        # Row 45: Total operating profit = (Total Net Sales GP - Total Expenses + Other Income + Interest) (write to column B)
        total_net_sales_gp = totals['total_net_sales_gp']['gross_profit']
        total_operating_profit = total_net_sales_gp - expenses['grand_total'] + other_income_interest.get('other_income', 0) + other_income_interest.get('interest_expense', 0)
        ws['B45'] = total_operating_profit
        
        # Row 46: F & I Income (write to column B)
        ws['B46'] = other_income_interest.get('fi_income', 0)
        
        # Row 47: Pre-Tax Income = Operating Profit + F&I Income (write to column B)
        ws['B47'] = total_operating_profit + other_income_interest.get('fi_income', 0)
        
        # Write Expenses to "Expenses, Miscellaneous" sheet
        expenses_ws = wb['Expenses, Miscellaneous']
        
        # Expense totals (rows 4-6, column B = "New" column)
        expenses_ws['B4'] = expenses.get('personnel', {}).get('total', 0)  # Personnel
        expenses_ws['B5'] = expenses.get('operating', {}).get('total', 0)  # Operating
        expenses_ws['B6'] = expenses.get('occupancy', {}).get('total', 0)  # Occupancy
        # B7 has a formula =SUM(B4:B6) which will calculate automatically
        
        # AR Aging (rows 22-26, column B)
        expenses_ws['B22'] = ar_aging.get('current', 0)  # Current
        expenses_ws['B23'] = ar_aging.get('days_31_60', 0)  # 31-60 days
        expenses_ws['B24'] = ar_aging.get('days_61_90', 0)  # 61-90 days
        expenses_ws['B25'] = ar_aging.get('days_91_plus', 0)  # 91+ days
        # B26 has a formula =SUM(B22:B25) which will calculate automatically
        
        # Save to BytesIO for download
        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generate filename with date range
        filename = f"Currie_Financial_Model_{start_date}_to_{end_date}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting Currie Excel: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to export Excel', 'message': str(e)}), 500


@currie_bp.route('/api/currie/discover-gl-accounts', methods=['GET'])
@jwt_required()
def discover_gl_accounts():
    """Debug endpoint to discover GL expense accounts"""
    try:
        # Get date range from query parameters
        start_date = request.args.get('start_date', '2025-09-01')
        end_date = request.args.get('end_date', '2025-11-30')
        
        query = """
        SELECT 
            AccountNo,
            COUNT(*) as TransactionCount,
            SUM(Amount) as TotalAmount
        FROM ben002.GLDetail
        WHERE Posted = 1
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND (
            AccountNo LIKE '5%' OR 
            AccountNo LIKE '6%' OR 
            AccountNo LIKE '7%'
          )
        GROUP BY AccountNo
        ORDER BY AccountNo
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        # Format for easy reading
        accounts = []
        for r in results:
            accounts.append({
                'account_no': r['AccountNo'],
                'transaction_count': int(r['TransactionCount']),
                'total_amount': float(r['TotalAmount'] or 0)
            })
        
        return jsonify({
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'total_accounts': len(accounts),
            'accounts': accounts
        })
        
    except Exception as e:
        logger.error(f"Error discovering GL accounts: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def is_full_calendar_month(start_date, end_date):
    """
    Check if the date range represents a full calendar month
    Excludes the current month to ensure GL.MTD is only used for closed/completed months
    
    Args:
        start_date: Start date string (YYYY-MM-DD)
        end_date: End date string (YYYY-MM-DD)
    
    Returns:
        Tuple of (is_full_month, year, month) or (False, None, None)
    """
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        now = datetime.now()
        
        # Check if start is first day of month
        if start.day != 1:
            return False, None, None
        
        # Check if end is last day of month
        last_day = calendar.monthrange(start.year, start.month)[1]
        if end.day != last_day:
            return False, None, None
        
        # Check if both dates are in the same month
        if start.year != end.year or start.month != end.month:
            return False, None, None
        
        # Exclude current month - always use GLDetail for in-process months
        if start.year == now.year and start.month == now.month:
            return False, None, None
        
        return True, start.year, start.month
    except:
        return False, None, None

def get_gl_expenses(start_date, end_date):
    """
    Get operating expenses from GL accounts
    Uses GL.MTD for full calendar months (exact Softbase match)
    Uses GLDetail for custom date ranges (flexibility)
    """
    try:
        # Check if this is a full calendar month
        is_full_month, year, month = is_full_calendar_month(start_date, end_date)
        
        if is_full_month:
            # Use GL.MTD for exact Softbase match
            return get_gl_expenses_from_gl_mtd(year, month)
        else:
            # Use GLDetail for custom date ranges
            return get_gl_expenses_from_gldetail(start_date, end_date)
    except Exception as e:
        logger.error(f"Error in get_gl_expenses: {e}")
        raise

def get_gl_expenses_from_gl_mtd(year, month):
    """
    Get operating expenses from GL.MTD (monthly summary table)
    This matches Softbase exactly for monthly reports
    """
    try:
        # Personnel Costs
        personnel_query = """
        SELECT 
            SUM(CASE WHEN AccountNo IN ('602600', '601100', '601500', '602700', '602701', '600400') THEN MTD ELSE 0 END) as personnel_total,
            SUM(CASE WHEN AccountNo = '602600' THEN MTD ELSE 0 END) as payroll,
            SUM(CASE WHEN AccountNo = '601100' THEN MTD ELSE 0 END) as payroll_taxes,
            SUM(CASE WHEN AccountNo IN ('601500', '602700', '602701') THEN MTD ELSE 0 END) as benefits,
            SUM(CASE WHEN AccountNo = '600400' THEN MTD ELSE 0 END) as commissions
        FROM ben002.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo IN ('602600', '601100', '601500', '602700', '602701', '600400')
        """
        
        # Occupancy Costs
        occupancy_query = """
        SELECT 
            SUM(MTD) as occupancy_total,
            SUM(CASE WHEN AccountNo IN ('600200', '600201') THEN MTD ELSE 0 END) as rent,
            SUM(CASE WHEN AccountNo = '604000' THEN MTD ELSE 0 END) as utilities,
            SUM(CASE WHEN AccountNo = '601700' THEN MTD ELSE 0 END) as insurance,
            SUM(CASE WHEN AccountNo = '600300' THEN MTD ELSE 0 END) as building_maintenance,
            SUM(CASE WHEN AccountNo = '600900' THEN MTD ELSE 0 END) as depreciation
        FROM ben002.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo IN ('600200', '600201', '600300', '604000', '601700', '600900')
        """
        
        # Operating Expenses
        operating_query = """
        SELECT 
            SUM(MTD) as operating_total,
            SUM(CASE WHEN AccountNo = '600000' THEN MTD ELSE 0 END) as advertising,
            SUM(CASE WHEN AccountNo IN ('600500', '601300') THEN MTD ELSE 0 END) as computer_it,
            SUM(CASE WHEN AccountNo IN ('603500', '603501', '602400') THEN MTD ELSE 0 END) as supplies,
            SUM(CASE WHEN AccountNo = '603600' THEN MTD ELSE 0 END) as telephone,
            SUM(CASE WHEN AccountNo = '603700' THEN MTD ELSE 0 END) as training,
            SUM(CASE WHEN AccountNo = '603800' THEN MTD ELSE 0 END) as travel,
            SUM(CASE WHEN AccountNo = '604100' THEN MTD ELSE 0 END) as vehicle_expense,
            SUM(CASE WHEN AccountNo = '603000' THEN MTD ELSE 0 END) as professional_services,
            SUM(CASE WHEN AccountNo IN ('601000', '601200', '602900', '603300', '603900', '602100', '602200') THEN MTD ELSE 0 END) as other
        FROM ben002.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo IN (
            '600000', '600500', '601000', '601200', '601300', '602100', '602200', 
            '602400', '602900', '603000', '603300', '603500', '603501', '603600', 
            '603700', '603800', '603900', '604100'
          )
        """
        
        personnel_result = sql_service.execute_query(personnel_query, [year, month])
        occupancy_result = sql_service.execute_query(occupancy_query, [year, month])
        operating_result = sql_service.execute_query(operating_query, [year, month])
        
        personnel = personnel_result[0] if personnel_result else {}
        occupancy = occupancy_result[0] if occupancy_result else {}
        operating = operating_result[0] if operating_result else {}
        
        return {
            'personnel': {
                'total': float(personnel.get('personnel_total') or 0),
                'payroll': float(personnel.get('payroll') or 0),
                'payroll_taxes': float(personnel.get('payroll_taxes') or 0),
                'benefits': float(personnel.get('benefits') or 0),
                'commissions': float(personnel.get('commissions') or 0)
            },
            'occupancy': {
                'total': float(occupancy.get('occupancy_total') or 0),
                'rent': float(occupancy.get('rent') or 0),
                'utilities': float(occupancy.get('utilities') or 0),
                'insurance': float(occupancy.get('insurance') or 0),
                'building_maintenance': float(occupancy.get('building_maintenance') or 0),
                'depreciation': float(occupancy.get('depreciation') or 0)
            },
            'operating': {
                'total': float(operating.get('operating_total') or 0),
                'advertising': float(operating.get('advertising') or 0),
                'computer_it': float(operating.get('computer_it') or 0),
                'supplies': float(operating.get('supplies') or 0),
                'telephone': float(operating.get('telephone') or 0),
                'training': float(operating.get('training') or 0),
                'travel': float(operating.get('travel') or 0),
                'vehicle_expense': float(operating.get('vehicle_expense') or 0),
                'professional_services': float(operating.get('professional_services') or 0),
                'other': float(operating.get('other') or 0)
            },
            'grand_total': (
                float(personnel.get('personnel_total') or 0) +
                float(occupancy.get('occupancy_total') or 0) +
                float(operating.get('operating_total') or 0)
            )
        }
        
    except Exception as e:
        logger.error(f"Error fetching GL expenses from GL.MTD: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'personnel': {'total': 0},
            'occupancy': {'total': 0},
            'operating': {'total': 0},
            'grand_total': 0
        }

def get_gl_expenses_from_gldetail(start_date, end_date):
    """
    Get operating expenses from GLDetail (transaction-level detail)
    Used for custom date ranges that aren't full calendar months
    """
    try:
        # Personnel Costs
        personnel_query = """
        SELECT 
            SUM(CASE WHEN AccountNo IN ('602600', '601100', '601500', '602700', '602701', '600400') THEN Amount ELSE 0 END) as personnel_total,
            SUM(CASE WHEN AccountNo = '602600' THEN Amount ELSE 0 END) as payroll,
            SUM(CASE WHEN AccountNo = '601100' THEN Amount ELSE 0 END) as payroll_taxes,
            SUM(CASE WHEN AccountNo IN ('601500', '602700', '602701') THEN Amount ELSE 0 END) as benefits,
            SUM(CASE WHEN AccountNo = '600400' THEN Amount ELSE 0 END) as commissions
        FROM ben002.GLDetail
        WHERE Posted = 1
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND AccountNo IN ('602600', '601100', '601500', '602700', '602701', '600400')
        """
        
        # Occupancy Costs
        occupancy_query = """
        SELECT 
            SUM(Amount) as occupancy_total,
            SUM(CASE WHEN AccountNo IN ('600200', '600201') THEN Amount ELSE 0 END) as rent,
            SUM(CASE WHEN AccountNo = '604000' THEN Amount ELSE 0 END) as utilities,
            SUM(CASE WHEN AccountNo = '601700' THEN Amount ELSE 0 END) as insurance,
            SUM(CASE WHEN AccountNo = '600300' THEN Amount ELSE 0 END) as building_maintenance,
            SUM(CASE WHEN AccountNo = '600900' THEN Amount ELSE 0 END) as depreciation
        FROM ben002.GLDetail
        WHERE Posted = 1
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND AccountNo IN ('600200', '600201', '600300', '604000', '601700', '600900')
        """
        
        # Operating Expenses
        operating_query = """
        SELECT 
            SUM(Amount) as operating_total,
            SUM(CASE WHEN AccountNo = '600000' THEN Amount ELSE 0 END) as advertising,
            SUM(CASE WHEN AccountNo IN ('600500', '601300') THEN Amount ELSE 0 END) as computer_it,
            SUM(CASE WHEN AccountNo IN ('603500', '603501', '602400') THEN Amount ELSE 0 END) as supplies,
            SUM(CASE WHEN AccountNo = '603600' THEN Amount ELSE 0 END) as telephone,
            SUM(CASE WHEN AccountNo = '603700' THEN Amount ELSE 0 END) as training,
            SUM(CASE WHEN AccountNo = '603800' THEN Amount ELSE 0 END) as travel,
            SUM(CASE WHEN AccountNo = '604100' THEN Amount ELSE 0 END) as vehicle_expense,
            SUM(CASE WHEN AccountNo = '603000' THEN Amount ELSE 0 END) as professional_services,
            SUM(CASE WHEN AccountNo IN ('601000', '601200', '602900', '603300', '603900', '602100', '602200') THEN Amount ELSE 0 END) as other
        FROM ben002.GLDetail
        WHERE Posted = 1
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND AccountNo IN (
            '600000', '600500', '601000', '601200', '601300', '602100', '602200', 
            '602400', '602900', '603000', '603300', '603500', '603501', '603600', 
            '603700', '603800', '603900', '604100'
          )
        """
        
        personnel_result = sql_service.execute_query(personnel_query, [start_date, end_date])
        occupancy_result = sql_service.execute_query(occupancy_query, [start_date, end_date])
        operating_result = sql_service.execute_query(operating_query, [start_date, end_date])
        
        personnel = personnel_result[0] if personnel_result else {}
        occupancy = occupancy_result[0] if occupancy_result else {}
        operating = operating_result[0] if operating_result else {}
        
        return {
            'personnel': {
                'total': float(personnel.get('personnel_total') or 0),
                'payroll': float(personnel.get('payroll') or 0),
                'payroll_taxes': float(personnel.get('payroll_taxes') or 0),
                'benefits': float(personnel.get('benefits') or 0),
                'commissions': float(personnel.get('commissions') or 0)
            },
            'occupancy': {
                'total': float(occupancy.get('occupancy_total') or 0),
                'rent': float(occupancy.get('rent') or 0),
                'utilities': float(occupancy.get('utilities') or 0),
                'insurance': float(occupancy.get('insurance') or 0),
                'building_maintenance': float(occupancy.get('building_maintenance') or 0),
                'depreciation': float(occupancy.get('depreciation') or 0)
            },
            'operating': {
                'total': float(operating.get('operating_total') or 0),
                'advertising': float(operating.get('advertising') or 0),
                'computer_it': float(operating.get('computer_it') or 0),
                'supplies': float(operating.get('supplies') or 0),
                'telephone': float(operating.get('telephone') or 0),
                'training': float(operating.get('training') or 0),
                'travel': float(operating.get('travel') or 0),
                'vehicle_expense': float(operating.get('vehicle_expense') or 0),
                'professional_services': float(operating.get('professional_services') or 0),
                'other': float(operating.get('other') or 0)
            },
            'grand_total': (
                float(personnel.get('personnel_total') or 0) +
                float(occupancy.get('occupancy_total') or 0) +
                float(operating.get('operating_total') or 0)
            )
        }
        
    except Exception as e:
        logger.error(f"Error fetching GL expenses: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'personnel': {'total': 0},
            'occupancy': {'total': 0},
            'operating': {'total': 0},
            'grand_total': 0
        }


@currie_bp.route('/api/currie/expenses', methods=['GET'])
@jwt_required()
def get_currie_expenses():
    """Get operating expenses for Currie Financial Model"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        expenses = get_gl_expenses(start_date, end_date)
        
        return jsonify(expenses)
        
    except Exception as e:
        logger.error(f"Error in get_currie_expenses: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def get_other_income_and_interest(start_date, end_date):
    """
    Get Other Income (Expenses), Interest (Expense), and F&I Income
    These appear in the bottom summary section of the Currie report
    
    Matches Excel template formulas:
    - Other Income (Expenses) = -SUM(601400, 602500, 603400, 604200, 999999)
    - Interest (Expense) = -601800
    - F & I Income = 440000
    """
    try:
        query = """
        SELECT 
            SUM(CASE WHEN AccountNo IN ('601400', '602500', '603400', '604200', '999999') THEN Amount ELSE 0 END) as other_expenses,
            SUM(CASE WHEN AccountNo = '601800' THEN Amount ELSE 0 END) as interest_expense,
            SUM(CASE WHEN AccountNo = '440000' THEN Amount ELSE 0 END) as fi_income
        FROM ben002.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND (
            AccountNo IN ('601400', '602500', '603400', '604200', '999999', '601800', '440000')
          )
        """
        
        result = sql_service.execute_query(query, [start_date, end_date])
        
        if result and len(result) > 0:
            row = result[0]
            # Return as negative because these are expenses that reduce operating profit
            # Excel formulas use -SUM() to make them negative
            return {
                'other_income': -float(row.get('other_expenses') or 0),  # Negative because it's an expense
                'interest_expense': -float(row.get('interest_expense') or 0),  # Negative because it's an expense
                'fi_income': float(row.get('fi_income') or 0)  # Positive because it's income
            }
        else:
            return {
                'other_income': 0,
                'interest_expense': 0,
                'fi_income': 0
            }
            
    except Exception as e:
        logger.error(f"Error fetching other income and interest: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'other_income': 0,
            'interest_expense': 0,
            'fi_income': 0
        }
