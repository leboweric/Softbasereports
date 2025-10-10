"""
Accounting inventory report endpoint - GL Based
"""
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from decimal import Decimal, ROUND_HALF_UP

accounting_inventory_bp = Blueprint('accounting_inventory', __name__)

def format_currency(amount):
    """Format amount to penny precision without rounding"""
    if amount is None:
        return Decimal('0.00')
    # Convert to Decimal for precise arithmetic
    decimal_amount = Decimal(str(amount))
    # Round to 2 decimal places using ROUND_HALF_UP
    return decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

@accounting_inventory_bp.route('/api/reports/departments/accounting/inventory', methods=['GET'])
@jwt_required()
def get_accounting_inventory():
    """
    Year-end inventory report based on GL accounts as requested by Marissa
    Uses GL account balances for accurate financial reporting
    """
    try:
        db = AzureSQLService()
        
        # Step 1: Get GL account balances for Oct 2025
        gl_balances_query = """
        SELECT 
            AccountNo,
            CAST(YTD AS DECIMAL(18,2)) as current_balance,
            CASE 
                WHEN AccountNo = '131000' THEN 'New Equipment'
                WHEN AccountNo = '131200' THEN 'Used Equipment + Batteries'
                WHEN AccountNo = '131300' THEN 'Allied Equipment'
                WHEN AccountNo = '183000' THEN 'Rental Fleet Gross Value'
                WHEN AccountNo = '193000' THEN 'Accumulated Depreciation'
                ELSE 'Other'
            END as Category
        FROM ben002.GL
        WHERE AccountNo IN ('131000', '131200', '131300', '183000', '193000')
        AND Year = 2025
        AND Month = 10
        AND AccountField = 'Actual'
        ORDER BY AccountNo
        """
        
        gl_balances = db.execute_query(gl_balances_query)
        
        # Step 2: Get YTD depreciation expense (Nov 2024 - Oct 2025 only)
        ytd_depreciation_query = """
        SELECT 
            CAST(SUM(CASE WHEN gld.Amount < 0 THEN ABS(gld.Amount) ELSE 0 END) AS DECIMAL(18,2)) as YTD_Depreciation_Expense
        FROM ben002.GLDetail gld
        WHERE gld.AccountNo = '193000'
        AND gld.EffectiveDate >= CAST('2024-11-01' AS datetime)
        AND gld.EffectiveDate <= CAST('2025-10-31' AS datetime)
        """
        
        ytd_depreciation_result = db.execute_query(ytd_depreciation_query)
        ytd_depreciation = format_currency(ytd_depreciation_result[0]['YTD_Depreciation_Expense']) if ytd_depreciation_result else Decimal('0.00')
        
        # Step 3: Get equipment counts and details for each category
        # Rental equipment (all 971 units, not just on rent)
        rental_equipment_query = """
        SELECT 
            e.SerialNo as serial_number,
            e.UnitNo,
            e.Make,
            e.Model,
            e.Cost as book_value,
            c.State as location_state,
            c.Name as customer_name,
            CASE 
                WHEN rental_check.is_on_rental = 1 THEN 'On Rental'
                ELSE 'Available'
            END as current_status
        FROM ben002.Equipment e
        LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
        LEFT JOIN (
            SELECT DISTINCT 
                wr.SerialNo,
                1 as is_on_rental
            FROM ben002.WORental wr
            INNER JOIN ben002.WO wo ON wr.WONo = wo.WONo
            WHERE wo.Type = 'R' 
            AND wo.ClosedDate IS NULL
            AND wo.WONo NOT LIKE '9%'
        ) rental_check ON e.SerialNo = rental_check.SerialNo
        WHERE e.InventoryDept = 60  -- Rental department
        ORDER BY e.Make, e.Model, e.SerialNo
        """
        
        rental_equipment = db.execute_query(rental_equipment_query)
        
        # Step 4: Get equipment details for other categories
        # New equipment (Dept 10 typically)
        new_equipment_query = """
        SELECT 
            e.SerialNo as serial_number,
            e.Make,
            e.Model,
            e.Cost as book_value
        FROM ben002.Equipment e
        WHERE e.InventoryDept = 10  -- New equipment department
        ORDER BY e.Make, e.Model
        """
        
        new_equipment = db.execute_query(new_equipment_query)
        
        # Used equipment + Batteries/Chargers (Dept 20, separate by keyword)
        used_equipment_query = """
        SELECT 
            e.SerialNo as serial_number,
            e.Make,
            e.Model,
            e.Cost as book_value,
            CASE 
                WHEN LOWER(e.Model) LIKE '%battery%' OR LOWER(e.Model) LIKE '%charger%' OR LOWER(e.Model) LIKE '%batt%' OR LOWER(e.Model) LIKE '%charge%' THEN 'batteries_chargers'
                ELSE 'used'
            END as subcategory
        FROM ben002.Equipment e
        WHERE e.InventoryDept = 20  -- Used equipment department
        ORDER BY e.Make, e.Model
        """
        
        used_equipment_data = db.execute_query(used_equipment_query)
        
        # Allied equipment (Dept 30 typically)
        allied_equipment_query = """
        SELECT 
            e.SerialNo as serial_number,
            e.Make,
            e.Model,
            e.Cost as book_value
        FROM ben002.Equipment e
        WHERE e.InventoryDept = 30  -- Allied equipment department
        ORDER BY e.Make, e.Model
        """
        
        allied_equipment = db.execute_query(allied_equipment_query)
        
        # Step 5: Organize data by GL account balances
        gl_account_balances = {}
        for balance in gl_balances:
            account_no = balance['AccountNo']
            gl_account_balances[account_no] = {
                'balance': str(format_currency(balance['current_balance'])),
                'category': balance['Category']
            }
        
        # Calculate net rental book value
        gross_rental = format_currency(gl_account_balances.get('183000', {}).get('balance', '0.00'))
        accumulated_dep = format_currency(gl_account_balances.get('193000', {}).get('balance', '0.00'))
        net_rental_value = gross_rental - abs(accumulated_dep)
        
        # Step 6: Format equipment data for each category
        def format_equipment_items(equipment_list, category_name):
            formatted_items = []
            for item in equipment_list:
                formatted_item = {
                    'serial_number': item['serial_number'],  # Changed from control_number
                    'make': item['Make'],
                    'model': item['Model'],
                    'book_value': float(format_currency(item['book_value'])) if item['book_value'] else 0.00,
                    'current_status': item.get('current_status', 'Available'),
                    'location_state': item.get('location_state'),
                    'customer_name': item.get('customer_name')
                }
                formatted_items.append(formatted_item)
            return formatted_items
        
        # Separate used equipment and batteries/chargers
        used_items = [item for item in used_equipment_data if item['subcategory'] == 'used']
        battery_items = [item for item in used_equipment_data if item['subcategory'] == 'batteries_chargers']
        
        # Build final summary using GL balances
        summary = {
            'rental': {
                'qty': len(rental_equipment),
                'gl_account_balance': gl_account_balances.get('183000', {}).get('balance', '0.00'),
                'net_book_value': str(format_currency(net_rental_value)),
                'gross_book_value': gl_account_balances.get('183000', {}).get('balance', '0.00'),
                'accumulated_depreciation': gl_account_balances.get('193000', {}).get('balance', '0.00'),
                'items': format_equipment_items(rental_equipment, 'rental')
            },
            'new': {
                'qty': len(new_equipment),
                'gl_account_balance': gl_account_balances.get('131000', {}).get('balance', '0.00'),
                'items': format_equipment_items(new_equipment, 'new')
            },
            'used': {
                'qty': len(used_items),
                'gl_account_balance': gl_account_balances.get('131200', {}).get('balance', '0.00'),  # Shared with batteries
                'items': format_equipment_items(used_items, 'used')
            },
            'batteries_chargers': {
                'qty': len(battery_items),
                'gl_account_balance': gl_account_balances.get('131200', {}).get('balance', '0.00'),  # Shared with used
                'items': format_equipment_items(battery_items, 'batteries_chargers')
            },
            'allied': {
                'qty': len(allied_equipment),
                'gl_account_balance': gl_account_balances.get('131300', {}).get('balance', '0.00'),
                'items': format_equipment_items(allied_equipment, 'allied')
            }
        }
        
        # Add overall totals
        summary['totals'] = {
            'total_equipment': sum(cat['qty'] for cat in summary.values() if isinstance(cat, dict) and 'qty' in cat),
            'ytd_depreciation_expense': str(ytd_depreciation)
        }
        
        # Add GL-based data quality notes
        summary['notes'] = [
            "Financial values based on GL account balances (Oct 2025)",
            "Rental net book value = Gross Book Value (183000) - Accumulated Depreciation (193000)",
            "YTD depreciation covers Nov 2024 - Oct 2025 fiscal year only",
            "Equipment counts from actual equipment inventory by department",
            "Used Equipment and Batteries/Chargers both use GL account 131200",
            "All amounts formatted to penny precision for Excel export"
        ]
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': f'Error generating inventory report: {str(e)}'}), 500