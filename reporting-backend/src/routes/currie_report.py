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
        
        # Get all the data
        new_equipment = get_new_equipment_sales(start_date, end_date)
        rental = get_rental_revenue(start_date, end_date)
        service = get_service_revenue(start_date, end_date)
        parts = get_parts_revenue(start_date, end_date)
        trucking = get_trucking_revenue(start_date, end_date)
        
        # Calculate number of months
        from datetime import datetime
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        months_diff = (end.year - start.year) * 12 + (end.month - start.month) + 1
        
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
        
        # Remove "New TB" sheet if it exists
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
        write_row(21, rental.get('rental_revenue', {}))
        write_row(22, {'sales': 0, 'cogs': 0, 'gross_profit': 0})  # Long term
        write_row(23, {'sales': 0, 'cogs': 0, 'gross_profit': 0})  # Re-rent
        
        # Write Service (rows 24-28)
        write_row(24, service.get('customer_labor', {}))
        write_row(25, service.get('internal_labor', {}))
        write_row(26, service.get('warranty_labor', {}))
        write_row(27, service.get('sublet', {}))
        write_row(28, service.get('other_service', {}))
        
        # Write Parts (rows 30-36)
        write_row(30, parts.get('counter_primary', {}))
        write_row(31, parts.get('counter_other', {}))
        write_row(32, parts.get('ro_primary', {}))
        write_row(33, parts.get('ro_other', {}))
        write_row(34, parts.get('internal_parts', {}))
        write_row(35, parts.get('warranty_parts', {}))
        write_row(36, parts.get('ecommerce_parts', {}))
        
        # Write Trucking (row 38)
        write_row(38, trucking)
        
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
