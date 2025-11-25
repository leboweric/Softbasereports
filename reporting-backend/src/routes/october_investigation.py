"""
October 2025 Investigation API
Analyzes October P&L anomaly - $2M revenue with only $58K profit
Version: 1.0.0
"""

from flask import Blueprint, jsonify
from src.services.azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

october_investigation_bp = Blueprint('october_investigation', __name__)
sql_service = AzureSQLService()

@october_investigation_bp.route('/api/investigation/october2025', methods=['GET'])
def investigate_october_2025():
    """Detailed investigation of October 2025 P&L"""
    try:
        results = {}
        
        # 1. Overall P&L Summary
        query1 = """
        SELECT 
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) as Revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) as COGS,
            SUM(CASE WHEN AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%' THEN Amount ELSE 0 END) as Expenses,
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) - 
             SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) as GrossProfit,
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) - 
             SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) -
             SUM(CASE WHEN AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%' THEN Amount ELSE 0 END) as OperatingProfit
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-10-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
        """
        results['pl_summary'] = sql_service.execute_query(query1)[0] if sql_service.execute_query(query1) else {}
        
        # 2. Top 20 COGS Accounts
        query2 = """
        SELECT TOP 20
            AccountNo,
            SUM(Amount) as Amount,
            COUNT(*) as TransactionCount,
            SUM(ABS(Amount)) as TotalVolume
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-10-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
          AND AccountNo LIKE '5%'
        GROUP BY AccountNo
        ORDER BY SUM(Amount) DESC
        """
        results['top_cogs_accounts'] = sql_service.execute_query(query2)
        
        # 3. Top 20 Expense Accounts
        query3 = """
        SELECT TOP 20
            AccountNo,
            SUM(Amount) as Amount,
            COUNT(*) as TransactionCount,
            SUM(ABS(Amount)) as TotalVolume
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-10-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
          AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
        GROUP BY AccountNo
        ORDER BY SUM(Amount) DESC
        """
        results['top_expense_accounts'] = sql_service.execute_query(query3)
        
        # 4. Large Transactions (>$50K)
        query4 = """
        SELECT 
            EffectiveDate,
            AccountNo,
            Amount,
            Posted
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-10-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
          AND ABS(Amount) > 50000
        ORDER BY ABS(Amount) DESC
        """
        results['large_transactions'] = sql_service.execute_query(query4)
        
        # 5. Offsetting Pairs
        query5 = """
        SELECT 
            t1.AccountNo,
            t1.EffectiveDate,
            t1.Amount as DebitAmount,
            t2.Amount as CreditAmount,
            ABS(t1.Amount + t2.Amount) as NetDifference
        FROM ben002.GLDetail t1
        JOIN ben002.GLDetail t2 
            ON t1.AccountNo = t2.AccountNo
            AND t1.EffectiveDate = t2.EffectiveDate
            AND ABS(t1.Amount + t2.Amount) < 1000
            AND t1.Amount > 0
            AND t2.Amount < 0
        WHERE t1.EffectiveDate >= '2025-10-01' 
          AND t1.EffectiveDate < '2025-11-01'
          AND t1.Posted = 1
          AND ABS(t1.Amount) > 50000
        ORDER BY ABS(t1.Amount) DESC
        """
        results['offsetting_pairs'] = sql_service.execute_query(query5)
        
        # 6. Transaction Summary
        query6 = """
        SELECT 
            COUNT(*) as TransactionCount,
            COUNT(DISTINCT AccountNo) as UniqueAccounts,
            SUM(CASE WHEN Amount > 0 THEN 1 ELSE 0 END) as DebitCount,
            SUM(CASE WHEN Amount < 0 THEN 1 ELSE 0 END) as CreditCount,
            SUM(ABS(Amount)) as TotalVolume
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-10-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
        """
        results['transaction_summary'] = sql_service.execute_query(query6)[0] if sql_service.execute_query(query6) else {}
        
        # 7. Daily Transaction Pattern
        query7 = """
        SELECT 
            DAY(EffectiveDate) as Day,
            COUNT(*) as Transactions,
            SUM(ABS(Amount)) as Volume
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-10-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
        GROUP BY DAY(EffectiveDate)
        ORDER BY DAY(EffectiveDate)
        """
        results['daily_pattern'] = sql_service.execute_query(query7)
        
        # 8. Compare to September 2025
        query8 = """
        SELECT 
            MONTH(EffectiveDate) as Month,
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) as Revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) as COGS,
            SUM(CASE WHEN AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%' THEN Amount ELSE 0 END) as Expenses,
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) - 
             SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) -
             SUM(CASE WHEN AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%' THEN Amount ELSE 0 END) as OperatingProfit
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-09-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
        GROUP BY MONTH(EffectiveDate)
        ORDER BY MONTH(EffectiveDate)
        """
        results['sep_oct_comparison'] = sql_service.execute_query(query8)
        
        # 9. Account 602600 (Salaries) Check
        query9 = """
        SELECT 
            COUNT(*) as TransactionCount,
            SUM(Amount) as NetAmount,
            MIN(Amount) as MinAmount,
            MAX(Amount) as MaxAmount,
            SUM(ABS(Amount)) as TotalVolume
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-10-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
          AND AccountNo = '602600'
        """
        results['account_602600'] = sql_service.execute_query(query9)[0] if sql_service.execute_query(query9) else {}
        
        # 10. Negative Expense Accounts
        query10 = """
        SELECT 
            AccountNo,
            SUM(Amount) as NetAmount,
            COUNT(*) as TransactionCount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-10-01' 
          AND EffectiveDate < '2025-11-01'
          AND Posted = 1
          AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
        GROUP BY AccountNo
        HAVING SUM(Amount) < 0
        ORDER BY SUM(Amount)
        """
        results['negative_expenses'] = sql_service.execute_query(query10)
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error investigating October 2025: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
