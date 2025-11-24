"""
P&L Dashboard Widget API
Provides monthly profit/loss metrics for dashboard display
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from datetime import datetime, timedelta
import logging
import calendar

logger = logging.getLogger(__name__)

pl_widget_bp = Blueprint('pl_widget', __name__)
sql_service = AzureSQLService()

# Import GL account mappings from pl_report
from src.routes.pl_report import GL_ACCOUNTS, EXPENSE_ACCOUNTS, OTHER_INCOME_ACCOUNTS

@pl_widget_bp.route('/api/pl/widget', methods=['GET'])
@jwt_required()
def get_pl_widget():
    """
    Get P&L widget data for dashboard
    Returns current month P&L, YTD P&L, average monthly P&L, and 12-month trend
    """
    try:
        # Get current date or use provided date
        as_of_date = request.args.get('as_of_date')
        if as_of_date:
            current_date = datetime.strptime(as_of_date, '%Y-%m-%d')
        else:
            current_date = datetime.now()
        
        # Always use last closed month (previous month)
        last_closed_month = current_date.replace(day=1) - timedelta(days=1)
        current_year = last_closed_month.year
        current_month = last_closed_month.month
        
        # Get current month P&L
        current_pl = get_monthly_pl(current_year, current_month)
        
        # Get YTD P&L
        ytd_pl = get_ytd_pl(current_year, current_month)
        
        # Get 12-month trend
        trend_data = get_pl_trend(current_year, current_month, months=12)
        
        # Calculate average monthly P&L from trend data
        avg_monthly_pl = sum(item['profit_loss'] for item in trend_data) / len(trend_data) if trend_data else 0
        
        # Determine health status
        if current_pl > 50000:
            health_status = 'profitable'
        elif current_pl > 0:
            health_status = 'break_even'
        else:
            health_status = 'loss'
        
        return jsonify({
            'current_pl': current_pl,
            'ytd_pl': ytd_pl,
            'avg_monthly_pl': avg_monthly_pl,
            'health_status': health_status,
            'trend': trend_data,
            'as_of_date': last_closed_month.strftime('%Y-%m-%d')
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_pl_widget: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def get_monthly_pl(year, month):
    """
    Get monthly profit/loss from GL.MTD
    Uses the same GL account mappings as the P&L Report
    Operating Profit = Revenue - COGS - Expenses
    """
    try:
        # Collect all revenue accounts from all departments
        all_revenue_accounts = []
        for dept_config in GL_ACCOUNTS.values():
            all_revenue_accounts.extend(dept_config['revenue'])
        
        # Collect all COGS accounts from all departments
        all_cogs_accounts = []
        for dept_config in GL_ACCOUNTS.values():
            all_cogs_accounts.extend(dept_config['cogs'])
        
        # Collect all expense accounts
        all_expense_accounts = []
        for category_accounts in EXPENSE_ACCOUNTS.values():
            all_expense_accounts.extend(category_accounts)
        
        # Build account lists for query
        revenue_list = "', '".join(all_revenue_accounts)
        cogs_list = "', '".join(all_cogs_accounts)
        expense_list = "', '".join(all_expense_accounts)
        
        # Query revenue
        revenue_query = f"""
        SELECT SUM(MTD) as total
        FROM ben002.GL
        WHERE Year = %s AND Month = %s
          AND AccountNo IN ('{revenue_list}')
        """
        revenue_result = sql_service.execute_query(revenue_query, [year, month])
        revenue = float(revenue_result[0].get('total') or 0) if revenue_result and revenue_result[0] else 0.0
        
        # Query COGS
        cogs_query = f"""
        SELECT SUM(MTD) as total
        FROM ben002.GL
        WHERE Year = %s AND Month = %s
          AND AccountNo IN ('{cogs_list}')
        """
        cogs_result = sql_service.execute_query(cogs_query, [year, month])
        cogs = float(cogs_result[0].get('total') or 0) if cogs_result and cogs_result[0] else 0.0
        
        # Query expenses
        expense_query = f"""
        SELECT SUM(MTD) as total
        FROM ben002.GL
        WHERE Year = %s AND Month = %s
          AND AccountNo IN ('{expense_list}')
        """
        expense_result = sql_service.execute_query(expense_query, [year, month])
        expenses = float(expense_result[0].get('total') or 0) if expense_result and expense_result[0] else 0.0
        
        # Calculate Operating Profit
        # In GL.MTD: Revenue is stored as negative (credits), COGS and Expenses are positive (debits)
        # Operating Profit = -Revenue - COGS - Expenses = -(Revenue + COGS + Expenses)
        operating_profit = -(revenue + cogs + expenses)
        
        return operating_profit
        
    except Exception as e:
        logger.error(f"Error getting monthly P&L: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0.0


def get_ytd_pl(year, month):
    """
    Get year-to-date profit/loss
    Sum of all months from January to current month
    """
    try:
        # Sum up monthly P&L for each month YTD
        ytd_total = 0.0
        for m in range(1, month + 1):
            monthly_pl = get_monthly_pl(year, m)
            ytd_total += monthly_pl
        
        return ytd_total
        
    except Exception as e:
        logger.error(f"Error getting YTD P&L: {str(e)}")
        return 0.0


def get_pl_trend(year, month, months=12):
    """
    Get P&L trend for the last N months (or all available months since November 2024)
    Includes the current month
    """
    try:
        trend_data = []
        cutover_year = 2024
        cutover_month = 11  # November 2024
        
        # Calculate starting point: either N months back or cutover month, whichever is later
        # Go back N-1 months from current month (to include current month in the count)
        start_date = datetime(year, month, 1)
        for i in range(months - 1):
            start_date = start_date.replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)
        
        # Don't go before cutover
        cutover_date = datetime(cutover_year, cutover_month, 1)
        if start_date < cutover_date:
            start_date = cutover_date
        
        # Generate trend data from start_date to current month (inclusive)
        current = start_date
        end_date = datetime(year, month, 1)
        
        while current <= end_date:
            target_year = current.year
            target_month = current.month
            
            # Get P&L for this month
            monthly_pl = get_monthly_pl(target_year, target_month)
            
            # Format month label
            month_label = f"{target_year}-{target_month:02d}"
            
            trend_data.append({
                'month': month_label,
                'profit_loss': monthly_pl
            })
            
            # Move to next month
            current = current + timedelta(days=32)
            current = current.replace(day=1)
        
        return trend_data
        
    except Exception as e:
        logger.error(f"Error getting P&L trend: {str(e)}")
        import traceback
        traceback.print_exc()
        return []
