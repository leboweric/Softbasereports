"""
P&L (Profit & Loss) Report Route
Generates departmental and consolidated P&L reports using GLDetail with exact GL account mappings
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging
from ..database import sql_service

logger = logging.getLogger(__name__)
pl_report_bp = Blueprint('pl_report', __name__)

# GL Account Mappings by Department
GL_ACCOUNTS = {
    'new_equipment': {
        'dept_code': 10,
        'dept_name': 'New Equipment',
        'revenue': ['412001', '413001', '414001', '421001', '426001', '431001', '434001', '410001'],
        'cogs': ['513001', '514001', '521001', '525001', '526001', '531001', '534001', '538000', '534013', '510001']
    },
    'used_equipment': {
        'dept_code': 20,
        'dept_name': 'Used Equipment',
        'revenue': ['412002', '413002', '414002', '421002', '426002', '431002', '434002', '436001', '410002'],
        'cogs': ['512002', '513002', '514002', '521002', '525002', '526002', '531002', '534002', '536001', '510002']
    },
    'parts': {
        'dept_code': 30,
        'dept_name': 'Parts',
        'revenue': ['421003', '424000', '429001', '430000', '433000', '434003', '410003', '410012', '410013', '410014', '410015', '410016'],
        'cogs': ['510003', '510012', '521003', '522001', '524000', '529002', '530000', '533000', '534003', '510013', '510014', '510015', '510016', '514003', '526003', '531003']
    },
    'service': {
        'dept_code': 40,
        'dept_name': 'Service',
        'revenue': ['421004', '421005', '421006', '421007', '423000', '425000', '428000', '429002', '432000', '434013', '435000', '435001', '435002', '435003', '435004', '410004', '410005', '410007'],
        'cogs': ['510004', '510005', '510007', '521004', '521005', '521006', '521007', '522000', '528000', '529001', '532000', '534015', '535001', '535002', '535003', '535004', '535005', '523000']
    },
    'rental': {
        'dept_code': 60,
        'dept_name': 'Rental',
        'revenue': ['411001', '419000', '420000', '421000', '434012', '410008'],
        'cogs': ['510008', '511001', '519000', '520000', '521008', '534014', '537001', '539000', '545000']
    },
    'transportation': {
        'dept_code': 80,
        'dept_name': 'Transportation',
        'revenue': ['434010', '434013', '421010', '410010'],
        'cogs': ['510010', '534010', '534012', '521010']
    },
    'administrative': {
        'dept_code': 90,
        'dept_name': 'Administrative',
        'revenue': ['422100', '427000', '434011', '421011', '410011'],
        'cogs': ['525000', '527000', '541000', '510011', '522100', '534011', '521011', '536002', '538001']
    }
}

# Expense Account Mappings (all in Administrative department)
EXPENSE_ACCOUNTS = {
    'depreciation': ['600900', '600901', '600902'],
    'salaries_wages': ['602000', '602001', '602300', '602301', '602302', '602600', '602610'],
    'payroll_benefits': ['602701'],
    'rent_facilities': ['600200', '600201', '600300', '601900'],
    'utilities': ['604000'],
    'insurance': ['601700'],
    'marketing': ['600000', '603300'],
    'professional_fees': ['603000'],
    'office_admin': ['600500', '602400', '602900', '603500', '603600'],
    'vehicle_equipment': ['602100', '604100'],
    'interest_finance': ['601800'],
    'other_expenses': [
        '600100', '600400', '600600', '600700', '600800', '601000', '601100', '601200', 
        '601300', '601400', '601500', '601600', '602200', '602500', '602601', '602700', 
        '602800', '603100', '603101', '603102', '603103', '603200', '603400', '603501', 
        '603700', '603800', '603900', '604200', '701000', '702000', '703000', '704000', 
        '705000', '706000', '999999'
    ]
}


def get_department_pl(start_date, end_date, dept_key, include_detail=False):
    """
    Get P&L data for a specific department
    
    Args:
        start_date: Start date for the report
        end_date: End date for the report
        dept_key: Department key from GL_ACCOUNTS
        include_detail: If True, include account-level detail
    
    Returns:
        Dictionary with revenue, cogs, gross_profit, gross_margin, and optionally account details
    """
    try:
        dept_config = GL_ACCOUNTS[dept_key]
        revenue_accounts = dept_config['revenue']
        cogs_accounts = dept_config['cogs']
        
        # Build account lists for SQL IN clause
        all_accounts = revenue_accounts + cogs_accounts
        account_list = "', '".join(all_accounts)
        
        if include_detail:
            # Get account-level detail
            query = f"""
            SELECT 
                AccountNo,
                SUM(ABS(Amount)) as total
            FROM ben002.GLDetail
            WHERE EffectiveDate >= %s 
              AND EffectiveDate <= %s
              AND Posted = 1
              AND AccountNo IN ('{account_list}')
            GROUP BY AccountNo
            """
            
            results = sql_service.execute_query(query, [start_date, end_date])
            
            revenue = 0
            cogs = 0
            revenue_detail = []
            cogs_detail = []
            
            for row in results:
                account_no = row['AccountNo']
                total = float(row['total'] or 0)
                
                if account_no in revenue_accounts:
                    revenue += total
                    revenue_detail.append({'account': account_no, 'amount': total})
                elif account_no in cogs_accounts:
                    cogs += total
                    cogs_detail.append({'account': account_no, 'amount': total})
            
            gross_profit = revenue - cogs
            gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
            
            return {
                'dept_code': dept_config['dept_code'],
                'dept_name': dept_config['dept_name'],
                'revenue': revenue,
                'cogs': cogs,
                'gross_profit': gross_profit,
                'gross_margin': gross_margin,
                'revenue_detail': revenue_detail,
                'cogs_detail': cogs_detail
            }
        else:
            # Get summary only
            revenue_list = "', '".join(revenue_accounts)
            cogs_list = "', '".join(cogs_accounts)
            
            query = f"""
            SELECT 
                SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN ABS(Amount) ELSE 0 END) as revenue,
                SUM(CASE WHEN AccountNo IN ('{cogs_list}') THEN ABS(Amount) ELSE 0 END) as cogs
            FROM ben002.GLDetail
            WHERE EffectiveDate >= %s 
              AND EffectiveDate <= %s
              AND Posted = 1
              AND AccountNo IN ('{account_list}')
            """
            
            results = sql_service.execute_query(query, [start_date, end_date])
            
            if results and len(results) > 0:
                row = results[0]
                revenue = float(row['revenue'] or 0)
                cogs = float(row['cogs'] or 0)
                gross_profit = revenue - cogs
                gross_margin = (gross_profit / revenue * 100) if revenue > 0 else 0
                
                return {
                    'dept_code': dept_config['dept_code'],
                    'dept_name': dept_config['dept_name'],
                    'revenue': revenue,
                    'cogs': cogs,
                    'gross_profit': gross_profit,
                    'gross_margin': gross_margin
                }
        
        return {
            'dept_code': dept_config['dept_code'],
            'dept_name': dept_config['dept_name'],
            'revenue': 0,
            'cogs': 0,
            'gross_profit': 0,
            'gross_margin': 0
        }
        
    except Exception as e:
        logger.error(f"Error fetching P&L for {dept_key}: {str(e)}")
        return None


def get_expense_data(start_date, end_date):
    """
    Get all operating expenses
    
    Args:
        start_date: Start date for the report
        end_date: End date for the report
    
    Returns:
        Dictionary with expense categories and totals
    """
    try:
        # Flatten all expense accounts
        all_expense_accounts = []
        for category_accounts in EXPENSE_ACCOUNTS.values():
            all_expense_accounts.extend(category_accounts)
        
        expense_list = "', '".join(all_expense_accounts)
        
        query = f"""
        SELECT 
            AccountNo,
            SUM(ABS(Amount)) as total
        FROM ben002.GLDetail
        WHERE EffectiveDate >= %s 
          AND EffectiveDate <= %s
          AND Posted = 1
          AND AccountNo IN ('{expense_list}')
        GROUP BY AccountNo
        """
        
        results = sql_service.execute_query(query, [start_date, end_date])
        
        # Organize by category
        expense_data = {}
        total_expenses = 0
        
        for category, accounts in EXPENSE_ACCOUNTS.items():
            category_total = 0
            for row in results:
                if row['AccountNo'] in accounts:
                    category_total += float(row['total'] or 0)
            
            expense_data[category] = category_total
            total_expenses += category_total
        
        expense_data['total_expenses'] = total_expenses
        
        return expense_data
        
    except Exception as e:
        logger.error(f"Error fetching expense data: {str(e)}")
        return {'total_expenses': 0}


@pl_report_bp.route('/api/reports/pl', methods=['GET'])
def get_pl_report():
    """
    Get P&L report with departmental and consolidated views
    
    Query Parameters:
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        view: 'consolidated' or 'departmental' (default: 'consolidated')
    
    Returns:
        JSON with P&L data
    """
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        view = request.args.get('view', 'consolidated')
        
        if not start_date or not end_date:
            return jsonify({
                'success': False,
                'error': 'start_date and end_date are required'
            }), 400
        
        # Validate dates
        try:
            datetime.strptime(start_date, '%Y-%m-%d')
            datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({
                'success': False,
                'error': 'Invalid date format. Use YYYY-MM-DD'
            }), 400
        
        # Check if detail is requested
        include_detail = request.args.get('detail', 'false').lower() == 'true'
        
        # Get data for all departments
        departments = {}
        total_revenue = 0
        total_cogs = 0
        
        for dept_key in GL_ACCOUNTS.keys():
            dept_data = get_department_pl(start_date, end_date, dept_key, include_detail)
            if dept_data:
                departments[dept_key] = dept_data
                total_revenue += dept_data['revenue']
                total_cogs += dept_data['cogs']
        
        # Get expense data
        expenses = get_expense_data(start_date, end_date)
        
        # Calculate consolidated metrics
        total_gross_profit = total_revenue - total_cogs
        gross_margin = (total_gross_profit / total_revenue * 100) if total_revenue > 0 else 0
        operating_profit = total_gross_profit - expenses['total_expenses']
        operating_margin = (operating_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Build response
        response = {
            'success': True,
            'start_date': start_date,
            'end_date': end_date,
            'consolidated': {
                'revenue': total_revenue,
                'cogs': total_cogs,
                'gross_profit': total_gross_profit,
                'gross_margin': gross_margin,
                'operating_expenses': expenses['total_expenses'],
                'operating_profit': operating_profit,
                'operating_margin': operating_margin
            },
            'departments': departments,
            'expenses': expenses
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error generating P&L report: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pl_report_bp.route('/api/reports/pl/mtd', methods=['GET'])
def get_pl_mtd():
    """
    Get Month-to-Date P&L report
    
    Query Parameters:
        year: Year (default: current year)
        month: Month (default: current month)
    
    Returns:
        JSON with MTD P&L data
    """
    try:
        # Get current date
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        month = request.args.get('month', now.month, type=int)
        
        # Calculate MTD date range
        start_date = f"{year}-{month:02d}-01"
        
        # Get last day of month
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
        
        from datetime import timedelta
        last_day = next_month - timedelta(days=1)
        end_date = last_day.strftime('%Y-%m-%d')
        
        # Forward to main P&L endpoint
        request.args = {'start_date': start_date, 'end_date': end_date}
        return get_pl_report()
        
    except Exception as e:
        logger.error(f"Error generating MTD P&L: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@pl_report_bp.route('/api/reports/pl/ytd', methods=['GET'])
def get_pl_ytd():
    """
    Get Year-to-Date P&L report
    
    Query Parameters:
        year: Year (default: current year)
    
    Returns:
        JSON with YTD P&L data
    """
    try:
        # Get current date
        now = datetime.now()
        year = request.args.get('year', now.year, type=int)
        
        # Calculate YTD date range
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
        
        # Forward to main P&L endpoint
        request.args = {'start_date': start_date, 'end_date': end_date}
        return get_pl_report()
        
    except Exception as e:
        logger.error(f"Error generating YTD P&L: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
