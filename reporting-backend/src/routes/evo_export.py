"""
EVO Export Route - Tenant-specific P&L Excel export
Populates the tenant's EVO template with GL data from the IPS database.

CRITICAL: This module uses direct XML/ZIP manipulation instead of openpyxl's
save mechanism. openpyxl corrupts Excel files by stripping printer settings,
query tables, shared strings, calc chains, and reordering XML attributes,
which triggers Excel's "We found a problem with some content" warning.
By working directly at the ZIP/XML level, we preserve the template's exact
structure for all unchanged content.
"""

from flask import Blueprint, jsonify, request, send_file
from datetime import datetime
import logging
import re
import os
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utils.tenant_utils import get_tenant_db
from src.models.user import User

logger = logging.getLogger(__name__)
evo_export_bp = Blueprint('evo_export', __name__)

# Map organization schema to template file
TEMPLATE_MAP = {
    'ind004': 'IPS_template.xlsx',
}

# Spreadsheet ML namespace
SSML_NS = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NS = {'s': SSML_NS}

# Sheet name to sheet file number mapping
SHEET_NAME_TO_NUM = {
    'TB': 1,
    'Balance Sheet': 2,
    'Trial Balance': 3,
    'Combined Detail P and L': 4,
    'Consolidated Expense Statement': 5,
    'Consolitated Income Statement': 6,
    'Dynamic Storage Solutions': 7,
    'C H Steel Solutions': 8,
    'AMI Sales Department': 9,
    'Canton Sales Department': 10,
    'Canton Parts Department': 11,
    'Canton Service Department': 12,
    'Canton Rental Department': 13,
    'Canton Used Department': 14,
    'Administration Department': 15,
    'Cleveland Sales Department': 16,
    'Cleveland Parts Department': 17,
    'Cleveland Service Department': 18,
    'Cleveland Rental Department': 19,
    'Cleveland Used Department': 20,
    'CLE-Consolitated Income Stateme': 21,
    'Cons. Inc. Stmt. - All Branches': 22,
    '3M Meeting Income Statement': 23,
}

# VLOOKUP column index to data field mapping
TB_COL_MAP = {1: 'AccountNo', 2: 'Year', 3: 'Month', 4: 'YTD', 5: 'MTD', 6: 'Description', 7: 'Type'}
TB2_COL_MAP = {1: 'AccountNo', 2: 'AccountField', 3: 'YTD', 4: 'MTD', 5: 'Type', 6: 'Description'}

# Regex to parse VLOOKUP formulas from raw XML
VLOOKUP_RE = re.compile(
    r'VLOOKUP\(([A-Z]+)(\d+),TB!(TB|TB1_1|TB2_),(\d+),FALSE\)(?:\*(-?1))?'
)

