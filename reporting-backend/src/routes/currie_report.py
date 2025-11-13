"""
Currie Financial Model Report API
Automates quarterly Currie reporting by extracting data from Softbase
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.azure_sql_service import AzureSQLService
from datetime import datetime, timedelta
import logging

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
        data['totals'] = calculate_totals(data)
        
        return jsonify(data), 200
        
    except Exception as e:
        logger.error(f"Error fetching Currie sales data: {str(e)}")
        return jsonify({'error': str(e)}), 500


def get_new_equipment_sales(start_date, end_date):
    """Get new equipment sales broken down by category using InvoiceReg table"""
    try:
        # Query for new equipment sales from InvoiceReg table
        # Using SaleCode to identify equipment types
        # LINDE/LINDEN = Primary Brand, others = Other Brands
        query = """
        SELECT 
            i.SaleCode,
            SUM(COALESCE(i.EquipmentTaxable, 0) + COALESCE(i.EquipmentNonTax, 0)) as sales,
            SUM(COALESCE(i.EquipmentCost, 0)) as cogs
        FROM ben002.InvoiceReg i
        WHERE i.InvoiceDate >= %s 
          AND i.InvoiceDate <= %s
          AND (COALESCE(i.EquipmentTaxable, 0) + COALESCE(i.EquipmentNonTax, 0)) > 0
        GROUP BY i.SaleCode
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
        
        # Map results to categories based on SaleCode
        for row in results:
            sales = float(row['sales'] or 0)
            cogs = float(row['cogs'] or 0)
            sale_code = (row['SaleCode'] or '').upper()
            
            # Linde = Primary Brand
            if sale_code in ('LINDE', 'LINDEN', 'NEWEQ'):
                categories['new_lift_truck_primary']['sales'] += sales
                categories['new_lift_truck_primary']['cogs'] += cogs
            # Used equipment
            elif sale_code in ('USEDEQ', 'RNTSALE'):
                categories['used_equipment']['sales'] += sales
                categories['used_equipment']['cogs'] += cogs
            # Other new equipment (KOM, etc.)
            elif sale_code in ('KOM', 'NEWEQP-R'):
                categories['new_lift_truck_other']['sales'] += sales
                categories['new_lift_truck_other']['cogs'] += cogs
            # Default to other new equipment
            else:
                categories['other_new_equipment']['sales'] += sales
                categories['other_new_equipment']['cogs'] += cogs
        
        # Calculate gross profit for each category
        for category in categories.values():
            category['gross_profit'] = category['sales'] - category['cogs']
        
        return categories
        
    except Exception as e:
        logger.error(f"Error fetching new equipment sales: {str(e)}")
        return {}


def get_rental_revenue(start_date, end_date):
    """Get rental revenue broken down by short-term, long-term, and re-rent"""
    try:
        # Query rental revenue from InvoiceReg table
        query = """
        SELECT 
            SUM(COALESCE(i.RentalTaxable, 0) + COALESCE(i.RentalNonTax, 0)) as sales,
            SUM(COALESCE(i.RentalCost, 0)) as cogs
        FROM ben002.InvoiceReg i
        WHERE i.InvoiceDate >= %s 
          AND i.InvoiceDate <= %s
          AND (COALESCE(i.RentalTaxable, 0) + COALESCE(i.RentalNonTax, 0)) > 0
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        rental_data = {
            'short_term': {'sales': 0, 'cogs': 0},
            'long_term': {'sales': 0, 'cogs': 0},
            'rerent': {'sales': 0, 'cogs': 0}
        }
        
        # For now, put all rental in short_term
        # TODO: Distinguish between short/long/rerent based on SaleCode or other fields
        if results and len(results) > 0:
            row = results[0]
            sales = float(row['sales'] or 0)
            cogs = float(row['cogs'] or 0)
            rental_data['short_term']['sales'] = sales
            rental_data['short_term']['cogs'] = cogs
        
        # Calculate gross profit
        for category in rental_data.values():
            category['gross_profit'] = category['sales'] - category['cogs']
        
        return rental_data
        
    except Exception as e:
        logger.error(f"Error fetching rental revenue: {str(e)}")
        return {}


def get_service_revenue(start_date, end_date):
    """Get service revenue broken down by customer, internal, warranty, sublet"""
    try:
        # Query service labor from InvoiceReg table
        query = """
        SELECT 
            SUM(COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0)) as sales,
            SUM(COALESCE(i.LaborCost, 0)) as cogs
        FROM ben002.InvoiceReg i
        WHERE i.InvoiceDate >= %s 
          AND i.InvoiceDate <= %s
          AND (COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0)) > 0
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        service_data = {
            'customer_labor': {'sales': 0, 'cogs': 0},
            'internal_labor': {'sales': 0, 'cogs': 0},
            'warranty_labor': {'sales': 0, 'cogs': 0},
            'sublet': {'sales': 0, 'cogs': 0},
            'other': {'sales': 0, 'cogs': 0}
        }
        
        # For now, put all labor in customer_labor
        # TODO: Distinguish between customer/internal/warranty based on SaleCode or WO Type
        if results and len(results) > 0:
            row = results[0]
            sales = float(row['sales'] or 0)
            cogs = float(row['cogs'] or 0)
            service_data['customer_labor']['sales'] = sales
            service_data['customer_labor']['cogs'] = cogs
        
        # Calculate gross profit
        for category in service_data.values():
            category['gross_profit'] = category['sales'] - category['cogs']
        
        return service_data
        
    except Exception as e:
        logger.error(f"Error fetching service revenue: {str(e)}")
        return {}


