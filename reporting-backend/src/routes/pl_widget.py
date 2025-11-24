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
    Revenue (4xxxxx) - COGS (5xxxxx) - Expenses (6xxxxx, 7xxxxx, 8xxxxx)
    """
    try:
        query = """
        SELECT 
            SUM(CASE WHEN AccountNo LIKE '4%' THEN MTD ELSE 0 END) as revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN MTD ELSE 0 END) as cogs,
            SUM(CASE WHEN AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%' THEN MTD ELSE 0 END) as expenses
        FROM ben002.GL
        WHERE Year = %s
          AND Month = %s
        """
        
        result = sql_service.execute_query(query, [year, month])
        
        if result and result[0]:
            revenue = float(result[0].get('revenue') or 0)
            cogs = float(result[0].get('cogs') or 0)
            expenses = float(result[0].get('expenses') or 0)
            
            # P&L calculation: Revenue - COGS - Expenses
            # Note: In GL, revenue is positive, COGS and expenses are negative
            # So we add them all (since COGS and expenses are already negative)
            net_pl = revenue + cogs + expenses
            
            return net_pl
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting monthly P&L: {str(e)}")
        return 0.0


def get_ytd_pl(year, month):
    """
    Get year-to-date profit/loss
    Sum of all months from January to current month
    """
    try:
        query = """
        SELECT 
            SUM(CASE WHEN AccountNo LIKE '4%' THEN MTD ELSE 0 END) as revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN MTD ELSE 0 END) as cogs,
            SUM(CASE WHEN AccountNo LIKE '6%' OR AccountNo LIKE '7%' OR AccountNo LIKE '8%' THEN MTD ELSE 0 END) as expenses
        FROM ben002.GL
        WHERE Year = %s
          AND Month <= %s
        """
        
        result = sql_service.execute_query(query, [year, month])
        
        if result and result[0]:
            revenue = float(result[0].get('revenue') or 0)
            cogs = float(result[0].get('cogs') or 0)
            expenses = float(result[0].get('expenses') or 0)
            
            net_pl = revenue + cogs + expenses
            
            return net_pl
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting YTD P&L: {str(e)}")
        return 0.0


def get_pl_trend(year, month, months=12):
    """
    Get P&L trend for the last N months starting from March 2025 (Softbase cutover)
    """
    try:
        trend_data = []
        cutover_year = 2025
        cutover_month = 3  # March 2025
        
        # Calculate starting point (N months back from current month)
        start_date = datetime(year, month, 1) - timedelta(days=1)  # Last day of previous month
        for i in range(months):
            start_date = start_date.replace(day=1) - timedelta(days=1)  # Go back one more month
        
        # Start from the month after our calculated start
        current = start_date.replace(day=1) + timedelta(days=32)
        current = current.replace(day=1)
        
        # Generate trend data for each month
        for i in range(months):
            target_year = current.year
            target_month = current.month
            
            # Skip months before Softbase cutover
            if target_year < cutover_year or (target_year == cutover_year and target_month < cutover_month):
                current = current + timedelta(days=32)
                current = current.replace(day=1)
                continue
            
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
        return []
