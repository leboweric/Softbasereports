"""
Cash Flow Dashboard Widget API
Provides quick cash flow metrics for dashboard display

Updated: Fixed cash position to use Ending balance instead of MTD
Added: Non-operating activities breakdown
Removed: Redundant Free CF and CapEx (always $0)
Fixed: Multi-tenant support - pattern-based account matching for all schemas
"""

from flask import Blueprint, jsonify, request, g
from flask_jwt_extended import jwt_required
from src.utils.tenant_utils import get_tenant_db, get_tenant_schema
from src.services.cache_service import cache_service
from src.config.gl_accounts_loader import get_expense_accounts
from datetime import datetime, timedelta
import logging
import calendar

from flask_jwt_extended import get_jwt_identity
from src.models.user import User

def _get_data_start_date():
    """Get the tenant's data start date. Returns None if no restriction."""
    try:
        if hasattr(g, 'current_organization') and g.current_organization:
            if g.current_organization.data_start_date:
                return g.current_organization.data_start_date
        return None  # No restriction
    except RuntimeError:
        return None


logger = logging.getLogger(__name__)

cashflow_widget_bp = Blueprint('cashflow_widget', __name__)
# sql_service is now obtained via get_tenant_db() for multi-tenant support
_sql_service = None
def get_sql_service():
    return get_tenant_db()
@cashflow_widget_bp.route('/api/cashflow/widget', methods=['GET'])
@jwt_required()
def get_cashflow_widget():
    """
    Get cash flow widget data for dashboard
    Returns current cash balance, operating cash flow, total cash movement, and 13-month trend
    """
    try:
        # Get current date or use provided date
        as_of_date = request.args.get('as_of_date')
        force_refresh = request.args.get('refresh', 'false').lower() == 'true'
        
        if as_of_date:
            current_date = datetime.strptime(as_of_date, '%Y-%m-%d')
        else:
            current_date = datetime.now()
        
        # Use cache with 1-hour TTL
        schema = get_tenant_schema()
        cache_key = f'cashflow_widget:{schema}:{as_of_date or current_date.strftime("%Y-%m-%d")}'
        
        def fetch_cashflow_data():
            return _fetch_cashflow_widget_data(current_date)
        
        result = cache_service.cache_query(cache_key, fetch_cashflow_data, ttl_seconds=3600, force_refresh=force_refresh)
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error in get_cashflow_widget: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def _fetch_cashflow_widget_data(current_date):
    """Internal function to fetch cashflow widget data"""
    # Always use last closed month (previous month)
    # This ensures we show complete month-end data, not partial current month
    last_closed_month = current_date.replace(day=1) - timedelta(days=1)
    current_year = last_closed_month.year
    current_month = last_closed_month.month
    
    # Get current cash balance (ending balance, not MTD)
    cash_balance = get_current_cash_balance(current_year, current_month)
    
    # Get current month operating cash flow
    operating_cf = get_monthly_operating_cashflow(current_year, current_month)
    
    # Get total cash movement for the month
    total_cash_movement = get_total_cash_movement(current_year, current_month)
    
    # Calculate non-operating cash flow (difference)
    non_operating_cf = total_cash_movement - operating_cf
    
    # Get breakdown of non-operating activities
    non_operating_breakdown = get_non_operating_breakdown(current_year, current_month)
    
    # Get 13-month trend (trailing 13 months)
    trend_data = get_cashflow_trend(current_year, current_month, months=13)
    
    # Determine health status based on operating CF
    health_status = 'healthy' if operating_cf > 0 else 'warning' if operating_cf > -50000 else 'critical'
    
    return {
        'cash_balance': cash_balance,
        'operating_cashflow': operating_cf,
        'total_cash_movement': total_cash_movement,
        'non_operating_cashflow': non_operating_cf,
        'non_operating_breakdown': non_operating_breakdown,
        'health_status': health_status,
        'trend': trend_data,
        'as_of_date': last_closed_month.strftime('%Y-%m-%d')
    }


def get_current_cash_balance(year, month):
    """
    Get current cash balance from GL cash accounts.
    Uses YTD (Year-To-Date balance) which represents the ending balance for balance sheet accounts.
    Uses pattern matching (AccountNo LIKE '11%') to work across all tenant schemas:
      - Bennett: 110000, 113000, 114000 (6-digit)
      - IPS: 11xxxxx (7-digit)
    """
    try:
        schema = get_tenant_schema()

        query = f"""
        SELECT SUM(YTD) as cash_balance
        FROM {schema}.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo LIKE '11%'
        """
        
        result = get_sql_service().execute_query(query, [year, month])
        
        if result and result[0]:
            return float(result[0].get('cash_balance') or 0)
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting cash balance: {str(e)}")
        return 0.0


