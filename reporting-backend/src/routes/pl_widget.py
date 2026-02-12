"""
P&L Dashboard Widget API
Provides monthly profit/loss metrics for dashboard display
"""

from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
from src.services.cache_service import cache_service
from src.utils.fiscal_year import get_tenant_cutover_date, get_fiscal_ytd_start
from src.models.user import User
from datetime import datetime, timedelta
import logging
import calendar

logger = logging.getLogger(__name__)

pl_widget_bp = Blueprint('pl_widget', __name__)
# sql_service is now obtained via get_tenant_db() for multi-tenant support
_sql_service = None
def get_sql_service():
    return get_tenant_db()
# Import GL account loader for tenant-specific GL accounts
from src.config.gl_accounts_loader import get_gl_accounts, get_expense_accounts, get_other_income_accounts

@pl_widget_bp.route('/api/pl/widget', methods=['GET'])
@jwt_required()
def get_pl_widget():
    """
    Get P&L widget data for dashboard
    Returns current month P&L, YTD P&L, average monthly P&L, and 12-month trend
    """
    try:
        schema = get_tenant_schema()
        
        # Ensure g.current_organization is set for fiscal year and cutover date calculations
        if not hasattr(g, 'current_organization') or not g.current_organization:
            user_id = get_jwt_identity()
            if user_id:
                user = User.query.get(int(user_id))
                if user and user.organization:
                    g.current_organization = user.organization
                    logger.info(f"P&L Widget: Set org context - {user.organization.name}, "
                               f"fiscal_year_start_month={user.organization.fiscal_year_start_month}, "
                               f"data_start_date={user.organization.data_start_date}")
        
        # Get current date or use provided date
        as_of_date = request.args.get('as_of_date')
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if as_of_date:
            current_date = datetime.strptime(as_of_date, '%Y-%m-%d')
        else:
            current_date = datetime.now()
        
        # Use cache with 1-hour TTL
        cache_key = f'pl_widget:{schema}:{as_of_date or current_date.strftime("%Y-%m-%d")}'
        
        def fetch_pl_widget_data():
            return _fetch_pl_widget_data(current_date, schema)
        
        result = cache_service.cache_query(cache_key, fetch_pl_widget_data, ttl_seconds=3600, force_refresh=force_refresh)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in get_pl_widget: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def _fetch_pl_widget_data(current_date, schema):
    """Internal function to fetch P&L widget data"""
    # Always use last closed month (previous month)
    last_closed_month = current_date.replace(day=1) - timedelta(days=1)
    current_year = last_closed_month.year
    current_month = last_closed_month.month
    
    # Get current month P&L
    current_pl = get_monthly_pl(current_year, current_month, schema)
    
    # Get 13-month trend (trailing 13 months)
    trend_data = get_pl_trend(current_year, current_month, schema, months=13)
    
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
    
    # Calculate average monthly P&L from trailing 12 months (all trend data)
    trailing_12_total = sum(item['profit_loss'] for item in trend_data) if trend_data else 0
    avg_monthly_pl = trailing_12_total / len(trend_data) if trend_data else 0
    
    # Determine health status
    if current_pl > 50000:
        health_status = 'profitable'
    elif current_pl > 0:
        health_status = 'break_even'
    else:
        health_status = 'loss'
    
    return {
        'current_pl': current_pl,
        'ytd_pl': ytd_pl,
        'avg_monthly_pl': avg_monthly_pl,
        'health_status': health_status,
        'trend': trend_data,
        'as_of_date': last_closed_month.strftime('%Y-%m-%d')
    }


def get_monthly_pl(year, month, schema):
    """
    Get monthly profit/loss from GL.MTD
    Uses dynamic LIKE queries to capture ALL accounts by prefix pattern.
    This ensures consistency with the P&L Report's consolidated totals.
    Operating Profit = Revenue (4%) - COGS (5%) - Expenses (6%)
    """
    try:
        # Dynamic query using LIKE patterns - captures ALL accounts
        query = f"""
        SELECT 
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN MTD ELSE 0 END) as revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN MTD ELSE 0 END) as cogs,
            SUM(CASE WHEN AccountNo LIKE '6%' THEN MTD ELSE 0 END) as expenses
        FROM {schema}.GL
        WHERE Year = %s AND Month = %s
          AND (AccountNo LIKE '4%' OR AccountNo LIKE '5%' OR AccountNo LIKE '6%')
        """
        
        result = get_sql_service().execute_query(query, [year, month])
        
        if result and result[0]:
            revenue = float(result[0].get('revenue') or 0)
            cogs = float(result[0].get('cogs') or 0)
            expenses = float(result[0].get('expenses') or 0)
        else:
            revenue = 0.0
            cogs = 0.0
            expenses = 0.0
        
        # Calculate Operating Profit
        # Revenue is positive (negated in query from credit convention)
        # COGS and Expenses are positive (debit convention)
        gross_profit = revenue - cogs
        operating_profit = gross_profit - expenses
        
        return operating_profit
        
    except Exception as e:
        logger.error(f"Error getting monthly P&L: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0.0


def get_ytd_pl(year, month, schema):
    """
    Get year-to-date profit/loss
    Sum of all months from January to current month
    """
    try:
        # Sum up monthly P&L for each month YTD
        ytd_total = 0.0
        for m in range(1, month + 1):
            monthly_pl = get_monthly_pl(year, m, schema)
            ytd_total += monthly_pl
        
        return ytd_total
        
    except Exception as e:
        logger.error(f"Error getting YTD P&L: {str(e)}")
        return 0.0


def get_pl_trend(year, month, schema, months=12):
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

        # Don't go before tenant's data start date
        cutover = get_tenant_cutover_date()
        if cutover and start_date < cutover:
            start_date = cutover
        
        # Generate trend data from start_date to current month (inclusive)
        current = start_date
        end_date = datetime(year, month, 1)
        
        while current <= end_date:
            target_year = current.year
            target_month = current.month
            
            # Get P&L for this month
            monthly_pl = get_monthly_pl(target_year, target_month, schema)
            
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