def get_parts_revenue(start_date, end_date):
    """Get parts revenue broken down by counter, RO, internal, warranty"""
    try:
        # Query parts sales from InvoiceReg table
        query = """
        SELECT 
            SUM(COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)) as sales,
            SUM(COALESCE(i.PartsCost, 0)) as cogs
        FROM ben002.InvoiceReg i
        WHERE i.InvoiceDate >= %s 
          AND i.InvoiceDate <= %s
          AND (COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)) > 0
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
        
        # For now, put all parts in counter_primary
        # TODO: Distinguish between counter/RO/internal/warranty based on SaleCode
        if results and len(results) > 0:
            row = results[0]
            sales = float(row['sales'] or 0)
            cogs = float(row['cogs'] or 0)
            parts_data['counter_primary']['sales'] = sales
            parts_data['counter_primary']['cogs'] = cogs
        
        # Calculate gross profit
        for category in parts_data.values():
            category['gross_profit'] = category['sales'] - category['cogs']
        
        return parts_data
        
    except Exception as e:
        logger.error(f"Error fetching parts revenue: {str(e)}")
        return {}


def get_trucking_revenue(start_date, end_date):
    """Get trucking/delivery revenue"""
    try:
        # Query trucking revenue from InvoiceReg table
        query = """
        SELECT 
            SUM(COALESCE(i.MiscTaxable, 0) + COALESCE(i.MiscNonTax, 0)) as sales,
            SUM(COALESCE(i.MiscCost, 0)) as cogs
        FROM ben002.InvoiceReg i
        WHERE i.InvoiceDate >= %s 
          AND i.InvoiceDate <= %s
          AND (COALESCE(i.MiscTaxable, 0) + COALESCE(i.MiscNonTax, 0)) > 0
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


def calculate_totals(data):
    """Calculate total sales, COGS, and GP across all categories"""
    totals = {
        'sales': 0,
        'cogs': 0,
        'gross_profit': 0
    }
    
    # Sum equipment sales
    if 'new_equipment' in data:
        for category in data['new_equipment'].values():
            totals['sales'] += category.get('sales', 0)
            totals['cogs'] += category.get('cogs', 0)
    
    # Sum rental
    if 'rental' in data:
        for category in data['rental'].values():
            totals['sales'] += category.get('sales', 0)
            totals['cogs'] += category.get('cogs', 0)
    
    # Sum service
    if 'service' in data:
        for category in data['service'].values():
            totals['sales'] += category.get('sales', 0)
            totals['cogs'] += category.get('cogs', 0)
    
    # Sum parts
    if 'parts' in data:
        for category in data['parts'].values():
            totals['sales'] += category.get('sales', 0)
            totals['cogs'] += category.get('cogs', 0)
    
    # Add trucking
    if 'trucking' in data:
        totals['sales'] += data['trucking'].get('sales', 0)
        totals['cogs'] += data['trucking'].get('cogs', 0)
    
    totals['gross_profit'] = totals['sales'] - totals['cogs']
    
    return totals
