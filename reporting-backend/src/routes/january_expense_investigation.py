"""
January 2025 Expense Investigation API
Focused analysis on the $563k expense anomaly vs ~$300k normal months
"""

from flask import Blueprint, jsonify
from src.services.azure_sql_service import AzureSQLService
import logging

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



logger = logging.getLogger(__name__)

january_expense_bp = Blueprint('january_expense_investigation', __name__)
sql_service = AzureSQLService()
schema = get_tenant_schema()
@january_expense_bp.route('/api/investigation/january2025/expenses', methods=['GET'])
def investigate_january_expenses():
    """
    Deep dive into January 2025 expenses to find the ~$250k anomaly
    """
    try:
        results = {}

        # Compare expense accounts month-by-month (Dec, Jan, Feb)
        query1 = """
        SELECT
            AccountNo,
            SUM(CASE WHEN MONTH(EffectiveDate) = 12 AND YEAR(EffectiveDate) = 2024 THEN Amount ELSE 0 END) as Dec2024,
            SUM(CASE WHEN MONTH(EffectiveDate) = 1 AND YEAR(EffectiveDate) = 2025 THEN Amount ELSE 0 END) as Jan2025,
            SUM(CASE WHEN MONTH(EffectiveDate) = 2 AND YEAR(EffectiveDate) = 2025 THEN Amount ELSE 0 END) as Feb2025
        FROM {schema}.GLDetail
        WHERE EffectiveDate >= '2024-12-01' AND EffectiveDate < '2025-03-01'
          AND Posted = 1
          AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
        GROUP BY AccountNo
        HAVING ABS(SUM(CASE WHEN MONTH(EffectiveDate) = 1 AND YEAR(EffectiveDate) = 2025 THEN Amount ELSE 0 END)) > 1000
        ORDER BY SUM(CASE WHEN MONTH(EffectiveDate) = 1 AND YEAR(EffectiveDate) = 2025 THEN Amount ELSE 0 END) DESC
        """
        results['expense_comparison'] = sql_service.execute_query(query1)

        # Find accounts with unusual January activity (>2x normal)
        query2 = """
        WITH MonthlyExpenses AS (
            SELECT
                AccountNo,
                SUM(CASE WHEN MONTH(EffectiveDate) = 12 AND YEAR(EffectiveDate) = 2024 THEN Amount ELSE 0 END) as Dec2024,
                SUM(CASE WHEN MONTH(EffectiveDate) = 1 AND YEAR(EffectiveDate) = 2025 THEN Amount ELSE 0 END) as Jan2025,
                SUM(CASE WHEN MONTH(EffectiveDate) = 2 AND YEAR(EffectiveDate) = 2025 THEN Amount ELSE 0 END) as Feb2025
            FROM {schema}.GLDetail
            WHERE EffectiveDate >= '2024-12-01' AND EffectiveDate < '2025-03-01'
              AND Posted = 1
              AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
            GROUP BY AccountNo
        )
        SELECT
            AccountNo,
            Dec2024,
            Jan2025,
            Feb2025,
            Jan2025 - ((Dec2024 + Feb2025) / 2) as JanVariance
        FROM MonthlyExpenses
        WHERE Jan2025 > (Dec2024 + Feb2025) / 2 * 1.5  -- Jan is 50%+ higher than average of Dec/Feb
          AND Jan2025 > 5000  -- Minimum threshold
        ORDER BY Jan2025 - ((Dec2024 + Feb2025) / 2) DESC
        """
        results['anomalous_accounts'] = sql_service.execute_query(query2)

        # Get account names for context
        query3 = """
        SELECT DISTINCT
            gl.AccountNo,
            a.Name as AccountName
        FROM {schema}.GLDetail gl
        LEFT JOIN {schema}.Accounts a ON gl.AccountNo = a.AccountNo
        WHERE gl.EffectiveDate >= '2025-01-01' AND gl.EffectiveDate < '2025-02-01'
          AND gl.Posted = 1
          AND (gl.AccountNo LIKE '6%' OR gl.AccountNo LIKE '7%' OR gl.AccountNo LIKE '8%')
        """
        account_names_raw = sql_service.execute_query(query3)
        results['account_names'] = {row['AccountNo']: row['AccountName'] for row in account_names_raw if row['AccountName']}

        # Look at January entries for accounts 602xxx (seems to have big numbers)
        query4 = """
        SELECT TOP 30
            gl.EffectiveDate,
            gl.AccountNo,
            a.Name as AccountName,
            gl.Amount,
            gl.Posted
        FROM {schema}.GLDetail gl
        LEFT JOIN {schema}.Accounts a ON gl.AccountNo = a.AccountNo
        WHERE gl.EffectiveDate >= '2025-01-01' AND gl.EffectiveDate < '2025-02-01'
          AND gl.Posted = 1
          AND gl.AccountNo LIKE '602%'
          AND ABS(gl.Amount) > 10000
        ORDER BY ABS(gl.Amount) DESC
        """
        results['large_602_entries'] = sql_service.execute_query(query4)

        # Total expenses by month for summary
        query5 = """
        SELECT
            YEAR(EffectiveDate) as Year,
            MONTH(EffectiveDate) as Month,
            SUM(Amount) as TotalExpenses
        FROM {schema}.GLDetail
        WHERE EffectiveDate >= '2024-11-01' AND EffectiveDate < '2025-04-01'
          AND Posted = 1
          AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY Year, Month
        """
        results['monthly_expense_totals'] = sql_service.execute_query(query5)

        return jsonify({
            'success': True,
            'data': results
        })

    except Exception as e:
        logger.error(f"Error in January expense investigation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
