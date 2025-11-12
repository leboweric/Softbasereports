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
    """Get new equipment sales broken down by category"""
    try:
        # Query for new equipment sales from Invoice table
        query = """
        SELECT 
            i.Type,
            i.Subtype,
            SUM(i.TotalSale) as sales,
            SUM(i.Cost) as cogs
        FROM ben002.Invoice i
        WHERE i.InvoiceDate >= %s 
          AND i.InvoiceDate <= %s
          AND i.Type IN ('Equipment', 'Allied', 'Battery', 'System')
          AND i.Status = 'Posted'
        GROUP BY i.Type, i.Subtype
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
        
        # Map results to categories
        for row in results:
            sales = float(row['sales'] or 0)
            cogs = float(row['cogs'] or 0)
            inv_type = row['Type']
            subtype = row['Subtype'] or ''
            
            if inv_type == 'Equipment':
                if 'Used' in subtype or 'Rental Disposal' in subtype:
                    categories['used_equipment']['sales'] += sales
                    categories['used_equipment']['cogs'] += cogs
                elif 'Primary' in subtype or 'Forklift' in subtype:
                    categories['new_lift_truck_primary']['sales'] += sales
                    categories['new_lift_truck_primary']['cogs'] += cogs
                else:
                    categories['other_new_equipment']['sales'] += sales
                    categories['other_new_equipment']['cogs'] += cogs
            elif inv_type == 'Allied':
                categories['new_allied']['sales'] += sales
                categories['new_allied']['cogs'] += cogs
            elif inv_type == 'Battery':
                categories['batteries']['sales'] += sales
                categories['batteries']['cogs'] += cogs
            elif inv_type == 'System':
                categories['systems']['sales'] += sales
                categories['systems']['cogs'] += cogs
        
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
        # Query rental revenue from Invoice table
        query = """
        SELECT 
            i.Subtype,
            SUM(i.TotalSale) as sales
        FROM ben002.Invoice i
        WHERE i.InvoiceDate >= %s 
          AND i.InvoiceDate <= %s
          AND i.Type = 'Rental'
          AND i.Status = 'Posted'
        GROUP BY i.Subtype
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        rental_data = {
            'short_term': {'sales': 0, 'cogs': 0},  # COGS calculated from expenses
            'long_term': {'sales': 0, 'cogs': 0},
            'rerent': {'sales': 0, 'cogs': 0}
        }
        
        for row in results:
            sales = float(row['sales'] or 0)
            subtype = (row['Subtype'] or '').lower()
            
            if 'short' in subtype or 'daily' in subtype or 'weekly' in subtype:
                rental_data['short_term']['sales'] += sales
            elif 'long' in subtype or 'monthly' in subtype:
                rental_data['long_term']['sales'] += sales
            elif 'rerent' in subtype or 're-rent' in subtype or 'subrent' in subtype:
                rental_data['rerent']['sales'] += sales
            else:
                # Default to short-term
                rental_data['short_term']['sales'] += sales
        
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
        # Query service labor from WOLabor table
        query = """
        SELECT 
            wo.Type as wo_type,
            wo.BillTo,
            SUM(l.LaborSale) as labor_sales,
            SUM(l.Hours * l.Rate) as labor_cost
        FROM ben002.WOLabor l
        JOIN ben002.WO wo ON l.WONumber = wo.Number
        WHERE l.DateOfLabor >= %s 
          AND l.DateOfLabor <= %s
          AND wo.Status = 'Closed'
        GROUP BY wo.Type, wo.BillTo
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        service_data = {
            'customer_labor': {'sales': 0, 'cogs': 0},
            'internal_labor': {'sales': 0, 'cogs': 0},
            'warranty_labor': {'sales': 0, 'cogs': 0},
            'sublet': {'sales': 0, 'cogs': 0},
            'other': {'sales': 0, 'cogs': 0}
        }
        
        for row in results:
            sales = float(row['labor_sales'] or 0)
            cogs = float(row['labor_cost'] or 0)
            wo_type = (row['wo_type'] or '').lower()
            bill_to = row['BillTo'] or ''
            
            if 'warranty' in wo_type:
                service_data['warranty_labor']['sales'] += sales
                service_data['warranty_labor']['cogs'] += cogs
            elif 'internal' in wo_type or 'shop' in wo_type or not bill_to:
                service_data['internal_labor']['sales'] += sales
                service_data['internal_labor']['cogs'] += cogs
            elif 'sublet' in wo_type:
                service_data['sublet']['sales'] += sales
                service_data['sublet']['cogs'] += cogs
            else:
                service_data['customer_labor']['sales'] += sales
                service_data['customer_labor']['cogs'] += cogs
        
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
        # Query parts sales from WOParts and Invoice tables
        query = """
        SELECT 
            wo.Type as wo_type,
            wo.BillTo,
            SUM(p.PartsSale) as parts_sales,
            SUM(p.PartsCost) as parts_cost
        FROM ben002.WOParts p
        JOIN ben002.WO wo ON p.WONumber = wo.Number
        WHERE p.DateAdded >= %s 
          AND p.DateAdded <= %s
          AND wo.Status = 'Closed'
        GROUP BY wo.Type, wo.BillTo
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
        
        for row in results:
            sales = float(row['parts_sales'] or 0)
            cogs = float(row['parts_cost'] or 0)
            wo_type = (row['wo_type'] or '').lower()
            bill_to = row['BillTo'] or ''
            
            if 'warranty' in wo_type:
                parts_data['warranty']['sales'] += sales
                parts_data['warranty']['cogs'] += cogs
            elif 'internal' in wo_type or 'shop' in wo_type or not bill_to:
                parts_data['internal']['sales'] += sales
                parts_data['internal']['cogs'] += cogs
            elif 'counter' in wo_type or 'parts' in wo_type:
                # Assume primary brand for now
                parts_data['counter_primary']['sales'] += sales
                parts_data['counter_primary']['cogs'] += cogs
            else:
                # Repair order parts
                parts_data['ro_primary']['sales'] += sales
                parts_data['ro_primary']['cogs'] += cogs
        
        # Calculate gross profit
        for category in parts_data.values():
            category['gross_profit'] = category['sales'] - category['cogs']
        
        return parts_data
        
    except Exception as e:
        logger.error(f"Error fetching parts revenue: {str(e)}")
        return {}


