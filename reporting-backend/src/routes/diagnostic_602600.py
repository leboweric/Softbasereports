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
        
        # 1. Get total for account 602600 with Posted=1 (what we currently use)
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
        results['posted_total'] = float(posted_result[0]['total'] or 0) if posted_result else 0
        results['posted_count'] = int(posted_result[0]['count'] or 0) if posted_result else 0
        
        # 2. Get total for account 602600 WITHOUT Posted filter
        query_all = """
        SELECT 
            SUM(Amount) as total,
            COUNT(*) as count
        FROM ben002.GLDetail
        WHERE AccountNo = '602600'
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
        """
        
        all_result = sql_service.execute_query(query_all, [start_date, end_date])
        results['all_total'] = float(all_result[0]['total'] or 0) if all_result else 0
        results['all_count'] = int(all_result[0]['count'] or 0) if all_result else 0
        
        # 3. Check for unposted transactions
        query_unposted = """
        SELECT 
            SUM(Amount) as total,
            COUNT(*) as count
        FROM ben002.GLDetail
        WHERE AccountNo = '602600'
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 0
        """
        
        unposted_result = sql_service.execute_query(query_unposted, [start_date, end_date])
        results['unposted_total'] = float(unposted_result[0]['total'] or 0) if unposted_result else 0
        results['unposted_count'] = int(unposted_result[0]['count'] or 0) if unposted_result else 0
        
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
            'current_query_result': results['posted_total'],
            'discrepancy': 251631.06 - results['posted_total'],
            'posted_vs_all_difference': results['all_total'] - results['posted_total'],
            'unposted_amount': results['unposted_total']
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
