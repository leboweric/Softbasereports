"""
Diagnostic endpoint to investigate account 602600 payroll discrepancy
Uses only confirmed columns: AccountNo, Amount, EffectiveDate, Posted
"""
from flask import Blueprint, jsonify, request
from src.services.azure_sql_service import AzureSQLService

diagnostic_bp = Blueprint('diagnostic', __name__)
sql_service = AzureSQLService()

@diagnostic_bp.route('/diagnostic/account-602600', methods=['GET'])
def diagnose_account_602600():
    """
    Investigate account 602600 to find the source of the $3,362.50 discrepancy
    """
    try:
        start_date = request.args.get('start_date', '2025-10-01')
        end_date = request.args.get('end_date', '2025-10-31')
        
        results = {}
        
        # 1. Get total for account 602600 from GLDetail with Posted=1 (what we currently use)
        query_posted = """
        SELECT 
            SUM(Amount) as total,
            COUNT(*) as count
        FROM ben002.GLDetail
        WHERE AccountNo = '602600'
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 1
        """
        
        posted_result = sql_service.execute_query(query_posted, [start_date, end_date])
        results['gldetail_posted_total'] = float(posted_result[0]['total'] or 0) if posted_result else 0
        results['gldetail_posted_count'] = int(posted_result[0]['count'] or 0) if posted_result else 0
        
        # 2. Get total for account 602600 from GL table (main GL table)
        # First, let's check what columns exist in GL table
        query_gl_columns = """
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
          AND TABLE_NAME = 'GL'
        ORDER BY ORDINAL_POSITION
        """
        
        gl_columns = sql_service.execute_query(query_gl_columns, [])
        results['gl_table_columns'] = [{'name': c['COLUMN_NAME'], 'type': c['DATA_TYPE']} for c in gl_columns] if gl_columns else []
        
        # 3. Try to query GL table (we'll use common column names)
        try:
            query_gl = """
            SELECT TOP 5 *
            FROM ben002.GL
            WHERE AccountNo = '602600'
            """
            gl_sample = sql_service.execute_query(query_gl, [])
            results['gl_table_sample'] = gl_sample if gl_sample else []
        except Exception as e:
            results['gl_table_error'] = str(e)
        
        # 4. Check for other GL tables
        query_tables = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = 'ben002'
          AND TABLE_NAME LIKE '%GL%'
        ORDER BY TABLE_NAME
        """
        
        gl_tables = sql_service.execute_query(query_tables, [])
        results['gl_tables'] = [t['TABLE_NAME'] for t in gl_tables] if gl_tables else []
        
        # 5. Summary
        results['summary'] = {
            'target_from_softbase': 251631.06,
            'gldetail_result': results['gldetail_posted_total'],
            'discrepancy': 251631.06 - results['gldetail_posted_total']
        }
        
        return jsonify({
            'success': True,
            'account': '602600',
            'period': f'{start_date} to {end_date}',
            'results': results
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
