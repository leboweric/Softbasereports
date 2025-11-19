"""
Diagnostic endpoint to investigate account 602600 payroll discrepancy
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
        
        # 1. Get all transactions for account 602600 with Posted=1
        query_posted = """
        SELECT 
            TransactionNo,
            Date,
            EffectiveDate,
            AccountNo,
            Amount,
            Posted,
            Description
        FROM GLDetail
        WHERE AccountNo = '602600'
          AND EffectiveDate BETWEEN %s AND %s
          AND Posted = 1
        ORDER BY EffectiveDate, TransactionNo
        """
        
        posted_transactions = sql_service.execute_query(query_posted, [start_date, end_date])
        results['posted_transactions'] = posted_transactions
        results['posted_count'] = len(posted_transactions) if posted_transactions else 0
        results['posted_total'] = sum(float(t['Amount'] or 0) for t in posted_transactions) if posted_transactions else 0
        
        # 2. Get all transactions for account 602600 WITHOUT Posted filter
        query_all = """
        SELECT 
            TransactionNo,
            Date,
            EffectiveDate,
            AccountNo,
            Amount,
            Posted,
            Description
        FROM GLDetail
        WHERE AccountNo = '602600'
          AND EffectiveDate BETWEEN %s AND %s
        ORDER BY EffectiveDate, TransactionNo
        """
        
        all_transactions = sql_service.execute_query(query_all, [start_date, end_date])
        results['all_transactions'] = all_transactions
        results['all_count'] = len(all_transactions) if all_transactions else 0
        results['all_total'] = sum(float(t['Amount'] or 0) for t in all_transactions) if all_transactions else 0
        
        # 3. Check if using Date instead of EffectiveDate makes a difference
        query_by_date = """
        SELECT 
            TransactionNo,
            Date,
            EffectiveDate,
            AccountNo,
            Amount,
            Posted,
            Description
        FROM GLDetail
        WHERE AccountNo = '602600'
          AND Date BETWEEN %s AND %s
          AND Posted = 1
        ORDER BY Date, TransactionNo
        """
        
        date_transactions = sql_service.execute_query(query_by_date, [start_date, end_date])
        results['date_field_transactions'] = date_transactions
        results['date_field_count'] = len(date_transactions) if date_transactions else 0
        results['date_field_total'] = sum(float(t['Amount'] or 0) for t in date_transactions) if date_transactions else 0
        
        # 4. Check for other GL tables
        query_tables = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME LIKE '%GL%'
        ORDER BY TABLE_NAME
        """
        
        gl_tables = sql_service.execute_query(query_tables, [])
        results['gl_tables'] = [t['TABLE_NAME'] for t in gl_tables] if gl_tables else []
        
        # 5. Summary
        results['summary'] = {
            'target_from_softbase': 251631.06,
            'current_query_result': 248268.56,
            'discrepancy': 3362.50,
            'posted_vs_all_difference': results['all_total'] - results['posted_total'],
            'effectivedate_vs_date_difference': results['date_field_total'] - results['posted_total']
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