def get_total_cash_movement(year, month):
    """
    Get total change in cash for the month.
    This is the MTD (Ending - Beginning) for cash accounts.
    Uses pattern matching to work across all tenant schemas.
    """
    try:
        schema = get_tenant_schema()

        query = f"""
        SELECT SUM(MTD) as cash_movement
        FROM {schema}.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo LIKE '11%'
        """
        
        result = get_sql_service().execute_query(query, [year, month])
        
        if result and result[0]:
            return float(result[0].get('cash_movement') or 0)
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting total cash movement: {str(e)}")
        return 0.0


def get_non_operating_breakdown(year, month):
    """
    Break down non-operating cash flows by category
    Shows where the difference between total cash movement and operating CF comes from
    """
    try:
        schema = get_tenant_schema()

        query = f"""
        SELECT 
            CASE 
                -- Working Capital Changes
                WHEN AccountNo LIKE '12%' THEN 'Accounts Receivable'
                WHEN AccountNo LIKE '13%' THEN 'Inventory'
                WHEN AccountNo LIKE '14%' THEN 'Other Current Assets'
                WHEN AccountNo LIKE '20%' THEN 'Accounts Payable'
                WHEN AccountNo LIKE '21%' THEN 'Other Current Liabilities'
                
                -- Investing Activities
                WHEN AccountNo LIKE '18%' THEN 'Equipment/Fixed Assets'
                WHEN AccountNo LIKE '19%' THEN 'Accumulated Depreciation'
                
                -- Financing Activities
                WHEN AccountNo LIKE '22%' THEN 'Long-term Debt'
                WHEN AccountNo LIKE '23%' THEN 'Notes Payable'
                WHEN AccountNo LIKE '30%' THEN 'Owner Equity'
                WHEN AccountNo LIKE '31%' THEN 'Retained Earnings'
                WHEN AccountNo LIKE '32%' THEN 'Distributions'
                
                -- Other
                ELSE 'Other'
            END as category,
            
            CASE 
                WHEN AccountNo LIKE '12%' OR AccountNo LIKE '13%' OR AccountNo LIKE '14%' 
                     OR AccountNo LIKE '20%' OR AccountNo LIKE '21%' THEN 'Working Capital'
                WHEN AccountNo LIKE '18%' OR AccountNo LIKE '19%' THEN 'Investing'
                WHEN AccountNo LIKE '22%' OR AccountNo LIKE '23%' OR AccountNo LIKE '30%' 
                     OR AccountNo LIKE '31%' OR AccountNo LIKE '32%' THEN 'Financing'
                ELSE 'Other'
            END as activity_type,
            
            SUM(MTD) as amount,
            COUNT(*) as account_count
            
        FROM {schema}.GL
        WHERE Year = %s
          AND Month = %s
          -- Exclude cash accounts (we're analyzing what changed cash)
          AND AccountNo NOT LIKE '11%'
          -- Exclude income statement accounts (already in Operating CF)
          AND AccountNo NOT LIKE '4%'  -- Revenue
          AND AccountNo NOT LIKE '5%'  -- COGS
          AND AccountNo NOT LIKE '6%'  -- Expenses
          -- Only include accounts with activity
          AND MTD != 0
        GROUP BY 
            CASE 
                WHEN AccountNo LIKE '12%' THEN 'Accounts Receivable'
                WHEN AccountNo LIKE '13%' THEN 'Inventory'
                WHEN AccountNo LIKE '14%' THEN 'Other Current Assets'
                WHEN AccountNo LIKE '20%' THEN 'Accounts Payable'
                WHEN AccountNo LIKE '21%' THEN 'Other Current Liabilities'
                WHEN AccountNo LIKE '18%' THEN 'Equipment/Fixed Assets'
                WHEN AccountNo LIKE '19%' THEN 'Accumulated Depreciation'
                WHEN AccountNo LIKE '22%' THEN 'Long-term Debt'
                WHEN AccountNo LIKE '23%' THEN 'Notes Payable'
                WHEN AccountNo LIKE '30%' THEN 'Owner Equity'
                WHEN AccountNo LIKE '31%' THEN 'Retained Earnings'
                WHEN AccountNo LIKE '32%' THEN 'Distributions'
                ELSE 'Other'
            END,
            CASE 
                WHEN AccountNo LIKE '12%' OR AccountNo LIKE '13%' OR AccountNo LIKE '14%' 
                     OR AccountNo LIKE '20%' OR AccountNo LIKE '21%' THEN 'Working Capital'
                WHEN AccountNo LIKE '18%' OR AccountNo LIKE '19%' THEN 'Investing'
                WHEN AccountNo LIKE '22%' OR AccountNo LIKE '23%' OR AccountNo LIKE '30%' 
                     OR AccountNo LIKE '31%' OR AccountNo LIKE '32%' THEN 'Financing'
                ELSE 'Other'
            END
        ORDER BY ABS(SUM(MTD)) DESC
        """
        
        result = get_sql_service().execute_query(query, [year, month])
        
        if not result:
            return {
                'breakdown': [],
                'summary': {
                    'working_capital': 0,
                    'investing': 0,
                    'financing': 0,
                    'other': 0
                }
            }
        
        # Organize results
        breakdown = []
        summary = {
            'working_capital': 0,
            'investing': 0,
            'financing': 0,
            'other': 0
        }
        
        for row in result:
            category = row.get('category', 'Other')
            activity_type = row.get('activity_type', 'Other')
            amount = float(row.get('amount') or 0)
            account_count = int(row.get('account_count') or 0)
            
            breakdown.append({
                'category': category,
                'activity_type': activity_type,
                'amount': amount,
                'account_count': account_count
            })
            
            # Add to summary
            if activity_type == 'Working Capital':
                summary['working_capital'] += amount
            elif activity_type == 'Investing':
                summary['investing'] += amount
            elif activity_type == 'Financing':
                summary['financing'] += amount
            else:
                summary['other'] += amount
        
        return {
            'breakdown': breakdown,
            'summary': summary
        }
        
    except Exception as e:
        logger.error(f"Error getting non-operating breakdown: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            'breakdown': [],
            'summary': {
                'working_capital': 0,
                'investing': 0,
                'financing': 0,
                'other': 0
            }
        }


