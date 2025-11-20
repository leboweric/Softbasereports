"""
Cash Flow Dashboard Widget API
Provides quick cash flow metrics for dashboard display
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from datetime import datetime, timedelta
import logging
import calendar

logger = logging.getLogger(__name__)

cashflow_widget_bp = Blueprint('cashflow_widget', __name__)
sql_service = AzureSQLService()

@cashflow_widget_bp.route('/api/cashflow/widget', methods=['GET'])
@jwt_required()
def get_cashflow_widget():
    """
    Get cash flow widget data for dashboard
    Returns current cash position, operating cash flow, and 6-month trend
    """
    try:
        # Get current date or use provided date
        as_of_date = request.args.get('as_of_date')
        if as_of_date:
            current_date = datetime.strptime(as_of_date, '%Y-%m-%d')
        else:
            current_date = datetime.now()
        
        current_year = current_date.year
        current_month = current_date.month
        
        # Get current cash position
        cash_position = get_current_cash_position(current_year, current_month)
        
        # Get current month operating cash flow
        current_month_cf = get_monthly_operating_cashflow(current_year, current_month)
        
        # Get 6-month trend
        trend_data = get_cashflow_trend(current_year, current_month, months=6)
        
        # Calculate free cash flow (Operating CF - CapEx)
        capex = get_monthly_capex(current_year, current_month)
        free_cashflow = current_month_cf - capex
        
        # Determine health status
        health_status = 'healthy' if current_month_cf > 0 else 'warning' if current_month_cf > -50000 else 'critical'
        
        return jsonify({
            'cash_position': cash_position,
            'operating_cashflow': current_month_cf,
            'free_cashflow': free_cashflow,
            'capex': capex,
            'health_status': health_status,
            'trend': trend_data,
            'as_of_date': current_date.strftime('%Y-%m-%d')
        }), 200
        
    except Exception as e:
        logger.error(f"Error in get_cashflow_widget: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


def get_current_cash_position(year, month):
    """Get current cash balance from GL accounts 110xxx-119xxx"""
    try:
        query = """
        SELECT SUM(MTD) as cash_balance
        FROM ben002.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo LIKE '11%'
        """
        
        result = sql_service.execute_query(query, [year, month])
        
        if result and result[0]:
            return float(result[0].get('cash_balance') or 0)
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting cash position: {str(e)}")
        return 0.0


def get_monthly_operating_cashflow(year, month):
    """
    Calculate operating cash flow for a month using indirect method
    Operating CF = Net Income + Depreciation + Changes in Working Capital
    """
    try:
        # Get Net Income (Revenue - COGS - Expenses)
        net_income = get_monthly_net_income(year, month)
        
        # Get Depreciation (add back - non-cash expense)
        depreciation = get_monthly_depreciation(year, month)
        
        # Get changes in working capital
        # For simplicity, we'll use a basic calculation
        # In a full implementation, you'd compare beginning and ending balances
        working_capital_change = 0  # Simplified for now
        
        operating_cf = net_income + depreciation + working_capital_change
        
        return operating_cf
        
    except Exception as e:
        logger.error(f"Error calculating operating cash flow: {str(e)}")
        return 0.0


def get_monthly_net_income(year, month):
    """Get net income for the month"""
    try:
        # Revenue (4xxxxx accounts - negative because they're credits)
        # COGS (5xxxxx accounts - positive because they're debits)
        # Expenses (6xxxxx accounts - positive because they're debits)
        
        query = """
        SELECT 
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN MTD ELSE 0 END) as revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN MTD ELSE 0 END) as cogs,
            SUM(CASE WHEN AccountNo LIKE '6%' THEN MTD ELSE 0 END) as expenses
        FROM ben002.GL
        WHERE Year = %s
          AND Month = %s
          AND (AccountNo LIKE '4%' OR AccountNo LIKE '5%' OR AccountNo LIKE '6%')
        """
        
        result = sql_service.execute_query(query, [year, month])
        
        if result and result[0]:
            revenue = float(result[0].get('revenue') or 0)
            cogs = float(result[0].get('cogs') or 0)
            expenses = float(result[0].get('expenses') or 0)
            
            net_income = revenue - cogs - expenses
            return net_income
        
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting net income: {str(e)}")
        return 0.0


def get_monthly_depreciation(year, month):
    """Get depreciation expense for the month (account 600900)"""
    try:
        query = """
        SELECT SUM(MTD) as depreciation
        FROM ben002.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo = '600900'
        """
        
        result = sql_service.execute_query(query, [year, month])
        
        if result and result[0]:
            return float(result[0].get('depreciation') or 0)
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting depreciation: {str(e)}")
        return 0.0


def get_monthly_capex(year, month):
    """
    Get capital expenditures for the month
    This would typically come from fixed asset purchases (18xxxx accounts)
    For now, we'll return 0 as a placeholder
    """
    try:
        # In a full implementation, you'd query GLDetail for fixed asset purchases
        # For now, return 0
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting capex: {str(e)}")
        return 0.0


def get_cashflow_trend(year, month, months=6):
    """Get cash flow trend for the last N months"""
    try:
        trend_data = []
        
        for i in range(months - 1, -1, -1):
            # Calculate the target month
            target_month = month - i
            target_year = year
            
            # Handle year rollover
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Get operating cash flow for this month
            cf = get_monthly_operating_cashflow(target_year, target_month)
            
            # Format month label
            month_label = f"{target_year}-{target_month:02d}"
            
            trend_data.append({
                'month': month_label,
                'cashflow': cf
            })
        
        return trend_data
        
    except Exception as e:
        logger.error(f"Error getting cash flow trend: {str(e)}")
        return []
