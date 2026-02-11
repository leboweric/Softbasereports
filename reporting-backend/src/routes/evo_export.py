"""
EVO Export Route - Tenant-specific P&L Excel export
Populates the tenant's EVO template with GL data from the IPS database.
The template contains VLOOKUP formulas that auto-calculate when opened in Excel.
"""

from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import logging
import calendar
import os
import copy
from io import BytesIO
from openpyxl import load_workbook
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utils.tenant_utils import get_tenant_db
from src.models.user import User

logger = logging.getLogger(__name__)
evo_export_bp = Blueprint('evo_export', __name__)

# Map organization schema to template file
TEMPLATE_MAP = {
    'ips001': 'IPS_template.xlsx',
    # Add more tenants here as needed:
    # 'bmh001': 'BMH_template.xlsx',
}

def get_tenant_schema():
    """Get the database schema for the current user's organization"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            if user and user.organization and user.organization.database_schema:
                return user.organization.database_schema
        return 'ben002'
    except:
        return 'ben002'

def get_tenant_db_service():
    return get_tenant_db()

def get_all_gl_data(schema, year, month):
    """
    Query ALL GL accounts for a given year/month.
    Returns a list of dicts with AccountNo, Year, Month, YTD, MTD, Description, Type.
    """
    query = f"""
    SELECT 
        g.AccountNo,
        g.Year,
        g.Month,
        g.YTD,
        g.MTD,
        c.Description,
        c.Type
    FROM {schema}.GL g
    LEFT JOIN {schema}.ChartOfAccounts c ON g.AccountNo = c.AccountNo
    WHERE g.Year = %s AND g.Month = %s
    ORDER BY g.AccountNo
    """
    try:
        results = get_tenant_db_service().execute_query(query, [year, month])
        rows = []
        for r in results:
            rows.append({
                'AccountNo': str(r.get('AccountNo', '')).strip(),
                'Year': int(r.get('Year', year)),
                'Month': int(r.get('Month', month)),
                'YTD': float(r.get('YTD', 0) or 0),
                'MTD': float(r.get('MTD', 0) or 0),
                'Description': str(r.get('Description', '') or ''),
                'Type': str(r.get('Type', '') or ''),
            })
        return rows
    except Exception as e:
        logger.error(f"Error fetching GL data for {schema} {year}-{month}: {e}")
        return []


def get_prior_month(year, month):
    """Return (year, month) for the prior month"""
    if month == 1:
        return (year - 1, 12)
    return (year, month - 1)


@evo_export_bp.route('/api/reports/pl/evo/export', methods=['GET'])
@jwt_required()
def export_evo():
    """
    Export P&L using the tenant-specific EVO Excel template.
    
    The template has a TB sheet with 3 Excel tables:
    - Table_TB (B5:H761): Current year/month data
    - Table_TB1_1 (P5:V753): Prior year same month data
    - Table_TB2_ (Y5:AD752): Prior month data (beginning balances)
    
    All other sheets use VLOOKUP formulas referencing these tables.
    
    Query Parameters:
        year: Year for the report (default: current year)
        month: Month for the report (default: current month)
    """
    try:
        schema = get_tenant_schema()
        
        # Get parameters
        now = datetime.now()
        year = request.args.get('year', type=int, default=now.year)
        month = request.args.get('month', type=int, default=now.month)
        
        logger.info(f"Generating EVO export for {year}-{month:02d}, schema: {schema}")
        
        # Find the template for this tenant
        template_file = TEMPLATE_MAP.get(schema)
        if not template_file:
            return jsonify({
                'error': f'No EVO template configured for this organization ({schema}). '
                         f'Please contact support to set up your custom template.'
            }), 404
        
        template_path = os.path.join(
            os.path.dirname(__file__), '..', 'templates', 'evo', template_file
        )
        
        if not os.path.exists(template_path):
            return jsonify({
                'error': f'Template file not found: {template_file}'
            }), 500
        
        # Load the template workbook (preserving formulas)
        wb = load_workbook(template_path)
        ws = wb['TB']
        
        # --- Fetch GL data for 3 periods ---
        
        # 1. Current year/month
        current_data = get_all_gl_data(schema, year, month)
        logger.info(f"Current period ({year}-{month}): {len(current_data)} accounts")
        
        # 2. Prior year, same month
        prior_year_data = get_all_gl_data(schema, year - 1, month)
        logger.info(f"Prior year ({year-1}-{month}): {len(prior_year_data)} accounts")
        
        # 3. Prior month (for beginning balances)
        prev_year, prev_month = get_prior_month(year, month)
        prior_month_data = get_all_gl_data(schema, prev_year, prev_month)
        logger.info(f"Prior month ({prev_year}-{prev_month}): {len(prior_month_data)} accounts")
        
        # --- Update control cells ---
        # A3 = month number, A4 = year
        ws.cell(row=3, column=1, value=month)
        ws.cell(row=4, column=1, value=year)
        
        # --- Populate Table_TB (columns B-H, starting row 6) ---
        # Clear existing data first
        for row in range(6, 762):
            for col in [2, 3, 4, 5, 6, 7, 8]:  # B-H
                ws.cell(row=row, column=col, value=None)
        
        for i, acct in enumerate(current_data):
            row = 6 + i
            if row > 761:
                break
            ws.cell(row=row, column=2, value=int(acct['AccountNo']) if acct['AccountNo'].isdigit() else acct['AccountNo'])  # B: AccountNo
            ws.cell(row=row, column=3, value=acct['Year'])      # C: Year
            ws.cell(row=row, column=4, value=acct['Month'])      # D: Month
            ws.cell(row=row, column=5, value=acct['YTD'])        # E: YTD
            ws.cell(row=row, column=6, value=acct['MTD'])        # F: MTD
            ws.cell(row=row, column=7, value=acct['Description'])# G: Description
            ws.cell(row=row, column=8, value=acct['Type'])       # H: Type
        
        # --- Populate Table_TB1_1 (columns P-V, starting row 6) ---
        for row in range(6, 754):
            for col in [16, 17, 18, 19, 20, 21, 22]:  # P-V
                ws.cell(row=row, column=col, value=None)
        
        for i, acct in enumerate(prior_year_data):
            row = 6 + i
            if row > 753:
                break
            ws.cell(row=row, column=16, value=int(acct['AccountNo']) if acct['AccountNo'].isdigit() else acct['AccountNo'])  # P: AccountNo
            ws.cell(row=row, column=17, value=acct['Year'])      # Q: Year
            ws.cell(row=row, column=18, value=acct['Month'])     # R: Month
            ws.cell(row=row, column=19, value=acct['YTD'])       # S: YTD
            ws.cell(row=row, column=20, value=acct['MTD'])       # T: MTD
            ws.cell(row=row, column=21, value=acct['Description'])# U: Description
            ws.cell(row=row, column=22, value=acct['Type'])      # V: Type
        
        # --- Populate Table_TB2_ (columns Y-AD, starting row 6) ---
        for row in range(6, 753):
            for col in [25, 26, 27, 28, 29, 30]:  # Y-AD
                ws.cell(row=row, column=col, value=None)
        
        for i, acct in enumerate(prior_month_data):
            row = 6 + i
            if row > 752:
                break
            ws.cell(row=row, column=25, value=int(acct['AccountNo']) if acct['AccountNo'].isdigit() else acct['AccountNo'])  # Y: AccountNo
            ws.cell(row=row, column=26, value='Actual')          # Z: AccountField
            ws.cell(row=row, column=27, value=acct['YTD'])       # AA: YTD
            ws.cell(row=row, column=28, value=acct['MTD'])       # AB: MTD
            ws.cell(row=row, column=29, value=acct['Type'])      # AC: Type
            ws.cell(row=row, column=30, value=acct['Description'])# AD: Description
        
        # --- Update the Excel table ranges to match actual data ---
        # Table_TB: B5:H{5+len(current_data)}
        new_tb_end = 5 + len(current_data)
        new_tb1_end = 5 + len(prior_year_data)
        new_tb2_end = 5 + len(prior_month_data)
        
        for table in ws.tables.values():
            if table.name == 'Table_TB':
                table.ref = f'B5:H{new_tb_end}'
            elif table.name == 'Table_TB1_1':
                table.ref = f'P5:V{new_tb1_end}'
            elif table.name == 'Table_TB2_':
                table.ref = f'Y5:AD{new_tb2_end}'
        
        # --- Save to BytesIO and return ---
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Generate filename matching Amy's naming convention
        month_str = f"{month:02d}"
        filename = f"{month_str}-{year}EVO.xlsx"
        
        logger.info(f"EVO export generated: {filename}")
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error exporting EVO: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to export EVO file', 'message': str(e)}), 500
