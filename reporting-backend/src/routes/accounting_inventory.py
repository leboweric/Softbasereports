"""
Accounting inventory report endpoint
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

accounting_inventory_bp = Blueprint('accounting_inventory', __name__)

@accounting_inventory_bp.route('/api/reports/departments/accounting/inventory', methods=['GET'])
@jwt_required()
def get_accounting_inventory():
    """
    Year-end inventory report categorized by equipment type
    """
    try:
        db = AzureSQLService()
        
        # Main query to get all equipment with financial, location, and depreciation details
        main_query = """
        SELECT 
            e.SerialNo as control_number,
            e.UnitNo,
            e.Make,
            e.Model,
            e.RentalStatus,
            e.Cost as book_value,
            e.Sell as sell_price,
            e.Retail as retail_price,
            e.InventoryDept,
            e.CustomerNo,
            e.RentalYTD,
            e.RentalITD,
            e.DayRent,
            e.WeekRent,
            e.MonthRent,
            c.State as location_state,
            c.Name as customer_name,
            -- Check if currently on rental
            CASE 
                WHEN rental_check.is_on_rental = 1 THEN 'On Rental'
                ELSE e.RentalStatus
            END as current_status,
            -- Add depreciation fields
            d.StartingValue as gross_book_value,
            d.NetBookValue as net_book_value,
            (d.StartingValue - d.NetBookValue) as accumulated_depreciation,
            d.Method as depreciation_method,
            d.RemainingMonths,
            d.TotalMonths
        FROM ben002.Equipment e
        LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
        LEFT JOIN (
            -- Subquery to check if equipment is currently on rental
            SELECT DISTINCT 
                wr.SerialNo,
                1 as is_on_rental
            FROM ben002.WORental wr
            INNER JOIN ben002.WO wo ON wr.WONo = wo.WONo
            WHERE wo.Type = 'R' 
            AND wo.ClosedDate IS NULL
            AND wo.WONo NOT LIKE '9%'  -- Exclude quotes
        ) rental_check ON e.SerialNo = rental_check.SerialNo
        LEFT JOIN ben002.Depreciation d ON e.SerialNo = d.SerialNo
            AND d.Inactive = 0  -- Only active depreciation records (NOT IsDeleted)
        WHERE e.SerialNo IS NOT NULL
            -- IsDeleted column removed - does not exist in Equipment table
        ORDER BY e.Make, e.Model, e.SerialNo
        """
        
        equipment_data = db.execute_query(main_query)
        
        # Initialize categories
        categories = {
            'rental': [],
            'used': [],
            'new': [],
            'batteries_chargers': [],
            'allied': []
        }
        
        # Process and categorize each equipment item
        for item in equipment_data:
            # Determine category based on available data
            category = categorize_equipment(item)
            
            # Format item for response
            formatted_item = {
                'control_number': item['control_number'],
                'unit_number': item['UnitNo'],
                'make': item['Make'],
                'model': item['Model'],
                'book_value': float(item['book_value']) if item['book_value'] else 0,
                'sell_price': float(item['sell_price']) if item['sell_price'] else 0,
                'rental_status': item['RentalStatus'],
                'current_status': item['current_status'],
                'location_state': item['location_state'],
                'customer_name': item['customer_name'],
                'rental_ytd': float(item['RentalYTD']) if item['RentalYTD'] else 0,
                'rental_itd': float(item['RentalITD']) if item['RentalITD'] else 0,
                'day_rent': float(item['DayRent']) if item['DayRent'] else 0,
                'month_rent': float(item['MonthRent']) if item['MonthRent'] else 0,
                # Depreciation data from Depreciation view
                'gross_book_value': float(item['gross_book_value']) if item['gross_book_value'] else None,
                'net_book_value': float(item['net_book_value']) if item['net_book_value'] else None,
                'accumulated_depreciation': float(item['accumulated_depreciation']) if item['accumulated_depreciation'] else None,
                'depreciation_method': item['depreciation_method'],
                'remaining_months': item['RemainingMonths'],
                'total_months': item['TotalMonths']
            }
            
            categories[category].append(formatted_item)
        
        # Calculate summary statistics
        summary = {
            'rental': {
                'qty': len(categories['rental']),
                'total_book_value': sum(item['book_value'] for item in categories['rental']),
                'items': categories['rental']
            },
            'used': {
                'qty': len(categories['used']),
                'total_book_value': sum(item['book_value'] for item in categories['used']),
                'items': categories['used']
            },
            'new': {
                'qty': len(categories['new']),
                'total_book_value': sum(item['book_value'] for item in categories['new']),
                'items': categories['new']
            },
            'batteries_chargers': {
                'qty': len(categories['batteries_chargers']),
                'total_book_value': sum(item['book_value'] for item in categories['batteries_chargers']),
                'items': categories['batteries_chargers']
            },
            'allied': {
                'qty': len(categories['allied']),
                'total_book_value': sum(item['book_value'] for item in categories['allied']),
                'items': categories['allied']
            }
        }
        
        # Add overall totals
        summary['totals'] = {
            'total_equipment': sum(cat['qty'] for cat in summary.values() if isinstance(cat, dict) and 'qty' in cat),
            'total_book_value': sum(cat['total_book_value'] for cat in summary.values() if isinstance(cat, dict) and 'total_book_value' in cat)
        }
        
        # Add data quality notes
        summary['notes'] = [
            "Book value represents original purchase cost from Equipment table",
            "Depreciation data sourced from Depreciation view (active records only)",
            "Gross book value, net book value, and accumulated depreciation available where depreciation records exist",
            "Rental equipment status determined by active work orders",
            "Location state shows current rental customer location"
        ]
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': f'Error generating inventory report: {str(e)}'}), 500

def categorize_equipment(item):
    """
    Determine equipment category based on available data
    """
    make = (item['Make'] or '').lower()
    model = (item['Model'] or '').lower()
    inventory_dept = item['InventoryDept']
    rental_itd = item['RentalITD'] or 0
    current_status = (item['current_status'] or '').lower()
    
    # Allied equipment (check make first)
    if 'allied' in make:
        return 'allied'
    
    # Batteries and Chargers (check model)
    battery_keywords = ['battery', 'charger', 'batt', 'charge']
    if any(keyword in model for keyword in battery_keywords):
        return 'batteries_chargers'
    
    # Equipment in Rental Department (InventoryDept = 60)
    if inventory_dept == 60:
        # Currently on rental
        if current_status == 'on rental':
            return 'rental'
        
        # Never rented (new)
        elif rental_itd == 0:
            return 'new'
        
        # Previously rented, now available (used)
        else:
            return 'used'
    
    # Default to used for other equipment
    return 'used'