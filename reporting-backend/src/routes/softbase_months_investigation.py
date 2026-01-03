"""
Softbase-Native Months Investigation API
Analyzes Mar 2025 - Oct 2025 for data quality verification
Version: 1.0.0
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

softbase_months_bp = Blueprint('softbase_months', __name__)
sql_service = AzureSQLService()
def analyze_month(year, month, month_name):
    """Analyze a single Softbase-native month"""
    
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{next_year}-{next_month:02d}-01"
    
    results = {'month_name': month_name, 'year': year, 'month': month}
    
    # Transaction Summary
    query1 = f"""
    SELECT 
        COUNT(*) as TransactionCount,
        COUNT(DISTINCT AccountNo) as UniqueAccounts,
        SUM(CASE WHEN Amount > 0 THEN 1 ELSE 0 END) as DebitCount,
        SUM(CASE WHEN Amount < 0 THEN 1 ELSE 0 END) as CreditCount,
        SUM(ABS(Amount)) as TotalVolume
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
    """
    results['transaction_summary'] = sql_service.execute_query(query1)[0] if sql_service.execute_query(query1) else {}
    
    # P&L Summary
    query2 = f"""
    SELECT 
        -SUM(CASE WHEN AccountNo LIKE '4%' THEN Amount ELSE 0 END) as Revenue,
        SUM(CASE WHEN AccountNo LIKE '5%' THEN Amount ELSE 0 END) as COGS,
        SUM(CASE WHEN AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%' THEN Amount ELSE 0 END) as Expenses
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
    """
    pl_data = sql_service.execute_query(query2)
    if pl_data:
        revenue = float(pl_data[0]['Revenue'] or 0)
        cogs = float(pl_data[0]['COGS'] or 0)
        expenses = float(pl_data[0]['Expenses'] or 0)
        results['pl_summary'] = {
            'revenue': revenue,
            'cogs': cogs,
            'expenses': expenses,
            'gross_profit': revenue - cogs,
            'operating_profit': revenue - cogs - expenses
        }
    
    # Offsetting Pairs Check
    query3 = f"""
    SELECT 
        t1.AccountNo,
        COUNT(*) as PairCount
    FROM {schema}.GLDetail t1
    JOIN {schema}.GLDetail t2 
        ON t1.AccountNo = t2.AccountNo
        AND t1.EffectiveDate = t2.EffectiveDate
        AND ABS(t1.Amount + t2.Amount) < 1000
        AND t1.Amount > 0
        AND t2.Amount < 0
    WHERE t1.EffectiveDate >= '{start_date}' 
      AND t1.EffectiveDate < '{end_date}'
      AND t1.Posted = 1
      AND ABS(t1.Amount) > 50000
    GROUP BY t1.AccountNo
    ORDER BY COUNT(*) DESC
    """
    results['offsetting_pairs'] = sql_service.execute_query(query3)
    
    # Account 602600 Analysis
    query4 = f"""
    SELECT 
        COUNT(*) as TransactionCount,
        SUM(Amount) as NetAmount,
        MIN(Amount) as MinAmount,
        MAX(Amount) as MaxAmount,
        SUM(ABS(Amount)) as TotalVolume
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
      AND AccountNo = '602600'
    """
    results['account_602600'] = sql_service.execute_query(query4)[0] if sql_service.execute_query(query4) else {}
    
    # Top Expense Accounts
    query5 = f"""
    SELECT TOP 10
        AccountNo,
        SUM(Amount) as Amount,
        COUNT(*) as TransactionCount
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
      AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
    GROUP BY AccountNo
    ORDER BY SUM(Amount) DESC
    """
    results['top_expenses'] = sql_service.execute_query(query5)
    
    # Negative Expense Accounts
    query6 = f"""
    SELECT 
        AccountNo,
        SUM(Amount) as NetAmount,
        COUNT(*) as TransactionCount
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
      AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
    GROUP BY AccountNo
    HAVING SUM(Amount) < 0
    ORDER BY SUM(Amount)
    """
    results['negative_expenses'] = sql_service.execute_query(query6)
    
    return results


@softbase_months_bp.route('/api/investigation/softbase-months', methods=['GET'])
def investigate_softbase_months():
    """Investigate all Softbase-native months (Mar-Oct 2025)"""
    try:
        months = [
            (2025, 3, "March 2025"),
            (2025, 4, "April 2025"),
            (2025, 5, "May 2025"),
            (2025, 6, "June 2025"),
            (2025, 7, "July 2025"),
            (2025, 8, "August 2025"),
            (2025, 9, "September 2025"),
            (2025, 10, "October 2025"),
        ]
        
        results = {}
        summary = {
            'transaction_counts': {},
            'operating_profits': {},
            'expenses': {},
            'offsetting_pairs_count': {},
            'account_602600_net': {}
        }
        
        for year, month, month_name in months:
            month_key = f"{month_name.lower().replace(' ', '_')}"
            month_data = analyze_month(year, month, month_name)
            results[month_key] = month_data
            
            # Build summary
            summary['transaction_counts'][month_name] = month_data['transaction_summary'].get('TransactionCount', 0)
            summary['operating_profits'][month_name] = month_data['pl_summary']['operating_profit']
            summary['expenses'][month_name] = month_data['pl_summary']['expenses']
            summary['offsetting_pairs_count'][month_name] = len(month_data['offsetting_pairs'])
            summary['account_602600_net'][month_name] = month_data['account_602600'].get('NetAmount', 0)
        
        results['summary'] = summary
        
        # Calculate averages
        avg_transactions = sum(summary['transaction_counts'].values()) / len(summary['transaction_counts'])
        avg_profit = sum(summary['operating_profits'].values()) / len(summary['operating_profits'])
        avg_expenses = sum(summary['expenses'].values()) / len(summary['expenses'])
        avg_602600 = sum(float(v or 0) for v in summary['account_602600_net'].values()) / len(summary['account_602600_net'])
        
        results['averages'] = {
            'avg_transactions': avg_transactions,
            'avg_operating_profit': avg_profit,
            'avg_expenses': avg_expenses,
            'avg_account_602600': avg_602600
        }
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error investigating Softbase months: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@softbase_months_bp.route('/api/investigation/full-year-comparison', methods=['GET'])
def full_year_comparison():
    """Compare all months: Migrated (Nov-Feb) vs Softbase (Mar-Oct)"""
    try:
        # Get migrated months data
        migrated_months = [
            (2024, 11, "November 2024"),
            (2024, 12, "December 2024"),
            (2025, 1, "January 2025"),
            (2025, 2, "February 2025"),
        ]
        
        # Get Softbase months data
        softbase_months = [
            (2025, 3, "March 2025"),
            (2025, 4, "April 2025"),
            (2025, 5, "May 2025"),
            (2025, 6, "June 2025"),
            (2025, 7, "July 2025"),
            (2025, 8, "August 2025"),
            (2025, 9, "September 2025"),
            (2025, 10, "October 2025"),
        ]
        
        results = {
            'migrated': {},
            'softbase': {}
        }
        
        # Analyze migrated months
        for year, month, month_name in migrated_months:
            month_key = f"{month_name.lower().replace(' ', '_')}"
            results['migrated'][month_key] = analyze_month(year, month, month_name)
        
        # Analyze Softbase months
        for year, month, month_name in softbase_months:
            month_key = f"{month_name.lower().replace(' ', '_')}"
            results['softbase'][month_key] = analyze_month(year, month, month_name)
        
        # Calculate comparison metrics
        migrated_avg_txn = sum(m['transaction_summary']['TransactionCount'] for m in results['migrated'].values()) / 4
        softbase_avg_txn = sum(m['transaction_summary']['TransactionCount'] for m in results['softbase'].values()) / 8
        
        migrated_avg_profit = sum(m['pl_summary']['operating_profit'] for m in results['migrated'].values()) / 4
        softbase_avg_profit = sum(m['pl_summary']['operating_profit'] for m in results['softbase'].values()) / 8
        
        migrated_avg_expenses = sum(m['pl_summary']['expenses'] for m in results['migrated'].values()) / 4
        softbase_avg_expenses = sum(m['pl_summary']['expenses'] for m in results['softbase'].values()) / 8
        
        results['comparison'] = {
            'migrated_avg_transactions': migrated_avg_txn,
            'softbase_avg_transactions': softbase_avg_txn,
            'transaction_ratio': softbase_avg_txn / migrated_avg_txn if migrated_avg_txn > 0 else 0,
            'migrated_avg_profit': migrated_avg_profit,
            'softbase_avg_profit': softbase_avg_profit,
            'migrated_avg_expenses': migrated_avg_expenses,
            'softbase_avg_expenses': softbase_avg_expenses
        }
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error in full year comparison: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
