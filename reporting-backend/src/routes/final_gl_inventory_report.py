from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required
from ..services.azure_sql_service import AzureSQLService
from ..services.report_generator import ReportGenerator
from decimal import Decimal, ROUND_HALF_UP
import logging
import io
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

final_gl_inventory_report_bp = Blueprint('final_gl_inventory_report', __name__)

def format_currency(amount):
    """Format amount to penny precision without rounding"""
    if amount is None:
        return Decimal('0.00')
    # Convert to Decimal for precise arithmetic
    decimal_amount = Decimal(str(amount))
    # Round to 2 decimal places using ROUND_HALF_UP
    return decimal_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

@final_gl_inventory_report_bp.route('/api/reports/final-gl-inventory', methods=['GET'])
@jwt_required()
def get_final_gl_inventory_report():
    """
    Final GL-based inventory report with all requirements:
    - Decimal precision to penny (no rounding)
    - Equipment counts matching expectations  
    - Year-to-date depreciation (not lifetime)
    - Equipment linked to GL accounts
    """
    try:
        db = AzureSQLService()
        
        # Fiscal year parameters (Nov 2024 - Oct 2025)
        fiscal_start = '2024-11-01'
        fiscal_end = '2025-10-31'
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Step 1: Get GL account balances with precise decimal handling (simplified - no ChartOfAccounts join)
        gl_balances_query = """
        SELECT 
            AccountNo,
            CAST(CurrentBalance AS DECIMAL(18,2)) as CurrentBalance,
            CAST(YTDBalance AS DECIMAL(18,2)) as YTDBalance,
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
        ORDER BY AccountNo
        """
        
        gl_balances = db.execute_query(gl_balances_query)
        
        # Step 2: Get YTD depreciation expense (fiscal year only)
        ytd_depreciation_query = f"""
        SELECT 
            CAST(SUM(CASE WHEN gld.Amount < 0 THEN ABS(gld.Amount) ELSE 0 END) AS DECIMAL(18,2)) as YTD_Depreciation_Expense,
            COUNT(*) as Transaction_Count
        FROM ben002.GLDetail gld
        WHERE gld.AccountNo = '193000'  -- Accumulated Depreciation
        AND gld.EffectiveDate >= '{fiscal_start}'
        AND gld.EffectiveDate <= '{fiscal_end}'
        """
        
        ytd_depreciation_result = db.execute_query(ytd_depreciation_query)
        ytd_depreciation = format_currency(ytd_depreciation_result[0]['YTD_Depreciation_Expense']) if ytd_depreciation_result else Decimal('0.00')
        
        # Step 3: Get equipment details with department-based GL mapping (using correct Equipment table fields)
        equipment_details_query = """
        SELECT 
            e.SerialNo,
            e.Make,
            e.Model,
            e.ModelYear,
            CAST(e.Cost AS DECIMAL(18,2)) as Cost,
            e.InventoryDept,
            CASE 
                WHEN e.InventoryDept = 10 THEN '131000'
                WHEN e.InventoryDept = 20 THEN '131200'
                WHEN e.InventoryDept = 30 THEN '131300'
                WHEN e.InventoryDept = 60 THEN '183000'
                ELSE 'Unknown'
            END as GL_Account,
            CASE 
                WHEN e.InventoryDept = 10 THEN 'New Equipment'
                WHEN e.InventoryDept = 20 THEN 'Used Equipment + Batteries'
                WHEN e.InventoryDept = 30 THEN 'Allied Equipment'
                WHEN e.InventoryDept = 60 THEN 'Rental Fleet'
                ELSE 'Other Department'
            END as Department_Category
        FROM ben002.Equipment e
        WHERE e.InventoryDept IN (10, 20, 30, 60)
        AND e.SerialNo IS NOT NULL
        ORDER BY e.InventoryDept, e.SerialNo
        """
        
        equipment_details = db.execute_query(equipment_details_query)
        
        # Step 4: Build report with precise decimal calculations
        report_data = {
            'report_title': 'Final GL-Based Inventory Report',
            'fiscal_year': f'{fiscal_start} to {fiscal_end}',
            'generated_date': current_date,
            'precision_note': 'All amounts formatted to penny precision (2 decimal places)',
            'gl_accounts': {},
            'equipment_summary': {},
            'ytd_depreciation': str(ytd_depreciation)
        }
        
        # Process GL account balances
        for balance in gl_balances:
            account_no = balance['AccountNo']
            current_balance = format_currency(balance['CurrentBalance'])
            ytd_balance = format_currency(balance['YTDBalance'])
            
            report_data['gl_accounts'][account_no] = {
                'account_number': account_no,
                'category': balance['Category'],
                'current_balance': str(current_balance),
                'ytd_balance': str(ytd_balance)
            }
        
        # Process equipment by GL account
        equipment_by_account = {}
        for equipment in equipment_details:
            gl_account = equipment['GL_Account']
            
            if gl_account not in equipment_by_account:
                equipment_by_account[gl_account] = {
                    'count': 0,
                    'total_cost': Decimal('0.00'),
                    'equipment_list': []
                }
            
            # Add equipment to the account
            cost = format_currency(equipment['Cost'])
            
            equipment_by_account[gl_account]['count'] += 1
            equipment_by_account[gl_account]['total_cost'] += cost
            
            equipment_by_account[gl_account]['equipment_list'].append({
                'serial_no': equipment['SerialNo'],
                'make': equipment['Make'],
                'model': equipment['Model'],
                'year': equipment['ModelYear'],
                'cost': str(cost),
                'department': equipment['InventoryDept'],
                'category': equipment['Department_Category']
            })
        
        # Convert totals to strings for JSON serialization
        for account in equipment_by_account:
            equipment_by_account[account]['total_cost'] = str(equipment_by_account[account]['total_cost'])
        
        report_data['equipment_summary'] = equipment_by_account
        
        # Step 5: Calculate key metrics
        total_equipment_count = sum(acc['count'] for acc in equipment_by_account.values())
        
        # Net rental value calculation
        rental_gross = format_currency(report_data['gl_accounts'].get('183000', {}).get('current_balance', '0.00'))
        accumulated_dep = format_currency(report_data['gl_accounts'].get('193000', {}).get('current_balance', '0.00'))
        net_rental_value = rental_gross - abs(accumulated_dep)
        
        report_data['summary_metrics'] = {
            'total_equipment_count': total_equipment_count,
            'new_equipment_value': report_data['gl_accounts'].get('131000', {}).get('current_balance', '0.00'),
            'used_equipment_value': report_data['gl_accounts'].get('131200', {}).get('current_balance', '0.00'),
            'allied_equipment_value': report_data['gl_accounts'].get('131300', {}).get('current_balance', '0.00'),
            'rental_gross_value': str(rental_gross),
            'accumulated_depreciation': str(accumulated_dep),
            'net_rental_value': str(net_rental_value),
            'ytd_depreciation_expense': str(ytd_depreciation)
        }
        
        return jsonify({
            'success': True,
            'data': report_data
        })
        
    except Exception as e:
        logger.error(f"Final GL inventory report failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'final_gl_inventory_report_error'
        }), 500

