from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db
from ..services.azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

accounting_diagnostics_bp = Blueprint('accounting_diagnostics', __name__)

@accounting_diagnostics_bp.route('/api/diagnostics/accounting-tables', methods=['GET'])
@jwt_required()
def discover_accounting_tables():
    """Comprehensive discovery of accounting and finance related tables"""
    try:
        db = get_tenant_db()
        schema = get_tenant_schema()
        # Step 1: Find all potential accounting/finance tables
        discovery_query = f"""
        SELECT 
            t.TABLE_NAME,
            t.TABLE_TYPE,
            COALESCE(CAST(p.rows AS INT), 0) as ROW_COUNT
        FROM INFORMATION_SCHEMA.TABLES t
        LEFT JOIN sys.partitions p 
            ON p.object_id = OBJECT_ID(t.TABLE_SCHEMA + '.' + t.TABLE_NAME)
            AND p.index_id IN (0,1)
        WHERE t.TABLE_SCHEMA = '{schema}'
        AND (
            -- Accounting/Finance keywords
            t.TABLE_NAME LIKE '%account%'
            OR t.TABLE_NAME LIKE '%GL%'
            OR t.TABLE_NAME LIKE '%ledger%'
            OR t.TABLE_NAME LIKE '%journal%'
            OR t.TABLE_NAME LIKE '%transaction%'
            
            -- Payables/Expenses
            OR t.TABLE_NAME LIKE '%AP%'
            OR t.TABLE_NAME LIKE '%payable%'
            OR t.TABLE_NAME LIKE '%expense%'
            OR t.TABLE_NAME LIKE '%vendor%'
            OR t.TABLE_NAME LIKE '%supplier%'
            OR t.TABLE_NAME LIKE '%purchase%'
            OR t.TABLE_NAME LIKE '%payment%'
            
            -- Payroll/HR
            OR t.TABLE_NAME LIKE '%payroll%'
            OR t.TABLE_NAME LIKE '%salary%'
            OR t.TABLE_NAME LIKE '%wage%'
            OR t.TABLE_NAME LIKE '%employee%'
            OR t.TABLE_NAME LIKE '%compensation%'
            
            -- Other G&A
            OR t.TABLE_NAME LIKE '%utility%'
            OR t.TABLE_NAME LIKE '%rent%'
            OR t.TABLE_NAME LIKE '%insurance%'
            OR t.TABLE_NAME LIKE '%tax%'
            OR t.TABLE_NAME LIKE '%fee%'
            
            -- Financial statements
            OR t.TABLE_NAME LIKE '%balance%'
            OR t.TABLE_NAME LIKE '%income%'
            OR t.TABLE_NAME LIKE '%profit%'
            OR t.TABLE_NAME LIKE '%loss%'
            OR t.TABLE_NAME LIKE '%PL%'
            OR t.TABLE_NAME LIKE '%BS%'
        )
        GROUP BY t.TABLE_NAME, t.TABLE_TYPE, p.rows
        ORDER BY t.TABLE_NAME
        """
        
        tables = db.execute_query(discovery_query)
        
        # Step 2: For each promising table, get detailed structure
        detailed_tables = []
        
        for table in tables:
            table_name = table['TABLE_NAME']
            
            # Get column information
            column_query = f"""
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = '{schema}'
            AND TABLE_NAME = '{table_name}'
            ORDER BY ORDINAL_POSITION
            """
            
            columns = db.execute_query(column_query)
            
            # Get sample data for tables with rows
            sample_data = []
            has_date_column = False
            date_columns = []
            
            row_count = table.get('ROW_COUNT') or 0
            if row_count > 0:
                # Check for date columns
                for col in columns:
                    if 'date' in col['COLUMN_NAME'].lower() or col['DATA_TYPE'] in ['datetime', 'date', 'datetime2']:
                        has_date_column = True
                        date_columns.append(col['COLUMN_NAME'])
                
                # Try to get recent sample data
                try:
                    if has_date_column and date_columns:
                        # Use the first date column found
                        date_col = date_columns[0]
                        sample_query = f"""
                        SELECT TOP 5 *
                        FROM {schema}.{table_name}
                        WHERE {date_col} >= '2025-01-01'
                        ORDER BY {date_col} DESC
                        """
                    else:
                        sample_query = f"""
                        SELECT TOP 5 *
                        FROM {schema}.{table_name}
                        """
                    
                    sample_data = db.execute_query(sample_query)
                except Exception as e:
                    logger.warning(f"Could not get sample data for {table_name}: {str(e)}")
            
            # Categorize the table
            category = categorize_table(table_name, columns)
            
            detailed_tables.append({
                'table_name': table_name,
                'row_count': table.get('ROW_COUNT') or 0,
                'category': category,
                'columns': [{
                    'name': col['COLUMN_NAME'],
                    'type': col['DATA_TYPE'],
                    'nullable': col['IS_NULLABLE'] == 'YES'
                } for col in columns],
                'has_date_column': has_date_column,
                'date_columns': date_columns,
                'sample_data': sample_data[:2] if sample_data else []  # Limit to 2 rows
            })
        
        # Step 3: Look for specific G&A expense patterns
        expense_analysis = analyze_expense_patterns(db, detailed_tables)
        
        # Step 4: Generate recommendations
        recommendations = generate_recommendations(detailed_tables, expense_analysis)
        
        return jsonify({
            'total_tables_found': len(tables),
            'tables': detailed_tables,
            'expense_analysis': expense_analysis,
            'recommendations': recommendations,
            'categories': {
                'general_ledger': [t for t in detailed_tables if t['category'] == 'general_ledger'],
                'accounts_payable': [t for t in detailed_tables if t['category'] == 'accounts_payable'],
                'payroll': [t for t in detailed_tables if t['category'] == 'payroll'],
                'vendor_management': [t for t in detailed_tables if t['category'] == 'vendor_management'],
                'expense_tracking': [t for t in detailed_tables if t['category'] == 'expense_tracking'],
                'financial_statements': [t for t in detailed_tables if t['category'] == 'financial_statements'],
                'other': [t for t in detailed_tables if t['category'] == 'other']
            }
        })
        
    except Exception as e:
        logger.error(f"Accounting table discovery failed: {str(e)}")
        return jsonify({
            'error': str(e),
            'type': 'accounting_discovery_error'
        }), 500

