"""
Currie Financial Model Report API
Automates quarterly Currie reporting by extracting data from Softbase
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
from src.services.cache_service import cache_service
from datetime import datetime, timedelta
import logging
import calendar

from flask_jwt_extended import get_jwt_identity
from src.models.user import User
from src.config.gl_accounts_loader import get_gl_accounts

logger = logging.getLogger(__name__)

currie_bp = Blueprint('currie', __name__)
# sql_service is now obtained via get_tenant_db() for multi-tenant support
_sql_service = None
def get_sql_service():
    return get_tenant_db()
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
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Use cache with 1-hour TTL, include tenant schema to isolate orgs
        user_identity = get_jwt_identity()
        schema = get_tenant_schema()
        cache_key = f'currie_sales_cogs_gp:{schema}:{start_date}:{end_date}'
        
        def fetch_data():
            return _fetch_sales_cogs_gp_data(start_date, end_date, user_identity)
        
        result = cache_service.cache_query(cache_key, fetch_data, ttl_seconds=3600, force_refresh=force_refresh)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching Currie sales data: {str(e)}")
        return jsonify({'error': str(e)}), 500

def _fetch_sales_cogs_gp_data(start_date, end_date, user_identity):
    """Internal function to fetch Currie sales/COGS/GP data"""
    try:
        
        # Calculate number of months
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        months_diff = (end.year - start.year) * 12 + end.month - start.month + 1
        
        # Get organization name for the current user
        user = User.query.get(user_identity)
        org_name = user.organization.name if user and user.organization else 'Unknown'
        
        # Get all revenue and COGS data
        data = {
            'dealership_info': {
                'name': org_name,
                'submitted_by': user_identity,
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
        
        # Add department-allocated expenses for Expenses & Metrics tab
        dept_allocations = {
            'new': 0.47517,
            'used': 0.03209,
            'rental': 0.20694,
            'parts': 0.13121,
            'service': 0.14953,
            'trucking': 0.00507
        }
        
        personnel_total = expenses.get('personnel', {}).get('total', 0)
        operating_total = expenses.get('operating', {}).get('total', 0)
        occupancy_total = expenses.get('occupancy', {}).get('total', 0)
        
        # Calculate department allocations
        personnel_new = personnel_total * dept_allocations['new']
        personnel_used = personnel_total * dept_allocations['used']
        personnel_parts = personnel_total * dept_allocations['parts']
        personnel_service = personnel_total * dept_allocations['service']
        personnel_rental = personnel_total * dept_allocations['rental']
        personnel_trucking = personnel_total * dept_allocations['trucking']
        personnel_ga = personnel_total * (1 - sum(dept_allocations.values()))
        
        operating_new = operating_total * dept_allocations['new']
        operating_used = operating_total * dept_allocations['used']
        operating_parts = operating_total * dept_allocations['parts']
        operating_service = operating_total * dept_allocations['service']
        operating_rental = operating_total * dept_allocations['rental']
        operating_trucking = operating_total * dept_allocations['trucking']
        operating_ga = operating_total * (1 - sum(dept_allocations.values()))
        
        occupancy_new = occupancy_total * dept_allocations['new']
        occupancy_used = occupancy_total * dept_allocations['used']
        occupancy_parts = occupancy_total * dept_allocations['parts']
        occupancy_service = occupancy_total * dept_allocations['service']
        occupancy_rental = occupancy_total * dept_allocations['rental']
        occupancy_trucking = occupancy_total * dept_allocations['trucking']
        occupancy_ga = occupancy_total * (1 - sum(dept_allocations.values()))
        
        data['department_expenses'] = {
            'personnel': {
                'new': personnel_new,
                'used': personnel_used,
                'total_sales_dept': personnel_new + personnel_used,
                'parts': personnel_parts,
                'service': personnel_service,
                'rental': personnel_rental,
                'trucking': personnel_trucking,
                'ga': personnel_ga,
                'total': personnel_total
            },
            'operating': {
                'new': operating_new,
                'used': operating_used,
                'total_sales_dept': operating_new + operating_used,
                'parts': operating_parts,
                'service': operating_service,
                'rental': operating_rental,
                'trucking': operating_trucking,
                'ga': operating_ga,
                'total': operating_total
            },
            'occupancy': {
                'new': occupancy_new,
                'used': occupancy_used,
                'total_sales_dept': occupancy_new + occupancy_used,
                'parts': occupancy_parts,
                'service': occupancy_service,
                'rental': occupancy_rental,
                'trucking': occupancy_trucking,
                'ga': occupancy_ga,
                'total': occupancy_total
            },
            'total': {
                'new': personnel_new + operating_new + occupancy_new,
                'used': personnel_used + operating_used + occupancy_used,
                'total_sales_dept': (personnel_new + personnel_used) + (operating_new + operating_used) + (occupancy_new + occupancy_used),
                'parts': personnel_parts + operating_parts + occupancy_parts,
                'service': personnel_service + operating_service + occupancy_service,
                'rental': personnel_rental + operating_rental + occupancy_rental,
                'trucking': personnel_trucking + operating_trucking + occupancy_trucking,
                'ga': personnel_ga + operating_ga + occupancy_ga,
                'total': personnel_total + operating_total + occupancy_total
            }
        }
        
        # Add AR Aging data
        data['ar_aging'] = get_ar_aging()
        
        # Add Balance Sheet data
        data['balance_sheet'] = get_balance_sheet_data(end_date)
        
        return data
        
    except Exception as e:
        logger.error(f"Error fetching Currie sales data: {str(e)}")
        raise e


def get_new_equipment_sales(start_date, end_date):
    """Get new equipment sales broken down by category using GLDetail table"""
    try:
        # Query for equipment sales and costs from GLDetail using approved GL accounts
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            AccountNo,
            SUM(Amount) as total_amount
        FROM {schema}.GLDetail
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
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
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
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            AccountNo,
            SUM(Amount) as total_amount
        FROM {schema}.GLDetail
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
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
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
        schema = get_tenant_schema()

        query = f"""
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
        FROM {schema}.GLDetail
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
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
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
        # Query parts sales and costs from GLDetail using tenant-specific GL accounts
        schema = get_tenant_schema()
        tenant_gl_accounts = get_gl_accounts(schema)
        parts_config = tenant_gl_accounts.get('parts', {})
        parts_revenue_accounts = parts_config.get('revenue', [])
        parts_cogs_accounts = parts_config.get('cogs', [])
        
        # Combine all parts accounts for the query
        all_parts_accounts = parts_revenue_accounts + parts_cogs_accounts
        accounts_list = "', '".join(all_parts_accounts)

        query = f"""
        SELECT 
            AccountNo,
            SUM(Amount) as total_amount
        FROM {schema}.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN ('{accounts_list}')
        GROUP BY AccountNo
        """
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
        parts_data = {
            'counter_primary': {'sales': 0, 'cogs': 0},
            'counter_other': {'sales': 0, 'cogs': 0},
            'ro_primary': {'sales': 0, 'cogs': 0},
            'ro_other': {'sales': 0, 'cogs': 0},
            'internal': {'sales': 0, 'cogs': 0},
            'warranty': {'sales': 0, 'cogs': 0},
            'ecommerce': {'sales': 0, 'cogs': 0}
        }
        
        # Map GL accounts to categories dynamically based on tenant
        # For simplicity, aggregate all parts revenue into counter_primary and all COGS into counter_primary
        # More granular breakdown would require tenant-specific account mapping
        for row in results:
            account = str(row['AccountNo'])
            amount = float(row['total_amount'] or 0)
            
            # Check if this is a revenue account or COGS account
            if account in parts_revenue_accounts:
                parts_data['counter_primary']['sales'] += -amount  # Revenue is credit (negative)
            elif account in parts_cogs_accounts:
                parts_data['counter_primary']['cogs'] += amount  # COGS is debit (positive)
        
        # Counter Other, RO Other, Internal, Warranty, and E-commerce remain at $0 for non-Bennett tenants
        
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
        schema = get_tenant_schema()

        query = f"""
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
        FROM {schema}.GLDetail
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
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
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
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if not start_date or not end_date:
            return jsonify({'error': 'start_date and end_date are required'}), 400
        
        # Use cache with 1-hour TTL
        schema = get_tenant_schema()
        cache_key = f'currie_metrics:{schema}:{start_date}:{end_date}'
        
        def fetch_metrics():
            return _fetch_currie_metrics_data(start_date, end_date)
        
        result = cache_service.cache_query(cache_key, fetch_metrics, ttl_seconds=3600, force_refresh=force_refresh)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error fetching Currie metrics: {str(e)}")
        return jsonify({'error': 'Failed to fetch metrics', 'message': str(e)}), 500

def _fetch_currie_metrics_data(start_date, end_date):
    """Internal function to fetch Currie metrics data"""
    # Calculate number of days in period
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
    
    # 7. Rental Fleet Metrics
    metrics['rental_fleet'] = get_rental_fleet_metrics(start_date, end_date)
    
    # 8. Revenue/GP per Technician (combine service revenue with tech count)
    tech_count = metrics.get('technician_count', {}).get('active_technicians', 0)
    service_revenue = totals.get('total_aftermarket', {}).get('sales', 0) - totals.get('total_aftermarket', {}).get('sales', 0) + (data.get('service', {}).get('customer_labor', {}).get('sales', 0) + data.get('service', {}).get('internal_labor', {}).get('sales', 0) + data.get('service', {}).get('warranty_labor', {}).get('sales', 0) + data.get('service', {}).get('sublet', {}).get('sales', 0) + data.get('service', {}).get('other', {}).get('sales', 0))
    service_gp_val = (data.get('service', {}).get('customer_labor', {}).get('gross_profit', 0) + data.get('service', {}).get('internal_labor', {}).get('gross_profit', 0) + data.get('service', {}).get('warranty_labor', {}).get('gross_profit', 0) + data.get('service', {}).get('sublet', {}).get('gross_profit', 0) + data.get('service', {}).get('other', {}).get('gross_profit', 0))
    num_months_calc = max(1, int(num_months))
    metrics['service_productivity'] = {
        'revenue_per_tech_monthly': round(service_revenue / num_months_calc / tech_count, 2) if tech_count > 0 else 0,
        'gp_per_tech_monthly': round(service_gp_val / num_months_calc / tech_count, 2) if tech_count > 0 else 0,
        'total_service_revenue': round(service_revenue, 2),
        'total_service_gp': round(service_gp_val, 2),
        'hours_per_tech_monthly': round((metrics.get('labor_metrics', {}).get('total_billed_hours', 0)) / num_months_calc / tech_count, 1) if tech_count > 0 else 0,
    }
    
    # 9. Department GP% summary for benchmarking
    service_total = totals.get('total_service', totals.get('total_aftermarket', {}))
    parts_total = totals.get('total_parts', {})
    rental_total = totals.get('total_rental', {})
    
    def calc_gp_pct(dept_data):
        sales = dept_data.get('sales', 0)
        gp = dept_data.get('gross_profit', 0)
        return round((gp / sales * 100) if sales > 0 else 0, 1)
    
    # Get service totals from the raw data
    svc_sales = sum(data.get('service', {}).get(k, {}).get('sales', 0) for k in ['customer_labor', 'internal_labor', 'warranty_labor', 'sublet', 'other'])
    svc_gp = sum(data.get('service', {}).get(k, {}).get('gross_profit', 0) for k in ['customer_labor', 'internal_labor', 'warranty_labor', 'sublet', 'other'])
    parts_sales = sum(data.get('parts', {}).get(k, {}).get('sales', 0) for k in data.get('parts', {}).keys())
    parts_gp_val = sum(data.get('parts', {}).get(k, {}).get('gross_profit', 0) for k in data.get('parts', {}).keys())
    rental_sales = data.get('rental', {}).get('sales', 0)
    rental_gp_val = data.get('rental', {}).get('gross_profit', 0)
    
    metrics['dept_gp_benchmarks'] = {
        'service': {
            'gp_pct': round((svc_gp / svc_sales * 100) if svc_sales > 0 else 0, 1),
            'target': 65.0,
            'sales': round(svc_sales, 2),
            'gp': round(svc_gp, 2)
        },
        'parts': {
            'gp_pct': round((parts_gp_val / parts_sales * 100) if parts_sales > 0 else 0, 1),
            'target': 40.0,
            'sales': round(parts_sales, 2),
            'gp': round(parts_gp_val, 2)
        },
        'rental': {
            'gp_pct': round((rental_gp_val / rental_sales * 100) if rental_sales > 0 else 0, 1),
            'target': 45.0,
            'sales': round(rental_sales, 2),
            'gp': round(rental_gp_val, 2)
        }
    }
    
    return {
        'metrics': metrics,
        'date_range': {
            'start_date': start_date,
            'end_date': end_date,
            'num_days': num_days
        },
        'generated_at': datetime.now().isoformat()
    }


def get_ar_aging():
    """Get AR aging buckets (reusing logic from department_reports)"""
    try:
        schema = get_tenant_schema()
        
        # Get total AR
        total_ar_query = f"""
        SELECT SUM(Amount) as total_ar
        FROM {schema}.ARDetail
        WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
            AND DeletionTime IS NULL
        """
        total_ar_result = get_sql_service().execute_query(total_ar_query, [])
        total_ar = float(total_ar_result[0]['total_ar']) if total_ar_result and total_ar_result[0]['total_ar'] else 0
        
        # Get AR aging buckets
        ar_query = f"""
        WITH InvoiceBalances AS (
            SELECT 
                ar.InvoiceNo,
                ar.CustomerNo,
                MIN(ar.Due) as Due,
                SUM(ar.Amount) as NetBalance
            FROM {schema}.ARDetail ar
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
        
        ar_results = get_sql_service().execute_query(ar_query, [])
        
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
        schema = get_tenant_schema()

        query = f"""
        SELECT COUNT(*) as total_service_calls
        FROM {schema}.WO
        WHERE OpenDate >= %s 
          AND OpenDate <= %s
          AND SaleDept IN ('40', '45', '47')  -- Field Service (40), Shop Service (45), PM (47)
        """
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
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
        schema = get_tenant_schema()

        query = f"""
        SELECT COUNT(DISTINCT Technician) as technician_count
        FROM {schema}.WO
        WHERE OpenDate >= %s 
          AND OpenDate <= %s
          AND Technician IS NOT NULL
          AND Technician != ''
        """
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
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
        schema = get_tenant_schema()
        
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
            FROM {schema}.WOParts wp
            INNER JOIN {schema}.WO w ON wp.WONo = w.WONo
            LEFT JOIN {schema}.Parts p ON wp.PartNo = p.PartNo
            WHERE w.OpenDate >= %s AND w.OpenDate <= %s
        )
        SELECT 
            COUNT(*) as TotalOrders,
            SUM(CASE WHEN StockStatus = 'In Stock' THEN 1 ELSE 0 END) as FilledOrders
        FROM PartsOrders
        """
        
        fill_rate_result = get_sql_service().execute_query(fill_rate_query, [start_date, end_date])
        
        total_orders = int(fill_rate_result[0]['TotalOrders'] or 0) if fill_rate_result else 0
        filled_orders = int(fill_rate_result[0]['FilledOrders'] or 0) if fill_rate_result else 0
        fill_rate = (filled_orders / total_orders * 100) if total_orders > 0 else 0
        
        # 2. Inventory Value - TOTAL current inventory (not period-specific)
        inventory_query = f"""
        SELECT SUM(OnHand * Cost) as TotalInventoryValue
        FROM {schema}.Parts
        WHERE OnHand > 0 AND Cost > 0
        """
        
        inventory_result = get_sql_service().execute_query(inventory_query, [])
        inventory_value = float(inventory_result[0]['TotalInventoryValue'] or 0) if inventory_result else 0
        
        # 3. Inventory Turnover - annualized based on period movement
        turnover_query = f"""
        SELECT 
            SUM(wp.Qty * p.Cost) as TotalCOGS
        FROM {schema}.WOParts wp
        INNER JOIN {schema}.WO w ON wp.WONo = w.WONo
        LEFT JOIN {schema}.Parts p ON wp.PartNo = p.PartNo
        WHERE w.OpenDate >= %s AND w.OpenDate <= %s
        """
        
        turnover_result = get_sql_service().execute_query(turnover_query, [start_date, end_date])
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
            FROM {schema}.Parts p
            LEFT JOIN {schema}.WOParts wp ON p.PartNo = wp.PartNo
            LEFT JOIN {schema}.WO w ON wp.WONo = w.WONo
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
        
        aging_result = get_sql_service().execute_query(aging_query, [])
        
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


def get_rental_fleet_metrics(start_date, end_date):
    """Get rental fleet metrics: fleet value, depreciation, financial utilization"""
    try:
        schema = get_tenant_schema()
        
        # 1. Rental Fleet Value from GL accounts
        # Account 183000 = Gross Rental Equipment, 193000 = Accumulated Depreciation
        fleet_query = f"""
        SELECT 
            SUM(CASE WHEN AccountNo LIKE '183%' THEN Balance ELSE 0 END) as gross_fleet_value,
            SUM(CASE WHEN AccountNo LIKE '193%' THEN ABS(Balance) ELSE 0 END) as accumulated_depreciation
        FROM {schema}.GLAccounts
        WHERE AccountNo LIKE '183%' OR AccountNo LIKE '193%'
        """
        
        fleet_result = get_sql_service().execute_query(fleet_query, [])
        gross_value = float(fleet_result[0]['gross_fleet_value'] or 0) if fleet_result else 0
        accum_deprec = float(fleet_result[0]['accumulated_depreciation'] or 0) if fleet_result else 0
        net_value = gross_value - accum_deprec
        
        # 2. Rental Revenue for the period (from GL)
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        days_in_period = (end - start).days + 1
        
        rental_rev_query = f"""
        SELECT ABS(SUM(Amount)) as rental_revenue
        FROM {schema}.GLDetail
        WHERE AccountNo IN ('400000','401000','402000','403000','404000','405000')
          AND PostDate >= %s AND PostDate <= %s
          AND Posted = 1
        """
        
        rental_rev_result = get_sql_service().execute_query(rental_rev_query, [start_date, end_date])
        period_revenue = float(rental_rev_result[0]['rental_revenue'] or 0) if rental_rev_result else 0
        
        # Annualize the revenue
        annualized_revenue = (period_revenue / days_in_period * 365) if days_in_period > 0 else 0
        
        # Financial Utilization = Annualized Revenue / Gross Fleet Value (acquisition cost)
        financial_utilization = (annualized_revenue / gross_value * 100) if gross_value > 0 else 0
        
        # Depreciation for the period
        deprec_query = f"""
        SELECT ABS(SUM(Amount)) as depreciation_expense
        FROM {schema}.GLDetail
        WHERE AccountNo LIKE '593%'
          AND PostDate >= %s AND PostDate <= %s
          AND Posted = 1
        """
        
        deprec_result = get_sql_service().execute_query(deprec_query, [start_date, end_date])
        period_depreciation = float(deprec_result[0]['depreciation_expense'] or 0) if deprec_result else 0
        annualized_depreciation = (period_depreciation / days_in_period * 365) if days_in_period > 0 else 0
        
        # Rental Multiple = Revenue / Depreciation
        rental_multiple = (annualized_revenue / annualized_depreciation) if annualized_depreciation > 0 else 0
        
        # Fleet unit count from Equipment table
        unit_query = f"""
        SELECT COUNT(*) as unit_count
        FROM {schema}.Equipment
        WHERE Status = 'A'
          AND RentalUnit = 1
        """
        
        unit_result = get_sql_service().execute_query(unit_query, [])
        unit_count = int(unit_result[0]['unit_count'] or 0) if unit_result else 0
        
        return {
            'gross_fleet_value': round(gross_value, 2),
            'accumulated_depreciation': round(accum_deprec, 2),
            'net_fleet_value': round(net_value, 2),
            'unit_count': unit_count,
            'annualized_revenue': round(annualized_revenue, 2),
            'financial_utilization': round(financial_utilization, 1),
            'annualized_depreciation': round(annualized_depreciation, 2),
            'rental_multiple': round(rental_multiple, 2),
            'revenue_per_unit': round(annualized_revenue / unit_count, 2) if unit_count > 0 else 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching rental fleet metrics: {str(e)}")
        import traceback
        traceback.print_exc()
        return {}


def get_labor_metrics(start_date, end_date):
    """Get labor productivity metrics from WOLabor"""
    try:
        # Use the same pattern as other successful queries: SUM(Sell) for labor value
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            COUNT(DISTINCT l.WONo) as wo_count,
            SUM(l.Hours) as total_hours,
            CASE 
                WHEN SUM(l.Hours) > 0 THEN SUM(l.Sell) / SUM(l.Hours)
                ELSE 0 
            END as avg_rate,
            SUM(l.Sell) as total_labor_value
        FROM {schema}.WOLabor l
        INNER JOIN {schema}.WO w ON l.WONo = w.WONo
        WHERE w.OpenDate >= %s 
          AND w.OpenDate <= %s
        """
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
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
        
        # Department allocation percentages (from Currie model)
        dept_allocations = {
            'new': 0.47517,
            'used': 0.03209,
            'rental': 0.20694,
            'parts': 0.13121,
            'service': 0.14953,
            'trucking': 0.00507
        }
        
        # Calculate department expenses for each category
        personnel_total = expenses.get('personnel', {}).get('total', 0)
        operating_total = expenses.get('operating', {}).get('total', 0)
        occupancy_total = expenses.get('occupancy', {}).get('total', 0)
        
        # Allocate Personnel expenses (row 4)
        personnel_new = personnel_total * dept_allocations['new']
        personnel_used = personnel_total * dept_allocations['used']
        personnel_parts = personnel_total * dept_allocations['parts']
        personnel_service = personnel_total * dept_allocations['service']
        personnel_rental = personnel_total * dept_allocations['rental']
        personnel_trucking = personnel_total * dept_allocations['trucking']
        personnel_ga = personnel_total - (personnel_new + personnel_used + personnel_parts + personnel_service + personnel_rental + personnel_trucking)
        
        expenses_ws['B4'] = personnel_new
        expenses_ws['C4'] = personnel_used
        expenses_ws['E4'] = personnel_parts
        expenses_ws['F4'] = personnel_service
        expenses_ws['G4'] = personnel_rental
        expenses_ws['I4'] = personnel_trucking
        expenses_ws['J4'] = personnel_ga
        
        # Allocate Operating expenses (row 5)
        operating_new = operating_total * dept_allocations['new']
        operating_used = operating_total * dept_allocations['used']
        operating_parts = operating_total * dept_allocations['parts']
        operating_service = operating_total * dept_allocations['service']
        operating_rental = operating_total * dept_allocations['rental']
        operating_trucking = operating_total * dept_allocations['trucking']
        operating_ga = operating_total - (operating_new + operating_used + operating_parts + operating_service + operating_rental + operating_trucking)
        
        expenses_ws['B5'] = operating_new
        expenses_ws['C5'] = operating_used
        expenses_ws['E5'] = operating_parts
        expenses_ws['F5'] = operating_service
        expenses_ws['G5'] = operating_rental
        expenses_ws['I5'] = operating_trucking
        expenses_ws['J5'] = operating_ga
        
        # Allocate Occupancy expenses (row 6)
        occupancy_new = occupancy_total * dept_allocations['new']
        occupancy_used = occupancy_total * dept_allocations['used']
        occupancy_parts = occupancy_total * dept_allocations['parts']
        occupancy_service = occupancy_total * dept_allocations['service']
        occupancy_rental = occupancy_total * dept_allocations['rental']
        occupancy_trucking = occupancy_total * dept_allocations['trucking']
        occupancy_ga = occupancy_total - (occupancy_new + occupancy_used + occupancy_parts + occupancy_service + occupancy_rental + occupancy_trucking)
        
        expenses_ws['B6'] = occupancy_new
        expenses_ws['C6'] = occupancy_used
        expenses_ws['E6'] = occupancy_parts
        expenses_ws['F6'] = occupancy_service
        expenses_ws['G6'] = occupancy_rental
        expenses_ws['I6'] = occupancy_trucking
        expenses_ws['J6'] = occupancy_ga
        # Row 7 has formulas =SUM(B4:B6) etc. which will calculate automatically
        
        # AR Aging (rows 22-26, column B)
        expenses_ws['B22'] = ar_aging.get('current', 0)  # Current
        expenses_ws['B23'] = ar_aging.get('days_31_60', 0)  # 31-60 days
        expenses_ws['B24'] = ar_aging.get('days_61_90', 0)  # 61-90 days
        expenses_ws['B25'] = ar_aging.get('days_91_plus', 0)  # 91+ days
        # B26 has a formula =SUM(B22:B25) which will calculate automatically
        
        # Write Balance Sheet data
        balance_sheet_data = get_balance_sheet_data(end_date)
        bs_ws = wb['Balance Sheet']
        
        # Helper function to sum account balances
        def sum_accounts(account_list):
            return sum(acc.get('balance', 0) for acc in account_list)
        
        # ASSETS
        assets = balance_sheet_data['assets']
        
        # Cash (B6) - sum all cash accounts
        bs_ws['B6'] = sum_accounts(assets['current_assets']['cash'])
        
        # Trade Accounts Receivable (B7) - sum AR accounts
        bs_ws['B7'] = sum_accounts(assets['current_assets']['accounts_receivable'])
        
        # All Other Accounts Receivable (B8) - set to 0 or use other current assets if needed
        bs_ws['B8'] = 0
        
        # Inventory breakdown - map by account description to match Currie web page exactly
        inventory_accounts = assets['current_assets']['inventory']
        new_equipment_primary = 0
        new_equipment_other = 0
        new_allied_inventory = 0
        other_new_equipment = 0
        used_equipment_inventory = 0
        parts_inventory = 0
        battery_inventory = 0
        other_inventory = 0
        
        for acc in inventory_accounts:
            desc = acc['description'].upper()
            balance = acc['balance']
            # Map based on account descriptions to match web page display
            if 'NEW TRUCK' in desc:
                new_equipment_primary += balance
            elif 'NEW ALLIED' in desc:
                new_allied_inventory += balance
            elif 'USED TRUCK' in desc:
                used_equipment_inventory += balance
            elif 'PARTS' in desc and 'MISC' not in desc:
                parts_inventory += balance
            elif 'BATTRY' in desc or 'BATTERY' in desc or 'CHARGER' in desc:
                battery_inventory += balance
            elif not ('WORK' in desc and 'PROCESS' in desc):
                # Everything else goes to Other Inventory EXCEPT WIP (Sublet Labor, Misc Parts, Reserve, etc.)
                # WIP is handled separately below
                other_inventory += balance
        
        bs_ws['B11'] = new_equipment_primary  # New Equipment, primary brand
        bs_ws['B12'] = new_equipment_other  # New Equipment, other brand (currently $0)
        bs_ws['B13'] = new_allied_inventory  # New Allied Inventory
        bs_ws['B14'] = other_new_equipment  # Other New Equipment (currently $0)
        bs_ws['B15'] = used_equipment_inventory  # Used Equipment Inventory
        bs_ws['B16'] = parts_inventory  # Parts Inventory
        bs_ws['B17'] = battery_inventory  # Battery Inventory
        bs_ws['B18'] = other_inventory  # Other Inventory
        
        # WIP (B21) - search for WORK-IN-PROCESS account
        wip_balance = 0
        for acc in inventory_accounts:
            if 'WORK' in acc['description'].upper() and 'PROCESS' in acc['description'].upper():
                wip_balance += acc['balance']
        bs_ws['B21'] = wip_balance
        
        # Other Current Assets (B23)
        bs_ws['B23'] = sum_accounts(assets['current_assets']['other_current'])
        
        # Fixed Assets
        # Rental Fleet (B27) = FIXED ASSETS - RENTAL EQUIPMENT + ACCUM. DEPREC. - RENTAL EQUIP.
        # Other LT/Fixed Assets (B28) = All other fixed assets with their depreciation
        rental_fleet_gross = 0
        rental_fleet_deprec = 0
        other_fixed = 0
        
        for acc in assets['fixed_assets']:
            desc = acc['description'].upper()
            balance = acc['balance']
            # Match rental equipment accounts - be more specific
            # Look for "RENTAL EQUIPMENT" or "RENTAL EQUIP" in description
            if ('RENTAL' in desc and 'EQUIP' in desc):
                if 'DEPREC' in desc or 'ACCUM' in desc:
                    rental_fleet_deprec += balance
                else:
                    rental_fleet_gross += balance
            else:
                other_fixed += balance
        
        bs_ws['B27'] = rental_fleet_gross + rental_fleet_deprec  # Rental Fleet (net)
        bs_ws['B28'] = other_fixed  # Other Long Term or Fixed Assets
        
        # Other Assets (B29)
        bs_ws['B29'] = sum_accounts(assets['other_assets'])
        
        # LIABILITIES - match Currie web page structure exactly
        liabilities = balance_sheet_data['liabilities']
        
        # Current Liabilities breakdown
        ap_primary = 0
        ap_other = 0
        notes_payable_current = 0
        short_term_rental_finance = 0
        used_equipment_financing = 0
        other_current_liabilities = 0
        
        for acc in liabilities['current_liabilities']:
            desc = acc['description'].upper()
            balance = acc['balance']
            # Map by description to match web page
            if 'ACCOUNTS PAYABLE' in desc and 'TRADE' in desc:
                ap_primary += balance
            elif 'RENTAL FINANCE' in desc or 'FLOOR PLAN' in desc:
                short_term_rental_finance += balance
            elif 'TRUCKS PURCHASED' in desc or 'USED EQUIPMENT' in desc:
                used_equipment_financing += balance
            else:
                # All other current liabilities
                other_current_liabilities += balance
        
        bs_ws['E7'] = ap_primary  # A/P Primary Brand (ACCOUNTS PAYABLE - TRADE)
        bs_ws['E8'] = ap_other  # A/P Other (currently $0)
        bs_ws['E9'] = notes_payable_current  # Notes Payable - due within 1 year (currently $0)
        bs_ws['E10'] = short_term_rental_finance  # Short Term Rental Finance
        bs_ws['E11'] = used_equipment_financing  # Used Equipment Financing
        bs_ws['E12'] = other_current_liabilities  # Other Current Liabilities
        
        # Long-term Liabilities breakdown - MATCH FRONTEND EXACTLY
        # Frontend: const longTermNotes = sumByPattern(['NOTES PAYABLE', 'SCALE BANK']);
        long_term_notes = 0
        for acc in liabilities['long_term_liabilities']:
            desc = acc['description'].upper()
            if 'NOTES PAYABLE' in desc or 'SCALE BANK' in desc:
                long_term_notes += acc['balance']
        
        # Frontend: const loansFromStockholders = sumByPattern(['STOCKHOLDER', 'SHAREHOLDER']);
        loans_from_stockholders = 0
        for acc in liabilities['long_term_liabilities']:
            desc = acc['description'].upper()
            if 'STOCKHOLDER' in desc or 'SHAREHOLDER' in desc:
                loans_from_stockholders += acc['balance']
        
        # Frontend: const ltRentalFleetFinancing = sumByPattern(['RENTAL', 'FLEET']) - shortTermRentalFinance;
        lt_rental_fleet_financing = 0
        for acc in liabilities['long_term_liabilities']:
            desc = acc['description'].upper()
            if 'RENTAL' in desc or 'FLEET' in desc:
                lt_rental_fleet_financing += acc['balance']
        lt_rental_fleet_financing -= short_term_rental_finance
        
        # Frontend: const otherLongTermDebt = total - (longTermNotes + loansFromStockholders + ltRentalFleetFinancing);
        total_long_term_liabilities = sum(acc['balance'] for acc in liabilities['long_term_liabilities'])
        other_long_term_debt = total_long_term_liabilities - (long_term_notes + loans_from_stockholders + lt_rental_fleet_financing)
        
        # Other Liabilities
        other_liab_remaining = sum_accounts(liabilities['other_liabilities'])
        
        bs_ws['E15'] = long_term_notes  # Long Term notes Payable
        bs_ws['E16'] = loans_from_stockholders  # Loans from Stockholders
        bs_ws['E17'] = lt_rental_fleet_financing  # LT Rental Fleet Financing
        bs_ws['E18'] = other_long_term_debt  # Other Long Term Debt
        
        # Other Liabilities (E23)
        bs_ws['E23'] = other_liab_remaining
        
        # EQUITY
        equity = balance_sheet_data['equity']
        
        # Capital Stock (E27)
        bs_ws['E27'] = sum_accounts(equity['capital_stock'])
        
        # Retained Earnings (E28)
        bs_ws['E28'] = sum_accounts(equity['retained_earnings']) + sum_accounts(equity['distributions'])
        
        # Current Year Net Income (E29)
        bs_ws['E29'] = equity.get('net_income', 0)
        
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
        
        schema = get_tenant_schema()

        
        query = f"""
        SELECT 
            AccountNo,
            COUNT(*) as TransactionCount,
            SUM(Amount) as TotalAmount
        FROM {schema}.GLDetail
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
        
        results = get_sql_service().execute_query(query, [start_date, end_date])
        
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
        schema = get_tenant_schema()
        # Personnel Costs
        personnel_query = f"""
        SELECT 
            SUM(CASE WHEN AccountNo IN ('602600', '601100', '601500', '602700', '602701', '600400') THEN MTD ELSE 0 END) as personnel_total,
            SUM(CASE WHEN AccountNo = '602600' THEN MTD ELSE 0 END) as payroll,
            SUM(CASE WHEN AccountNo = '601100' THEN MTD ELSE 0 END) as payroll_taxes,
            SUM(CASE WHEN AccountNo IN ('601500', '602700', '602701') THEN MTD ELSE 0 END) as benefits,
            SUM(CASE WHEN AccountNo = '600400' THEN MTD ELSE 0 END) as commissions
        FROM {schema}.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo IN ('602600', '601100', '601500', '602700', '602701', '600400')
        """
        
        # Occupancy Costs
        occupancy_query = f"""
        SELECT 
            SUM(MTD) as occupancy_total,
            SUM(CASE WHEN AccountNo IN ('600200', '600201') THEN MTD ELSE 0 END) as rent,
            SUM(CASE WHEN AccountNo = '604000' THEN MTD ELSE 0 END) as utilities,
            SUM(CASE WHEN AccountNo = '601700' THEN MTD ELSE 0 END) as insurance,
            SUM(CASE WHEN AccountNo = '600300' THEN MTD ELSE 0 END) as building_maintenance,
            SUM(CASE WHEN AccountNo = '600900' THEN MTD ELSE 0 END) as depreciation
        FROM {schema}.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo IN ('600200', '600201', '600300', '604000', '601700', '600900')
        """
        
        # Operating Expenses
        operating_query = f"""
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
        FROM {schema}.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo IN (
            '600000', '600500', '601000', '601200', '601300', '602100', '602200', 
            '602400', '602900', '603000', '603300', '603500', '603501', '603600', 
            '603700', '603800', '603900', '604100'
          )
        """
        
        personnel_result = get_sql_service().execute_query(personnel_query, [year, month])
        occupancy_result = get_sql_service().execute_query(occupancy_query, [year, month])
        operating_result = get_sql_service().execute_query(operating_query, [year, month])
        
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
        schema = get_tenant_schema()
        
        # Personnel Costs
        personnel_query = f"""
        SELECT 
            SUM(CASE WHEN AccountNo IN ('602600', '601100', '601500', '602700', '602701', '600400') THEN Amount ELSE 0 END) as personnel_total,
            SUM(CASE WHEN AccountNo = '602600' THEN Amount ELSE 0 END) as payroll,
            SUM(CASE WHEN AccountNo = '601100' THEN Amount ELSE 0 END) as payroll_taxes,
            SUM(CASE WHEN AccountNo IN ('601500', '602700', '602701') THEN Amount ELSE 0 END) as benefits,
            SUM(CASE WHEN AccountNo = '600400' THEN Amount ELSE 0 END) as commissions
        FROM {schema}.GLDetail
        WHERE Posted = 1
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND AccountNo IN ('602600', '601100', '601500', '602700', '602701', '600400')
        """
        
        # Occupancy Costs
        occupancy_query = f"""
        SELECT 
            SUM(Amount) as occupancy_total,
            SUM(CASE WHEN AccountNo IN ('600200', '600201') THEN Amount ELSE 0 END) as rent,
            SUM(CASE WHEN AccountNo = '604000' THEN Amount ELSE 0 END) as utilities,
            SUM(CASE WHEN AccountNo = '601700' THEN Amount ELSE 0 END) as insurance,
            SUM(CASE WHEN AccountNo = '600300' THEN Amount ELSE 0 END) as building_maintenance,
            SUM(CASE WHEN AccountNo = '600900' THEN Amount ELSE 0 END) as depreciation
        FROM {schema}.GLDetail
        WHERE Posted = 1
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND AccountNo IN ('600200', '600201', '600300', '604000', '601700', '600900')
        """
        
        # Operating Expenses
        operating_query = f"""
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
        FROM {schema}.GLDetail
        WHERE Posted = 1
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND AccountNo IN (
            '600000', '600500', '601000', '601200', '601300', '602100', '602200', 
            '602400', '602900', '603000', '603300', '603500', '603501', '603600', 
            '603700', '603800', '603900', '604100'
          )
        """
        
        personnel_result = get_sql_service().execute_query(personnel_query, [start_date, end_date])
        occupancy_result = get_sql_service().execute_query(occupancy_query, [start_date, end_date])
        operating_result = get_sql_service().execute_query(operating_query, [start_date, end_date])
        
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
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            SUM(CASE WHEN AccountNo IN ('601400', '602500', '603400', '604200', '999999') THEN Amount ELSE 0 END) as other_expenses,
            SUM(CASE WHEN AccountNo = '601800' THEN Amount ELSE 0 END) as interest_expense,
            SUM(CASE WHEN AccountNo = '440000' THEN Amount ELSE 0 END) as fi_income
        FROM {schema}.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND (
            AccountNo IN ('601400', '602500', '603400', '604200', '999999', '601800', '440000')
          )
        """
        
        result = get_sql_service().execute_query(query, [start_date, end_date])
        
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


