"""
Diagnostic endpoint to investigate account 602600 payroll discrepancy
Hypothesis: Softbase uses GL.MTD (monthly summary) instead of GLDetail transactions
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
        
        # 1. Get total for account 602600 from GLDetail (what we currently use)
        query_gldetail = """
        SELECT 
            SUM(Amount) as total,
            COUNT(*) as count
        FROM ben002.GLDetail
        WHERE AccountNo = '602600'
          AND EffectiveDate >= %s
          AND EffectiveDate <= %s
          AND Posted = 1
        """
        
        gldetail_result = sql_service.execute_query(query_gldetail, [start_date, end_date])
        results['gldetail_total'] = float(gldetail_result[0]['total'] or 0) if gldetail_result else 0
        results['gldetail_count'] = int(gldetail_result[0]['count'] or 0) if gldetail_result else 0
        
        # 2. Get MTD from GL table for October 2025 (what Softbase likely uses!)
        query_gl_mtd = """
        SELECT 
            AccountNo,
            Year,
            Month,
            MTD,
            YTD,
            NumberOfTrans,
            LastEffectiveDate
        FROM ben002.GL
        WHERE AccountNo = '602600'
          AND Year = 2025
          AND Month = 10
        """
        
        gl_mtd_result = sql_service.execute_query(query_gl_mtd, [])
        if gl_mtd_result and len(gl_mtd_result) > 0:
            results['gl_mtd_total'] = float(gl_mtd_result[0]['MTD'] or 0)
            results['gl_mtd_record'] = gl_mtd_result[0]
        else:
            results['gl_mtd_total'] = 0
            results['gl_mtd_record'] = None
        
        # 3. Summary
        target = 251631.06
        results['summary'] = {
            'target_from_softbase': target,
            'gldetail_sum': results['gldetail_total'],
            'gl_mtd_value': results.get('gl_mtd_total', 0),
            'gldetail_vs_target': target - results['gldetail_total'],
            'gl_mtd_vs_target': target - results.get('gl_mtd_total', 0),
            'conclusion': 'GL.MTD matches!' if abs(target - results.get('gl_mtd_total', 0)) < 1 else 'Still investigating...'
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
