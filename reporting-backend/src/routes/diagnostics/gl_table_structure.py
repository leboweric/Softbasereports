from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

gl_table_structure_bp = Blueprint('gl_table_structure', __name__)

@gl_table_structure_bp.route('/api/diagnostics/gl-structure', methods=['GET'])
@jwt_required()
def get_gl_structure():
    """Get the structure of GL tables to understand how to query them"""
    try:
        db = AzureSQLService()
        
        # Get columns for GL tables
        query = """
        SELECT 
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_NAME IN ('GL', 'GLDetail', 'ChartOfAccounts')
        ORDER BY TABLE_NAME, ORDINAL_POSITION
        """
        
        columns = db.execute_query(query)
        
        # Get sample expense records from GLDetail
        sample_query = """
        SELECT TOP 5
            *
        FROM ben002.GLDetail
        WHERE AccountNo LIKE '6%'
        ORDER BY EffectiveDate DESC
        """
        
        try:
            samples = db.execute_query(sample_query)
        except:
            samples = []
        
        # Get account names from ChartOfAccounts
        accounts_query = """
        SELECT TOP 10
            AccountNo,
            AccountDescription
        FROM ben002.ChartOfAccounts
        WHERE AccountNo LIKE '6%'
        ORDER BY AccountNo
        """
        
        try:
            accounts = db.execute_query(accounts_query)
        except:
            accounts = []
        
        # Group columns by table
        tables = {}
        for col in columns:
            table = col['TABLE_NAME']
            if table not in tables:
                tables[table] = []
            tables[table].append({
                'column': col['COLUMN_NAME'],
                'type': col['DATA_TYPE']
            })
        
        return jsonify({
            'tables': tables,
            'sample_records': samples,
            'expense_accounts': accounts
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to get GL structure: {str(e)}'
        }), 500