# Known VLOOKUP column locations per sheet
VLOOKUP_LOCATIONS = {
    'Balance Sheet':               (5, 175, [5, 7]),
    'Trial Balance':               (7, 130, [5, 7, 9, 13]),
    'Combined Detail P and L':     (7, 638, [5, 8, 11, 14]),
    'Dynamic Storage Solutions':   (6, 59,  [5, 8, 11, 14]),
    'C H Steel Solutions':         (6, 60,  [5, 8, 11, 14]),
    'AMI Sales Department':        (7, 52,  [5, 8, 11, 14]),
    'Canton Sales Department':     (7, 59,  [5, 8, 11, 14]),
    'Canton Parts Department':     (7, 85,  [5, 8, 11, 14]),
    'Canton Service Department':   (7, 80,  [7, 10, 13, 16]),
    'Canton Rental Department':    (7, 39,  [5, 8, 11, 14]),
    'Canton Used Department':      (7, 48,  [5, 8, 11, 14]),
    'Administration Department':   (7, 51,  [5, 8, 11, 14]),
    'Cleveland Sales Department':  (7, 62,  [5, 8, 11, 14]),
    'Cleveland Parts Department':  (7, 76,  [5, 8, 11, 14]),
    'Cleveland Service Department':(7, 80,  [7, 10, 13, 16]),
    'Cleveland Rental Department': (7, 37,  [5, 8, 11, 14]),
    'Cleveland Used Department':   (7, 48,  [5, 8, 11, 14]),
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
    """Query ALL GL accounts for a given year/month."""
    query = f"""
    SELECT 
        g.AccountNo, g.Year, g.Month, g.YTD, g.MTD,
        c.Description, c.Type
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


def build_lookup_dicts(current_data, prior_year_data, prior_month_data):
    """Build lookup dictionaries keyed by account number string."""
    tb_lookup = {acct['AccountNo']: acct for acct in current_data}
    tb1_lookup = {acct['AccountNo']: acct for acct in prior_year_data}
    tb2_lookup = {acct['AccountNo']: acct for acct in prior_month_data}
    return tb_lookup, tb1_lookup, tb2_lookup


# ─── Shared String Resolution ────────────────────────────────────────────────

def load_shared_strings(zip_file):
    """Load the shared string table from the xlsx zip."""
    try:
        ss_data = zip_file.read('xl/sharedStrings.xml')
        root = ET.fromstring(ss_data)
        strings = []
        for si in root.findall(f'{{{SSML_NS}}}si'):
            t = si.find(f'{{{SSML_NS}}}t')
            strings.append(t.text if t is not None and t.text else '')
        return strings
    except (KeyError, ET.ParseError):
        return []


# ─── Column Helpers ───────────────────────────────────────────────────────────

def col_num_to_letter(n):
    """Convert 1-based column number to letter(s): 1=A, 26=Z, 27=AA"""
    result = ''
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result = chr(65 + remainder) + result
    return result


def col_letter_to_num(col_str):
    """Convert column letter(s) to 1-based number: A=1, B=2"""
    result = 0
    for ch in col_str.upper():
        result = result * 26 + (ord(ch) - ord('A') + 1)
    return result


# ─── Raw XML Cell Manipulation ────────────────────────────────────────────────

def format_num(value):
    """Format a number for XML, avoiding floating point artifacts."""
    if isinstance(value, float):
        # Round to avoid artifacts like 8245.059999999999
        rounded = round(value, 10)
        # Use repr-like formatting but clean
        s = f'{rounded:.10f}'.rstrip('0').rstrip('.')
        return s
    return str(value)


def build_cell_xml(col_letter, row_num, value, style_id='1'):
    """Build a cell XML element string for a given value."""
    ref = f'{col_letter}{row_num}'
    
    if value is None or value == '':
        return f'<c r="{ref}" s="{style_id}"/>'
    
    if isinstance(value, str):
        # Escape XML special characters
        escaped = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        return f'<c r="{ref}" s="{style_id}" t="inlineStr"><is><t>{escaped}</t></is></c>'
    elif isinstance(value, (int, float)):
        return f'<c r="{ref}" s="{style_id}"><v>{format_num(value)}</v></c>'
    else:
        return f'<c r="{ref}" s="{style_id}"><v>{value}</v></c>'


def modify_tb_sheet(raw_xml, current_data, prior_year_data, prior_month_data, year, month):
    """
    Modify the TB sheet XML to populate with GL data.
    Works on raw bytes to preserve exact XML structure.
    """
    xml_str = raw_xml.decode('utf-8')
    
    # 1. Update control cells A3 (month) and A4 (year)
    xml_str = re.sub(
        r'(<c r="A3"[^>]*>)<v>[^<]*</v>(</c>)',
        rf'\g<1><v>{month}</v>\g<2>',
        xml_str
    )
    xml_str = re.sub(
        r'(<c r="A4"[^>]*>)<v>[^<]*</v>(</c>)',
        rf'\g<1><v>{year}</v>\g<2>',
        xml_str
    )
    
    # 2. Build new row content for each data table
    # We need to replace entire rows because the cell structure changes
    # (shared strings -> inline strings, different values)
    
    # Helper to build a complete row for Table_TB (cols B-H)
    def build_tb_row(row_num, acct):
        """Build cells for Table_TB columns B through H."""
        acct_no = int(acct['AccountNo']) if acct['AccountNo'].isdigit() else acct['AccountNo']
        cells = [
            build_cell_xml('B', row_num, acct_no),
            build_cell_xml('C', row_num, acct['Year']),
            build_cell_xml('D', row_num, acct['Month']),
            build_cell_xml('E', row_num, acct['YTD']),
            build_cell_xml('F', row_num, acct['MTD']),
            build_cell_xml('G', row_num, acct['Description']),
            build_cell_xml('H', row_num, acct['Type']),
        ]
        return ''.join(cells)
    
    # Helper to build cells for Table_TB1_1 (cols P-V)
    def build_tb1_row(row_num, acct):
        cells = [
            build_cell_xml('P', row_num, int(acct['AccountNo']) if acct['AccountNo'].isdigit() else acct['AccountNo']),
            build_cell_xml('Q', row_num, acct['Year']),
            build_cell_xml('R', row_num, acct['Month']),
            build_cell_xml('S', row_num, acct['YTD']),
            build_cell_xml('T', row_num, acct['MTD']),
            build_cell_xml('U', row_num, acct['Description']),
            build_cell_xml('V', row_num, acct['Type']),
        ]
        return ''.join(cells)
    
    # Helper to build cells for Table_TB2_ (cols Y-AD)
    def build_tb2_row(row_num, acct):
        cells = [
            build_cell_xml('Y', row_num, int(acct['AccountNo']) if acct['AccountNo'].isdigit() else acct['AccountNo']),
            build_cell_xml('Z', row_num, 'Actual'),
            build_cell_xml('AA', row_num, acct['YTD']),
            build_cell_xml('AB', row_num, acct['MTD']),
            build_cell_xml('AC', row_num, acct['Type']),
            build_cell_xml('AD', row_num, acct['Description']),
        ]
        return ''.join(cells)
    
    # Helper to build empty cells for a table
    def build_empty_cells(row_num, col_letters):
        return ''.join(f'<c r="{cl}{row_num}" s="1"/>' for cl in col_letters)
    
    # 3. Replace each data row
    # Strategy: find each <row r="N"...>...</row> and replace the table cells
    # We need to be careful to preserve non-table cells (like column A)
    
    # For rows 6 through max, replace the table data cells
    # Table_TB: rows 6-761, cols B-H
    # Table_TB1_1: rows 6-753, cols P-V  
    # Table_TB2_: rows 6-752, cols Y-AD
    
    max_row = 761  # Max row across all tables
    
    for row_num in range(6, max_row + 1):
        # Find the existing row element
        row_pattern = re.compile(
            r'<row r="' + str(row_num) + r'"([^>]*)>(.*?)</row>',
            re.DOTALL
        )
        row_match = row_pattern.search(xml_str)
        
        if not row_match:
            continue
        
        row_attrs = row_match.group(1)
        row_content = row_match.group(2)
        
        # Parse existing cells to preserve non-table cells (like column A)
        cell_pattern = re.compile(r'<c r="([A-Z]+)' + str(row_num) + r'"[^>]*(?:/>|>.*?</c>)', re.DOTALL)
        existing_cells = {}
        for cell_match in cell_pattern.finditer(row_content):
            col = cell_match.group(1)
            existing_cells[col] = cell_match.group(0)
        
        # Build new row content
        new_cells = []
        
        # Keep column A if it exists
        if 'A' in existing_cells:
            new_cells.append(existing_cells['A'])
        
        # Table_TB data (cols B-H)
        data_idx = row_num - 6
        if data_idx < len(current_data):
            new_cells.append(build_tb_row(row_num, current_data[data_idx]))
        elif row_num <= 761:
            new_cells.append(build_empty_cells(row_num, ['B', 'C', 'D', 'E', 'F', 'G', 'H']))
        
        # Keep any cells between H and P (cols I-O) if they exist
        for col in ['I', 'J', 'K', 'L', 'M', 'N', 'O']:
            if col in existing_cells:
                new_cells.append(existing_cells[col])
        
        # Table_TB1_1 data (cols P-V)
        if row_num <= 753:
            if data_idx < len(prior_year_data):
                new_cells.append(build_tb1_row(row_num, prior_year_data[data_idx]))
            else:
                new_cells.append(build_empty_cells(row_num, ['P', 'Q', 'R', 'S', 'T', 'U', 'V']))
        
        # Keep any cells between V and Y (cols W-X) if they exist
        for col in ['W', 'X']:
            if col in existing_cells:
                new_cells.append(existing_cells[col])
        
        # Table_TB2_ data (cols Y-AD)
        if row_num <= 752:
            if data_idx < len(prior_month_data):
                new_cells.append(build_tb2_row(row_num, prior_month_data[data_idx]))
            else:
                new_cells.append(build_empty_cells(row_num, ['Y', 'Z', 'AA', 'AB', 'AC', 'AD']))
        
        new_row_content = ''.join(new_cells)
        new_row = f'<row r="{row_num}"{row_attrs}>{new_row_content}</row>'
        
        xml_str = xml_str[:row_match.start()] + new_row + xml_str[row_match.end():]
    
    return xml_str.encode('utf-8')


def resolve_vlookup_value(formula_text, sheet_xml_str, shared_strings, 
                          tb_lookup, tb1_lookup, tb2_lookup):
    """
    Resolve a VLOOKUP formula to its computed value.
    Uses the shared string table to resolve account numbers from column A.
    """
    match = VLOOKUP_RE.search(formula_text)
    if not match:
        return None
    
    ref_col = match.group(1)  # e.g., 'A'
    ref_row = match.group(2)  # e.g., '7'
    table_name = match.group(3)  # 'TB', 'TB1_1', or 'TB2_'
    col_idx = int(match.group(4))
    multiplier_str = match.group(5)
    multiplier = int(multiplier_str) if multiplier_str else 1
    
    # Find the lookup cell (e.g., A7) value
    cell_ref = f'{ref_col}{ref_row}'
    
    # Try to find the cell in the XML
    cell_pattern = re.compile(
        r'<c r="' + re.escape(cell_ref) + r'"([^>]*)(?:/>|>(.*?)</c>)',
        re.DOTALL
    )
    cell_match = cell_pattern.search(sheet_xml_str)
    if not cell_match:
        return 0
    
    cell_attrs = cell_match.group(1)
    cell_content = cell_match.group(2) or ''
    
    # Extract value
    lookup_value = None
    
    # Check if it's a shared string
    if 't="s"' in cell_attrs:
        v_match = re.search(r'<v>(\d+)</v>', cell_content)
        if v_match and shared_strings:
            ss_idx = int(v_match.group(1))
            if ss_idx < len(shared_strings):
                lookup_value = shared_strings[ss_idx]
    elif 't="inlineStr"' in cell_attrs:
        t_match = re.search(r'<t>([^<]*)</t>', cell_content)
        if t_match:
            lookup_value = t_match.group(1)
    else:
        v_match = re.search(r'<v>([^<]*)</v>', cell_content)
        if v_match:
            lookup_value = v_match.group(1)
    
    if lookup_value is None:
        return 0
    
    # Convert to lookup key
    try:
        lookup_key = str(int(float(lookup_value)))
    except (ValueError, TypeError):
        lookup_key = str(lookup_value).strip()
    
    # Select lookup dict and column map
    if table_name == 'TB':
        lookup_dict = tb_lookup
        col_map = TB_COL_MAP
    elif table_name == 'TB1_1':
        lookup_dict = tb1_lookup
        col_map = TB_COL_MAP
    elif table_name == 'TB2_':
        lookup_dict = tb2_lookup
        col_map = TB2_COL_MAP
    else:
        return 0
    
    acct_data = lookup_dict.get(lookup_key)
    if acct_data is None:
        return 0
    
    field_name = col_map.get(col_idx)
    if field_name is None:
        return 0
    
    value = acct_data.get(field_name, 0)
    if value is None:
        value = 0
    
    if isinstance(value, (int, float)):
        return value * multiplier
    return value


def update_vlookup_cached_values(raw_xml, sheet_name, shared_strings,
                                  tb_lookup, tb1_lookup, tb2_lookup):
    """
    Update cached values in VLOOKUP formula cells.
    Preserves the formula element, only updates the <v> cached value.
    Works on raw XML bytes to preserve exact structure.
    """
    xml_str = raw_xml.decode('utf-8')
    total_computed = 0
    
    if sheet_name not in VLOOKUP_LOCATIONS:
        return raw_xml, 0
    
    min_row, max_row, cols = VLOOKUP_LOCATIONS[sheet_name]
    col_letters = [col_num_to_letter(c) for c in cols]
    
    # Find all VLOOKUP cells and update their cached values
    for col_letter in col_letters:
        for row_num in range(min_row, max_row + 1):
            cell_ref = f'{col_letter}{row_num}'
            
            # Find the cell element
            cell_pattern = re.compile(
                r'<c r="' + re.escape(cell_ref) + r'"([^>]*)>(.*?)</c>',
                re.DOTALL
            )
            cell_match = cell_pattern.search(xml_str)
            if not cell_match:
                continue
            
            cell_attrs = cell_match.group(1)
            cell_content = cell_match.group(2)
            
            # Check if it has a VLOOKUP formula
            f_match = re.search(r'<f>(.*?)</f>', cell_content)
            if not f_match or 'VLOOKUP' not in f_match.group(1):
                continue
            
            formula = f_match.group(1)
            
            # Resolve the VLOOKUP
            result = resolve_vlookup_value(
                formula, xml_str, shared_strings,
                tb_lookup, tb1_lookup, tb2_lookup
            )
            
            if result is None:
                continue
            
            # Build new cell content: keep formula, update value
            formatted_val = format_num(result)
            new_content = f'<f>{formula}</f><v>{formatted_val}</v>'
            new_cell = f'<c r="{cell_ref}"{cell_attrs}>{new_content}</c>'
            
            xml_str = xml_str[:cell_match.start()] + new_cell + xml_str[cell_match.end():]
            total_computed += 1
    
    return xml_str.encode('utf-8'), total_computed


@evo_export_bp.route('/api/reports/pl/evo/export', methods=['GET'])
@jwt_required()
def export_evo():
    """
    Export P&L using the tenant-specific EVO Excel template.
    Uses direct XML/ZIP manipulation to preserve template structure.
    """
    try:
        schema = get_tenant_schema()
        
        now = datetime.now()
        year = request.args.get('year', type=int, default=now.year)
        month = request.args.get('month', type=int, default=now.month)
        
        logger.info(f"Generating EVO export for {year}-{month:02d}, schema: {schema}")
        
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
            return jsonify({'error': f'Template file not found: {template_file}'}), 500
        
        # --- Fetch GL data for 3 periods ---
        current_data = get_all_gl_data(schema, year, month)
        logger.info(f"Current period ({year}-{month}): {len(current_data)} accounts")
        
        prior_year_data = get_all_gl_data(schema, year - 1, month)
        logger.info(f"Prior year ({year-1}-{month}): {len(prior_year_data)} accounts")
        
        prev_year, prev_month = get_prior_month(year, month)
        prior_month_data = get_all_gl_data(schema, prev_year, prev_month)
        logger.info(f"Prior month ({prev_year}-{prev_month}): {len(prior_month_data)} accounts")
        
        tb_lookup, tb1_lookup, tb2_lookup = build_lookup_dicts(
            current_data, prior_year_data, prior_month_data
        )
        
        # --- Process template at ZIP/XML level ---
        output = BytesIO()
        total_vlookups = 0
        
        with zipfile.ZipFile(template_path, 'r') as zin:
            # Load shared strings for resolving account numbers in P&L sheets
            shared_strings = load_shared_strings(zin)
            logger.info(f"Loaded {len(shared_strings)} shared strings from template")
            
            with zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    raw_data = zin.read(item.filename)
                    
                    if item.filename == 'xl/worksheets/sheet1.xml':
                        # TB sheet - populate with GL data
                        modified = modify_tb_sheet(
                            raw_data, current_data, prior_year_data,
                            prior_month_data, year, month
                        )
                        zout.writestr(item, modified)
                        logger.info(f"Populated TB sheet: {len(current_data)} current, "
                                   f"{len(prior_year_data)} prior year, "
                                   f"{len(prior_month_data)} prior month")
                    
                    elif (item.filename.startswith('xl/worksheets/sheet') 
                          and item.filename.endswith('.xml')):
                        # P&L sheets - update VLOOKUP cached values
                        sheet_num = int(re.search(r'sheet(\d+)\.xml', item.filename).group(1))
                        
                        sheet_name = None
                        for name, num in SHEET_NAME_TO_NUM.items():
                            if num == sheet_num:
                                sheet_name = name
                                break
                        
                        if sheet_name and sheet_name in VLOOKUP_LOCATIONS:
                            modified, computed = update_vlookup_cached_values(
                                raw_data, sheet_name, shared_strings,
                                tb_lookup, tb1_lookup, tb2_lookup
                            )
                            zout.writestr(item, modified)
                            total_vlookups += computed
                            if computed > 0:
                                logger.info(f"Updated {computed} VLOOKUP values in '{sheet_name}'")
                        else:
                            # No VLOOKUPs to update, copy as-is
                            zout.writestr(item, raw_data)
                    else:
                        # All other files: copy byte-for-byte
                        zout.writestr(item, raw_data)
        
        output.seek(0)
        
        month_str = f"{month:02d}"
        filename = f"{month_str}-{year}EVO.xlsx"
        
        logger.info(f"EVO export generated: {filename} ({total_vlookups} VLOOKUPs updated)")
        
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
