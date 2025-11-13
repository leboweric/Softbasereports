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
        data['totals'] = calculate_totals(data, months_diff)
        
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
    """Get rental revenue as a single consolidated category"""
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
            'sales': 0,
            'cogs': 0,
            'gross_profit': 0
        }
        
        # Softbase doesn't distinguish short/long/rerent, so we return a single category
        if results and len(results) > 0:
            row = results[0]
            rental_data['sales'] = float(row['sales'] or 0)
            rental_data['cogs'] = float(row['cogs'] or 0)
            rental_data['gross_profit'] = rental_data['sales'] - rental_data['cogs']
        
        return rental_data
        
    except Exception as e:
        logger.error(f"Error fetching rental revenue: {str(e)}")
        return {}


def get_service_revenue(start_date, end_date):
    """Get service revenue broken down by customer, internal, warranty, sublet"""
    try:
        # Query service labor from InvoiceReg table with proper classification
        # Based on SaleCode patterns found in existing reports
        query = """
        SELECT 
            -- Customer Labor: Standard service codes (SVE, SVES)
            SUM(CASE 
                WHEN i.SaleCode IN ('SVE', 'SVES') 
                THEN COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0)
                ELSE 0 
            END) as customer_sales,
            SUM(CASE 
                WHEN i.SaleCode IN ('SVE', 'SVES') 
                THEN COALESCE(i.LaborCost, 0)
                ELSE 0 
            END) as customer_cogs,
            
            -- Internal Labor: Internal customer numbers
            SUM(CASE 
                WHEN i.BillTo IN ('900006', '900066') 
                THEN COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0)
                ELSE 0 
            END) as internal_sales,
            SUM(CASE 
                WHEN i.BillTo IN ('900006', '900066') 
                THEN COALESCE(i.LaborCost, 0)
                ELSE 0 
            END) as internal_cogs,
            
            -- Warranty Labor: Warranty codes
            SUM(CASE 
                WHEN (i.SaleCode LIKE '%WARR%' OR i.SaleCode = 'SVEW') 
                THEN COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0)
                ELSE 0 
            END) as warranty_sales,
            SUM(CASE 
                WHEN (i.SaleCode LIKE '%WARR%' OR i.SaleCode = 'SVEW') 
                THEN COALESCE(i.LaborCost, 0)
                ELSE 0 
            END) as warranty_cogs,
            
            -- Sublet: Sublet codes
            SUM(CASE 
                WHEN (i.SaleCode LIKE '%SUB%' OR i.SaleCode = 'SVE-STL') 
                THEN COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0)
                ELSE 0 
            END) as sublet_sales,
            SUM(CASE 
                WHEN (i.SaleCode LIKE '%SUB%' OR i.SaleCode = 'SVE-STL') 
                THEN COALESCE(i.LaborCost, 0)
                ELSE 0 
            END) as sublet_cogs,
            
            -- Other Service: Everything else with labor revenue
            SUM(CASE 
                WHEN i.SaleCode NOT IN ('SVE', 'SVES')
                     AND i.BillTo NOT IN ('900006', '900066')
                     AND i.SaleCode NOT LIKE '%WARR%' AND i.SaleCode != 'SVEW'
                     AND i.SaleCode NOT LIKE '%SUB%' AND i.SaleCode != 'SVE-STL'
                THEN COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0)
                ELSE 0 
            END) as other_sales,
            SUM(CASE 
                WHEN i.SaleCode NOT IN ('SVE', 'SVES')
                     AND i.BillTo NOT IN ('900006', '900066')
                     AND i.SaleCode NOT LIKE '%WARR%' AND i.SaleCode != 'SVEW'
                     AND i.SaleCode NOT LIKE '%SUB%' AND i.SaleCode != 'SVE-STL'
                THEN COALESCE(i.LaborCost, 0)
                ELSE 0 
            END) as other_cogs
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
    """Get parts revenue broken down by counter, RO, internal, warranty"""
    try:
        # Query parts sales from InvoiceReg table with proper classification
        # Based on SaleCode patterns found in existing reports
        query = """
        SELECT 
            -- Counter Primary Brand: CSTPRT with Linde codes
            SUM(CASE 
                WHEN i.SaleCode = 'CSTPRT' AND (i.SaleCode LIKE '%LINDE%' OR i.SaleCode LIKE '%LINDEN%')
                THEN COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)
                WHEN i.SaleCode = 'CSTPRT'
                THEN COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)
                ELSE 0 
            END) as counter_primary_sales,
            SUM(CASE 
                WHEN i.SaleCode = 'CSTPRT' AND (i.SaleCode LIKE '%LINDE%' OR i.SaleCode LIKE '%LINDEN%')
                THEN COALESCE(i.PartsCost, 0)
                WHEN i.SaleCode = 'CSTPRT'
                THEN COALESCE(i.PartsCost, 0)
                ELSE 0 
            END) as counter_primary_cogs,
            
            -- Counter Other Brand: CSTPRT without Linde (for now, count as 0 since we can't distinguish)
            0 as counter_other_sales,
            0 as counter_other_cogs,
            
            -- RO Primary Brand: Parts with WONumber and Linde codes
            -- Note: We're using SaleCode as proxy since WONumber field may not exist in InvoiceReg
            SUM(CASE 
                WHEN i.SaleCode IN ('LINDE', 'LINDEN') AND i.SaleCode != 'CSTPRT'
                THEN COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)
                ELSE 0 
            END) as ro_primary_sales,
            SUM(CASE 
                WHEN i.SaleCode IN ('LINDE', 'LINDEN') AND i.SaleCode != 'CSTPRT'
                THEN COALESCE(i.PartsCost, 0)
                ELSE 0 
            END) as ro_primary_cogs,
            
            -- RO Other Brand: Other parts codes (not counter, not Linde)
            SUM(CASE 
                WHEN i.SaleCode NOT IN ('CSTPRT', 'LINDE', 'LINDEN')
                     AND i.BillTo NOT IN ('900006', '900066')
                     AND i.SaleCode NOT LIKE '%WARR%'
                     AND i.SaleCode NOT LIKE '%ECOM%' AND i.SaleCode NOT LIKE '%WEB%'
                     AND (COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)) > 0
                THEN COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)
                ELSE 0 
            END) as ro_other_sales,
            SUM(CASE 
                WHEN i.SaleCode NOT IN ('CSTPRT', 'LINDE', 'LINDEN')
                     AND i.BillTo NOT IN ('900006', '900066')
                     AND i.SaleCode NOT LIKE '%WARR%'
                     AND i.SaleCode NOT LIKE '%ECOM%' AND i.SaleCode NOT LIKE '%WEB%'
                     AND (COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)) > 0
                THEN COALESCE(i.PartsCost, 0)
                ELSE 0 
            END) as ro_other_cogs,
            
            -- Internal Parts: Internal customer numbers
            SUM(CASE 
                WHEN i.BillTo IN ('900006', '900066')
                THEN COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)
                ELSE 0 
            END) as internal_sales,
            SUM(CASE 
                WHEN i.BillTo IN ('900006', '900066')
                THEN COALESCE(i.PartsCost, 0)
                ELSE 0 
            END) as internal_cogs,
            
            -- Warranty Parts: Warranty codes
            SUM(CASE 
                WHEN i.SaleCode LIKE '%WARR%'
                THEN COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)
                ELSE 0 
            END) as warranty_sales,
            SUM(CASE 
                WHEN i.SaleCode LIKE '%WARR%'
                THEN COALESCE(i.PartsCost, 0)
                ELSE 0 
            END) as warranty_cogs,
            
            -- E-Commerce Parts: Online sales codes
            SUM(CASE 
                WHEN (i.SaleCode LIKE '%ECOM%' OR i.SaleCode LIKE '%WEB%')
                THEN COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0)
                ELSE 0 
            END) as ecommerce_sales,
            SUM(CASE 
                WHEN (i.SaleCode LIKE '%ECOM%' OR i.SaleCode LIKE '%WEB%')
                THEN COALESCE(i.PartsCost, 0)
                ELSE 0 
            END) as ecommerce_cogs
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
        
        # Map query results to parts_data
        if results and len(results) > 0:
            row = results[0]
            parts_data['counter_primary']['sales'] = float(row['counter_primary_sales'] or 0)
            parts_data['counter_primary']['cogs'] = float(row['counter_primary_cogs'] or 0)
            parts_data['counter_other']['sales'] = float(row['counter_other_sales'] or 0)
            parts_data['counter_other']['cogs'] = float(row['counter_other_cogs'] or 0)
            parts_data['ro_primary']['sales'] = float(row['ro_primary_sales'] or 0)
            parts_data['ro_primary']['cogs'] = float(row['ro_primary_cogs'] or 0)
            parts_data['ro_other']['sales'] = float(row['ro_other_sales'] or 0)
            parts_data['ro_other']['cogs'] = float(row['ro_other_cogs'] or 0)
            parts_data['internal']['sales'] = float(row['internal_sales'] or 0)
            parts_data['internal']['cogs'] = float(row['internal_cogs'] or 0)
            parts_data['warranty']['sales'] = float(row['warranty_sales'] or 0)
            parts_data['warranty']['cogs'] = float(row['warranty_cogs'] or 0)
            parts_data['ecommerce']['sales'] = float(row['ecommerce_sales'] or 0)
            parts_data['ecommerce']['cogs'] = float(row['ecommerce_cogs'] or 0)
        
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


