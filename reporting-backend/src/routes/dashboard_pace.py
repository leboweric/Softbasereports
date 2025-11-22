from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
from datetime import datetime

dashboard_pace_bp = Blueprint('dashboard_pace', __name__)

@dashboard_pace_bp.route('/api/dashboard/sales-pace', methods=['GET'])
@jwt_required()
def get_sales_pace():
    """Get sales and quotes pace data comparing current month to previous month through same day"""
    try:
        db = AzureSQLService()
        
        # Get current date info
        now = datetime.now()
        current_year = now.year
        current_month = now.month
        current_day = now.day
        
        # Calculate previous month
        if current_month == 1:
            prev_month = 12
            prev_year = current_year - 1
        else:
            prev_month = current_month - 1
            prev_year = current_year
        
        # GL Account Mappings (same as dashboard_optimized.py)
        GL_ACCOUNTS = {
            'new_equipment': {
                'revenue': ['410001', '412001', '413001', '414001', '421001', '426001', '431001', '434001'],
                'cogs': ['510001', '513001', '514001', '521001', '525001', '526001', '531001', '534001', '534013', '538000']
            },
            'used_equipment': {
                'revenue': ['410002', '412002', '413002', '414002', '421002', '426002', '431002', '434002', '436001'],
                'cogs': ['510002', '512002', '513002', '514002', '521002', '525002', '526002', '531002', '534002', '536001']
            },
            'parts': {
                'revenue': ['410003', '410012', '410014', '410015', '421003', '424000', '429001', '430000', '433000', '434003', '436002', '439000'],
                'cogs': ['510003', '510012', '510013', '510014', '510015', '521003', '522001', '524000', '529002', '530000', '533000', '534003', '536002', '542000', '543000', '544000']
            },
            'service': {
                'revenue': ['410004', '410005', '410007', '410016', '421004', '421005', '421006', '421007', '423000', '425000', '428000', '429002', '432000', '435000', '435001', '435002', '435003', '435004'],
                'cogs': ['510004', '510005', '510007', '512001', '521004', '521005', '521006', '521007', '522000', '523000', '528000', '529001', '534015', '535001', '535002', '535003', '535004', '535005']
            },
            'rental': {
                'revenue': ['410008', '411001', '419000', '420000', '421000', '434012'],
                'cogs': ['510008', '511001', '519000', '520000', '521008', '534014', '537001', '539000', '545000']
            },
            'transportation': {
                'revenue': ['410010', '421010', '434010', '434013'],
                'cogs': ['510010', '521010', '534010', '534012']
            },
            'administrative': {
                'revenue': ['410011', '421011', '422100', '427000', '434011'],
                'cogs': ['510011', '521011', '522100', '525000', '527000', '532000', '534011', '540000', '541000']
            }
        }
        
        OTHER_INCOME_ACCOUNTS = ['701000', '702000', '703000', '704000', '705000', '706000']
        
        # Collect all revenue accounts
        all_revenue_accounts = []
        for dept in GL_ACCOUNTS.values():
            all_revenue_accounts.extend(dept['revenue'])
        all_revenue_accounts.extend(OTHER_INCOME_ACCOUNTS)
        
        # Collect equipment revenue accounts (new + used)
        equipment_revenue_accounts = []
        equipment_revenue_accounts.extend(GL_ACCOUNTS['new_equipment']['revenue'])
        equipment_revenue_accounts.extend(GL_ACCOUNTS['used_equipment']['revenue'])
        
        # Format for SQL IN clause
        revenue_list = "', '".join(all_revenue_accounts)
        equipment_list = "', '".join(equipment_revenue_accounts)
        
        # Query to get sales using GLDetail (matches dashboard_optimized.py logic)
        current_sales_query = f"""
        SELECT 
            -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as total_sales,
            -SUM(CASE WHEN AccountNo NOT IN ('{equipment_list}') AND AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as sales_no_equipment
        FROM ben002.GLDetail
        WHERE YEAR(EffectiveDate) = {current_year}
            AND MONTH(EffectiveDate) = {current_month}
            AND DAY(EffectiveDate) <= {current_day}
            AND Posted = 1
        """
        
        prev_sales_query = f"""
        SELECT 
            -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as total_sales,
            -SUM(CASE WHEN AccountNo NOT IN ('{equipment_list}') AND AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as sales_no_equipment
        FROM ben002.GLDetail
        WHERE YEAR(EffectiveDate) = {prev_year}
            AND MONTH(EffectiveDate) = {prev_month}
            AND DAY(EffectiveDate) <= {current_day}
            AND Posted = 1
        """
        
        # Execute queries
        current_results = db.execute_query(current_sales_query)
        prev_results = db.execute_query(prev_sales_query)
        
        # Process results
        current_sales = 0
        previous_sales = 0
        current_no_equip = 0
        previous_no_equip = 0
        
        if current_results and len(current_results) > 0:
            current_sales = float(current_results[0]['total_sales'] or 0)
            current_no_equip = float(current_results[0]['sales_no_equipment'] or 0)
            
        if prev_results and len(prev_results) > 0:
            previous_sales = float(prev_results[0]['total_sales'] or 0)
            previous_no_equip = float(prev_results[0]['sales_no_equipment'] or 0)
        
        # Get full month totals for context using GLDetail
        full_month_query = f"""
        SELECT 
            -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as total_sales,
            -SUM(CASE WHEN AccountNo NOT IN ('{equipment_list}') AND AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as sales_no_equipment
        FROM ben002.GLDetail
        WHERE YEAR(EffectiveDate) = {prev_year}
            AND MONTH(EffectiveDate) = {prev_month}
            AND Posted = 1
        """
        
        full_month_results = db.execute_query(full_month_query)
        previous_full_month = float(full_month_results[0]['total_sales'] or 0) if full_month_results else 0
        previous_full_month_no_equip = float(full_month_results[0]['sales_no_equipment'] or 0) if full_month_results else 0
        
        # Get adaptive comparison data using GLDetail
        adaptive_query = f"""
        WITH MonthlyTotals AS (
            SELECT 
                YEAR(EffectiveDate) as year,
                MONTH(EffectiveDate) as month,
                -SUM(CASE WHEN AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as total_sales,
                -SUM(CASE WHEN AccountNo NOT IN ('{equipment_list}') AND AccountNo IN ('{revenue_list}') THEN Amount ELSE 0 END) as sales_no_equipment
            FROM ben002.GLDetail
            WHERE EffectiveDate >= DATEADD(month, -12, GETDATE())
                AND YEAR(EffectiveDate) * 100 + MONTH(EffectiveDate) < {current_year} * 100 + {current_month}
                AND Posted = 1
            GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
        )
        SELECT 
            AVG(total_sales) as avg_monthly_sales,
            AVG(sales_no_equipment) as avg_monthly_sales_no_equip,
            MAX(total_sales) as best_monthly_sales,
            MAX(sales_no_equipment) as best_monthly_sales_no_equip,
            MIN(total_sales) as worst_monthly_sales,
            MIN(sales_no_equipment) as worst_monthly_sales_no_equip,
            COUNT(*) as months_available,
            MAX(CASE WHEN month = {current_month} THEN total_sales END) as same_month_last_year,
            MAX(CASE WHEN month = {current_month} THEN sales_no_equipment END) as same_month_last_year_no_equip
        FROM MonthlyTotals
        """
        
        adaptive_results = db.execute_query(adaptive_query)
        adaptive_data = adaptive_results[0] if adaptive_results else {}
        
        avg_monthly_sales = float(adaptive_data.get('avg_monthly_sales') or 0)
        avg_monthly_sales_no_equip = float(adaptive_data.get('avg_monthly_sales_no_equip') or 0)
        best_monthly_sales = float(adaptive_data.get('best_monthly_sales') or 0)
        best_monthly_sales_no_equip = float(adaptive_data.get('best_monthly_sales_no_equip') or 0)
        worst_monthly_sales = float(adaptive_data.get('worst_monthly_sales') or 0)
        worst_monthly_sales_no_equip = float(adaptive_data.get('worst_monthly_sales_no_equip') or 0)
        months_available = int(adaptive_data.get('months_available') or 0)
        same_month_last_year = float(adaptive_data.get('same_month_last_year') or 0)
        same_month_last_year_no_equip = float(adaptive_data.get('same_month_last_year_no_equip') or 0)
        
        # Calculate multiple pace percentages for adaptive comparison
        # 1. Previous month comparison (existing logic)
        if current_sales > previous_full_month and previous_full_month > 0:
            pace_pct_prev_month = ((current_sales / previous_full_month) - 1) * 100
            comparison_base = "full_previous_month"
        else:
            pace_pct_prev_month = ((current_sales / previous_sales) - 1) * 100 if previous_sales > 0 else 0
            comparison_base = "same_day_previous_month"
            
        if current_no_equip > previous_full_month_no_equip and previous_full_month_no_equip > 0:
            pace_pct_prev_month_no_equip = ((current_no_equip / previous_full_month_no_equip) - 1) * 100
            comparison_base_no_equip = "full_previous_month"
        else:
            pace_pct_prev_month_no_equip = ((current_no_equip / previous_no_equip) - 1) * 100 if previous_no_equip > 0 else 0
            comparison_base_no_equip = "same_day_previous_month"
        
        # Project current month based on pace (calculate BEFORE using in comparisons)
        days_in_month = 31  # Approximate, could be calculated exactly
        projected_total = (current_sales / current_day) * days_in_month if current_day > 0 else 0
        projected_no_equip = (current_no_equip / current_day) * days_in_month if current_day > 0 else 0
        
        # 2. Available months average comparison (use projected total for fair comparison)
        pace_pct_avg = ((projected_total / avg_monthly_sales) - 1) * 100 if avg_monthly_sales > 0 else 0
        pace_pct_avg_no_equip = ((projected_no_equip / avg_monthly_sales_no_equip) - 1) * 100 if avg_monthly_sales_no_equip > 0 else 0
        
        # 3. Same month last year comparison (if available) - use projected total for fair comparison
        pace_pct_same_month_ly = ((projected_total / same_month_last_year) - 1) * 100 if same_month_last_year > 0 else None
        pace_pct_same_month_ly_no_equip = ((projected_no_equip / same_month_last_year_no_equip) - 1) * 100 if same_month_last_year_no_equip > 0 else None
        
        # 4. Performance indicators - use projected total for fair comparison
        is_best_month = projected_total > best_monthly_sales
        is_best_month_no_equip = projected_no_equip > best_monthly_sales_no_equip
        
        # Maintain backward compatibility - use previous month as primary pace
        pace_pct = pace_pct_prev_month
        pace_pct_no_equip = pace_pct_prev_month_no_equip
        
        # Get quotes pace data
        current_quotes_query = f"""
        WITH LatestQuotes AS (
            SELECT 
                WONo,
                MAX(CAST(CreationTime AS DATE)) as latest_quote_date
            FROM ben002.WOQuote
            WHERE YEAR(CreationTime) = {current_year}
                AND MONTH(CreationTime) = {current_month}
                AND DAY(CreationTime) <= {current_day}
                AND Amount > 0
            GROUP BY WONo
        ),
        QuoteTotals AS (
            SELECT 
                lq.WONo,
                SUM(wq.Amount) as wo_total
            FROM LatestQuotes lq
            INNER JOIN ben002.WOQuote wq
                ON lq.WONo = wq.WONo
                AND CAST(wq.CreationTime AS DATE) = lq.latest_quote_date
            WHERE wq.Amount > 0
            GROUP BY lq.WONo
        )
        SELECT SUM(wo_total) as total_quotes
        FROM QuoteTotals
        """
        
        prev_quotes_query = f"""
        WITH LatestQuotes AS (
            SELECT 
                WONo,
                MAX(CAST(CreationTime AS DATE)) as latest_quote_date
            FROM ben002.WOQuote
            WHERE YEAR(CreationTime) = {prev_year}
                AND MONTH(CreationTime) = {prev_month}
                AND DAY(CreationTime) <= {current_day}
                AND Amount > 0
            GROUP BY WONo
        ),
        QuoteTotals AS (
            SELECT 
                lq.WONo,
                SUM(wq.Amount) as wo_total
            FROM LatestQuotes lq
            INNER JOIN ben002.WOQuote wq
                ON lq.WONo = wq.WONo
                AND CAST(wq.CreationTime AS DATE) = lq.latest_quote_date
            WHERE wq.Amount > 0
            GROUP BY lq.WONo
        )
        SELECT SUM(wo_total) as total_quotes
        FROM QuoteTotals
        """
        
        # Execute quotes queries
        current_quotes_results = db.execute_query(current_quotes_query)
        prev_quotes_results = db.execute_query(prev_quotes_query)
        
        # Process quotes results
        current_quotes = float(current_quotes_results[0]['total_quotes'] or 0) if current_quotes_results else 0
        previous_quotes = float(prev_quotes_results[0]['total_quotes'] or 0) if prev_quotes_results else 0
        
        # Calculate quotes pace percentage
        quotes_pace_pct = ((current_quotes / previous_quotes) - 1) * 100 if previous_quotes > 0 else 0
        
        return jsonify({
            'current_month': {
                'year': current_year,
                'month': current_month,
                'day': current_day,
                'sales_to_date': current_sales,
                'sales_no_equipment_to_date': current_no_equip,
                'projected_total': projected_total,
                'projected_no_equipment': projected_no_equip
            },
            'previous_month': {
                'year': prev_year,
                'month': prev_month,
                'sales_through_same_day': previous_sales,
                'sales_no_equipment_through_same_day': previous_no_equip,
                'full_month_total': previous_full_month,
                'full_month_no_equipment': previous_full_month_no_equip
            },
            'pace': {
                # Primary pace (previous month) - for backward compatibility
                'percentage': round(pace_pct, 1),
                'percentage_no_equipment': round(pace_pct_no_equip, 1),
                'ahead_behind': 'ahead' if pace_pct > 0 else 'behind' if pace_pct < 0 else 'on pace',
                'ahead_behind_no_equipment': 'ahead' if pace_pct_no_equip > 0 else 'behind' if pace_pct_no_equip < 0 else 'on pace',
                'comparison_base': comparison_base,
                'comparison_base_no_equipment': comparison_base_no_equip,
                'exceeded_previous_month': current_sales > previous_full_month,
                'exceeded_previous_month_no_equipment': current_no_equip > previous_full_month_no_equip
            },
            'adaptive_comparisons': {
                'available_months_count': months_available,
                'vs_available_average': {
                    'percentage': round(pace_pct_avg, 1) if avg_monthly_sales > 0 else None,
                    'percentage_no_equipment': round(pace_pct_avg_no_equip, 1) if avg_monthly_sales_no_equip > 0 else None,
                    'average_monthly_sales': avg_monthly_sales,
                    'average_monthly_sales_no_equip': avg_monthly_sales_no_equip,
                    'ahead_behind': 'ahead' if pace_pct_avg > 0 else 'behind' if pace_pct_avg < 0 else 'on pace' if avg_monthly_sales > 0 else None,
                    'ahead_behind_no_equipment': 'ahead' if pace_pct_avg_no_equip > 0 else 'behind' if pace_pct_avg_no_equip < 0 else 'on pace' if avg_monthly_sales_no_equip > 0 else None
                },
                'vs_same_month_last_year': {
                    'percentage': round(pace_pct_same_month_ly, 1) if pace_pct_same_month_ly is not None else None,
                    'percentage_no_equipment': round(pace_pct_same_month_ly_no_equip, 1) if pace_pct_same_month_ly_no_equip is not None else None,
                    'last_year_sales': same_month_last_year if same_month_last_year > 0 else None,
                    'last_year_sales_no_equip': same_month_last_year_no_equip if same_month_last_year_no_equip > 0 else None,
                    'ahead_behind': 'ahead' if pace_pct_same_month_ly and pace_pct_same_month_ly > 0 else 'behind' if pace_pct_same_month_ly and pace_pct_same_month_ly < 0 else 'on pace' if pace_pct_same_month_ly is not None else None,
                    'ahead_behind_no_equipment': 'ahead' if pace_pct_same_month_ly_no_equip and pace_pct_same_month_ly_no_equip > 0 else 'behind' if pace_pct_same_month_ly_no_equip and pace_pct_same_month_ly_no_equip < 0 else 'on pace' if pace_pct_same_month_ly_no_equip is not None else None
                },
                'performance_indicators': {
                    'is_best_month_ever': is_best_month,
                    'is_best_month_ever_no_equipment': is_best_month_no_equip,
                    'best_month_sales': best_monthly_sales,
                    'best_month_sales_no_equip': best_monthly_sales_no_equip,
                    'worst_month_sales': worst_monthly_sales,
                    'worst_month_sales_no_equip': worst_monthly_sales_no_equip,
                    'vs_best_percentage': round(((current_sales / best_monthly_sales) - 1) * 100, 1) if best_monthly_sales > 0 else None,
                    'vs_worst_percentage': round(((current_sales / worst_monthly_sales) - 1) * 100, 1) if worst_monthly_sales > 0 else None
                }
            },
            'quotes': {
                'current_month_to_date': current_quotes,
                'previous_month_through_same_day': previous_quotes,
                'pace_percentage': round(quotes_pace_pct, 1),
                'ahead_behind': 'ahead' if quotes_pace_pct > 0 else 'behind' if quotes_pace_pct < 0 else 'on pace'
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get sales pace: {str(e)}'}), 500