"""
P&L Dashboard Widget API
Provides monthly profit/loss metrics for dashboard display
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from src.utils.fiscal_year import SOFTBASE_CUTOVER_DATE, get_fiscal_ytd_start
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
        
        # Get 12-month trend
        trend_data = get_pl_trend(current_year, current_month, months=12)
        
        # Debug logging
        logger.info(f"=" * 80)
        logger.info(f"P&L Widget Calculation for {current_year}-{current_month:02d}")
        logger.info(f"Trend data has {len(trend_data)} months:")
        for item in trend_data:
            logger.info(f"  {item['month']}: ${item['profit_loss']:,.2f}")
        
        # Calculate fiscal YTD (from fiscal year start to current month)
        fiscal_ytd_start = get_fiscal_ytd_start()
        ytd_pl = sum(
            item['profit_loss'] 
            for item in trend_data 
            if datetime.strptime(item['month'], '%Y-%m').replace(day=1) >= fiscal_ytd_start
        ) if trend_data else 0
        logger.info(f"Fiscal YTD start: {fiscal_ytd_start.strftime('%Y-%m-%d')}")
        logger.info(f"Fiscal YTD P&L: ${ytd_pl:,.2f}")
        logger.info(f"=" * 80)
        
        # Calculate average monthly P&L from fiscal YTD months
        fiscal_ytd_months = [
            item for item in trend_data 
            if datetime.strptime(item['month'], '%Y-%m').replace(day=1) >= fiscal_ytd_start
        ]
        avg_monthly_pl = ytd_pl / len(fiscal_ytd_months) if fiscal_ytd_months else 0
        
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

        # Add Other Income/Contra-Revenue accounts (7xxxxx series)
        # These accounts (like A/R Discounts) reduce total revenue
        all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)

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
        
        # Query all three categories in a single query (matching P&L Report approach)
        query = f"""
        SELECT 
            -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN MTD ELSE 0 END) as revenue,
            SUM(CASE WHEN AccountNo IN ('{cogs_list}') THEN MTD ELSE 0 END) as cogs,
            SUM(CASE WHEN AccountNo IN ('{expense_list}') THEN MTD ELSE 0 END) as expenses
        FROM ben002.GL
        WHERE Year = %s AND Month = %s
          AND (AccountNo IN ('{revenue_list}') 
               OR AccountNo IN ('{cogs_list}')
               OR AccountNo IN ('{expense_list}'))
        """
        
        result = sql_service.execute_query(query, [year, month])
        
        if result and result[0]:
            revenue = float(result[0].get('revenue') or 0)
            cogs = float(result[0].get('cogs') or 0)
            expenses = float(result[0].get('expenses') or 0)
        else:
            revenue = 0.0
            cogs = 0.0
            expenses = 0.0
        
        # Calculate Operating Profit (matching P&L Report)
        # Revenue is now positive (negated in query)
        # COGS and Expenses are positive (debits)
        gross_profit = revenue - cogs
        operating_profit = gross_profit - expenses
        
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

        # Calculate starting point: either N months back or cutover month, whichever is later
        # Go back N-1 months from current month (to include current month in the count)
        start_date = datetime(year, month, 1)
        for i in range(months - 1):
            start_date = start_date.replace(day=1) - timedelta(days=1)
        start_date = start_date.replace(day=1)

        # Don't go before Softbase cutover (March 2025)
        if start_date < SOFTBASE_CUTOVER_DATE:
            start_date = SOFTBASE_CUTOVER_DATE
        
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