def calculate_totals(data, num_months):
    """Calculate total sales, COGS, and GP across all categories with subtotals"""
    
    # Calculate subtotals for each section
    total_new_equipment = {'sales': 0, 'cogs': 0, 'gross_profit': 0}
    if 'new_equipment' in data:
        for category in data['new_equipment'].values():
            total_new_equipment['sales'] += category.get('sales', 0)
            total_new_equipment['cogs'] += category.get('cogs', 0)
        total_new_equipment['gross_profit'] = total_new_equipment['sales'] - total_new_equipment['cogs']
    
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
    total_sales_dept = {
        'sales': total_new_equipment['sales'],
        'cogs': total_new_equipment['cogs'],
        'gross_profit': total_new_equipment['gross_profit']
    }
    
    total_aftermarket = {
        'sales': total_service['sales'] + total_parts['sales'],
        'cogs': total_service['cogs'] + total_parts['cogs'],
        'gross_profit': 0
    }
    total_aftermarket['gross_profit'] = total_aftermarket['sales'] - total_aftermarket['cogs']
    
    # Grand total
    grand_total = {
        'sales': total_new_equipment['sales'] + total_rental['sales'] + total_service['sales'] + total_parts['sales'],
        'cogs': total_new_equipment['cogs'] + total_rental['cogs'] + total_service['cogs'] + total_parts['cogs'],
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
        'total_new_equipment': total_new_equipment,
        'total_sales_dept': total_sales_dept,
        'total_rental': total_rental,
        'total_service': total_service,
        'total_parts': total_parts,
        'total_aftermarket': total_aftermarket,
        'grand_total': grand_total,
        'total_company': grand_total,  # Alias for grand_total
        'avg_monthly_sales_gp': avg_monthly_sales_gp,
        # Keep legacy format for backward compatibility
        'sales': grand_total['sales'],
        'cogs': grand_total['cogs'],
        'gross_profit': grand_total['gross_profit']
    }
