from flask import Blueprint, jsonify
from src.utils.tenant_utils import get_tenant_db
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService

analyze_gl_accounts_bp = Blueprint('analyze_gl_accounts', __name__)

@analyze_gl_accounts_bp.route('/api/diagnostics/analyze-gl-accounts', methods=['GET'])
@jwt_required()
def analyze_gl_accounts():
    """Analyze GL accounts starting with 6 to understand what expense data we have"""
    try:
        db = get_tenant_db()
        results = {}
        
        # 1. Get all unique expense accounts (6xxxxx) with descriptions from ChartOfAccounts
        chart_accounts_query = """
        SELECT 
            AccountNo,
            AccountDescription,
            AccountType
        FROM ben002.ChartOfAccounts
        WHERE AccountNo LIKE '6%'
        ORDER BY AccountNo
        """
        
        results['chart_of_accounts'] = db.execute_query(chart_accounts_query)
        
        # 2. Get summary of GLDetail transactions by account
        gl_summary_query = """
        SELECT 
            gld.AccountNo,
            coa.AccountDescription,
            COUNT(*) as transaction_count,
            MIN(gld.EffectiveDate) as first_transaction,
            MAX(gld.EffectiveDate) as last_transaction,
            SUM(gld.Amount) as total_amount,
            AVG(gld.Amount) as avg_amount
        FROM ben002.GLDetail gld
        LEFT JOIN ben002.ChartOfAccounts coa ON gld.AccountNo = coa.AccountNo
        WHERE gld.AccountNo LIKE '6%'
        GROUP BY gld.AccountNo, coa.AccountDescription
        ORDER BY gld.AccountNo
        """
        
        results['gl_summary'] = db.execute_query(gl_summary_query)
        
        # 3. Get recent sample transactions to see what the data looks like
        sample_transactions_query = """
        SELECT TOP 20
            gld.AccountNo,
            coa.AccountDescription,
            gld.EffectiveDate,
            gld.Amount,
            gld.TransactionType,
            gld.Description as TransactionDescription,
            gld.Reference
        FROM ben002.GLDetail gld
        LEFT JOIN ben002.ChartOfAccounts coa ON gld.AccountNo = coa.AccountNo
        WHERE gld.AccountNo LIKE '6%'
        ORDER BY gld.EffectiveDate DESC
        """
        
        results['sample_transactions'] = db.execute_query(sample_transactions_query)
        
        # 4. Check what columns GLDetail actually has
        columns_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'ben002'
        AND TABLE_NAME = 'GLDetail'
        ORDER BY ORDINAL_POSITION
        """
        
        results['gldetail_columns'] = db.execute_query(columns_query)
        
        # 5. Monthly totals for 2025 to see if we have recent data
        monthly_2025_query = """
        SELECT 
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            COUNT(*) as transaction_count,
            SUM(Amount) as total_expenses
        FROM ben002.GLDetail
        WHERE AccountNo LIKE '6%'
        AND EffectiveDate >= '2025-01-01'
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY year, month
        """
        
        results['monthly_2025'] = db.execute_query(monthly_2025_query)
        
        # 6. Check if GL table has current balances
        gl_balances_query = """
        SELECT TOP 10
            gl.AccountNo,
            coa.AccountDescription,
            gl.CurrentBalance,
            gl.LastTransDate,
            gl.LastTransAmount
        FROM ben002.GL gl
        LEFT JOIN ben002.ChartOfAccounts coa ON gl.AccountNo = coa.AccountNo
        WHERE gl.AccountNo LIKE '6%'
        ORDER BY gl.AccountNo
        """
        
        try:
            results['gl_balances'] = db.execute_query(gl_balances_query)
        except:
            # GL table might have different column names
            results['gl_balances'] = []
        
        return jsonify(results), 200
        
    except Exception as e:
        return jsonify({
            'error': f'Failed to analyze GL accounts: {str(e)}'
        }), 500