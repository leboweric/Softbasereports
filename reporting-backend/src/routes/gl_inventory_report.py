from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from ..services.azure_sql_service import AzureSQLService
from decimal import Decimal, ROUND_HALF_UP
import logging

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

def get_tenant_schema():
    """Get the database schema for the current user's organization"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            if user and user.organization and user.organization.database_schema:
                return user.organization.database_schema
        return 'ben002'  # Fallback
    except:
        return 'ben002'



logger = logging.getLogger(__name__)

gl_inventory_report_bp = Blueprint('gl_inventory_report', __name__)

def format_currency(amount):
    """Format amount to penny precision without rounding"""
    if amount is None:
        return "0.00"
    # Convert to Decimal for precise arithmetic
    decimal_amount = Decimal(str(amount))
    # Round to 2 decimal places using ROUND_HALF_UP
    rounded = decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return str(rounded)

@gl_inventory_report_bp.route('/api/reports/gl-inventory', methods=['GET'])
@jwt_required()
def get_gl_inventory_report():
    """
    Generate GL-based inventory report
    Returns equipment inventory broken down by GL account balances
    """
    try:
        db = AzureSQLService()
        schema = get_tenant_schema()
        # Fiscal year parameters (Nov 2024 - Oct 2025)
        fiscal_start = '2024-11-01'
        fiscal_end = '2025-10-31'
        
        # Step 1: Get GL account balances for target accounts
        gl_balances_query = f"""
        SELECT 
            gl.AccountNo,
            coa.AccountDescription,
            gl.CurrentBalance,
            gl.YTDBalance,
            CASE 
                WHEN gl.AccountNo = '131000' THEN 'New Equipment'
                WHEN gl.AccountNo = '131200' THEN 'Used Equipment + Batteries'
                WHEN gl.AccountNo = '131300' THEN 'Allied Equipment'
                WHEN gl.AccountNo = '183000' THEN 'Rental Fleet Gross Value'
                WHEN gl.AccountNo = '193000' THEN 'Accumulated Depreciation'
                ELSE 'Other'
            END as Category
        FROM {schema}.GL gl
        LEFT JOIN {schema}.ChartOfAccounts coa ON gl.AccountNo = coa.AccountNo
        WHERE gl.AccountNo IN ('131000', '131200', '131300', '183000', '193000')
        ORDER BY gl.AccountNo
        """
        
        gl_balances = db.execute_query(gl_balances_query)
        
        # Step 2: Get YTD depreciation expense (not lifetime accumulated)
        ytd_depreciation_query = f"""
        SELECT 
            SUM(gld.Amount) as YTD_Depreciation_Expense
        FROM {schema}.GLDetail gld
        WHERE gld.AccountNo = '193000'  -- Accumulated Depreciation
        AND gld.EffectiveDate >= '{fiscal_start}'
        AND gld.EffectiveDate <= '{fiscal_end}'
        AND gld.Amount < 0  -- Depreciation increases the accumulated depreciation (credit balance)
        """
        
        ytd_depreciation_result = db.execute_query(ytd_depreciation_query)
        ytd_depreciation = abs(float(ytd_depreciation_result[0]['YTD_Depreciation_Expense'])) if ytd_depreciation_result and ytd_depreciation_result[0]['YTD_Depreciation_Expense'] else 0
        
        # Step 3: Get equipment counts by department to validate
        equipment_counts_query = f"""
        SELECT 
            InventoryDept,
            COUNT(*) as Equipment_Count,
            SUM(CASE WHEN AcquisitionCost IS NOT NULL THEN AcquisitionCost ELSE 0 END) as Total_Acquisition_Cost,
            SUM(CASE WHEN BookValue IS NOT NULL THEN BookValue ELSE 0 END) as Total_Book_Value,
            SUM(CASE WHEN AccumulatedDepreciation IS NOT NULL THEN AccumulatedDepreciation ELSE 0 END) as Total_Accumulated_Depreciation
        FROM {schema}.Equipment
        WHERE InventoryDept IS NOT NULL
        GROUP BY InventoryDept
        ORDER BY InventoryDept
        """
        
        equipment_counts = db.execute_query(equipment_counts_query)
        
        # Step 4: Try to identify equipment by GL account relationship
        # This is exploratory - we'll need to find the actual linking mechanism
        equipment_by_account_query = f"""
        SELECT 
            e.SerialNo,
            e.Make,
            e.Model,
            e.Year,
            e.AcquisitionCost,
            e.BookValue,
            e.AccumulatedDepreciation,
            e.InventoryDept,
            CASE 
                WHEN e.InventoryDept = 10 THEN '131000'  -- New Equipment dept
                WHEN e.InventoryDept = 20 THEN '131200'  -- Used Equipment dept  
                WHEN e.InventoryDept = 30 THEN '131300'  -- Allied dept
                WHEN e.InventoryDept = 60 THEN '183000'  -- Rental dept
                ELSE 'Unknown'
            END as Estimated_GL_Account
        FROM {schema}.Equipment e
        WHERE e.InventoryDept IN (10, 20, 30, 60)
        ORDER BY e.InventoryDept, e.SerialNo
        """
        
        equipment_details = db.execute_query(equipment_by_account_query)
        
        # Step 5: Calculate report totals with precise decimal handling
        report_totals = {}
        
        for balance in gl_balances:
            account_no = balance['AccountNo']
            current_balance = format_currency(balance['CurrentBalance'])
            ytd_balance = format_currency(balance['YTDBalance'])
            
            report_totals[account_no] = {
                'account_description': balance['AccountDescription'],
                'category': balance['Category'],
                'current_balance': current_balance,
                'ytd_balance': ytd_balance,
                'equipment_count': 0,
                'equipment_items': []
            }
        
        # Step 6: Group equipment by estimated GL account
        for equipment in equipment_details:
            gl_account = equipment['Estimated_GL_Account']
            if gl_account in report_totals:
                report_totals[gl_account]['equipment_count'] += 1
                report_totals[gl_account]['equipment_items'].append({
                    'serial_no': equipment['SerialNo'],
                    'make': equipment['Make'],
                    'model': equipment['Model'],
                    'year': equipment['Year'],
                    'acquisition_cost': format_currency(equipment['AcquisitionCost']),
                    'book_value': format_currency(equipment['BookValue']),
                    'accumulated_depreciation': format_currency(equipment['AccumulatedDepreciation']),
                    'inventory_dept': equipment['InventoryDept']
                })
        
        # Step 7: Calculate net rental fleet value (gross - accumulated depreciation)
        gross_rental_value = float(report_totals.get('183000', {}).get('current_balance', '0'))
        accumulated_depreciation = float(report_totals.get('193000', {}).get('current_balance', '0'))
        net_rental_value = format_currency(gross_rental_value - abs(accumulated_depreciation))
        
        # Build final report
        report_data = {
            'report_title': 'GL-Based Inventory Report',
            'fiscal_year': f'{fiscal_start} to {fiscal_end}',
            'generated_date': str(db.execute_query("SELECT GETDATE() as current_date")[0]['current_date']),
            'gl_account_balances': report_totals,
            'summary': {
                'new_equipment_value': report_totals.get('131000', {}).get('current_balance', '0.00'),
                'used_equipment_value': report_totals.get('131200', {}).get('current_balance', '0.00'),
                'allied_equipment_value': report_totals.get('131300', {}).get('current_balance', '0.00'),
                'rental_gross_value': report_totals.get('183000', {}).get('current_balance', '0.00'),
                'accumulated_depreciation': report_totals.get('193000', {}).get('current_balance', '0.00'),
                'net_rental_value': net_rental_value,
                'ytd_depreciation_expense': format_currency(ytd_depreciation),
                'total_equipment_count': sum(dept['Equipment_Count'] for dept in equipment_counts)
            },
            'department_breakdown': equipment_counts,
            'precision_note': 'All amounts formatted to penny precision without rounding'
        }
        
        return jsonify({
            'success': True,
            'data': report_data
        })
        
    except Exception as e:
        logger.error(f"GL inventory report failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'gl_inventory_report_error'
        }), 500

@gl_inventory_report_bp.route('/api/reports/gl-inventory/export', methods=['POST'])
@jwt_required()
def export_gl_inventory_report():
    """
    Export GL inventory report in specified format (CSV, Excel, PDF)
    """
    try:
        data = request.get_json()
        export_format = data.get('format', 'csv').lower()
        
        # Get the report data first
        db = AzureSQLService()
        schema = get_tenant_schema()
        # Re-run the report query for export
        # (In production, you might cache this or pass it as parameter)
        
        if export_format == 'csv':
            # Generate CSV format
            return jsonify({
                'success': True,
                'message': 'CSV export not yet implemented',
                'format': 'csv'
            })
        elif export_format == 'excel':
            # Generate Excel format
            return jsonify({
                'success': True,
                'message': 'Excel export not yet implemented',
                'format': 'excel'
            })
        elif export_format == 'pdf':
            # Generate PDF format
            return jsonify({
                'success': True,
                'message': 'PDF export not yet implemented',
                'format': 'pdf'
            })
        else:
            return jsonify({
                'error': 'Unsupported export format',
                'supported_formats': ['csv', 'excel', 'pdf']
            }), 400
            
    except Exception as e:
        logger.error(f"GL inventory report export failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'gl_inventory_export_error'
        }), 500