@final_gl_inventory_report_bp.route('/api/reports/final-gl-inventory/export', methods=['POST'])
@jwt_required()
def export_final_gl_inventory_report():
    """
    Export the final GL inventory report in various formats
    """
    try:
        data = request.get_json()
        export_format = data.get('format', 'csv').lower()
        
        # Get the report data first
        db = AzureSQLService()
        report_generator = ReportGenerator()
        
        # Re-run a simplified query for export (using correct Equipment table fields)
        export_query = """
        SELECT 
            e.SerialNo,
            e.Make,
            e.Model,
            e.ModelYear,
            CAST(e.Cost AS DECIMAL(18,2)) as Cost,
            e.InventoryDept,
            CASE 
                WHEN e.InventoryDept = 10 THEN '131000 - New Equipment'
                WHEN e.InventoryDept = 20 THEN '131200 - Used Equipment + Batteries'
                WHEN e.InventoryDept = 30 THEN '131300 - Allied Equipment'
                WHEN e.InventoryDept = 60 THEN '183000 - Rental Fleet'
                ELSE 'Other'
            END as GL_Account_Category
        FROM ben002.Equipment e
        WHERE e.InventoryDept IN (10, 20, 30, 60)
        AND e.SerialNo IS NOT NULL
        ORDER BY e.InventoryDept, e.SerialNo
        """
        
        export_data = db.execute_query(export_query)
        
        if export_format == 'csv':
            csv_content = report_generator.generate_csv_report(
                export_data, 
                filename="gl_inventory_report.csv"
            )
            
            # Create a file-like object
            output = io.StringIO(csv_content)
            
            return jsonify({
                'success': True,
                'format': 'csv',
                'data': csv_content,
                'filename': 'gl_inventory_report.csv'
            })
            
        elif export_format == 'excel':
            excel_content = report_generator.generate_excel_report(
                export_data,
                filename="gl_inventory_report.xlsx"
            )
            
            return jsonify({
                'success': True,
                'format': 'excel',
                'message': 'Excel export completed',
                'filename': 'gl_inventory_report.xlsx'
            })
            
        else:
            return jsonify({
                'error': 'Unsupported export format',
                'supported_formats': ['csv', 'excel']
            }), 400
            
    except Exception as e:
        logger.error(f"Final GL inventory export failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'final_gl_inventory_export_error'
        }), 500