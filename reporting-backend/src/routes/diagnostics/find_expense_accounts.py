from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

find_expense_accounts_bp = Blueprint('find_expense_accounts', __name__)

@find_expense_accounts_bp.route('/api/diagnostics/find-expense-accounts', methods=['GET'])
@jwt_required()
def find_expense_accounts():
    """Search ALL tables for any column containing values starting with 6"""
    try:
        db = AzureSQLService()
        results = {
            'tables_with_6_accounts': [],
            'gl_table_check': {},
            'all_numeric_columns': []
        }
        
        # First, let's check GL tables specifically (even if they show 0 rows)
        gl_check_query = """
        -- Check GL table
        SELECT 'GL' as table_name, COUNT(*) as row_count,
               (SELECT COUNT(*) FROM ben002.GL WHERE AccountNo LIKE '6%') as accounts_starting_with_6
        FROM ben002.GL
        UNION ALL
        -- Check GLDetail table  
        SELECT 'GLDetail' as table_name, COUNT(*) as row_count,
               (SELECT COUNT(*) FROM ben002.GLDetail WHERE AccountNo LIKE '6%') as accounts_starting_with_6
        FROM ben002.GLDetail
        UNION ALL
        -- Check ChartOfAccounts table
        SELECT 'ChartOfAccounts' as table_name, COUNT(*) as row_count,
               (SELECT COUNT(*) FROM ben002.ChartOfAccounts WHERE AccountNo LIKE '6%') as accounts_starting_with_6
        FROM ben002.ChartOfAccounts
        """
        
        try:
            gl_results = db.execute_query(gl_check_query)
            for row in gl_results:
                results['gl_table_check'][row['table_name']] = {
                    'total_rows': row['row_count'],
                    'accounts_with_6': row['accounts_starting_with_6']
                }
        except Exception as e:
            results['gl_table_check']['error'] = str(e)
        
        # Get all tables and their string/numeric columns
        column_search_query = """
        SELECT 
            t.TABLE_NAME,
            c.COLUMN_NAME,
            c.DATA_TYPE,
            t.TABLE_TYPE
        FROM INFORMATION_SCHEMA.TABLES t
        INNER JOIN INFORMATION_SCHEMA.COLUMNS c 
            ON t.TABLE_SCHEMA = c.TABLE_SCHEMA 
            AND t.TABLE_NAME = c.TABLE_NAME
        WHERE t.TABLE_SCHEMA = 'ben002'
        AND t.TABLE_TYPE = 'BASE TABLE'
        AND (
            c.DATA_TYPE IN ('varchar', 'nvarchar', 'char', 'nchar', 'text')
            OR (c.DATA_TYPE IN ('int', 'smallint', 'bigint', 'decimal', 'numeric', 'money', 'float') 
                AND c.COLUMN_NAME LIKE '%account%' 
                OR c.COLUMN_NAME LIKE '%acct%'
                OR c.COLUMN_NAME LIKE '%code%'
                OR c.COLUMN_NAME LIKE '%dept%'
                OR c.COLUMN_NAME LIKE '%gl%')
        )
        ORDER BY t.TABLE_NAME, c.COLUMN_NAME
        """
        
        columns_to_check = db.execute_query(column_search_query)
        
        # Group by table
        tables_to_check = {}
        for col in columns_to_check:
            table = col['TABLE_NAME']
            if table not in tables_to_check:
                tables_to_check[table] = []
            tables_to_check[table].append({
                'column': col['COLUMN_NAME'],
                'type': col['DATA_TYPE']
            })
        
        # Check each table/column for values starting with 6
        for table, columns in tables_to_check.items():
            for col_info in columns:
                column = col_info['column']
                dtype = col_info['type']
                
                try:
                    if dtype in ['varchar', 'nvarchar', 'char', 'nchar', 'text']:
                        check_query = f"""
                        SELECT TOP 1 1 as found
                        FROM ben002.{table}
                        WHERE {column} LIKE '6%'
                        """
                    else:
                        # For numeric columns, cast to string
                        check_query = f"""
                        SELECT TOP 1 1 as found
                        FROM ben002.{table}
                        WHERE CAST({column} AS VARCHAR) LIKE '6%'
                        """
                    
                    result = db.execute_query(check_query)
                    if result and len(result) > 0:
                        # Found values starting with 6! Get more details
                        detail_query = f"""
                        SELECT TOP 10 
                            {column} as account_value,
                            COUNT(*) OVER() as total_count
                        FROM ben002.{table}
                        WHERE {column} LIKE '6%' OR CAST({column} AS VARCHAR) LIKE '6%'
                        """
                        
                        details = db.execute_query(detail_query)
                        
                        results['tables_with_6_accounts'].append({
                            'table': table,
                            'column': column,
                            'data_type': dtype,
                            'sample_values': [d['account_value'] for d in details[:5]],
                            'total_matching_rows': details[0]['total_count'] if details else 0
                        })
                        
                except Exception as e:
                    # Skip columns that cause errors
                    pass
        
        # Also check for any transaction-like tables we might have missed
        transaction_tables_query = """
        SELECT DISTINCT TABLE_NAME
        FROM INFORMATION_SCHEMA.TABLES
        WHERE TABLE_SCHEMA = 'ben002'
        AND (
            TABLE_NAME LIKE '%trans%'
            OR TABLE_NAME LIKE '%journal%'
            OR TABLE_NAME LIKE '%entry%'
            OR TABLE_NAME LIKE '%ledger%'
            OR TABLE_NAME LIKE '%account%'
            OR TABLE_NAME LIKE '%expense%'
            OR TABLE_NAME LIKE '%payment%'
            OR TABLE_NAME LIKE '%voucher%'
        )
        """
        
        transaction_tables = db.execute_query(transaction_tables_query)
        results['potential_transaction_tables'] = [t['TABLE_NAME'] for t in transaction_tables]
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Search failed: {str(e)}'
        }), 500