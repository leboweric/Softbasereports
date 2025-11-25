"""
January 2025 P&L Investigation API
Analyzes potential data migration issues from Minitrac to Softbase
"""

from flask import Blueprint, jsonify
from src.services.azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

january_investigation_bp = Blueprint('january_investigation', __name__)
sql_service = AzureSQLService()

@january_investigation_bp.route('/api/investigation/january2025', methods=['GET'])
def investigate_january_2025():
    """
    Comprehensive investigation of January 2025 P&L anomaly
    Returns multiple analyses to identify data migration issues
    """
    try:
        results = {}
        
        # ============================================================================
        # ANALYSIS 1: Monthly Transaction Counts (Nov 2024 - Apr 2025)
        # ============================================================================
        query1 = """
        SELECT 
            YEAR(EffectiveDate) as Year,
            MONTH(EffectiveDate) as Month,
            COUNT(*) as TransactionCount,
            COUNT(DISTINCT AccountNo) as UniqueAccounts,
            SUM(CASE WHEN Amount > 0 THEN 1 ELSE 0 END) as DebitCount,
            SUM(CASE WHEN Amount < 0 THEN 1 ELSE 0 END) as CreditCount,
            SUM(ABS(Amount)) as TotalVolume
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2024-11-01' AND EffectiveDate < '2025-05-01'
          AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY Year, Month
        """
        results['transaction_volume'] = sql_service.execute_query(query1)
        
        # Calculate statistics
        if results['transaction_volume']:
            counts = [row['TransactionCount'] for row in results['transaction_volume']]
            avg_count = sum(counts) / len(counts)
            jan_data = [row for row in results['transaction_volume'] if row['Month'] == 1]
            jan_count = jan_data[0]['TransactionCount'] if jan_data else 0
            results['transaction_stats'] = {
                'average': avg_count,
                'january': jan_count,
                'variance_pct': ((jan_count - avg_count) / avg_count * 100) if avg_count > 0 else 0
            }
        
        # ============================================================================
        # ANALYSIS 2: Large Transactions in January 2025 (> $50K)
        # ============================================================================
        query2 = """
        SELECT TOP 50
            EffectiveDate,
            AccountNo,
            Amount,
            Description,
            Reference,
            Posted
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-01-01' AND EffectiveDate < '2025-02-01'
          AND ABS(Amount) > 50000
          AND Posted = 1
        ORDER BY ABS(Amount) DESC
        """
        results['large_transactions'] = sql_service.execute_query(query2)
        
        # ============================================================================
        # ANALYSIS 3: Account-Level Summary for January 2025
        # ============================================================================
        query3 = """
        SELECT TOP 30
            AccountNo,
            COUNT(*) as TransactionCount,
            SUM(Amount) as NetAmount,
            SUM(ABS(Amount)) as TotalVolume,
            MIN(Amount) as MinAmount,
            MAX(Amount) as MaxAmount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-01-01' AND EffectiveDate < '2025-02-01'
          AND Posted = 1
        GROUP BY AccountNo
        ORDER BY SUM(ABS(Amount)) DESC
        """
        results['account_summary'] = sql_service.execute_query(query3)
        
        # ============================================================================
        # ANALYSIS 4: Duplicate Transaction Detection
        # ============================================================================
        query4 = """
        SELECT TOP 50
            EffectiveDate,
            AccountNo,
            Amount,
            Description,
            COUNT(*) as DuplicateCount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-01-01' AND EffectiveDate < '2025-02-01'
          AND Posted = 1
        GROUP BY EffectiveDate, AccountNo, Amount, Description
        HAVING COUNT(*) > 1
        ORDER BY COUNT(*) DESC, ABS(Amount) DESC
        """
        results['potential_duplicates'] = sql_service.execute_query(query4)
        
        # ============================================================================
        # ANALYSIS 5: P&L Breakdown for January 2025
        # ============================================================================
        
        # Revenue accounts (4xxxxx)
        query5a = """
        SELECT 
            AccountNo,
            -SUM(Amount) as Amount,
            COUNT(*) as TransactionCount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-01-01' AND EffectiveDate < '2025-02-01'
          AND Posted = 1
          AND AccountNo LIKE '4%'
        GROUP BY AccountNo
        ORDER BY -SUM(Amount) DESC
        """
        
        # COGS accounts (5xxxxx)
        query5b = """
        SELECT 
            AccountNo,
            SUM(Amount) as Amount,
            COUNT(*) as TransactionCount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-01-01' AND EffectiveDate < '2025-02-01'
          AND Posted = 1
          AND AccountNo LIKE '5%'
        GROUP BY AccountNo
        ORDER BY SUM(Amount) DESC
        """
        
        # Expense accounts (6xxxxx, 7xxxxx, 8xxxxx)
        query5c = """
        SELECT 
            AccountNo,
            SUM(Amount) as Amount,
            COUNT(*) as TransactionCount
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-01-01' AND EffectiveDate < '2025-02-01'
          AND Posted = 1
          AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
        GROUP BY AccountNo
        ORDER BY SUM(Amount) DESC
        """
        
        revenue_data = sql_service.execute_query(query5a)
        cogs_data = sql_service.execute_query(query5b)
        expense_data = sql_service.execute_query(query5c)
        
        total_revenue = sum(row['Amount'] for row in revenue_data)
        total_cogs = sum(row['Amount'] for row in cogs_data)
        total_expenses = sum(row['Amount'] for row in expense_data)
        
        results['pl_breakdown'] = {
            'revenue_accounts': revenue_data,
            'cogs_accounts': cogs_data,
            'expense_accounts': expense_data,
            'totals': {
                'revenue': total_revenue,
                'cogs': total_cogs,
                'expenses': total_expenses,
                'gross_profit': total_revenue - total_cogs,
                'operating_profit': total_revenue - total_cogs - total_expenses
            }
        }
        
        # ============================================================================
        # ANALYSIS 6: Month-to-Month P&L Comparison (Dec, Jan, Feb)
        # ============================================================================
        query6 = """
        SELECT 
            YEAR(EffectiveDate) as Year,
            MONTH(EffectiveDate) as Month,
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) as Revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) as COGS,
            SUM(CASE WHEN AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%' THEN Amount ELSE 0 END) as Expenses
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2024-12-01' AND EffectiveDate < '2025-03-01'
          AND Posted = 1
        GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY Year, Month
        """
        comparison_data = sql_service.execute_query(query6)
        
        # Add calculated fields
        for row in comparison_data:
            row['GrossProfit'] = row['Revenue'] - row['COGS']
            row['OperatingProfit'] = row['GrossProfit'] - row['Expenses']
        
        results['month_comparison'] = comparison_data
        
        # ============================================================================
        # ANALYSIS 7: Search for Migration/Adjustment Keywords
        # ============================================================================
        query7 = """
        SELECT 
            EffectiveDate,
            AccountNo,
            Amount,
            Description,
            Reference
        FROM ben002.GLDetail
        WHERE EffectiveDate >= '2025-01-01' AND EffectiveDate < '2025-02-01'
          AND Posted = 1
          AND (
              Description LIKE '%migration%' OR
              Description LIKE '%adjustment%' OR
              Description LIKE '%opening%' OR
              Description LIKE '%balance%' OR
              Description LIKE '%conversion%' OR
              Description LIKE '%minitrac%' OR
              Reference LIKE '%migration%' OR
              Reference LIKE '%adjustment%' OR
              Reference LIKE '%opening%' OR
              Reference LIKE '%conversion%'
          )
        ORDER BY ABS(Amount) DESC
        """
        results['migration_keywords'] = sql_service.execute_query(query7)
        
        # ============================================================================
        # ANALYSIS 8: Unusual Account Activity (accounts with Jan activity but not Dec/Feb)
        # ============================================================================
        query8 = """
        WITH JanAccounts AS (
            SELECT DISTINCT AccountNo
            FROM ben002.GLDetail
            WHERE EffectiveDate >= '2025-01-01' AND EffectiveDate < '2025-02-01'
              AND Posted = 1
        ),
        DecFebAccounts AS (
            SELECT DISTINCT AccountNo
            FROM ben002.GLDetail
            WHERE ((EffectiveDate >= '2024-12-01' AND EffectiveDate < '2025-01-01')
                OR (EffectiveDate >= '2025-02-01' AND EffectiveDate < '2025-03-01'))
              AND Posted = 1
        )
        SELECT 
            j.AccountNo,
            COUNT(*) as TransactionCount,
            SUM(g.Amount) as TotalAmount
        FROM JanAccounts j
        LEFT JOIN DecFebAccounts d ON j.AccountNo = d.AccountNo
        JOIN ben002.GLDetail g ON j.AccountNo = g.AccountNo
            AND g.EffectiveDate >= '2025-01-01' 
            AND g.EffectiveDate < '2025-02-01'
            AND g.Posted = 1
        WHERE d.AccountNo IS NULL
        GROUP BY j.AccountNo
        ORDER BY ABS(SUM(g.Amount)) DESC
        """
        results['unusual_accounts'] = sql_service.execute_query(query8)
        
        return jsonify({
            'success': True,
            'data': results
        })
        
    except Exception as e:
        logger.error(f"Error in January 2025 investigation: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