def get_monthly_operating_cashflow(year, month):
    """
    Calculate operating cash flow for a month using indirect method
    Operating CF = Net Income + Depreciation + Changes in Working Capital
    Note: Working capital changes set to 0 (simplified)
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
        
        schema = get_tenant_schema()

        
        query = f"""
        SELECT 
            -SUM(CASE WHEN AccountNo LIKE '4%' THEN MTD ELSE 0 END) as revenue,
            SUM(CASE WHEN AccountNo LIKE '5%' THEN MTD ELSE 0 END) as cogs,
            SUM(CASE WHEN AccountNo LIKE '6%' THEN MTD ELSE 0 END) as expenses
        FROM {schema}.GL
        WHERE Year = %s
          AND Month = %s
          AND (AccountNo LIKE '4%' OR AccountNo LIKE '5%' OR AccountNo LIKE '6%')
        """
        
        result = get_sql_service().execute_query(query, [year, month])
        
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
    """
    Get depreciation expense for the month.
    Uses tenant-aware depreciation accounts from gl_accounts_loader.
    """
    try:
        schema = get_tenant_schema()
        
        # Get tenant-specific depreciation accounts
        expense_accounts = get_expense_accounts(schema)
        depreciation_accounts = expense_accounts.get('depreciation', [])
        
        if not depreciation_accounts:
            logger.warning(f"No depreciation accounts configured for schema {schema}")
            return 0.0
        
        # Build IN clause with the tenant's depreciation accounts
        placeholders = ', '.join([f"'{acc}'" for acc in depreciation_accounts])

        query = f"""
        SELECT SUM(MTD) as depreciation
        FROM {schema}.GL
        WHERE Year = %s
          AND Month = %s
          AND AccountNo IN ({placeholders})
        """
        
        result = get_sql_service().execute_query(query, [year, month])
        
        if result and result[0]:
            return float(result[0].get('depreciation') or 0)
        return 0.0
        
    except Exception as e:
        logger.error(f"Error getting depreciation: {str(e)}")
        return 0.0


def get_cashflow_trend(year, month, months=13):
    """
    Get cash balance trend for trailing months.
    Uses tenant's data_start_date to determine the earliest month to include.
    """
    try:
        trend_data = []
        
        # Get tenant's data start date (None = no restriction)
        data_start = _get_data_start_date()
        
        for i in range(months - 1, -1, -1):
            # Calculate the target month
            target_month = month - i
            target_year = year
            
            # Handle year rollover
            while target_month <= 0:
                target_month += 12
                target_year -= 1
            
            # Skip months before the tenant's data start date (if set)
            if data_start:
                if target_year < data_start.year or (target_year == data_start.year and target_month < data_start.month):
                    continue
            
            # Get cash balance for this month (ending balance)
            cash_balance = get_current_cash_balance(target_year, target_month)
            
            # Format month label
            month_label = f"{target_year}-{target_month:02d}"
            
            trend_data.append({
                'month': month_label,
                'cashflow': cash_balance  # Keep field name for frontend compatibility
            })
        
        return trend_data
        
    except Exception as e:
        logger.error(f"Error getting cash balance trend: {str(e)}")
        return []
