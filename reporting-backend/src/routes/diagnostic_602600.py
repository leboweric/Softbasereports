"""
Diagnostic endpoint to investigate account 602600 payroll discrepancy
Hypothesis: Softbase uses GL.MTD (monthly summary) instead of GLDetail transactions
"""
from flask import Blueprint, jsonify, request
from src.services.azure_sql_service import AzureSQLService

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

def get_tenant_schema():
    """Get the database schema for the current user's organization"""
    try:
        user_id = get_jwt_identity()
        if user_id:
            user = User.query.get(int(user_id))
            if user and user.organization and user.organization.database_schema:
                return user.organization.database_schema
        return 'ben002'  # Fallback
    except:
        return 'ben002'



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
        FROM {schema}.GLDetail
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
        FROM {schema}.GL
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
