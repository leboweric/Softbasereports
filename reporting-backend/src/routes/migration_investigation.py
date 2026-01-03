"""
Migration Investigation API - All Migrated Months
Analyzes Nov 2024, Dec 2024, Jan 2025, Feb 2025 for data migration issues
Version: 1.0.0
"""

from flask import Blueprint, jsonify, request
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

migration_investigation_bp = Blueprint('migration_investigation', __name__)
sql_service = AzureSQLService()
def investigate_month(year, month, month_name):
    """
    Investigate a single month for migration issues
    
    Args:
        year: Year (e.g., 2024)
        month: Month number (1-12)
        month_name: Month name for display (e.g., "November 2024")
    
    Returns:
        Dictionary with investigation results
    """
    # Calculate date range
    if month == 12:
        next_month = 1
        next_year = year + 1
    else:
        next_month = month + 1
        next_year = year
    
    start_date = f"{year}-{month:02d}-01"
    end_date = f"{next_year}-{next_month:02d}-01"
    
    results = {
        'month_name': month_name,
        'year': year,
        'month': month
    }
    
    # ============================================================================
    # ANALYSIS 1: Transaction Summary
    # ============================================================================
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
    
    # ============================================================================
    # ANALYSIS 2: Large Transactions (> $50K)
    # ============================================================================
    query2 = f"""
    SELECT TOP 50
        EffectiveDate,
        AccountNo,
        Amount,
        Posted
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND ABS(Amount) > 50000
      AND Posted = 1
    ORDER BY ABS(Amount) DESC
    """
    results['large_transactions'] = sql_service.execute_query(query2)
    
    # ============================================================================
    # ANALYSIS 3: Offsetting Transaction Pairs
    # ============================================================================
    query3 = f"""
    SELECT 
        t1.EffectiveDate,
        t1.AccountNo,
        t1.Amount as DebitAmount,
        t2.Amount as CreditAmount,
        ABS(t1.Amount + t2.Amount) as NetDifference
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
    ORDER BY ABS(t1.Amount) DESC
    """
    results['offsetting_pairs'] = sql_service.execute_query(query3)
    
    # ============================================================================
    # ANALYSIS 4: P&L Breakdown
    # ============================================================================
    
    # Revenue
    query4a = f"""
    SELECT 
        AccountNo,
        -SUM(Amount) as Amount,
        COUNT(*) as TransactionCount
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
      AND AccountNo LIKE '4%'
    GROUP BY AccountNo
    ORDER BY -SUM(Amount) DESC
    """
    
    # COGS
    query4b = f"""
    SELECT 
        AccountNo,
        SUM(Amount) as Amount,
        COUNT(*) as TransactionCount
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
      AND AccountNo LIKE '5%'
    GROUP BY AccountNo
    ORDER BY SUM(Amount) DESC
    """
    
    # Expenses
    query4c = f"""
    SELECT 
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
    
    revenue_data = sql_service.execute_query(query4a)
    cogs_data = sql_service.execute_query(query4b)
    expense_data = sql_service.execute_query(query4c)
    
    total_revenue = sum(row['Amount'] for row in revenue_data)
    total_cogs = sum(row['Amount'] for row in cogs_data)
    total_expenses = sum(row['Amount'] for row in expense_data)
    
    results['pl_breakdown'] = {
        'revenue_accounts': revenue_data[:20],  # Top 20
        'cogs_accounts': cogs_data[:20],
        'expense_accounts': expense_data[:20],
        'totals': {
            'revenue': total_revenue,
            'cogs': total_cogs,
            'expenses': total_expenses,
            'gross_profit': total_revenue - total_cogs,
            'operating_profit': total_revenue - total_cogs - total_expenses
        }
    }
    
    # ============================================================================
    # ANALYSIS 5: Expense Accounts with Large Offsetting Entries
    # ============================================================================
    query5 = f"""
    SELECT 
        AccountNo,
        COUNT(*) as TransactionCount,
        SUM(Amount) as NetAmount,
        MIN(Amount) as MinAmount,
        MAX(Amount) as MaxAmount,
        SUM(ABS(Amount)) as TotalVolume
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
      AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
    GROUP BY AccountNo
    HAVING SUM(ABS(Amount)) > 100000
    ORDER BY SUM(ABS(Amount)) DESC
    """
    results['high_volume_expenses'] = sql_service.execute_query(query5)
    
    # ============================================================================
    # ANALYSIS 6: Last Day of Month Batch Entries
    # ============================================================================
    # Get the last day of the month
    last_day_query = f"""
    SELECT MAX(DAY(EffectiveDate)) as LastDay
    FROM {schema}.GLDetail
    WHERE EffectiveDate >= '{start_date}' AND EffectiveDate < '{end_date}'
      AND Posted = 1
    """
    last_day_result = sql_service.execute_query(last_day_query)
    last_day = last_day_result[0]['LastDay'] if last_day_result else 31
    
    last_day_date = f"{year}-{month:02d}-{last_day:02d}"
    
    query6 = f"""
    SELECT 
        AccountNo,
        COUNT(*) as TransactionCount,
        SUM(Amount) as NetAmount,
        SUM(ABS(Amount)) as TotalVolume
    FROM {schema}.GLDetail
    WHERE EffectiveDate = '{last_day_date}'
      AND Posted = 1
      AND (AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%')
    GROUP BY AccountNo
    HAVING SUM(ABS(Amount)) > 10000
    ORDER BY SUM(ABS(Amount)) DESC
    """
    results['last_day_expenses'] = sql_service.execute_query(query6)
    
    return results


@migration_investigation_bp.route('/api/investigation/november2024', methods=['GET'])
def investigate_november_2024():
    """Investigate November 2024 for migration issues"""
    try:
        results = investigate_month(2024, 11, "November 2024")
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error investigating November 2024: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@migration_investigation_bp.route('/api/investigation/december2024', methods=['GET'])
def investigate_december_2024():
    """Investigate December 2024 for migration issues"""
    try:
        results = investigate_month(2024, 12, "December 2024")
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error investigating December 2024: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@migration_investigation_bp.route('/api/investigation/february2025', methods=['GET'])
def investigate_february_2025():
    """Investigate February 2025 for migration issues"""
    try:
        results = investigate_month(2025, 2, "February 2025")
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error investigating February 2025: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@migration_investigation_bp.route('/api/investigation/all-migrated-months', methods=['GET'])
def investigate_all_migrated_months():
    """
    Investigate all migrated months (Nov 2024 - Feb 2025) in one call
    Returns comparative analysis across all four months
    """
    try:
        results = {
            'november_2024': investigate_month(2024, 11, "November 2024"),
            'december_2024': investigate_month(2024, 12, "December 2024"),
            'january_2025': investigate_month(2025, 1, "January 2025"),
            'february_2025': investigate_month(2025, 2, "February 2025")
        }
        
        # Add comparative summary
        summary = {
            'transaction_counts': {},
            'operating_profits': {},
            'total_expenses': {},
            'offsetting_pairs_count': {}
        }
        
        for month_key, month_data in results.items():
            month_name = month_data['month_name']
            summary['transaction_counts'][month_name] = month_data['transaction_summary'].get('TransactionCount', 0)
            summary['operating_profits'][month_name] = month_data['pl_breakdown']['totals']['operating_profit']
            summary['total_expenses'][month_name] = month_data['pl_breakdown']['totals']['expenses']
            summary['offsetting_pairs_count'][month_name] = len(month_data['offsetting_pairs'])
        
        results['comparative_summary'] = summary
        
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        logger.error(f"Error investigating all migrated months: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