def categorize_table(table_name, columns):
    """Categorize a table based on its name and columns"""
    table_lower = table_name.lower()
    column_names = [col['COLUMN_NAME'].lower() for col in columns]
    
    # General Ledger
    if any(term in table_lower for term in ['gl', 'generalledger', 'ledger']):
        return 'general_ledger'
    
    # Accounts Payable
    if any(term in table_lower for term in ['ap', 'payable', 'accountspayable']):
        return 'accounts_payable'
    
    # Payroll
    if any(term in table_lower for term in ['payroll', 'salary', 'wage', 'compensation']):
        return 'payroll'
    
    # Vendor Management
    if any(term in table_lower for term in ['vendor', 'supplier']):
        return 'vendor_management'
    
    # Expense Tracking
    if 'expense' in table_lower:
        return 'expense_tracking'
    
    # Financial Statements
    if any(term in table_lower for term in ['balance', 'income', 'profit', 'loss', 'pl', 'bs']):
        return 'financial_statements'
    
    # Check column patterns
    if any('account' in col and 'code' in col for col in column_names):
        return 'general_ledger'
    
    if any('vendor' in col for col in column_names) and any('amount' in col for col in column_names):
        return 'accounts_payable'
    
    return 'other'

def analyze_expense_patterns(db, tables):
    """Analyze tables to find G&A expense patterns"""
    analysis = {
        'potential_expense_tables': [],
        'gl_account_structure': None,
        'vendor_invoice_tables': [],
        'payroll_tables': []
    }
    
    for table in tables:
        table_name = table['table_name']
        
        # Look for GL account structure
        if table['category'] == 'general_ledger' and table['row_count'] > 0:
            # Try to find account categories
            try:
                account_query = f"""
                SELECT TOP 20 *
                FROM {schema}.{table_name}
                WHERE 1=1
                """
                accounts = db.execute_query(account_query)
                if accounts:
                    analysis['gl_account_structure'] = {
                        'table': table_name,
                        'sample_accounts': accounts[:5]
                    }
            except:
                pass
        
        # Look for vendor invoice tables
        if table['category'] in ['accounts_payable', 'vendor_management'] and table['row_count'] > 0:
            analysis['vendor_invoice_tables'].append({
                'table': table_name,
                'row_count': table['row_count'],
                'has_amount_column': any('amount' in col['name'].lower() for col in table['columns']),
                'has_vendor_column': any('vendor' in col['name'].lower() for col in table['columns'])
            })
        
        # Look for payroll tables
        if table['category'] == 'payroll' and table['row_count'] > 0:
            analysis['payroll_tables'].append({
                'table': table_name,
                'row_count': table['row_count']
            })
    
    return analysis

def generate_recommendations(tables, analysis):
    """Generate recommendations for G&A expense queries"""
    recommendations = []
    
    # Check for GL tables
    gl_tables = [t for t in tables if t['category'] == 'general_ledger' and t['row_count'] > 0]
    if gl_tables:
        recommendations.append({
            'type': 'general_ledger',
            'message': f"Found {len(gl_tables)} GL table(s). Consider using these for G&A expense tracking.",
            'tables': [t['table_name'] for t in gl_tables],
            'query_hint': "Look for expense account codes (typically 5000-7000 range)"
        })
    
    # Check for AP tables
    ap_tables = [t for t in tables if t['category'] == 'accounts_payable' and t['row_count'] > 0]
    if ap_tables:
        recommendations.append({
            'type': 'accounts_payable',
            'message': f"Found {len(ap_tables)} AP table(s) for vendor invoices.",
            'tables': [t['table_name'] for t in ap_tables],
            'query_hint': "Filter by expense categories or vendor types"
        })
    
    # Check for direct expense tables
    expense_tables = [t for t in tables if t['category'] == 'expense_tracking' and t['row_count'] > 0]
    if expense_tables:
        recommendations.append({
            'type': 'expense_tracking',
            'message': f"Found {len(expense_tables)} direct expense tracking table(s).",
            'tables': [t['table_name'] for t in expense_tables],
            'query_hint': "These may contain categorized G&A expenses"
        })
    
    # If no suitable tables found
    if not (gl_tables or ap_tables or expense_tables):
        recommendations.append({
            'type': 'warning',
            'message': "No clear G&A expense tables found. Consider checking with database administrator.",
            'tables': [],
            'query_hint': "May need to join multiple tables or use different schema"
        })
    
    return recommendations

# Register blueprint
def register_routes(app):
    app.register_blueprint(accounting_diagnostics_bp)