def get_balance_sheet_data(as_of_date):
    """
    Get Balance Sheet data from GL accounts
    Assets: 1xxxxx series
    Liabilities: 2xxxxx series  
    Equity: 3xxxxx series
    
    Returns categorized balance sheet accounts with balances as of the specified date
    """
    try:
        # Parse the date to get year and month
        date_obj = datetime.strptime(as_of_date, '%Y-%m-%d')
        year = date_obj.year
        month = date_obj.month
        
        # Query GL.YTD for balance sheet accounts
        # For balance sheet accounts, we want the cumulative Year-To-Date balance
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            gl.AccountNo,
            COALESCE(coa.Description, gl.AccountNo) as Description,
            gl.YTD as balance
        FROM {schema}.GL gl
        LEFT JOIN {schema}.ChartOfAccounts coa ON gl.AccountNo = coa.AccountNo
        WHERE gl.Year = %s 
          AND gl.Month = %s
          AND (
            gl.AccountNo LIKE '1%'  -- Assets
            OR gl.AccountNo LIKE '2%'  -- Liabilities
            OR gl.AccountNo LIKE '3%'  -- Equity
          )
          AND gl.YTD != 0
        ORDER BY gl.AccountNo
        """
        
        result = get_sql_service().execute_query(query, [year, month])
        
        logger.info(f"Balance Sheet query for year={year}, month={month}")
        logger.info(f"Query returned {len(result) if result else 0} rows")
        if result:
            logger.info(f"First row sample: {result[0]}")
        
        # Calculate current year net income from ALL P&L accounts
        # P&L accounts are everything NOT on the balance sheet (not 1xx, 2xx, 3xx)
        # This includes: 4xx=Revenue, 5xx=COGS, 6xx=Expenses, 7xx=Other Income/Expense
        # In Softbase GL, revenue is stored as negative (credit), COGS/expenses as positive (debit)
        # Net income = sum of all P&L accounts YTD (result will be negative = profit)
        net_income_query = f"""
        SELECT COALESCE(SUM(gl.YTD), 0) as net_income
        FROM {schema}.GL gl
        WHERE gl.Year = %s 
          AND gl.Month = %s
          AND gl.AccountNo NOT LIKE '1%'  -- Exclude Assets
          AND gl.AccountNo NOT LIKE '2%'  -- Exclude Liabilities
          AND gl.AccountNo NOT LIKE '3%'  -- Exclude Equity
        """
        net_income_result = get_sql_service().execute_query(net_income_query, [year, month])
        net_income = float(net_income_result[0].get('net_income', 0)) if net_income_result else 0
        logger.info(f"Current year net income (P&L accounts): {net_income:,.2f}")
        
        # Categorize accounts
        assets = {
            'current_assets': {
                'cash': [],
                'accounts_receivable': [],
                'inventory': [],
                'other_current': []
            },
            'fixed_assets': [],
            'other_assets': [],
            'total': 0
        }
        
        liabilities = {
            'current_liabilities': [],
            'long_term_liabilities': [],
            'other_liabilities': [],
            'total': 0
        }
        
        equity = {
            'capital_stock': [],
            'retained_earnings': [],
            'distributions': [],
            'net_income': net_income,
            'total': 0
        }
        
        if result:
            for row in result:
                account_no = str(row.get('AccountNo', '')).strip()
                description = row.get('Description', '').strip()
                balance = float(row.get('balance', 0))
                
                account_data = {
                    'account': account_no,
                    'description': description,
                    'balance': balance
                }
                
                # Categorize by account number
                if account_no.startswith('1'):  # Assets
                    # Current Assets
                    if account_no.startswith('11'):  # Cash accounts (110xxx-119xxx)
                        assets['current_assets']['cash'].append(account_data)
                    elif account_no.startswith('12'):  # AR accounts (120xxx-129xxx)
                        assets['current_assets']['accounts_receivable'].append(account_data)
                    elif account_no.startswith('13'):  # Inventory accounts (130xxx-139xxx)
                        assets['current_assets']['inventory'].append(account_data)
                    elif account_no.startswith('14') or account_no.startswith('15'):  # Other current (140xxx-159xxx)
                        assets['current_assets']['other_current'].append(account_data)
                    # Fixed Assets
                    elif account_no.startswith('18') or account_no.startswith('19'):  # Fixed assets and depreciation (180xxx-199xxx)
                        assets['fixed_assets'].append(account_data)
                    # Other Assets
                    else:
                        assets['other_assets'].append(account_data)
                    
                    assets['total'] += balance
                
                elif account_no.startswith('2'):  # Liabilities
                    # Current Liabilities (210xxx-249xxx)
                    if account_no.startswith('21') or account_no.startswith('22') or account_no.startswith('23') or account_no.startswith('24'):
                        liabilities['current_liabilities'].append(account_data)
                    # Long-term Liabilities (250xxx-269xxx)
                    elif account_no.startswith('25') or account_no.startswith('26'):
                        liabilities['long_term_liabilities'].append(account_data)
                    # Other Liabilities
                    else:
                        liabilities['other_liabilities'].append(account_data)
                    
                    liabilities['total'] += balance
                
                elif account_no.startswith('3'):  # Equity
                    if account_no.startswith('31'):  # Capital Stock
                        equity['capital_stock'].append(account_data)
                    elif account_no.startswith('33'):  # Distributions
                        equity['distributions'].append(account_data)
                    elif account_no.startswith('34'):  # Retained Earnings
                        equity['retained_earnings'].append(account_data)
                    else:
                        equity['retained_earnings'].append(account_data)  # Default to retained earnings
                    
                    equity['total'] += balance
        
        # Add current year net income to equity total
        equity['total'] += net_income
        
        return {
            'assets': assets,
            'liabilities': liabilities,
            'equity': equity,
            'as_of_date': as_of_date,
            'balanced': abs(assets['total'] + liabilities['total'] + equity['total']) < 0.01
        }
        
    except Exception as e:
        logger.error(f"Error fetching balance sheet data: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'assets': {'current_assets': {'cash': [], 'accounts_receivable': [], 'inventory': [], 'other_current': []}, 'fixed_assets': [], 'other_assets': [], 'total': 0},
            'liabilities': {'current_liabilities': [], 'long_term_liabilities': [], 'other_liabilities': [], 'total': 0},
            'equity': {'capital_stock': [], 'retained_earnings': [], 'distributions': [], 'total': 0},
            'as_of_date': as_of_date,
            'balanced': False,
            'error': str(e)
        }