def get_trucking_revenue(start_date, end_date):
    """Get trucking department revenue"""
    try:
        # Query trucking revenue from Invoice table
        query = """
        SELECT 
            SUM(i.TotalSale) as sales,
            SUM(i.Cost) as cogs
        FROM ben002.Invoice i
        WHERE i.InvoiceDate >= %s 
          AND i.InvoiceDate <= %s
          AND i.Type = 'Trucking'
          AND i.Status = 'Posted'
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        if results and len(results) > 0:
            row = results[0]
            sales = float(row['sales'] or 0)
            cogs = float(row['cogs'] or 0)
            return {
                'sales': sales,
                'cogs': cogs,
                'gross_profit': sales - cogs
            }
        
        return {'sales': 0, 'cogs': 0, 'gross_profit': 0}
        
    except Exception as e:
        logger.error(f"Error fetching trucking revenue: {str(e)}")
        return {'sales': 0, 'cogs': 0, 'gross_profit': 0}


def calculate_totals(data):
    """Calculate total sales, COGS, and gross profit across all categories"""
    totals = {
        'total_new_equipment': {'sales': 0, 'cogs': 0, 'gross_profit': 0},
        'total_sales_dept': {'sales': 0, 'cogs': 0, 'gross_profit': 0},
        'total_rental': {'sales': 0, 'cogs': 0, 'gross_profit': 0},
        'total_service': {'sales': 0, 'cogs': 0, 'gross_profit': 0},
        'total_parts': {'sales': 0, 'cogs': 0, 'gross_profit': 0},
        'total_aftermarket': {'sales': 0, 'cogs': 0, 'gross_profit': 0},
        'total_company': {'sales': 0, 'cogs': 0, 'gross_profit': 0},
        'avg_monthly_sales_gp': 0
    }
    
    # Sum new equipment
    for category in data['new_equipment'].values():
        totals['total_new_equipment']['sales'] += category['sales']
        totals['total_new_equipment']['cogs'] += category['cogs']
        totals['total_new_equipment']['gross_profit'] += category['gross_profit']
    
    # Total sales dept = new equipment
    totals['total_sales_dept'] = totals['total_new_equipment'].copy()
    
    # Sum rental
    for category in data['rental'].values():
        totals['total_rental']['sales'] += category['sales']
        totals['total_rental']['cogs'] += category['cogs']
        totals['total_rental']['gross_profit'] += category['gross_profit']
    
    # Sum service
    for category in data['service'].values():
        totals['total_service']['sales'] += category['sales']
        totals['total_service']['cogs'] += category['cogs']
        totals['total_service']['gross_profit'] += category['gross_profit']
    
    # Sum parts
    for category in data['parts'].values():
        totals['total_parts']['sales'] += category['sales']
        totals['total_parts']['cogs'] += category['cogs']
        totals['total_parts']['gross_profit'] += category['gross_profit']
    
    # Total aftermarket = rental + service + parts
    totals['total_aftermarket']['sales'] = (
        totals['total_rental']['sales'] +
        totals['total_service']['sales'] +
        totals['total_parts']['sales']
    )
    totals['total_aftermarket']['cogs'] = (
        totals['total_rental']['cogs'] +
        totals['total_service']['cogs'] +
        totals['total_parts']['cogs']
    )
    totals['total_aftermarket']['gross_profit'] = (
        totals['total_aftermarket']['sales'] - totals['total_aftermarket']['cogs']
    )
    
    # Total company = sales dept + aftermarket + trucking
    totals['total_company']['sales'] = (
        totals['total_sales_dept']['sales'] +
        totals['total_aftermarket']['sales'] +
        data['trucking']['sales']
    )
    totals['total_company']['cogs'] = (
        totals['total_sales_dept']['cogs'] +
        totals['total_aftermarket']['cogs'] +
        data['trucking']['cogs']
    )
    totals['total_company']['gross_profit'] = (
        totals['total_company']['sales'] - totals['total_company']['cogs']
    )
    
    # Average monthly sales & GP
    num_months = data['dealership_info']['num_months']
    if num_months > 0:
        totals['avg_monthly_sales_gp'] = totals['total_company']['sales'] / num_months
    
    return totals
