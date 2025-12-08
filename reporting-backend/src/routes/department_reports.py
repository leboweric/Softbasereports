# Department-specific report endpoints
# Version 1.0.1 - Added Guaranteed Maintenance profitability endpoint
from flask import jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from flask import request
from src.services.azure_sql_service import AzureSQLService
from src.utils.auth_decorators import require_permission, require_department
from src.utils.fiscal_year import get_fiscal_year_months, get_fiscal_year_start_month
import json
import logging

logger = logging.getLogger(__name__)

# Salesman name aliases - maps variant names to canonical names
# This handles cases where the same person has multiple entries in Softbase
SALESMAN_ALIASES = {
    'Tod Auge': 'Todd Auge',
    # Add more aliases here as needed, e.g.:
    # 'Bob Smith': 'Robert Smith',
}

def normalize_salesman_name(name):
    """Normalize salesman name using alias mapping"""
    if name is None:
        return name
    return SALESMAN_ALIASES.get(name, name)

def get_db():
    """Get database connection"""
    return AzureSQLService()


def register_department_routes(reports_bp):
    """Register department report routes with the reports blueprint"""
    
    @reports_bp.route('/departments/service/pace', methods=['GET'])
    @require_permission('view_service')
    def get_service_pace():
        """Get service department revenue pace comparing current month to previous month"""
        try:
            db = get_db()
            
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
            
            # Get service revenue through same day for current and previous month
            # Using LaborTaxable + LaborNonTax to match the main labor revenue query
            current_query = f"""
            SELECT SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {current_year}
                AND MONTH(InvoiceDate) = {current_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND (COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) > 0
            """
            
            prev_query = f"""
            SELECT SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND (COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) > 0
            """
            
            # Get full previous month total for comparison
            full_month_query = f"""
            SELECT SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND (COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) > 0
            """
            
            # Get adaptive comparison data
            adaptive_query = f"""
            WITH MonthlyTotals AS (
                SELECT 
                    YEAR(InvoiceDate) as year,
                    MONTH(InvoiceDate) as month,
                    SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as total_revenue
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
                    AND YEAR(InvoiceDate) * 100 + MONTH(InvoiceDate) < {current_year} * 100 + {current_month}
                    AND (COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) > 0
                GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            )
            SELECT 
                AVG(total_revenue) as avg_monthly_revenue,
                MAX(total_revenue) as best_monthly_revenue,
                MIN(total_revenue) as worst_monthly_revenue,
                COUNT(*) as months_available,
                MAX(CASE WHEN month = {current_month} THEN total_revenue END) as same_month_last_year
            FROM MonthlyTotals
            """
            
            current_result = db.execute_query(current_query)
            prev_result = db.execute_query(prev_query)
            full_month_result = db.execute_query(full_month_query)
            adaptive_result = db.execute_query(adaptive_query)
            
            current_revenue = float(current_result[0]['total_revenue'] or 0) if current_result else 0
            previous_revenue = float(prev_result[0]['total_revenue'] or 0) if prev_result else 0
            previous_full_month = float(full_month_result[0]['total_revenue'] or 0) if full_month_result else 0
            
            # Extract adaptive data
            adaptive_data = adaptive_result[0] if adaptive_result else {}
            avg_monthly_revenue = float(adaptive_data.get('avg_monthly_revenue') or 0)
            best_monthly_revenue = float(adaptive_data.get('best_monthly_revenue') or 0)
            worst_monthly_revenue = float(adaptive_data.get('worst_monthly_revenue') or 0)
            months_available = int(adaptive_data.get('months_available') or 0)
            same_month_last_year = float(adaptive_data.get('same_month_last_year') or 0)
            
            # Calculate multiple pace percentages for adaptive comparison
            # 1. Previous month comparison (existing logic)
            if current_revenue > previous_full_month and previous_full_month > 0:
                pace_percentage = round(((current_revenue / previous_full_month) - 1) * 100, 1)
                comparison_base = "full_previous_month"
            else:
                pace_percentage = round(((current_revenue / previous_revenue) - 1) * 100, 1) if previous_revenue > 0 else 0
                comparison_base = "same_day_previous_month"
            
            # Calculate projected month total for fair comparison
            import calendar
            days_in_month = calendar.monthrange(current_year, current_month)[1]
            projected_revenue = (current_revenue / current_day) * days_in_month if current_day > 0 else 0
            
            # 2. Additional adaptive comparisons (use projected total for fair comparison)
            pace_pct_avg = round(((projected_revenue / avg_monthly_revenue) - 1) * 100, 1) if avg_monthly_revenue > 0 else None
            pace_pct_same_month_ly = round(((projected_revenue / same_month_last_year) - 1) * 100, 1) if same_month_last_year > 0 else None
            is_best_month = projected_revenue > best_monthly_revenue
            
            return jsonify({
                'pace_percentage': pace_percentage,
                'current_revenue': current_revenue,
                'previous_revenue': previous_revenue,
                'previous_full_month': previous_full_month,
                'current_month': current_month,
                'current_day': current_day,
                'comparison_base': comparison_base,
                'exceeded_previous_month': current_revenue > previous_full_month,
                'adaptive_comparisons': {
                    'available_months_count': months_available,
                    'vs_available_average': {
                        'percentage': pace_pct_avg,
                        'average_monthly_revenue': avg_monthly_revenue,
                        'ahead_behind': 'ahead' if pace_pct_avg and pace_pct_avg > 0 else 'behind' if pace_pct_avg and pace_pct_avg < 0 else 'on pace' if pace_pct_avg is not None else None
                    },
                    'vs_same_month_last_year': {
                        'percentage': pace_pct_same_month_ly,
                        'last_year_revenue': same_month_last_year if same_month_last_year > 0 else None,
                        'ahead_behind': 'ahead' if pace_pct_same_month_ly and pace_pct_same_month_ly > 0 else 'behind' if pace_pct_same_month_ly and pace_pct_same_month_ly < 0 else 'on pace' if pace_pct_same_month_ly is not None else None
                    },
                    'performance_indicators': {
                        'is_best_month_ever': is_best_month,
                        'best_month_revenue': best_monthly_revenue,
                        'worst_month_revenue': worst_monthly_revenue,
                        'vs_best_percentage': round(((current_revenue / best_monthly_revenue) - 1) * 100, 1) if best_monthly_revenue > 0 else None,
                        'vs_worst_percentage': round(((current_revenue / worst_monthly_revenue) - 1) * 100, 1) if worst_monthly_revenue > 0 else None
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching service pace: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/parts/open-work-orders', methods=['GET'])
    @require_permission('view_parts_work_orders', 'view_parts')
    def get_parts_open_work_orders():
        """Get open Parts work orders summary"""
        try:
            from src.routes.dashboard_optimized import DashboardQueries
            db = get_db()
            queries = DashboardQueries(db)
            
            result = queries.get_open_parts_work_orders()
            return jsonify(result)
            
        except Exception as e:
            logger.error(f"Error fetching open parts work orders: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/parts/open-work-orders-details', methods=['GET'])
    @require_permission('view_parts_work_orders', 'view_parts')
    def get_parts_open_work_orders_details():
        """Get detailed list of open Parts work orders"""
        try:
            db = get_db()
            
            query = """
            SELECT 
                w.WONo,
                w.Type,
                w.OpenDate,
                w.BillTo,
                c.Name as CustomerName,
                DATEDIFF(day, w.OpenDate, GETDATE()) as DaysSinceOpened,
                COALESCE(p.parts_count, 0) as parts_count,
                COALESCE(p.parts_list, '') as parts_list,
                COALESCE(p.parts_total, 0) as parts_total,
                COALESCE(m.misc_total, 0) as misc_total,
                COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0) as total_value
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.Number
            LEFT JOIN (
                SELECT 
                    WONo, 
                    COUNT(DISTINCT PartNo) as parts_count,
                    STRING_AGG(CAST(PartNo + ' (' + CAST(CAST(Qty AS INT) AS VARCHAR) + ')' AS VARCHAR(MAX)), ', ') 
                        WITHIN GROUP (ORDER BY PartNo) as parts_list,
                    SUM(Sell * Qty) as parts_total 
                FROM ben002.WOParts 
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_total 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            WHERE w.ClosedDate IS NULL
              AND w.DeletionTime IS NULL
              AND w.Type = 'P'
              AND w.WONo NOT LIKE '91%'  -- Exclude quotes (quotes start with 91)
            ORDER BY w.OpenDate ASC
            """
            
            results = db.execute_query(query)
            
            work_orders = []
            if results:
                for row in results:
                    work_orders.append({
                        'wo_number': row['WONo'],
                        'type': row['Type'],
                        'open_date': row['OpenDate'].strftime('%Y-%m-%d') if row['OpenDate'] else None,
                        'bill_to': row['BillTo'],
                        'customer_name': row['CustomerName'] or 'Unknown',
                        'parts_count': int(row['parts_count']),
                        'parts_list': row['parts_list'] or 'No parts',
                        'days_open': int(row['DaysSinceOpened']),
                        'parts_total': float(row['parts_total'] or 0),
                        'misc_total': float(row['misc_total'] or 0),
                        'total_value': float(row['total_value'] or 0)
                    })
            
            # Calculate summary stats
            total_count = len(work_orders)
            total_value = sum(wo['total_value'] for wo in work_orders)
            avg_days_open = sum(wo['days_open'] for wo in work_orders) / total_count if total_count > 0 else 0
            over_seven_days = sum(1 for wo in work_orders if wo['days_open'] > 7)
            over_fourteen_days = sum(1 for wo in work_orders if wo['days_open'] > 14)
            over_thirty_days = sum(1 for wo in work_orders if wo['days_open'] > 30)
            
            return jsonify({
                'summary': {
                    'count': total_count,
                    'total_value': total_value,
                    'avg_days_open': int(avg_days_open),
                    'over_7_days': over_seven_days,
                    'over_14_days': over_fourteen_days,
                    'over_30_days': over_thirty_days
                },
                'work_orders': work_orders
            })
            
        except Exception as e:
            logger.error(f"Error fetching open parts work order details: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/parts/work-order-status', methods=['GET'])
    @jwt_required()
    def get_parts_wo_status():
        """Diagnostic endpoint to check Parts work order status"""
        try:
            db = get_db()
            
            # First query for counts
            count_query = """
            SELECT 
                COUNT(*) as total_count,
                COUNT(CASE WHEN Type = 'P' THEN 1 END) as parts_count,
                COUNT(CASE WHEN Type = 'P' AND CompletedDate IS NOT NULL THEN 1 END) as parts_completed,
                COUNT(CASE WHEN Type = 'P' AND ClosedDate IS NOT NULL THEN 1 END) as parts_closed,
                COUNT(CASE WHEN Type = 'P' AND InvoiceDate IS NOT NULL THEN 1 END) as parts_invoiced,
                COUNT(CASE WHEN Type = 'P' AND CompletedDate IS NOT NULL AND ClosedDate IS NULL THEN 1 END) as parts_awaiting_invoice
            FROM ben002.WO
            WHERE DeletionTime IS NULL
            """
            
            # Second query for open parts value
            value_query = """
            SELECT 
                SUM(COALESCE(p.parts_total, 0) + COALESCE(m.misc_total, 0)) as open_parts_value
            FROM ben002.WO w
            LEFT JOIN (
                SELECT WONo, SUM(Sell * Qty) as parts_total
                FROM ben002.WOParts
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_total
                FROM ben002.WOMisc
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            WHERE w.Type = 'P' 
            AND w.ClosedDate IS NULL
            AND w.DeletionTime IS NULL
            AND w.WONo NOT LIKE '91%'  -- Exclude quotes (quotes start with 91)
            """
            
            count_result = db.execute_query(count_query)
            value_result = db.execute_query(value_query)
            
            # Combine results
            result = count_result[0] if count_result else {}
            if value_result and value_result[0]:
                result['open_parts_value'] = value_result[0]['open_parts_value'] or 0
            else:
                result['open_parts_value'] = 0
            
            # Also get a sample of Parts work orders
            sample_query = """
            SELECT TOP 10 
                WONo,
                Type,
                OpenDate,
                CompletedDate,
                ClosedDate,
                InvoiceDate,
                BillTo,
                CASE 
                    WHEN CompletedDate IS NULL THEN 'Open'
                    WHEN ClosedDate IS NULL THEN 'Awaiting Invoice'
                    ELSE 'Closed/Invoiced'
                END as Status
            FROM ben002.WO
            WHERE Type = 'P' AND DeletionTime IS NULL
            AND WONo NOT LIKE '91%'  -- Exclude quotes (quotes start with 91)
            ORDER BY WONo DESC
            """
            
            samples = db.execute_query(sample_query)
            
            return jsonify({
                'summary': result,
                'sample_work_orders': samples if samples else []
            })
            
        except Exception as e:
            logger.error(f"Error checking parts work order status: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/parts/awaiting-invoice-details', methods=['GET'])
    @jwt_required()
    def get_parts_awaiting_invoice_details():
        """Get detailed list of Parts work orders awaiting invoice"""
        try:
            db = get_db()
            
            query = """
            SELECT 
                w.WONo,
                w.Type,
                w.CompletedDate,
                w.BillTo,
                c.Name as CustomerName,
                w.UnitNo,
                e.Make,
                e.Model,
                w.Technician,
                DATEDIFF(day, w.CompletedDate, GETDATE()) as DaysSinceCompleted,
                COALESCE(p.parts_sell, 0) as parts_total,
                COALESCE(m.misc_sell, 0) as misc_total,
                COALESCE(p.parts_sell, 0) + COALESCE(m.misc_sell, 0) as total_value
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.Number
            LEFT JOIN ben002.Equipment e ON w.UnitNo = e.UnitNo
            LEFT JOIN (
                SELECT WONo, SUM(Sell * Qty) as parts_sell 
                FROM ben002.WOParts 
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_sell 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            WHERE w.CompletedDate IS NOT NULL
              AND w.ClosedDate IS NULL
              AND w.InvoiceDate IS NULL
              AND w.DeletionTime IS NULL
              AND w.Type = 'P'
              AND w.WONo NOT LIKE '91%'  -- Exclude quotes (quotes start with 91)
            ORDER BY w.CompletedDate ASC
            """
            
            results = db.execute_query(query)
            
            work_orders = []
            if results:
                for row in results:
                    work_orders.append({
                        'wo_number': row['WONo'],
                        'type': row['Type'],
                        'completed_date': row['CompletedDate'].strftime('%Y-%m-%d') if row['CompletedDate'] else None,
                        'bill_to': row['BillTo'],
                        'customer_name': row['CustomerName'] or 'Unknown',
                        'unit_no': row['UnitNo'],
                        'make': row['Make'],
                        'model': row['Model'],
                        'technician': row['Technician'],
                        'days_waiting': int(row['DaysSinceCompleted']),
                        'parts_total': float(row['parts_total'] or 0),
                        'misc_total': float(row['misc_total'] or 0),
                        'total_value': float(row['total_value'] or 0)
                    })
            
            # Calculate summary stats
            total_count = len(work_orders)
            total_value = sum(wo['total_value'] for wo in work_orders)
            avg_days = sum(wo['days_waiting'] for wo in work_orders) / total_count if total_count > 0 else 0
            
            return jsonify({
                'work_orders': work_orders,
                'summary': {
                    'count': total_count,
                    'total_value': total_value,
                    'avg_days_waiting': round(avg_days, 1),
                    'over_3_days': len([wo for wo in work_orders if wo['days_waiting'] > 3]),
                    'over_5_days': len([wo for wo in work_orders if wo['days_waiting'] > 5]),
                    'over_7_days': len([wo for wo in work_orders if wo['days_waiting'] > 7])
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching parts awaiting invoice details: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/work-order-types', methods=['GET'])
    @jwt_required()
    def get_all_work_order_types():
        """Get all unique work order types from the database"""
        try:
            db = get_db()
            
            query = """
            SELECT DISTINCT 
                Type,
                COUNT(*) as count
            FROM ben002.WO
            WHERE Type IS NOT NULL
            GROUP BY Type
            ORDER BY COUNT(*) DESC
            """
            
            results = db.execute_query(query)
            
            types_list = []
            if results:
                for row in results:
                    types_list.append({
                        'type': row['Type'],
                        'count': int(row['count']),
                        'description': {
                            'S': 'Service',
                            'R': 'Rental',
                            'P': 'Parts',
                            'PM': 'Preventive Maintenance',
                            'SH': 'Shop',
                            'E': 'Equipment',
                            'I': 'Internal',
                            'W': 'Warranty'
                        }.get(row['Type'], f'Unknown ({row["Type"]})')
                    })
            
            return jsonify({
                'work_order_types': types_list,
                'total_types': len(types_list)
            })
            
        except Exception as e:
            logger.error(f"Error fetching work order types: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/service/awaiting-invoice-details', methods=['GET'])
    @jwt_required()
    def get_service_awaiting_invoice_details():
        """Get detailed list of Service, Shop, and PM work orders awaiting invoice"""
        try:
            db = get_db()
            
            query = """
            SELECT 
                w.WONo,
                w.Type,
                w.CompletedDate,
                w.BillTo,
                c.Name as CustomerName,
                w.UnitNo,
                e.Make,
                e.Model,
                w.Technician,
                DATEDIFF(day, w.CompletedDate, GETDATE()) as DaysSinceCompleted,
                -- Include labor quotes for flat rate labor
                COALESCE(l.labor_sell, 0) + COALESCE(lq.quote_amount, 0) as labor_total,
                COALESCE(p.parts_sell, 0) as parts_total,
                COALESCE(m.misc_sell, 0) as misc_total,
                COALESCE(l.labor_sell, 0) + COALESCE(lq.quote_amount, 0) + 
                COALESCE(p.parts_sell, 0) + COALESCE(m.misc_sell, 0) as total_value
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.Number
            LEFT JOIN ben002.Equipment e ON w.UnitNo = e.UnitNo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as labor_sell 
                FROM ben002.WOLabor 
                GROUP BY WONo
            ) l ON w.WONo = l.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Amount) as quote_amount 
                FROM ben002.WOQuote 
                WHERE Type = 'L'
                GROUP BY WONo
            ) lq ON w.WONo = lq.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell * Qty) as parts_sell 
                FROM ben002.WOParts 
                GROUP BY WONo
            ) p ON w.WONo = p.WONo
            LEFT JOIN (
                SELECT WONo, SUM(Sell) as misc_sell 
                FROM ben002.WOMisc 
                GROUP BY WONo
            ) m ON w.WONo = m.WONo
            WHERE w.CompletedDate IS NOT NULL
              AND w.ClosedDate IS NULL
              AND w.InvoiceDate IS NULL
              AND w.DeletionTime IS NULL
              AND w.Type IN ('S', 'SH', 'PM')
              AND c.Name NOT IN (
                'NEW EQUIP PREP - EXPENSE',
                'RENTAL FLEET - EXPENSE', 
                'USED EQUIP. PREP-EXPENSE',
                'SVC REWORK/SVC WARRANTY',
                'NEW EQ. INTNL RNTL/DEMO'
              )  -- Exclude internal expense accounts
            ORDER BY w.CompletedDate ASC
            """
            
            results = db.execute_query(query)
            
            work_orders = []
            if results:
                for row in results:
                    work_orders.append({
                        'wo_number': row['WONo'],
                        'type': row['Type'],
                        'completed_date': row['CompletedDate'].strftime('%Y-%m-%d') if row['CompletedDate'] else None,
                        'bill_to': row['BillTo'],
                        'customer_name': row['CustomerName'] or 'Unknown',
                        'unit_no': row['UnitNo'],
                        'make': row['Make'],
                        'model': row['Model'],
                        'technician': row['Technician'],
                        'days_waiting': int(row['DaysSinceCompleted']),
                        'labor_total': float(row['labor_total'] or 0),
                        'parts_total': float(row['parts_total'] or 0),
                        'misc_total': float(row['misc_total'] or 0),
                        'total_value': float(row['total_value'] or 0)
                    })
            
            # Calculate summary stats
            total_count = len(work_orders)
            total_value = sum(wo['total_value'] for wo in work_orders)
            avg_days = sum(wo['days_waiting'] for wo in work_orders) / total_count if total_count > 0 else 0
            
            return jsonify({
                'work_orders': work_orders,
                'summary': {
                    'count': total_count,
                    'total_value': total_value,
                    'avg_days_waiting': round(avg_days, 1),
                    'over_3_days': len([wo for wo in work_orders if wo['days_waiting'] > 3]),
                    'over_5_days': len([wo for wo in work_orders if wo['days_waiting'] > 5]),
                    'over_7_days': len([wo for wo in work_orders if wo['days_waiting'] > 7])
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching service awaiting invoice details: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/service', methods=['GET'])
    @jwt_required()
    def get_service_department_report():
        """Get Service Department report data"""
        try:
            db = get_db()
            
            # Monthly Labor Revenue and Margins - Last 12 months
            # Using GLDetail for 100% accurate P&L matching
            # Revenue: GL 410004 (Field) + GL 410005 (Shop)
            # Cost: GL 510004 (Field Cost) + GL 510005 (Shop Cost)
            labor_revenue_query = """
            SELECT 
                YEAR(EffectiveDate) as year,
                MONTH(EffectiveDate) as month,
                -- Combined revenue
                ABS(SUM(CASE WHEN AccountNo IN ('410004', '410005') THEN Amount ELSE 0 END)) as labor_revenue,
                ABS(SUM(CASE WHEN AccountNo IN ('510004', '510005') THEN Amount ELSE 0 END)) as labor_cost,
                -- Field (410004 / 510004)
                ABS(SUM(CASE WHEN AccountNo = '410004' THEN Amount ELSE 0 END)) as field_revenue,
                ABS(SUM(CASE WHEN AccountNo = '510004' THEN Amount ELSE 0 END)) as field_cost,
                -- Shop (410005 / 510005)
                ABS(SUM(CASE WHEN AccountNo = '410005' THEN Amount ELSE 0 END)) as shop_revenue,
                ABS(SUM(CASE WHEN AccountNo = '510005' THEN Amount ELSE 0 END)) as shop_cost
            FROM ben002.GLDetail
            WHERE AccountNo IN ('410004', '410005', '510004', '510005')
                AND EffectiveDate >= DATEADD(month, -13, GETDATE())
                AND Posted = 1
            GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            """
            
            labor_revenue_result = db.execute_query(labor_revenue_query)
            
            monthlyLaborRevenue = []
            monthlyFieldRevenue = []
            monthlyShopRevenue = []
            
            # Create a dictionary to store data by year-month key
            revenue_by_month = {}
            for row in labor_revenue_result:
                year_month_key = (row['year'], row['month'])
                revenue_by_month[year_month_key] = row
            
            # Get fiscal year months (12 consecutive months starting with fiscal year start)
            fiscal_year_months = get_fiscal_year_months()
            
            # Generate data for each fiscal year month
            for year, month in fiscal_year_months:
                month_date = datetime(year, month, 1)
                # Include year in label if spanning multiple calendar years
                if fiscal_year_months[0][0] != fiscal_year_months[-1][0]:
                    month_str = month_date.strftime("%b '%y")
                else:
                    month_str = month_date.strftime("%b")
                year_month_key = (year, month)
                prior_year_key = (year - 1, month)  # Same month, previous year
                
                # Get data for this month if it exists
                row = revenue_by_month.get(year_month_key)
                prior_row = revenue_by_month.get(prior_year_key)
                
                if row:
                    # Combined
                    labor_revenue = float(row['labor_revenue'] or 0)
                    labor_cost = float(row['labor_cost'] or 0)
                    combined_margin = round(((labor_revenue - labor_cost) / labor_revenue) * 100, 1) if labor_revenue > 0 else None
                    
                    # Field
                    field_revenue = float(row['field_revenue'] or 0)
                    field_cost = float(row['field_cost'] or 0)
                    field_margin = round(((field_revenue - field_cost) / field_revenue) * 100, 1) if field_revenue > 0 else None
                    
                    # Shop
                    shop_revenue = float(row['shop_revenue'] or 0)
                    shop_cost = float(row['shop_cost'] or 0)
                    shop_margin = round(((shop_revenue - shop_cost) / shop_revenue) * 100, 1) if shop_revenue > 0 else None
                else:
                    # No data for this month
                    labor_revenue = 0
                    combined_margin = None
                    field_revenue = 0
                    field_margin = None
                    shop_revenue = 0
                    shop_margin = None
                
                # Get prior year data for comparison
                if prior_row:
                    prior_labor_revenue = float(prior_row['labor_revenue'] or 0)
                    prior_field_revenue = float(prior_row['field_revenue'] or 0)
                    prior_shop_revenue = float(prior_row['shop_revenue'] or 0)
                else:
                    prior_labor_revenue = 0
                    prior_field_revenue = 0
                    prior_shop_revenue = 0
                
                monthlyLaborRevenue.append({
                    'month': month_str,
                    'amount': labor_revenue,
                    'margin': combined_margin,
                    'prior_year_amount': prior_labor_revenue
                })
                
                monthlyFieldRevenue.append({
                    'month': month_str,
                    'amount': field_revenue,
                    'margin': field_margin,
                    'prior_year_amount': prior_field_revenue
                })
                
                monthlyShopRevenue.append({
                    'month': month_str,
                    'amount': shop_revenue,
                    'margin': shop_margin,
                    'prior_year_amount': prior_shop_revenue
                })
            
            # No need for padding logic anymore - we generate exactly 12 months above
            
            return jsonify({
                'monthlyLaborRevenue': monthlyLaborRevenue,
                'monthlyFieldRevenue': monthlyFieldRevenue,
                'monthlyShopRevenue': monthlyShopRevenue
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'service_report_error'
            }), 500


    @reports_bp.route('/departments/parts/pace', methods=['GET'])
    @jwt_required()
    def get_parts_pace():
        """Get parts department sales pace comparing current month to previous month"""
        try:
            db = get_db()
            
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
            
            # Get parts sales through same day for current and previous month
            # Using PartsTaxable + PartsNonTax to match the main parts revenue query
            current_query = f"""
            SELECT SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as total_sales
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {current_year}
                AND MONTH(InvoiceDate) = {current_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND (COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) > 0
            """
            
            prev_query = f"""
            SELECT SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as total_sales
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND (COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) > 0
            """
            
            # Get full previous month total for comparison
            full_month_query = f"""
            SELECT SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as total_sales
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND (COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) > 0
            """
            
            # Get adaptive comparison data
            adaptive_query = f"""
            WITH MonthlyTotals AS (
                SELECT 
                    YEAR(InvoiceDate) as year,
                    MONTH(InvoiceDate) as month,
                    SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as total_sales
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
                    AND YEAR(InvoiceDate) * 100 + MONTH(InvoiceDate) < {current_year} * 100 + {current_month}
                    AND (COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) > 0
                GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            )
            SELECT 
                AVG(total_sales) as avg_monthly_sales,
                MAX(total_sales) as best_monthly_sales,
                MIN(total_sales) as worst_monthly_sales,
                COUNT(*) as months_available,
                MAX(CASE WHEN month = {current_month} THEN total_sales END) as same_month_last_year
            FROM MonthlyTotals
            """
            
            current_result = db.execute_query(current_query)
            prev_result = db.execute_query(prev_query)
            full_month_result = db.execute_query(full_month_query)
            adaptive_result = db.execute_query(adaptive_query)
            
            current_sales = float(current_result[0]['total_sales'] or 0) if current_result else 0
            previous_sales = float(prev_result[0]['total_sales'] or 0) if prev_result else 0
            previous_full_month = float(full_month_result[0]['total_sales'] or 0) if full_month_result else 0
            
            # Extract adaptive data
            adaptive_data = adaptive_result[0] if adaptive_result else {}
            avg_monthly_sales = float(adaptive_data.get('avg_monthly_sales') or 0)
            best_monthly_sales = float(adaptive_data.get('best_monthly_sales') or 0)
            worst_monthly_sales = float(adaptive_data.get('worst_monthly_sales') or 0)
            months_available = int(adaptive_data.get('months_available') or 0)
            same_month_last_year = float(adaptive_data.get('same_month_last_year') or 0)
            
            # Calculate multiple pace percentages for adaptive comparison
            # 1. Previous month comparison (existing logic)
            if current_sales > previous_full_month and previous_full_month > 0:
                pace_percentage = round(((current_sales / previous_full_month) - 1) * 100, 1)
                comparison_base = "full_previous_month"
            else:
                pace_percentage = round(((current_sales / previous_sales) - 1) * 100, 1) if previous_sales > 0 else 0
                comparison_base = "same_day_previous_month"
            
            # Calculate projected month total for fair comparison
            import calendar
            days_in_month = calendar.monthrange(current_year, current_month)[1]
            projected_sales = (current_sales / current_day) * days_in_month if current_day > 0 else 0
            
            # 2. Additional adaptive comparisons (use projected total for fair comparison)
            pace_pct_avg = round(((projected_sales / avg_monthly_sales) - 1) * 100, 1) if avg_monthly_sales > 0 else None
            pace_pct_same_month_ly = round(((projected_sales / same_month_last_year) - 1) * 100, 1) if same_month_last_year > 0 else None
            is_best_month = projected_sales > best_monthly_sales
            
            return jsonify({
                'pace_percentage': pace_percentage,
                'current_sales': current_sales,
                'previous_sales': previous_sales,
                'previous_full_month': previous_full_month,
                'current_month': current_month,
                'current_day': current_day,
                'comparison_base': comparison_base,
                'exceeded_previous_month': current_sales > previous_full_month,
                'adaptive_comparisons': {
                    'available_months_count': months_available,
                    'vs_available_average': {
                        'percentage': pace_pct_avg,
                        'average_monthly_sales': avg_monthly_sales,
                        'ahead_behind': 'ahead' if pace_pct_avg and pace_pct_avg > 0 else 'behind' if pace_pct_avg and pace_pct_avg < 0 else 'on pace' if pace_pct_avg is not None else None
                    },
                    'vs_same_month_last_year': {
                        'percentage': pace_pct_same_month_ly,
                        'last_year_sales': same_month_last_year if same_month_last_year > 0 else None,
                        'ahead_behind': 'ahead' if pace_pct_same_month_ly and pace_pct_same_month_ly > 0 else 'behind' if pace_pct_same_month_ly and pace_pct_same_month_ly < 0 else 'on pace' if pace_pct_same_month_ly is not None else None
                    },
                    'performance_indicators': {
                        'is_best_month_ever': is_best_month,
                        'best_month_sales': best_monthly_sales,
                        'worst_month_sales': worst_monthly_sales,
                        'vs_best_percentage': round(((current_sales / best_monthly_sales) - 1) * 100, 1) if best_monthly_sales > 0 else None,
                        'vs_worst_percentage': round(((current_sales / worst_monthly_sales) - 1) * 100, 1) if worst_monthly_sales > 0 else None
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching parts pace: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/parts', methods=['GET'])
    @require_permission('view_parts')
    def get_parts_department_report():
        """Get Parts Department report data"""
        try:
            db = get_db()
            
            # Monthly Parts Revenue and Margins - Last 12 months
            # Using GLDetail for 100% accurate P&L matching
            # Revenue: GL 410003 (Counter) + GL 410012 (Customer Repair Order)
            # Cost: GL 510003 (Counter Cost) + GL 510012 (Customer Repair Order Cost)
            parts_revenue_query = """
            SELECT 
                YEAR(EffectiveDate) as year,
                MONTH(EffectiveDate) as month,
                -- Combined revenue
                ABS(SUM(CASE WHEN AccountNo IN ('410003', '410012') THEN Amount ELSE 0 END)) as parts_revenue,
                ABS(SUM(CASE WHEN AccountNo IN ('510003', '510012') THEN Amount ELSE 0 END)) as parts_cost,
                -- Counter (410003 / 510003)
                ABS(SUM(CASE WHEN AccountNo = '410003' THEN Amount ELSE 0 END)) as counter_revenue,
                ABS(SUM(CASE WHEN AccountNo = '510003' THEN Amount ELSE 0 END)) as counter_cost,
                -- Repair Order (410012 / 510012)
                ABS(SUM(CASE WHEN AccountNo = '410012' THEN Amount ELSE 0 END)) as repair_order_revenue,
                ABS(SUM(CASE WHEN AccountNo = '510012' THEN Amount ELSE 0 END)) as repair_order_cost
            FROM ben002.GLDetail
            WHERE AccountNo IN ('410003', '410012', '510003', '510012')
                AND EffectiveDate >= DATEADD(month, -13, GETDATE())
                AND Posted = 1
            GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            """
            
            parts_revenue_result = db.execute_query(parts_revenue_query)
            
            monthlyPartsRevenue = []
            monthlyCounterRevenue = []
            monthlyRepairOrderRevenue = []
            
            # Create a dictionary to store data by year-month key
            revenue_by_month = {}
            for row in parts_revenue_result:
                year_month_key = (row['year'], row['month'])
                revenue_by_month[year_month_key] = row
            
            # Get fiscal year months (12 consecutive months starting with fiscal year start)
            fiscal_year_months = get_fiscal_year_months()
            
            # Generate data for each fiscal year month
            for year, month in fiscal_year_months:
                month_date = datetime(year, month, 1)
                # Include year in label if spanning multiple calendar years
                if fiscal_year_months[0][0] != fiscal_year_months[-1][0]:
                    month_str = month_date.strftime("%b '%y")
                else:
                    month_str = month_date.strftime("%b")
                year_month_key = (year, month)
                prior_year_key = (year - 1, month)  # Same month, previous year
                
                # Get data for this month if it exists
                row = revenue_by_month.get(year_month_key)
                prior_row = revenue_by_month.get(prior_year_key)
                
                if row:
                    # Combined
                    parts_revenue = float(row['parts_revenue'] or 0)
                    parts_cost = float(row['parts_cost'] or 0)
                    combined_margin = round(((parts_revenue - parts_cost) / parts_revenue) * 100, 1) if parts_revenue > 0 else None
                    
                    # Counter
                    counter_revenue = float(row['counter_revenue'] or 0)
                    counter_cost = float(row['counter_cost'] or 0)
                    counter_margin = round(((counter_revenue - counter_cost) / counter_revenue) * 100, 1) if counter_revenue > 0 else None
                    
                    # Repair Order
                    repair_order_revenue = float(row['repair_order_revenue'] or 0)
                    repair_order_cost = float(row['repair_order_cost'] or 0)
                    repair_order_margin = round(((repair_order_revenue - repair_order_cost) / repair_order_revenue) * 100, 1) if repair_order_revenue > 0 else None
                else:
                    # No data for this month
                    parts_revenue = 0
                    combined_margin = None
                    counter_revenue = 0
                    counter_margin = None
                    repair_order_revenue = 0
                    repair_order_margin = None
                
                # Get prior year data for comparison
                if prior_row:
                    prior_parts_revenue = float(prior_row['parts_revenue'] or 0)
                    prior_counter_revenue = float(prior_row['counter_revenue'] or 0)
                    prior_repair_order_revenue = float(prior_row['repair_order_revenue'] or 0)
                else:
                    prior_parts_revenue = 0
                    prior_counter_revenue = 0
                    prior_repair_order_revenue = 0
                
                monthlyPartsRevenue.append({
                    'month': month_str,
                    'amount': parts_revenue,
                    'margin': combined_margin,
                    'prior_year_amount': prior_parts_revenue
                })
                
                monthlyCounterRevenue.append({
                    'month': month_str,
                    'amount': counter_revenue,
                    'margin': counter_margin,
                    'prior_year_amount': prior_counter_revenue
                })
                
                monthlyRepairOrderRevenue.append({
                    'month': month_str,
                    'amount': repair_order_revenue,
                    'margin': repair_order_margin,
                    'prior_year_amount': prior_repair_order_revenue
                })
            
            # No need for padding logic anymore - we generate exactly 12 months above
            
            return jsonify({
                'monthlyPartsRevenue': monthlyPartsRevenue,
                'monthlyCounterRevenue': monthlyCounterRevenue,
                'monthlyRepairOrderRevenue': monthlyRepairOrderRevenue
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'parts_report_error'
            }), 500


    @reports_bp.route('/departments/parts/top10', methods=['GET'])
    @jwt_required()
    def get_parts_top10():
        """Get top 10 parts by quantity sold in last 30 days"""
        try:
            db = get_db()
            
            top_parts_query = """
            SELECT TOP 10
                wp.PartNo,
                MAX(wp.Description) as Description,
                COUNT(DISTINCT wp.WONo) as OrderCount,
                SUM(wp.Qty) as TotalQuantity,
                SUM(wp.Sell * wp.Qty) as TotalRevenue,
                AVG(wp.Sell / NULLIF(wp.Qty, 0)) as AvgUnitPrice,
                MAX(p.OnHand) as CurrentStock,
                MAX(p.Cost) as UnitCost,
                CASE 
                    WHEN MAX(p.OnHand) = 0 THEN 'Out of Stock'
                    WHEN MAX(p.OnHand) < 10 THEN 'Low Stock'
                    ELSE 'In Stock'
                END as StockStatus
            FROM ben002.WOParts wp
            LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
            INNER JOIN ben002.WO w ON wp.WONo = w.WONo
            WHERE w.OpenDate >= DATEADD(day, -30, GETDATE())
            AND wp.Qty > 0
            AND wp.Description NOT LIKE '%OIL%'
            AND wp.Description NOT LIKE '%GREASE%'
            AND wp.Description NOT LIKE '%ANTI-FREEZE%'
            AND wp.Description NOT LIKE '%ANTIFREEZE%'
            AND wp.Description NOT LIKE '%COOLANT%'
            GROUP BY wp.PartNo
            ORDER BY SUM(wp.Qty) DESC
            """
            
            results = db.execute_query(top_parts_query)
            
            top_parts = []
            for part in results:
                top_parts.append({
                    'partNo': part.get('PartNo', ''),
                    'description': part.get('Description', ''),
                    'orderCount': part.get('OrderCount', 0),
                    'totalQuantity': part.get('TotalQuantity', 0),
                    'totalRevenue': float(part.get('TotalRevenue', 0)),
                    'avgUnitPrice': float(part.get('AvgUnitPrice', 0)),
                    'currentStock': part.get('CurrentStock', 0),
                    'unitCost': float(part.get('UnitCost', 0)),
                    'stockStatus': part.get('StockStatus', '')
                })
            
            return jsonify({
                'topParts': top_parts,
                'period': 'Last 30 days'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'top_parts_error'
            }), 500


    @reports_bp.route('/departments/parts/reorder-alert', methods=['GET'])
    @require_permission('view_parts_stock_alerts', 'view_parts')
    def get_parts_reorder_alert():
        """Get parts reorder point alerts - identifies parts needing reorder"""
        try:
            db = get_db()
            
            # Calculate average daily usage and current stock levels
            reorder_alert_query = """
            WITH PartUsage AS (
                -- Calculate average daily usage over last 90 days
                SELECT 
                    wp.PartNo,
                    MAX(wp.Description) as Description,
                    COUNT(DISTINCT wp.WONo) as OrderCount,
                    SUM(wp.Qty) as TotalQtyUsed,
                    DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) + 1 as DaysInPeriod,
                    CAST(SUM(wp.Qty) AS FLOAT) / NULLIF(DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) + 1, 0) as AvgDailyUsage
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                WHERE w.OpenDate >= DATEADD(day, -90, GETDATE())
                    AND wp.Qty > 0
                GROUP BY wp.PartNo
                HAVING COUNT(DISTINCT wp.WONo) >= 3  -- At least 3 orders in period
            ),
            CurrentStock AS (
                -- Get current stock levels and costs
                SELECT 
                    PartNo,
                    MAX(OnHand) as OnHand,
                    MAX(OnOrder) as OnOrder,
                    MAX(Cost) as Cost,
                    MAX(List) as List,
                    -- Estimate reorder point as 14 days of average usage (2 week lead time)
                    -- This should be replaced with actual reorder point field if available
                    0 as ReorderPoint,
                    0 as MinStock
                FROM ben002.Parts
                WHERE OnHand IS NOT NULL
                GROUP BY PartNo
            )
            SELECT 
                cs.PartNo,
                pu.Description,
                cs.OnHand as CurrentStock,
                cs.OnOrder as OnOrder,
                CAST(pu.AvgDailyUsage AS DECIMAL(10,2)) as AvgDailyUsage,
                -- Calculate days of stock remaining
                CASE 
                    WHEN pu.AvgDailyUsage > 0 
                    THEN CAST(cs.OnHand / pu.AvgDailyUsage AS INT)
                    ELSE 999
                END as DaysOfStock,
                -- Estimate reorder point (14 days lead time + 7 days safety stock)
                CAST(CEILING(pu.AvgDailyUsage * 21) AS INT) as SuggestedReorderPoint,
                -- Reorder quantity (30 days worth)
                CAST(CEILING(pu.AvgDailyUsage * 30) AS INT) as SuggestedOrderQty,
                cs.Cost,
                cs.List,
                pu.OrderCount as OrdersLast90Days,
                -- Alert level
                CASE 
                    WHEN cs.OnHand <= 0 THEN 'Out of Stock'
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 7) THEN 'Critical'
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 14) THEN 'Low'
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 21) THEN 'Reorder'
                    ELSE 'OK'
                END as AlertLevel
            FROM CurrentStock cs
            INNER JOIN PartUsage pu ON cs.PartNo = pu.PartNo
            WHERE cs.OnHand < (pu.AvgDailyUsage * 21)  -- Below suggested reorder point
                OR cs.OnHand <= 0  -- Or completely out
            ORDER BY 
                CASE 
                    WHEN cs.OnHand <= 0 THEN 1
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 7) THEN 2
                    WHEN cs.OnHand < (pu.AvgDailyUsage * 14) THEN 3
                    ELSE 4
                END,
                pu.AvgDailyUsage DESC
            """
            
            reorder_alerts = db.execute_query(reorder_alert_query)
            
            # Get summary statistics
            summary_query = """
            WITH PartUsage AS (
                SELECT 
                    wp.PartNo,
                    CAST(SUM(wp.Qty) AS FLOAT) / NULLIF(DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) + 1, 0) as AvgDailyUsage
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                WHERE w.OpenDate >= DATEADD(day, -90, GETDATE())
                    AND wp.Qty > 0
                GROUP BY wp.PartNo
                HAVING COUNT(DISTINCT wp.WONo) >= 3
            ),
            PartsAggregated AS (
                SELECT 
                    PartNo,
                    MAX(OnHand) as OnHand
                FROM ben002.Parts
                GROUP BY PartNo
            )
            SELECT 
                COUNT(CASE WHEN pa.OnHand <= 0 THEN 1 END) as OutOfStock,
                COUNT(CASE WHEN pa.OnHand > 0 AND pa.OnHand < (pu.AvgDailyUsage * 7) THEN 1 END) as Critical,
                COUNT(CASE WHEN pa.OnHand >= (pu.AvgDailyUsage * 7) AND pa.OnHand < (pu.AvgDailyUsage * 14) THEN 1 END) as Low,
                COUNT(CASE WHEN pa.OnHand >= (pu.AvgDailyUsage * 14) AND pa.OnHand < (pu.AvgDailyUsage * 21) THEN 1 END) as NeedsReorder,
                COUNT(*) as TotalTrackedParts
            FROM PartsAggregated pa
            INNER JOIN PartUsage pu ON pa.PartNo = pu.PartNo
            """
            
            summary_result = db.execute_query(summary_query)
            
            summary = {
                'outOfStock': 0,
                'critical': 0,
                'low': 0,
                'needsReorder': 0,
                'totalTracked': 0
            }
            
            if summary_result and len(summary_result) > 0:
                row = summary_result[0]
                summary = {
                    'outOfStock': row.get('OutOfStock', 0),
                    'critical': row.get('Critical', 0),
                    'low': row.get('Low', 0),
                    'needsReorder': row.get('NeedsReorder', 0),
                    'totalTracked': row.get('TotalTrackedParts', 0)
                }
            
            # Format the alerts
            formatted_alerts = []
            for alert in reorder_alerts:
                formatted_alerts.append({
                    'partNo': alert.get('PartNo', ''),
                    'description': alert.get('Description', ''),
                    'currentStock': alert.get('CurrentStock', 0),
                    'onOrder': alert.get('OnOrder', 0),
                    'avgDailyUsage': float(alert.get('AvgDailyUsage', 0)),
                    'daysOfStock': alert.get('DaysOfStock', 0),
                    'suggestedReorderPoint': alert.get('SuggestedReorderPoint', 0),
                    'suggestedOrderQty': alert.get('SuggestedOrderQty', 0),
                    'cost': float(alert.get('Cost', 0)),
                    'listPrice': float(alert.get('List', 0)),
                    'ordersLast90Days': alert.get('OrdersLast90Days', 0),
                    'alertLevel': alert.get('AlertLevel', 'Unknown')
                })
            
            return jsonify({
                'summary': summary,
                'alerts': formatted_alerts,
                'leadTimeAssumption': 14,  # Days
                'safetyStockDays': 7,
                'analysisInfo': {
                    'period': 'Last 90 days',
                    'method': 'Average daily usage calculation',
                    'reorderFormula': '(Lead Time + Safety Stock) × Avg Daily Usage'
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'reorder_alert_error'
            }), 500


    @reports_bp.route('/departments/parts/velocity', methods=['GET'])
    @jwt_required()
    def get_parts_velocity_analysis():
        """Get parts velocity analysis - identifies fast vs slow moving inventory"""
        try:
            db = get_db()
            
            # Get time period from query params (default 365 days)
            days_back = int(request.args.get('days', 365))
            
            # Parts velocity analysis query
            velocity_query = f"""
            WITH PartMovement AS (
                -- Calculate part movement over the period
                SELECT 
                    p.PartNo,
                    MAX(p.Description) as Description,
                    MAX(p.OnHand) as CurrentStock,
                    MAX(p.Cost) as Cost,
                    MAX(p.List) as ListPrice,
                    MAX(p.OnHand * p.Cost) as InventoryValue,
                    -- Count of times ordered
                    COALESCE(wp.OrderCount, 0) as OrderCount,
                    -- Total quantity sold/used
                    COALESCE(wp.TotalQtyMoved, 0) as TotalQtyMoved,
                    -- Days since last movement
                    DATEDIFF(day, wp.LastMovementDate, GETDATE()) as DaysSinceLastMovement,
                    -- Average days between orders
                    wp.AvgDaysBetweenOrders,
                    -- Calculate annual turnover rate
                    CASE 
                        WHEN MAX(p.OnHand) > 0 AND wp.TotalQtyMoved > 0
                        THEN CAST(wp.TotalQtyMoved AS FLOAT) * (365.0 / {days_back}) / MAX(p.OnHand)
                        ELSE 0
                    END as AnnualTurnoverRate
                FROM ben002.Parts p
                LEFT JOIN (
                    SELECT 
                        wp.PartNo,
                        COUNT(DISTINCT wp.WONo) as OrderCount,
                        SUM(wp.Qty) as TotalQtyMoved,
                        MAX(w.OpenDate) as LastMovementDate,
                        -- Calculate average days between orders
                        CASE 
                            WHEN COUNT(DISTINCT w.OpenDate) > 1
                            THEN DATEDIFF(day, MIN(w.OpenDate), MAX(w.OpenDate)) / (COUNT(DISTINCT w.OpenDate) - 1)
                            ELSE NULL
                        END as AvgDaysBetweenOrders
                    FROM ben002.WOParts wp
                    INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                    WHERE w.OpenDate >= DATEADD(day, -{days_back}, GETDATE())
                    GROUP BY wp.PartNo
                ) wp ON p.PartNo = wp.PartNo
                WHERE p.OnHand > 0 OR wp.OrderCount > 0  -- Parts with stock or movement
                GROUP BY p.PartNo, wp.OrderCount, wp.TotalQtyMoved, wp.LastMovementDate, wp.AvgDaysBetweenOrders
            )
            SELECT 
                PartNo,
                Description,
                CurrentStock,
                Cost,
                ListPrice,
                InventoryValue,
                OrderCount,
                TotalQtyMoved,
                DaysSinceLastMovement,
                AvgDaysBetweenOrders,
                AnnualTurnoverRate,
                -- Velocity classification
                CASE 
                    WHEN DaysSinceLastMovement IS NULL THEN 'No Movement'
                    WHEN DaysSinceLastMovement > 365 THEN 'Dead Stock'
                    WHEN DaysSinceLastMovement > 180 THEN 'Slow Moving'
                    WHEN AnnualTurnoverRate >= 12 THEN 'Very Fast'
                    WHEN AnnualTurnoverRate >= 6 THEN 'Fast'
                    WHEN AnnualTurnoverRate >= 2 THEN 'Medium'
                    WHEN AnnualTurnoverRate >= 0.5 THEN 'Slow'
                    ELSE 'Very Slow'
                END as VelocityCategory,
                -- Stock health indicator
                CASE
                    WHEN CurrentStock = 0 AND OrderCount > 0 THEN 'Stockout Risk'
                    WHEN DaysSinceLastMovement > 365 AND CurrentStock > 0 THEN 'Obsolete Risk'
                    WHEN AnnualTurnoverRate < 0.5 AND InventoryValue > 1000 THEN 'Overstock Risk'
                    WHEN AnnualTurnoverRate > 12 AND CurrentStock < 10 THEN 'Understock Risk'
                    ELSE 'Normal'
                END as StockHealth
            FROM PartMovement
            ORDER BY InventoryValue DESC
            """
            
            velocity_results = db.execute_query(velocity_query)
            
            # Summary statistics by category
            summary_query = f"""
            WITH PartMovement AS (
                SELECT 
                    p.PartNo,
                    MAX(p.OnHand * p.Cost) as InventoryValue,
                    COALESCE(wp.TotalQtyMoved, 0) as TotalQtyMoved,
                    DATEDIFF(day, wp.LastMovementDate, GETDATE()) as DaysSinceLastMovement,
                    CASE 
                        WHEN MAX(p.OnHand) > 0 AND wp.TotalQtyMoved > 0
                        THEN CAST(wp.TotalQtyMoved AS FLOAT) * (365.0 / {days_back}) / MAX(p.OnHand)
                        ELSE 0
                    END as AnnualTurnoverRate
                FROM ben002.Parts p
                LEFT JOIN (
                    SELECT 
                        wp.PartNo,
                        SUM(wp.Qty) as TotalQtyMoved,
                        MAX(w.OpenDate) as LastMovementDate
                    FROM ben002.WOParts wp
                    INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                    WHERE w.OpenDate >= DATEADD(day, -{days_back}, GETDATE())
                    GROUP BY wp.PartNo
                ) wp ON p.PartNo = wp.PartNo
                WHERE p.OnHand > 0 OR wp.TotalQtyMoved > 0
                GROUP BY p.PartNo, wp.TotalQtyMoved, wp.LastMovementDate
            )
            SELECT 
                CASE 
                    WHEN DaysSinceLastMovement IS NULL THEN 'No Movement'
                    WHEN DaysSinceLastMovement > 365 THEN 'Dead Stock'
                    WHEN DaysSinceLastMovement > 180 THEN 'Slow Moving'
                    WHEN AnnualTurnoverRate >= 12 THEN 'Very Fast'
                    WHEN AnnualTurnoverRate >= 6 THEN 'Fast'
                    WHEN AnnualTurnoverRate >= 2 THEN 'Medium'
                    WHEN AnnualTurnoverRate >= 0.5 THEN 'Slow'
                    ELSE 'Very Slow'
                END as VelocityCategory,
                COUNT(*) as PartCount,
                SUM(InventoryValue) as TotalValue,
                AVG(AnnualTurnoverRate) as AvgTurnoverRate
            FROM PartMovement
            GROUP BY 
                CASE 
                    WHEN DaysSinceLastMovement IS NULL THEN 'No Movement'
                    WHEN DaysSinceLastMovement > 365 THEN 'Dead Stock'
                    WHEN DaysSinceLastMovement > 180 THEN 'Slow Moving'
                    WHEN AnnualTurnoverRate >= 12 THEN 'Very Fast'
                    WHEN AnnualTurnoverRate >= 6 THEN 'Fast'
                    WHEN AnnualTurnoverRate >= 2 THEN 'Medium'
                    WHEN AnnualTurnoverRate >= 0.5 THEN 'Slow'
                    ELSE 'Very Slow'
                END
            """
            
            summary_results = db.execute_query(summary_query)
            
            # Monthly movement trend
            trend_query = f"""
            SELECT 
                YEAR(w.OpenDate) as Year,
                MONTH(w.OpenDate) as Month,
                COUNT(DISTINCT wp.PartNo) as UniqueParts,
                COUNT(DISTINCT wp.WONo) as OrderCount,
                SUM(wp.Qty) as TotalQuantity,
                SUM(wp.Qty * wp.Cost) as TotalValue
            FROM ben002.WOParts wp
            INNER JOIN ben002.WO w ON wp.WONo = w.WONo
            WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate)
            ORDER BY Year, Month
            """
            
            trend_results = db.execute_query(trend_query)
            
            # Format results
            parts_list = []
            for part in velocity_results:
                parts_list.append({
                    'partNo': part.get('PartNo', ''),
                    'description': part.get('Description', ''),
                    'currentStock': part.get('CurrentStock', 0),
                    'cost': float(part.get('Cost', 0)),
                    'listPrice': float(part.get('ListPrice', 0)),
                    'inventoryValue': float(part.get('InventoryValue', 0)),
                    'orderCount': part.get('OrderCount', 0),
                    'totalQtyMoved': part.get('TotalQtyMoved', 0),
                    'daysSinceLastMovement': part.get('DaysSinceLastMovement'),
                    'avgDaysBetweenOrders': part.get('AvgDaysBetweenOrders'),
                    'annualTurnoverRate': float(part.get('AnnualTurnoverRate', 0)),
                    'velocityCategory': part.get('VelocityCategory', 'Unknown'),
                    'stockHealth': part.get('StockHealth', 'Unknown')
                })
            
            summary = {}
            for cat in summary_results:
                summary[cat['VelocityCategory']] = {
                    'partCount': cat.get('PartCount', 0),
                    'totalValue': float(cat.get('TotalValue', 0)),
                    'avgTurnoverRate': float(cat.get('AvgTurnoverRate', 0))
                }
            
            movement_trend = []
            for row in trend_results:
                month_date = datetime(row['Year'], row['Month'], 1)
                movement_trend.append({
                    'month': month_date.strftime("%b %Y"),
                    'uniqueParts': row.get('UniqueParts', 0),
                    'orderCount': row.get('OrderCount', 0),
                    'totalQuantity': row.get('TotalQuantity', 0),
                    'totalValue': float(row.get('TotalValue', 0))
                })
            
            return jsonify({
                'parts': parts_list,  # Return all parts for category filtering
                'summary': summary,
                'movementTrend': movement_trend,
                'analysisInfo': {
                    'period': f'Last {days_back} days',
                    'velocityCategories': {
                        'Very Fast': 'Turnover > 12x/year',
                        'Fast': 'Turnover 6-12x/year',
                        'Medium': 'Turnover 2-6x/year',
                        'Slow': 'Turnover 0.5-2x/year',
                        'Very Slow': 'Turnover < 0.5x/year',
                        'Slow Moving': 'No movement 180-365 days',
                        'Dead Stock': 'No movement > 365 days',
                        'No Movement': 'Never ordered'
                    }
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'velocity_analysis_error'
            }), 500


    @reports_bp.route('/departments/parts/forecast', methods=['GET'])
    @require_permission('view_parts_forecast', 'view_parts')
    def get_parts_demand_forecast():
        """Get parts demand forecast based on historical usage and trends"""
        try:
            db = get_db()
            
            # Get forecast period from query params (default 90 days)
            forecast_days = int(request.args.get('days', 90))
            
            # Historical demand analysis with seasonality
            forecast_query = f"""
            WITH HistoricalDemand AS (
                -- Get 12 months of historical data
                SELECT 
                    wp.PartNo,
                    MAX(wp.Description) as Description,
                    YEAR(w.OpenDate) as Year,
                    MONTH(w.OpenDate) as Month,
                    SUM(wp.Qty) as MonthlyQty,
                    COUNT(DISTINCT wp.WONo) as OrderCount
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
                    AND wp.Qty > 0
                GROUP BY wp.PartNo, YEAR(w.OpenDate), MONTH(w.OpenDate)
            ),
            PartTrends AS (
                -- Calculate trends and seasonality
                SELECT 
                    PartNo,
                    Description,
                    AVG(MonthlyQty) as AvgMonthlyDemand,
                    STDEV(MonthlyQty) as DemandStdDev,
                    MAX(MonthlyQty) as PeakMonthlyDemand,
                    MIN(MonthlyQty) as MinMonthlyDemand,
                    COUNT(DISTINCT CONCAT(Year, '-', Month)) as ActiveMonths,
                    -- Calculate trend (simple linear regression slope)
                    (12 * SUM(CAST(Month + (Year - 2024) * 12 AS FLOAT) * MonthlyQty) - 
                     SUM(CAST(Month + (Year - 2024) * 12 AS FLOAT)) * SUM(MonthlyQty)) /
                    (12 * SUM(POWER(CAST(Month + (Year - 2024) * 12 AS FLOAT), 2)) - 
                     POWER(SUM(CAST(Month + (Year - 2024) * 12 AS FLOAT)), 2)) as TrendSlope
                FROM HistoricalDemand
                GROUP BY PartNo, Description
                HAVING COUNT(DISTINCT CONCAT(Year, '-', Month)) >= 3  -- At least 3 months of data
            ),
            CurrentInventory AS (
                SELECT 
                    PartNo,
                    MAX(OnHand) as CurrentStock,
                    MAX(OnOrder) as OnOrder,
                    MAX(Cost) as UnitCost
                FROM ben002.Parts
                GROUP BY PartNo
            ),
            EquipmentCounts AS (
                -- Count equipment that uses each part (based on recent service)
                SELECT 
                    wp.PartNo,
                    COUNT(DISTINCT CASE WHEN w.UnitNo IS NOT NULL THEN w.UnitNo END) as EquipmentCount,
                    0 as AvgEquipmentHours
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
                GROUP BY wp.PartNo
            )
            SELECT 
                pt.PartNo,
                pt.Description,
                -- Current state
                COALESCE(ci.CurrentStock, 0) as CurrentStock,
                COALESCE(ci.OnOrder, 0) as OnOrder,
                COALESCE(ci.UnitCost, 0) as UnitCost,
                -- Historical metrics
                pt.AvgMonthlyDemand,
                pt.PeakMonthlyDemand,
                pt.ActiveMonths,
                COALESCE(ec.EquipmentCount, 0) as EquipmentUsingPart,
                -- Forecast for period
                CAST(pt.AvgMonthlyDemand * ({forecast_days} / 30.0) * 
                     CASE 
                         WHEN pt.TrendSlope > 0 THEN 1.1  -- Growing demand
                         WHEN pt.TrendSlope < -0.5 THEN 0.9  -- Declining demand
                         ELSE 1.0  -- Stable demand
                     END AS INT) as ForecastDemand,
                -- Safety stock recommendation (based on variability)
                CAST(
                    CASE 
                        WHEN pt.DemandStdDev > pt.AvgMonthlyDemand THEN pt.AvgMonthlyDemand * 0.5
                        ELSE pt.DemandStdDev * 1.65  -- 95% service level
                    END AS INT
                ) as SafetyStock,
                -- Reorder recommendation
                CASE 
                    WHEN COALESCE(ci.CurrentStock, 0) + COALESCE(ci.OnOrder, 0) < 
                         (pt.AvgMonthlyDemand * ({forecast_days} / 30.0)) 
                    THEN 'Order Now'
                    WHEN COALESCE(ci.CurrentStock, 0) + COALESCE(ci.OnOrder, 0) < 
                         (pt.AvgMonthlyDemand * ({forecast_days} / 30.0) * 1.5)
                    THEN 'Order Soon'
                    ELSE 'Adequate Stock'
                END as OrderRecommendation,
                -- Trend indicator
                CASE 
                    WHEN pt.TrendSlope > 1 THEN 'Strong Growth'
                    WHEN pt.TrendSlope > 0 THEN 'Growing'
                    WHEN pt.TrendSlope < -1 THEN 'Declining Fast'
                    WHEN pt.TrendSlope < 0 THEN 'Declining'
                    ELSE 'Stable'
                END as DemandTrend
            FROM PartTrends pt
            LEFT JOIN CurrentInventory ci ON pt.PartNo = ci.PartNo
            LEFT JOIN EquipmentCounts ec ON pt.PartNo = ec.PartNo
            WHERE pt.AvgMonthlyDemand > 0
            ORDER BY 
                CASE 
                    WHEN COALESCE(ci.CurrentStock, 0) + COALESCE(ci.OnOrder, 0) < 
                         (pt.AvgMonthlyDemand * ({forecast_days} / 30.0)) 
                    THEN 1 
                    ELSE 2 
                END,
                (pt.AvgMonthlyDemand * COALESCE(ci.UnitCost, 0)) DESC
            """
            
            forecast_results = db.execute_query(forecast_query)
            
            # Monthly trend for visualization
            monthly_trend_query = """
            SELECT 
                YEAR(w.OpenDate) as Year,
                MONTH(w.OpenDate) as Month,
                COUNT(DISTINCT wp.PartNo) as UniqueParts,
                SUM(wp.Qty) as TotalQuantity,
                COUNT(DISTINCT w.WONo) as WorkOrders
            FROM ben002.WOParts wp
            INNER JOIN ben002.WO w ON wp.WONo = w.WONo
            WHERE w.OpenDate >= DATEADD(month, -12, GETDATE())
            GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate)
            ORDER BY Year, Month
            """
            
            trend_results = db.execute_query(monthly_trend_query)
            
            # Check if queries returned results
            if not forecast_results:
                forecast_results = []
            if not trend_results:
                trend_results = []
            
            # Format results
            forecasts = []
            total_forecast_value = 0
            
            for part in forecast_results:
                forecast_value = float(part.get('ForecastDemand', 0)) * float(part.get('UnitCost', 0))
                total_forecast_value += forecast_value
                
                forecasts.append({
                    'partNo': part.get('PartNo', ''),
                    'description': part.get('Description', ''),
                    'currentStock': part.get('CurrentStock', 0),
                    'onOrder': part.get('OnOrder', 0),
                    'unitCost': float(part.get('UnitCost', 0)),
                    'avgMonthlyDemand': float(part.get('AvgMonthlyDemand', 0)),
                    'peakMonthlyDemand': part.get('PeakMonthlyDemand', 0),
                    'forecastDemand': part.get('ForecastDemand', 0),
                    'safetyStock': part.get('SafetyStock', 0),
                    'orderRecommendation': part.get('OrderRecommendation', ''),
                    'demandTrend': part.get('DemandTrend', ''),
                    'equipmentCount': part.get('EquipmentUsingPart', 0),
                    'forecastValue': forecast_value
                })
            
            monthly_trend = []
            for row in trend_results:
                month_date = datetime(row['Year'], row['Month'], 1)
                monthly_trend.append({
                    'month': month_date.strftime("%b %Y"),
                    'actualDemand': row.get('TotalQuantity', 0),
                    'uniqueParts': row.get('UniqueParts', 0),
                    'workOrders': row.get('WorkOrders', 0)
                })
            
            # Add forecast data points for visualization
            if monthly_trend and len(monthly_trend) > 0:
                try:
                    # Calculate average of last 3 months
                    recent_months = monthly_trend[-3:] if len(monthly_trend) >= 3 else monthly_trend
                    recent_demand = [m['actualDemand'] for m in recent_months if 'actualDemand' in m]
                    avg_recent_demand = sum(recent_demand) / len(recent_demand) if recent_demand else 0
                    
                    # Add current and future months with forecast
                    current_date = datetime.now()
                    for i in range(3):  # Next 3 months
                        forecast_date = current_date + timedelta(days=30 * (i + 1))
                        monthly_trend.append({
                            'month': forecast_date.strftime("%b %Y"),
                            'actualDemand': 0,  # No actual data for future
                            'forecast': int(avg_recent_demand * (1.05 ** (i + 1))),  # 5% growth per month
                            'uniqueParts': 0,
                            'workOrders': 0
                        })
                except Exception as e:
                    # If forecast generation fails, just continue without forecast points
                    pass
            
            # Summary statistics
            order_now_count = sum(1 for f in forecasts if f['orderRecommendation'] == 'Order Now')
            order_soon_count = sum(1 for f in forecasts if f['orderRecommendation'] == 'Order Soon')
            
            return jsonify({
                'forecasts': forecasts,  # All parts, no limit
                'monthlyTrend': monthly_trend,
                'summary': {
                    'totalParts': len(forecasts),
                    'orderNowCount': order_now_count,
                    'orderSoonCount': order_soon_count,
                    'totalForecastValue': total_forecast_value,
                    'forecastPeriod': forecast_days
                },
                'forecastDays': forecast_days,
                'leadTimeAssumption': 14,
                'analysisInfo': {
                    'description': 'Based on 12 months historical usage patterns with trend analysis',
                    'period': 'Last 12 months'
                },
                'forecastInfo': {
                    'method': 'Historical average with trend adjustment',
                    'confidence': 'Based on 12 months historical data',
                    'factors': [
                        'Average monthly demand',
                        'Demand trend (growing/declining)',
                        'Seasonal variations',
                        'Equipment count using part'
                    ]
                }
            })
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Forecast error: {str(e)}")
            print(f"Traceback: {error_details}")
            return jsonify({
                'error': str(e),
                'type': 'forecast_error',
                'details': error_details[:500]  # First 500 chars of traceback
            }), 500


    @reports_bp.route('/departments/parts/fill-rate', methods=['GET'])
    @jwt_required()
    def get_parts_fill_rate():
        """Get parts fill rate analysis - shows parts that were not in stock when ordered"""
        try:
            db = get_db()
            
            # Get the time period (default last 30 days)
            days_back = request.args.get('days', 30, type=int)
            
            # Query to find parts orders and their stock status
            # This identifies when a part was requested but had zero or insufficient stock
            fill_rate_query = f"""
            WITH PartsOrders AS (
                SELECT 
                    wp.PartNo,
                    wp.WONo,
                    w.OpenDate as OrderDate,
                    wp.Qty as OrderedQty,
                    wp.BOQty as BackorderQty,
                    wp.Description,
                    -- Get the current stock level (approximation)
                    COALESCE(p.OnHand, 0) as CurrentStock,
                    -- Determine if this was a stockout based on backorder quantity
                    CASE 
                        WHEN wp.BOQty > 0 THEN 'Backordered'
                        WHEN p.OnHand IS NULL OR p.OnHand = 0 THEN 'Out of Stock'
                        WHEN p.OnHand < wp.Qty THEN 'Partial Stock'
                        ELSE 'In Stock'
                    END as StockStatus,
                    w.BillTo as Customer
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
                WHERE w.OpenDate >= DATEADD(day, -{days_back}, GETDATE())
                    AND (wp.PartNo LIKE 'L%' OR wp.Description LIKE '%LINDE%')  -- Linde parts
            )
            SELECT 
                -- Overall metrics
                COUNT(*) as TotalOrders,
                SUM(CASE WHEN StockStatus = 'In Stock' THEN 1 ELSE 0 END) as FilledOrders,
                SUM(CASE WHEN StockStatus != 'In Stock' THEN 1 ELSE 0 END) as UnfilledOrders,
                SUM(CASE WHEN StockStatus = 'Backordered' THEN 1 ELSE 0 END) as BackorderedOrders,
                CAST(
                    CAST(SUM(CASE WHEN StockStatus = 'In Stock' THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) * 100 
                AS DECIMAL(5,2)) as FillRate
            FROM PartsOrders
            """
            
            fill_rate_result = db.execute_query(fill_rate_query)
            
            # Get details of parts most frequently out of stock
            problem_parts_query = f"""
            WITH PartsOrders AS (
                SELECT 
                    wp.PartNo,
                    wp.Description,
                    wp.Qty as OrderedQty,
                    COALESCE(p.OnHand, 0) as StockOnHand,
                    CASE 
                        WHEN p.OnHand IS NULL OR p.OnHand = 0 THEN 'Out of Stock'
                        WHEN p.OnHand < wp.Qty THEN 'Insufficient Stock'
                        ELSE 'In Stock'
                    END as StockStatus
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
                WHERE w.OpenDate >= DATEADD(day, -{days_back}, GETDATE())
                    AND (wp.PartNo LIKE 'L%' OR wp.Description LIKE '%LINDE%')
            )
            SELECT TOP 10
                PartNo,
                MAX(Description) as Description,
                COUNT(*) as TotalOrders,
                SUM(CASE WHEN StockStatus != 'In Stock' THEN 1 ELSE 0 END) as StockoutCount,
                MAX(StockOnHand) as CurrentStock,
                CAST(
                    CAST(SUM(CASE WHEN StockStatus != 'In Stock' THEN 1 ELSE 0 END) AS FLOAT) / 
                    CAST(COUNT(*) AS FLOAT) * 100 
                AS DECIMAL(5,2)) as StockoutRate
            FROM PartsOrders
            GROUP BY PartNo
            HAVING SUM(CASE WHEN StockStatus != 'In Stock' THEN 1 ELSE 0 END) > 0
            ORDER BY StockoutCount DESC
            """
            
            problem_parts_result = db.execute_query(problem_parts_query)
            
            # Parse results
            fill_rate_data = {}
            if fill_rate_result and len(fill_rate_result) > 0:
                row = fill_rate_result[0]
                fill_rate_data = {
                    'totalOrders': row.get('TotalOrders', 0),
                    'filledOrders': row.get('FilledOrders', 0),
                    'unfilledOrders': row.get('UnfilledOrders', 0),
                    'fillRate': float(row.get('FillRate', 0))
                }
            else:
                fill_rate_data = {
                    'totalOrders': 0,
                    'filledOrders': 0,
                    'unfilledOrders': 0,
                    'fillRate': 0
                }
            
            # Parse problem parts
            problem_parts = []
            if problem_parts_result:
                for row in problem_parts_result:
                    problem_parts.append({
                        'partNo': row.get('PartNo', ''),
                        'description': row.get('Description', ''),
                        'totalOrders': row.get('TotalOrders', 0),
                        'stockoutCount': row.get('StockoutCount', 0),
                        'currentStock': row.get('CurrentStock', 0),
                        'stockoutRate': float(row.get('StockoutRate', 0))
                    })
            
            # Get fill rate trend over time
            trend_query = f"""
            WITH MonthlyOrders AS (
                SELECT 
                    YEAR(w.OpenDate) as Year,
                    MONTH(w.OpenDate) as Month,
                    COUNT(*) as TotalOrders,
                    SUM(CASE 
                        WHEN p.OnHand IS NULL OR p.OnHand = 0 OR p.OnHand < wp.Qty 
                        THEN 0 ELSE 1 
                    END) as FilledOrders
                FROM ben002.WOParts wp
                INNER JOIN ben002.WO w ON wp.WONo = w.WONo
                LEFT JOIN ben002.Parts p ON wp.PartNo = p.PartNo
                WHERE w.OpenDate >= DATEADD(month, -6, GETDATE())
                    AND (wp.PartNo LIKE 'L%' OR wp.Description LIKE '%LINDE%')
                GROUP BY YEAR(w.OpenDate), MONTH(w.OpenDate)
            )
            SELECT 
                Year,
                Month,
                TotalOrders,
                FilledOrders,
                CAST(
                    CAST(FilledOrders AS FLOAT) / CAST(TotalOrders AS FLOAT) * 100 
                AS DECIMAL(5,2)) as FillRate
            FROM MonthlyOrders
            ORDER BY Year, Month
            """
            
            trend_result = db.execute_query(trend_query)
            
            fill_rate_trend = []
            if trend_result:
                for row in trend_result:
                    month_date = datetime(row['Year'], row['Month'], 1)
                    fill_rate_trend.append({
                        'month': month_date.strftime("%b"),
                        'fillRate': float(row.get('FillRate', 0)),
                        'totalOrders': row.get('TotalOrders', 0),
                        'filledOrders': row.get('FilledOrders', 0)
                    })
            
            return jsonify({
                'summary': fill_rate_data,
                'problemParts': problem_parts,
                'fillRateTrend': fill_rate_trend,
                'period': f'Last {days_back} days'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'parts_fill_rate_error'
            }), 500

    @reports_bp.route('/departments/parts/inventory-by-location', methods=['GET'])
    @require_permission('view_parts_inventory_location', 'view_parts')
    def get_parts_inventory_by_location():
        """Get parts inventory value by bin location"""
        try:
            db = get_db()
            
            # Get optional location filter from query params
            location_filter = request.args.get('location', '')
            
            # Log the incoming request
            print(f"[DEBUG] Inventory by location request - Filter: '{location_filter}'")
            
            # Sanitize location filter to prevent SQL injection
            if location_filter:
                # Remove any potentially dangerous characters
                location_filter = location_filter.replace("'", "''").replace(";", "").replace("--", "")
                print(f"[DEBUG] Sanitized filter: '{location_filter}'")
            
            # Build the query to get all bin locations with their values
            if location_filter:
                location_condition = f"AND UPPER(Location) LIKE '%{location_filter.upper()}%'"
            else:
                location_condition = ""
            
            print(f"[DEBUG] Location condition: '{location_condition}'")
            
            query = f"""
            WITH AllBins AS (
                -- Primary Bin location
                SELECT 
                    Bin as Location,
                    PartNo,
                    Description,
                    OnHand,
                    Cost,
                    CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                FROM ben002.Parts 
                WHERE Bin IS NOT NULL AND Bin != '' AND OnHand > 0
                
                UNION ALL
                
                -- Bin1 location
                SELECT 
                    Bin1 as Location,
                    PartNo,
                    Description,
                    OnHand,
                    Cost,
                    CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                FROM ben002.Parts 
                WHERE Bin1 IS NOT NULL AND Bin1 != '' AND OnHand > 0
                
                UNION ALL
                
                -- Bin2 location
                SELECT 
                    Bin2 as Location,
                    PartNo,
                    Description,
                    OnHand,
                    Cost,
                    CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                FROM ben002.Parts 
                WHERE Bin2 IS NOT NULL AND Bin2 != '' AND OnHand > 0
                
                UNION ALL
                
                -- Bin3 location
                SELECT 
                    Bin3 as Location,
                    PartNo,
                    Description,
                    OnHand,
                    Cost,
                    CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                FROM ben002.Parts 
                WHERE Bin3 IS NOT NULL AND Bin3 != '' AND OnHand > 0
                
                UNION ALL
                
                -- Bin4 location
                SELECT 
                    Bin4 as Location,
                    PartNo,
                    Description,
                    OnHand,
                    Cost,
                    CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                FROM ben002.Parts 
                WHERE Bin4 IS NOT NULL AND Bin4 != '' AND OnHand > 0
            ),
            LocationSummary AS (
                SELECT 
                    UPPER(LTRIM(RTRIM(Location))) as Location,
                    COUNT(DISTINCT PartNo) as PartCount,
                    COUNT(*) as TotalEntries,
                    CAST(SUM(TotalValue) AS DECIMAL(10,2)) as TotalValue
                FROM AllBins
                WHERE 1=1 {location_condition}
                GROUP BY UPPER(LTRIM(RTRIM(Location)))
            )
            SELECT 
                Location,
                PartCount,
                TotalEntries,
                TotalValue
            FROM LocationSummary
            ORDER BY TotalValue DESC
            """
            
            print(f"[DEBUG] About to execute summary query")
            
            try:
                summary_result = db.execute_query(query)
                print(f"[DEBUG] Summary query executed successfully, rows returned: {len(summary_result) if summary_result else 0}")
            except Exception as query_error:
                print(f"[ERROR] Summary query failed: {str(query_error)}")
                print(f"[ERROR] Query was: {query[:500]}...")  # Print first 500 chars of query
                return jsonify({
                    'error': f'Database query failed: {str(query_error)}',
                    'type': 'query_execution_error',
                    'location_filter': location_filter
                }), 500
            
            # Get details for specific location if requested
            details = []
            if location_filter:
                # Location filter is already sanitized above
                safe_filter = location_filter.upper()
                details_query = f"""
                WITH AllBins AS (
                    SELECT 'Primary' as BinType, Bin as Location, PartNo, Description, OnHand, Cost,
                           CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                    FROM ben002.Parts 
                    WHERE Bin IS NOT NULL AND Bin != '' AND OnHand > 0
                        AND UPPER(Bin) LIKE '%{safe_filter}%'
                    
                    UNION ALL
                    
                    SELECT 'Alt 1' as BinType, Bin1 as Location, PartNo, Description, OnHand, Cost,
                           CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                    FROM ben002.Parts 
                    WHERE Bin1 IS NOT NULL AND Bin1 != '' AND OnHand > 0
                        AND UPPER(Bin1) LIKE '%{safe_filter}%'
                    
                    UNION ALL
                    
                    SELECT 'Alt 2' as BinType, Bin2 as Location, PartNo, Description, OnHand, Cost,
                           CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                    FROM ben002.Parts 
                    WHERE Bin2 IS NOT NULL AND Bin2 != '' AND OnHand > 0
                        AND UPPER(Bin2) LIKE '%{safe_filter}%'
                    
                    UNION ALL
                    
                    SELECT 'Alt 3' as BinType, Bin3 as Location, PartNo, Description, OnHand, Cost,
                           CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                    FROM ben002.Parts 
                    WHERE Bin3 IS NOT NULL AND Bin3 != '' AND OnHand > 0
                        AND UPPER(Bin3) LIKE '%{safe_filter}%'
                    
                    UNION ALL
                    
                    SELECT 'Alt 4' as BinType, Bin4 as Location, PartNo, Description, OnHand, Cost,
                           CAST(OnHand * Cost AS DECIMAL(10,2)) as TotalValue
                    FROM ben002.Parts 
                    WHERE Bin4 IS NOT NULL AND Bin4 != '' AND OnHand > 0
                        AND UPPER(Bin4) LIKE '%{safe_filter}%'
                )
                SELECT 
                    PartNo,
                    Description,
                    Location,
                    BinType,
                    OnHand,
                    Cost,
                    TotalValue
                FROM AllBins
                ORDER BY TotalValue DESC
                """
                
                print(f"[DEBUG] About to execute details query for filter: '{safe_filter}'")
                
                try:
                    details_result = db.execute_query(details_query)
                    print(f"[DEBUG] Details query executed successfully, rows returned: {len(details_result) if details_result else 0}")
                except Exception as details_error:
                    print(f"[ERROR] Details query failed: {str(details_error)}")
                    # Don't fail the whole request if details fail, just log it
                    details_result = None
                
                if details_result:
                    for row in details_result:
                        details.append({
                            'partNo': row.get('PartNo', ''),
                            'description': row.get('Description', ''),
                            'location': row.get('Location', ''),
                            'binType': row.get('BinType', ''),
                            'onHand': float(row.get('OnHand', 0)),
                            'cost': float(row.get('Cost', 0)),
                            'totalValue': float(row.get('TotalValue', 0))
                        })
            
            # Parse summary results
            locations = []
            grand_total = 0
            if summary_result:
                for row in summary_result:
                    location_value = float(row.get('TotalValue', 0))
                    grand_total += location_value
                    locations.append({
                        'location': row.get('Location', ''),
                        'partCount': row.get('PartCount', 0),
                        'totalEntries': row.get('TotalEntries', 0),
                        'totalValue': location_value
                    })
            
            return jsonify({
                'locations': locations,
                'details': details,
                'grandTotal': grand_total,
                'locationFilter': location_filter
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"[ERROR] Unexpected error in inventory-by-location endpoint: {str(e)}")
            print(f"[ERROR] Full traceback: {error_trace}")
            
            return jsonify({
                'error': str(e),
                'type': 'parts_inventory_location_error',
                'location_filter': request.args.get('location', ''),
                'debug_info': 'Check server logs for detailed error information'
            }), 500


    @reports_bp.route('/departments/parts/employee-invoice-details', methods=['GET'])
    @jwt_required()
    def get_parts_employee_invoice_details():
        """Get detailed invoice list for a specific employee's parts sales using OpenBy field"""
        try:
            db = get_db()
            
            employee_id = request.args.get('employee_id')  # This is now the employee name
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            days_back = request.args.get('days', 30, type=int)
            
            # Build date filter
            if start_date and end_date:
                date_filter = f"InvoiceDate BETWEEN '{start_date}' AND '{end_date}'"
            else:
                date_filter = f"InvoiceDate >= DATEADD(day, -{days_back}, GETDATE())"
            
            # Build employee filter (employee_id is now the name)
            if employee_id and employee_id != 'all':
                # Escape single quotes in employee name for SQL
                safe_employee_name = employee_id.replace("'", "''")
                employee_filter = f"AND OpenBy = '{safe_employee_name}'"
            else:
                employee_filter = ""
            
            # Get invoice details - ONLY CSTPRT sale code
            query = f"""
            SELECT 
                InvoiceNo,
                InvoiceDate,
                ISNULL(OpenBy, 'Unknown') as EmployeeName,
                BillTo,
                BillToName,
                ISNULL(PartsTaxable, 0) as PartsTaxable,
                ISNULL(PartsNonTax, 0) as PartsNonTax,
                ISNULL(PartsTaxable, 0) + ISNULL(PartsNonTax, 0) as TotalParts,
                ISNULL(LaborTaxable, 0) + ISNULL(LaborNonTax, 0) as TotalLabor,
                ISNULL(MiscTaxable, 0) + ISNULL(MiscNonTax, 0) as TotalMisc,
                GrandTotal,
                SaleCode,
                ISNULL(ClosedBy, OpenBy) as ClosedBy
            FROM ben002.InvoiceReg
            WHERE (ISNULL(PartsTaxable, 0) > 0 OR ISNULL(PartsNonTax, 0) > 0)
                AND SaleCode = 'CSTPRT'
                AND OpenBy IS NOT NULL
                AND OpenBy != ''
                AND {date_filter}
                {employee_filter}
            ORDER BY InvoiceDate DESC, InvoiceNo DESC
            """
            
            result = db.execute_query(query)
            
            invoices = []
            if result:
                for row in result:
                    invoices.append({
                        'invoiceNo': row.get('InvoiceNo'),
                        'invoiceDate': row.get('InvoiceDate').strftime('%Y-%m-%d %H:%M') if row.get('InvoiceDate') else None,
                        'employeeId': row.get('EmployeeName'),  # Now using name as ID
                        'employeeName': row.get('EmployeeName'),
                        'billTo': row.get('BillTo', ''),
                        'billToName': row.get('BillToName', ''),
                        'partsTaxable': float(row.get('PartsTaxable', 0)),
                        'partsNonTax': float(row.get('PartsNonTax', 0)),
                        'totalParts': float(row.get('TotalParts', 0)),
                        'totalLabor': float(row.get('TotalLabor', 0)),
                        'totalMisc': float(row.get('TotalMisc', 0)),
                        'grandTotal': float(row.get('GrandTotal', 0)),
                        'saleCode': row.get('SaleCode', ''),
                        'lastModifiedBy': row.get('ClosedBy', '')
                    })
            
            return jsonify({
                'invoices': invoices,
                'count': len(invoices),
                'totalParts': sum(inv['totalParts'] for inv in invoices)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'invoice_details_error'
            }), 500


    @reports_bp.route('/departments/parts/employee-performance', methods=['GET'])
    @jwt_required()
    def get_parts_employee_performance():
        """Get parts sales performance by employee using OpenBy field for actual names"""
        try:
            db = get_db()
            
            # Get date range from query params
            days_back = request.args.get('days', 30, type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Build date filter
            if start_date and end_date:
                date_filter = f"InvoiceDate BETWEEN '{start_date}' AND '{end_date}'"
            else:
                date_filter = f"InvoiceDate >= DATEADD(day, -{days_back}, GETDATE())"
            
            # Main query to get parts sales by employee using OpenBy field
            query = f"""
            WITH PartsSales AS (
                SELECT 
                    ISNULL(OpenBy, 'Unknown') as EmployeeName,
                    COUNT(DISTINCT InvoiceNo) as TotalInvoices,
                    COUNT(DISTINCT CAST(InvoiceDate AS DATE)) as DaysWorked,
                    SUM(ISNULL(PartsTaxable, 0) + ISNULL(PartsNonTax, 0)) as TotalPartsSales,
                    AVG(ISNULL(PartsTaxable, 0) + ISNULL(PartsNonTax, 0)) as AvgInvoiceValue,
                    MAX(InvoiceDate) as LastSaleDate,
                    MIN(InvoiceDate) as FirstSaleDate
                FROM ben002.InvoiceReg
                WHERE (ISNULL(PartsTaxable, 0) > 0 OR ISNULL(PartsNonTax, 0) > 0)
                    AND SaleCode = 'CSTPRT'
                    AND OpenBy IS NOT NULL
                    AND OpenBy != ''
                    AND {date_filter}
                GROUP BY OpenBy
            ),
            DailyAverages AS (
                SELECT 
                    EmployeeName,
                    TotalInvoices,
                    DaysWorked,
                    TotalPartsSales,
                    AvgInvoiceValue,
                    CASE 
                        WHEN DaysWorked > 0 THEN TotalPartsSales / DaysWorked 
                        ELSE 0 
                    END as AvgDailySales,
                    CASE 
                        WHEN DaysWorked > 0 THEN CAST(TotalInvoices AS FLOAT) / DaysWorked 
                        ELSE 0 
                    END as AvgDailyInvoices,
                    LastSaleDate,
                    FirstSaleDate
                FROM PartsSales
            )
            SELECT 
                EmployeeName,
                TotalInvoices,
                DaysWorked,
                CAST(TotalPartsSales AS DECIMAL(10,2)) as TotalPartsSales,
                CAST(AvgInvoiceValue AS DECIMAL(10,2)) as AvgInvoiceValue,
                CAST(AvgDailySales AS DECIMAL(10,2)) as AvgDailySales,
                CAST(AvgDailyInvoices AS DECIMAL(5,1)) as AvgDailyInvoices,
                LastSaleDate,
                FirstSaleDate,
                DATEDIFF(day, LastSaleDate, GETDATE()) as DaysSinceLastSale
            FROM DailyAverages
            ORDER BY TotalPartsSales DESC
            """
            
            result = db.execute_query(query)
            
            # First, let's check what columns exist for employee tracking
            # Looking for CreatedBy, ChangedBy, ClosedBy or similar fields
            check_columns_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = 'ben002' 
                AND TABLE_NAME = 'InvoiceReg'
                AND (COLUMN_NAME LIKE '%Created%' 
                    OR COLUMN_NAME LIKE '%Changed%' 
                    OR COLUMN_NAME LIKE '%Closed%'
                    OR COLUMN_NAME LIKE '%User%'
                    OR COLUMN_NAME LIKE '%Employee%')
            """
            
            try:
                columns_result = db.execute_query(check_columns_query)
                available_columns = [row['COLUMN_NAME'] for row in columns_result] if columns_result else []
                
                # Log available columns for debugging
                print(f"Available employee-related columns: {available_columns}")
            except:
                available_columns = []
            
            # Parse results
            employees = []
            total_sales = 0
            
            if result:
                for row in result:
                    emp_name = row.get('EmployeeName', 'Unknown')
                    
                    # Split name into first and last
                    name_parts = emp_name.split(' ', 1) if emp_name else ['', '']
                    first_name = name_parts[0] if name_parts else ''
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    employee_data = {
                        'employeeId': emp_name,  # Use name as ID for now
                        'employeeName': emp_name,
                        'firstName': first_name,
                        'lastName': last_name,
                        'totalInvoices': row.get('TotalInvoices', 0),
                        'daysWorked': row.get('DaysWorked', 0),
                        'totalSales': float(row.get('TotalPartsSales', 0)),
                        'avgInvoiceValue': float(row.get('AvgInvoiceValue', 0)),
                        'avgDailySales': float(row.get('AvgDailySales', 0)),
                        'avgDailyInvoices': float(row.get('AvgDailyInvoices', 0)),
                        'lastSaleDate': row.get('LastSaleDate').strftime('%Y-%m-%d') if row.get('LastSaleDate') else None,
                        'firstSaleDate': row.get('FirstSaleDate').strftime('%Y-%m-%d') if row.get('FirstSaleDate') else None,
                        'daysSinceLastSale': row.get('DaysSinceLastSale', 0)
                    }
                    employees.append(employee_data)
                    total_sales += employee_data['totalSales']
            
            # Calculate percentages
            for emp in employees:
                emp['percentOfTotal'] = round((emp['totalSales'] / total_sales * 100), 1) if total_sales > 0 else 0
            
            # Note: Detailed parts breakdown by employee removed due to data model constraints
            # InvoiceReg doesn't directly link to WOParts, would need InvoiceSales table
            # or different approach to get part-level details per employee
            
            # Prepare top performer with name
            top_performer = None
            if employees:
                top_performer = employees[0].copy()
                # Ensure the top performer has the name fields
                if not top_performer.get('employeeName'):
                    top_performer['employeeName'] = ''
            
            return jsonify({
                'employees': employees,
                'summary': {
                    'totalEmployees': len(employees),
                    'totalSales': total_sales,
                    'topPerformer': top_performer,
                    'period': f'Last {days_back} days' if not start_date else f'{start_date} to {end_date}'
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'parts_employee_performance_error'
            }), 500


    @reports_bp.route('/departments/rental/pace', methods=['GET'])
    @jwt_required()
    def get_rental_pace():
        """Get rental department revenue pace comparing current month to previous month"""
        try:
            db = get_db()
            
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
            
            # Get rental revenue through same day for current and previous month
            # Use RentalTaxable + RentalNonTax to match the monthly revenue calculation
            current_query = f"""
            SELECT SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {current_year}
                AND MONTH(InvoiceDate) = {current_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
            """
            
            prev_query = f"""
            SELECT SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND DAY(InvoiceDate) <= {current_day}
                AND (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
            """
            
            # Get full previous month total for comparison
            full_month_query = f"""
            SELECT SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as total_revenue
            FROM ben002.InvoiceReg
            WHERE YEAR(InvoiceDate) = {prev_year}
                AND MONTH(InvoiceDate) = {prev_month}
                AND (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
            """
            
            # Get adaptive comparison data
            adaptive_query = f"""
            WITH MonthlyTotals AS (
                SELECT 
                    YEAR(InvoiceDate) as year,
                    MONTH(InvoiceDate) as month,
                    SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as total_revenue
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
                    AND YEAR(InvoiceDate) * 100 + MONTH(InvoiceDate) < {current_year} * 100 + {current_month}
                    AND (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
                GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            )
            SELECT 
                AVG(total_revenue) as avg_monthly_revenue,
                MAX(total_revenue) as best_monthly_revenue,
                MIN(total_revenue) as worst_monthly_revenue,
                COUNT(*) as months_available,
                MAX(CASE WHEN month = {current_month} THEN total_revenue END) as same_month_last_year
            FROM MonthlyTotals
            """
            
            current_result = db.execute_query(current_query)
            prev_result = db.execute_query(prev_query)
            full_month_result = db.execute_query(full_month_query)
            adaptive_result = db.execute_query(adaptive_query)
            
            current_revenue = float(current_result[0]['total_revenue'] or 0) if current_result else 0
            previous_revenue = float(prev_result[0]['total_revenue'] or 0) if prev_result else 0
            previous_full_month = float(full_month_result[0]['total_revenue'] or 0) if full_month_result else 0
            
            # Extract adaptive data
            adaptive_data = adaptive_result[0] if adaptive_result else {}
            avg_monthly_revenue = float(adaptive_data.get('avg_monthly_revenue') or 0)
            best_monthly_revenue = float(adaptive_data.get('best_monthly_revenue') or 0)
            worst_monthly_revenue = float(adaptive_data.get('worst_monthly_revenue') or 0)
            months_available = int(adaptive_data.get('months_available') or 0)
            same_month_last_year = float(adaptive_data.get('same_month_last_year') or 0)
            
            # Calculate multiple pace percentages for adaptive comparison
            # 1. Previous month comparison (existing logic)
            if current_revenue > previous_full_month and previous_full_month > 0:
                pace_percentage = round(((current_revenue / previous_full_month) - 1) * 100, 1)
                comparison_base = "full_previous_month"
            else:
                pace_percentage = round(((current_revenue / previous_revenue) - 1) * 100, 1) if previous_revenue > 0 else 0
                comparison_base = "same_day_previous_month"
            
            # Calculate projected month total for fair comparison
            import calendar
            days_in_month = calendar.monthrange(current_year, current_month)[1]
            projected_revenue = (current_revenue / current_day) * days_in_month if current_day > 0 else 0
            
            # 2. Additional adaptive comparisons (use projected total for fair comparison)
            pace_pct_avg = round(((projected_revenue / avg_monthly_revenue) - 1) * 100, 1) if avg_monthly_revenue > 0 else None
            pace_pct_same_month_ly = round(((projected_revenue / same_month_last_year) - 1) * 100, 1) if same_month_last_year > 0 else None
            is_best_month = projected_revenue > best_monthly_revenue
            
            return jsonify({
                'pace_percentage': pace_percentage,
                'current_revenue': current_revenue,
                'previous_revenue': previous_revenue,
                'previous_full_month': previous_full_month,
                'current_month': current_month,
                'current_day': current_day,
                'comparison_base': comparison_base,
                'exceeded_previous_month': current_revenue > previous_full_month,
                'adaptive_comparisons': {
                    'available_months_count': months_available,
                    'vs_available_average': {
                        'percentage': pace_pct_avg,
                        'average_monthly_revenue': avg_monthly_revenue,
                        'ahead_behind': 'ahead' if pace_pct_avg and pace_pct_avg > 0 else 'behind' if pace_pct_avg and pace_pct_avg < 0 else 'on pace' if pace_pct_avg is not None else None
                    },
                    'vs_same_month_last_year': {
                        'percentage': pace_pct_same_month_ly,
                        'last_year_revenue': same_month_last_year if same_month_last_year > 0 else None,
                        'ahead_behind': 'ahead' if pace_pct_same_month_ly and pace_pct_same_month_ly > 0 else 'behind' if pace_pct_same_month_ly and pace_pct_same_month_ly < 0 else 'on pace' if pace_pct_same_month_ly is not None else None
                    },
                    'performance_indicators': {
                        'is_best_month_ever': is_best_month,
                        'best_month_revenue': best_monthly_revenue,
                        'worst_month_revenue': worst_monthly_revenue,
                        'vs_best_percentage': round(((current_revenue / best_monthly_revenue) - 1) * 100, 1) if best_monthly_revenue > 0 else None,
                        'vs_worst_percentage': round(((current_revenue / worst_monthly_revenue) - 1) * 100, 1) if worst_monthly_revenue > 0 else None
                    }
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching rental pace: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/rental', methods=['GET'])
    @require_permission('view_rental')
    def get_rental_department_report():
        """Get Rental Department report data"""
        try:
            db = get_db()
            
            # 1. Summary metrics
            summary_query = """
            SELECT 
                -- Total Fleet Size
                (SELECT COUNT(*) FROM ben002.Equipment 
                 WHERE WebRentalFlag = 1) as totalFleetSize,
                
                -- Units on Rent
                (SELECT COUNT(*) FROM ben002.Equipment 
                 WHERE RentalStatus = 'Rented') as unitsOnRent,
                 
                -- Monthly Revenue
                (SELECT SUM(GrandTotal) 
                 FROM ben002.InvoiceReg 
                 WHERE MONTH(InvoiceDate) = MONTH(GETDATE())
                 AND YEAR(InvoiceDate) = YEAR(GETDATE())) as monthlyRevenue
            """
            
            summary_result = db.execute_query(summary_query)
            
            total_fleet = summary_result[0][0] or 1  # Avoid division by zero
            units_on_rent = summary_result[0][1] or 0
            
            summary = {
                'totalFleetSize': total_fleet,
                'unitsOnRent': units_on_rent,
                'utilizationRate': round((units_on_rent / total_fleet) * 100, 1) if total_fleet > 0 else 0,
                'monthlyRevenue': float(summary_result[0][2] or 0),
                'overdueReturns': 0,  # Would need return date tracking
                'maintenanceDue': 0   # Would need maintenance schedule
            }
            
            # 2. Fleet by Category
            fleet_query = """
            SELECT 
                CASE 
                    WHEN Model LIKE '%EXCAVATOR%' THEN 'Excavators'
                    WHEN Model LIKE '%LOADER%' THEN 'Loaders'
                    WHEN Model LIKE '%DOZER%' THEN 'Dozers'
                    WHEN Model LIKE '%COMPACTOR%' THEN 'Compactors'
                    ELSE 'Other'
                END as category,
                COUNT(*) as total,
                SUM(CASE WHEN RentalStatus = 'Rented' THEN 1 ELSE 0 END) as onRent
            FROM ben002.Equipment
            WHERE WebRentalFlag = 1
            GROUP BY 
                CASE 
                    WHEN Model LIKE '%EXCAVATOR%' THEN 'Excavators'
                    WHEN Model LIKE '%LOADER%' THEN 'Loaders'
                    WHEN Model LIKE '%DOZER%' THEN 'Dozers'
                    WHEN Model LIKE '%COMPACTOR%' THEN 'Compactors'
                    ELSE 'Other'
                END
            """
            
            fleet_result = db.execute_query(fleet_query)
            
            fleetByCategory = []
            for row in fleet_result:
                total = row[1]
                on_rent = row[2]
                fleetByCategory.append({
                    'category': row[0],
                    'total': total,
                    'onRent': on_rent,
                    'available': total - on_rent
                })
            
            # 3. Active Rentals
            rentals_query = """
            SELECT TOP 5
                w.WONo,
                w.BillTo as Customer,
                e.Make + ' ' + e.Model as equipment,
                w.OpenDate as startDate,
                NULL as endDate,  -- Would need return tracking
                0 as dailyRate,   -- Would need rate table
                'Active' as status
            FROM ben002.WO w
            -- Equipment join removed - column mapping issues
            -- JOIN ben002.Equipment e ON w.UnitNo = e.StockNo
            WHERE w.Type = 'R' AND w.ClosedDate IS NULL
            ORDER BY w.OpenDate DESC
            """
            
            rentals_result = db.execute_query(rentals_query)
            
            activeRentals = []
            for row in rentals_result:
                activeRentals.append({
                    'contractNumber': f'RC-{row[0]}',
                    'customer': row[1] or 'Unknown',
                    'equipment': row[2] or 'N/A',
                    'startDate': row[3].strftime('%Y-%m-%d') if row[3] else '',
                    'endDate': row[4].strftime('%Y-%m-%d') if row[4] else '',
                    'dailyRate': row[5],
                    'status': row[6]
                })
            
            # 4. Monthly Trend
            trend_query = """
            SELECT 
                DATENAME(month, InvoiceDate) as month,
                SUM(GrandTotal) as revenue,
                COUNT(*) as rentals
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY DATENAME(month, InvoiceDate), MONTH(InvoiceDate), YEAR(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            trend_result = db.execute_query(trend_query)
            
            monthlyTrend = []
            for row in trend_result:
                monthlyTrend.append({
                    'month': row[0][:3],
                    'revenue': float(row[1] or 0),
                    'utilization': 0
                })
            
            # Rental duration data not available yet
            rentalsByDuration = []
            
            topCustomers = []
            
            return jsonify({
                'summary': summary,
                'fleetByCategory': fleetByCategory,
                'activeRentals': activeRentals,
                'monthlyTrend': monthlyTrend,
                'rentalsByDuration': rentalsByDuration,
                'topCustomers': topCustomers
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_report_error'
            }), 500


    @reports_bp.route('/departments/rental/sale-codes', methods=['GET'])
    @jwt_required()
    def get_sale_codes():
        """Get all unique SaleCodes to identify rental patterns"""
        try:
            db = get_db()
            
            # Get unique sale codes with counts
            codes_query = """
            SELECT 
                w.SaleCode,
                w.SaleDept,
                COUNT(*) as Count,
                MIN(c.CustomerName) as SampleCustomer
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.Customer
            WHERE w.Type = 'S'
            AND w.OpenDate >= DATEADD(month, -3, GETDATE())
            GROUP BY w.SaleCode, w.SaleDept
            ORDER BY Count DESC
            """
            
            codes = db.execute_query(codes_query)
            
            # Also get a sample of work orders that might be rental
            rental_sample_query = """
            SELECT TOP 10
                w.WONo,
                w.SaleCode,
                w.SaleDept,
                w.BillTo,
                c.CustomerName,
                w.Comments
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.Customer
            WHERE w.Type = 'S'
            AND (
                c.CustomerName LIKE '%Rental%' OR
                w.Comments LIKE '%rental%' OR
                w.Comments LIKE '%RENTAL%'
            )
            ORDER BY w.OpenDate DESC
            """
            
            rental_samples = db.execute_query(rental_sample_query)
            
            return jsonify({
                'sale_codes': codes,
                'rental_samples': rental_samples
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'sale_codes_error'
            }), 500

    @reports_bp.route('/departments/rental/wo-schema', methods=['GET'])
    @jwt_required()
    def get_wo_schema():
        """Diagnostic endpoint to understand WO table structure"""
        try:
            db = get_db()
            
            # Get column information for WO table
            schema_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
            AND TABLE_NAME = 'WO'
            ORDER BY ORDINAL_POSITION
            """
            
            columns = db.execute_query(schema_query)
            
            # Get a sample work order to see actual data
            sample_query = """
            SELECT TOP 1 *
            FROM ben002.WO
            WHERE Type = 'S'
            ORDER BY OpenDate DESC
            """
            
            sample = db.execute_query(sample_query)
            
            # Check for potential customer/billto fields
            customer_fields = []
            if columns:
                for col in columns:
                    col_name = col.get('COLUMN_NAME', '').lower()
                    if any(term in col_name for term in ['customer', 'cust', 'bill', 'client', 'account']):
                        customer_fields.append(col.get('COLUMN_NAME'))
            
            # Check WOLabor, WOParts, WOMisc table structures
            labor_cols_query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'WOLabor'
            ORDER BY ORDINAL_POSITION
            """
            
            parts_cols_query = """
            SELECT COLUMN_NAME, DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' AND TABLE_NAME = 'WOParts'
            ORDER BY ORDINAL_POSITION
            """
            
            labor_cols = db.execute_query(labor_cols_query)
            parts_cols = db.execute_query(parts_cols_query)
            
            return jsonify({
                'wo_columns': columns,
                'sample_work_order': sample[0] if sample else None,
                'potential_customer_fields': customer_fields,
                'labor_columns': labor_cols,
                'parts_columns': parts_cols
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'schema_error'
            }), 500


    @reports_bp.route('/departments/rental/service-report', methods=['GET'])
    @jwt_required()
    def get_rental_service_report():
        """Get Service Work Orders billed to Rental Department"""
        try:
            db = get_db()
            
            # Optimized query for rental work orders based on BillTo and Department
            optimized_query = """
            WITH RentalWOs AS (
                SELECT TOP 100
                    w.WONo,
                    w.BillTo,
                    w.BillTo as CustomerName,
                    COALESCE(w.ShipTo, w.ShipName, 'N/A') as ShipToCustomer,
                    w.UnitNo as Equipment,
                    w.SerialNo as SerialNumber,
                    w.Make,
                    w.Model,
                    w.OpenDate,
                    w.CompletedDate,
                    w.ClosedDate,
                    w.InvoiceDate,
                    CAST(NULL as varchar(50)) as InvoiceNo,
                    CASE 
                        WHEN w.ClosedDate IS NOT NULL THEN 'Closed'
                        WHEN w.InvoiceDate IS NOT NULL THEN 'Invoiced'
                        WHEN w.CompletedDate IS NOT NULL THEN 'Completed'
                        ELSE 'Open'
                    END as Status,
                    -- Calculate days since completion for completed but not invoiced WOs
                    CASE 
                        WHEN w.CompletedDate IS NOT NULL 
                             AND w.ClosedDate IS NULL 
                             AND w.InvoiceDate IS NULL 
                        THEN DATEDIFF(day, w.CompletedDate, GETDATE())
                        ELSE NULL
                    END as DaysSinceCompleted,
                    w.SaleCode,
                    w.SaleDept
                FROM ben002.WO w
                WHERE w.BillTo IN ('900006', '900066')  -- Specific BillTo customers
                AND w.SaleDept IN ('47', '45', '40')  -- PM (47), Shop Service (45), Field Service (40)
                AND (
                    -- Include Open work orders (not closed, not invoiced, not completed)
                    (w.ClosedDate IS NULL AND w.InvoiceDate IS NULL AND w.CompletedDate IS NULL)
                    OR 
                    -- Include Completed work orders (but not yet closed or invoiced)
                    (w.CompletedDate IS NOT NULL AND w.ClosedDate IS NULL AND w.InvoiceDate IS NULL)
                )
                AND w.OpenDate >= '2025-06-01'  -- Only work orders opened on or after June 1, 2025
                AND (
                    (w.WONo LIKE '140%' AND w.Type = 'S') OR  -- RENTR (Rental Repairs)
                    (w.WONo LIKE '145%' AND w.Type = 'SH') OR  -- RENTRS (Rental Shop) - Shop type
                    (w.WONo LIKE '147%' AND w.Type = 'PM')    -- RENTPM (Rental PM)
                )
                AND w.SaleCode IN ('RENTR', 'RENTRS', 'RENTPM')  -- Include all rental-related SaleCodes
                AND w.WONo NOT IN ('140001773', '140001780')  -- Exclude corrupt work orders
                ORDER BY w.OpenDate DESC
            ),
            -- Get sell prices (what customer pays) instead of costs
            LaborCosts AS (
                SELECT 
                    WONo,
                    SUM(Cost) as LaborCost,
                    SUM(Sell) as LaborSell
                FROM ben002.WOLabor
                WHERE WONo IN (SELECT WONo FROM RentalWOs)
                GROUP BY WONo
            ),
            -- Include labor quotes (flat rate labor)
            LaborQuotes AS (
                SELECT 
                    WONo,
                    SUM(Amount) as QuoteAmount
                FROM ben002.WOQuote
                WHERE WONo IN (SELECT WONo FROM RentalWOs)
                  AND Type = 'L'
                GROUP BY WONo
            ),
            PartsCosts AS (
                SELECT 
                    WONo,
                    SUM(Cost) as PartsCost,
                    SUM(Sell) as PartsSell
                FROM ben002.WOParts
                WHERE WONo IN (SELECT WONo FROM RentalWOs)
                GROUP BY WONo
            ),
            MiscCosts AS (
                SELECT 
                    WONo,
                    SUM(Cost) as MiscCost,
                    SUM(Sell) as MiscSell
                FROM ben002.WOMisc
                WHERE WONo IN (SELECT WONo FROM RentalWOs)
                GROUP BY WONo
            )
            SELECT 
                r.*,
                -- Get actual rental customer name using same approach as Availability Report
                COALESCE(rental_cust.Name, r.ShipToCustomer) as ActualShipToCustomer,
                COALESCE(l.LaborCost, 0) as LaborCost,
                COALESCE(p.PartsCost, 0) as PartsCost,
                COALESCE(m.MiscCost, 0) as MiscCost,
                COALESCE(l.LaborCost, 0) + COALESCE(p.PartsCost, 0) + COALESCE(m.MiscCost, 0) as TotalCost,
                -- New fields for invoice totals (sell prices)
                COALESCE(l.LaborSell, 0) as LaborSell,
                COALESCE(lq.QuoteAmount, 0) as LaborQuote,
                COALESCE(p.PartsSell, 0) as PartsSell,
                COALESCE(m.MiscSell, 0) as MiscSell,
                -- Total invoice amount (what customer pays)
                COALESCE(l.LaborSell, 0) + COALESCE(lq.QuoteAmount, 0) + COALESCE(p.PartsSell, 0) + COALESCE(m.MiscSell, 0) as InvoiceTotal
            FROM RentalWOs r
            LEFT JOIN LaborCosts l ON r.WONo = l.WONo
            LEFT JOIN LaborQuotes lq ON r.WONo = lq.WONo
            LEFT JOIN PartsCosts p ON r.WONo = p.WONo
            LEFT JOIN MiscCosts m ON r.WONo = m.WONo
            -- Join to find rental customer OUTSIDE the CTE, just like Availability Report
            LEFT JOIN (
                SELECT 
                    wr.SerialNo, 
                    wr.UnitNo, 
                    MAX(wo.WONo) as MaxWONo
                FROM ben002.WORental wr
                INNER JOIN ben002.WO wo ON wr.WONo = wo.WONo
                WHERE wo.Type = 'R' 
                AND wo.RentalContractNo IS NOT NULL 
                AND wo.RentalContractNo > 0
                GROUP BY wr.SerialNo, wr.UnitNo
            ) latest_rental ON (r.SerialNumber = latest_rental.SerialNo OR r.Equipment = latest_rental.UnitNo)
            LEFT JOIN ben002.WO rental_wo ON latest_rental.MaxWONo = rental_wo.WONo
            LEFT JOIN ben002.Customer rental_cust ON rental_wo.BillTo = rental_cust.Number
            ORDER BY InvoiceTotal DESC, r.OpenDate DESC
            """
            
            results = db.execute_query(optimized_query)
            
            # Process the results
            work_orders = []
            total_cost = 0
            total_invoice = 0
            
            for wo in results:
                labor_cost = float(wo.get('LaborCost', 0) or 0)
                parts_cost = float(wo.get('PartsCost', 0) or 0)
                misc_cost = float(wo.get('MiscCost', 0) or 0)
                total_wo_cost = float(wo.get('TotalCost', 0) or 0)
                
                # Invoice totals (sell prices)
                labor_sell = float(wo.get('LaborSell', 0) or 0)
                labor_quote = float(wo.get('LaborQuote', 0) or 0)
                parts_sell = float(wo.get('PartsSell', 0) or 0)
                misc_sell = float(wo.get('MiscSell', 0) or 0)
                invoice_total = float(wo.get('InvoiceTotal', 0) or 0)
                
                total_cost += total_wo_cost
                total_invoice += invoice_total
                
                work_orders.append({
                    'woNumber': wo.get('WONo'),
                    'billTo': wo.get('BillTo') or '',
                    'customer': wo.get('CustomerName') or wo.get('BillTo') or 'Unknown',
                    'shipToCustomer': wo.get('ActualShipToCustomer') or wo.get('ShipToCustomer') or '',
                    'unitNumber': wo.get('Equipment') or '',  # This is UnitNo from the query
                    'serialNumber': wo.get('SerialNumber') or '',
                    'make': wo.get('Make') or '',
                    'model': wo.get('Model') or '',
                    'openDate': wo.get('OpenDate').strftime('%Y-%m-%d') if wo.get('OpenDate') else None,
                    'completedDate': wo.get('CompletedDate').strftime('%Y-%m-%d') if wo.get('CompletedDate') else None,
                    'status': wo.get('Status'),
                    'daysSinceCompleted': wo.get('DaysSinceCompleted'),
                    'laborCost': labor_cost,
                    'partsCost': parts_cost,
                    'miscCost': misc_cost,
                    'totalCost': invoice_total  # Use invoice total instead of cost
                })
            
            
            # Calculate awaiting invoice metrics
            awaiting_invoice = [wo for wo in work_orders if wo['status'] == 'Completed']
            days_waiting = [wo['daysSinceCompleted'] for wo in awaiting_invoice if wo['daysSinceCompleted'] is not None]
            
            awaiting_invoice_metrics = {
                'count': len(awaiting_invoice),
                'totalValue': sum(wo['totalCost'] for wo in awaiting_invoice),
                'avgDaysWaiting': sum(days_waiting) / len(days_waiting) if days_waiting else 0,
                'overThreeDays': len([d for d in days_waiting if d > 3]),
                'overFiveDays': len([d for d in days_waiting if d > 5])
            }
            
            # Calculate totals - now using invoice amounts
            summary = {
                'totalWorkOrders': len(work_orders),
                'totalLaborCost': sum(wo['laborCost'] for wo in work_orders),
                'totalPartsCost': sum(wo['partsCost'] for wo in work_orders),
                'totalMiscCost': sum(wo['miscCost'] for wo in work_orders),
                'totalCost': total_invoice,  # Use invoice total
                'averageCostPerWO': total_invoice / len(work_orders) if work_orders else 0,
                'awaitingInvoice': awaiting_invoice_metrics
            }
            
            # Monthly trend query for rental work orders
            monthly_trend_query = """
            WITH MonthlyWOs AS (
                SELECT 
                    w.WONo,
                    YEAR(w.OpenDate) as Year,
                    MONTH(w.OpenDate) as Month,
                    DATENAME(month, w.OpenDate) as MonthName
                FROM ben002.WO w
                WHERE w.BillTo IN ('900006', '900066')
                AND w.SaleDept IN ('47', '45', '40')
                AND w.ClosedDate IS NULL  -- Only open work orders
                AND w.InvoiceDate IS NULL
                AND w.CompletedDate IS NULL  -- Not completed
                AND w.OpenDate >= '2025-06-01'  -- Only work orders opened on or after June 1, 2025
                AND (
                    (w.WONo LIKE '140%' AND w.Type = 'S') OR  -- RENTR (Rental Repairs) - Service only
                    (w.WONo LIKE '145%' AND w.Type = 'S') OR  -- RENTS (Rental Shop) - Service only
                    (w.WONo LIKE '147%' AND w.Type = 'PM')    -- RENTPM (Rental PM) - PM only
                )
            )
            SELECT 
                mw.Year,
                mw.Month,
                mw.MonthName,
                COUNT(DISTINCT mw.WONo) as WorkOrderCount,
                COALESCE(SUM(l.Cost), 0) as LaborCost,
                COALESCE(SUM(p.Cost), 0) as PartsCost,
                COALESCE(SUM(m.Cost), 0) as MiscCost,
                COALESCE(SUM(l.Cost) + SUM(p.Cost) + SUM(m.Cost), 0) as TotalCost
            FROM MonthlyWOs mw
            LEFT JOIN ben002.WOLabor l ON mw.WONo = l.WONo
            LEFT JOIN ben002.WOParts p ON mw.WONo = p.WONo
            LEFT JOIN ben002.WOMisc m ON mw.WONo = m.WONo
            GROUP BY mw.Year, mw.Month, mw.MonthName
            ORDER BY mw.Year DESC, mw.Month DESC
            """
            
            try:
                monthly_trend = db.execute_query(monthly_trend_query)
                trend_data = []
                for row in monthly_trend:
                    trend_data.append({
                        'year': row.get('Year'),
                        'month': row.get('Month'),
                        'monthName': row.get('MonthName'),
                        'workOrderCount': row.get('WorkOrderCount'),
                        'laborCost': float(row.get('LaborCost', 0) or 0),
                        'partsCost': float(row.get('PartsCost', 0) or 0),
                        'miscCost': float(row.get('MiscCost', 0) or 0),
                        'totalCost': float(row.get('TotalCost', 0) or 0)
                    })
            except Exception as e:
                # Fallback to empty trend data
                print(f"Monthly trend error: {e}")
                trend_data = []
            
            return jsonify({
                'summary': summary,
                'workOrders': work_orders,
                'monthlyTrend': trend_data
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_service_report_error'
            }), 500

    @reports_bp.route('/departments/rental/wo-detail/<wo_number>', methods=['GET'])
    @jwt_required()
    def get_rental_wo_detail(wo_number):
        """Get detailed breakdown of a specific work order"""
        try:
            db = get_db()
            
            # Get work order header
            wo_query = """
            SELECT 
                w.*,
                c.Name as CustomerName
            FROM ben002.WO w
            LEFT JOIN ben002.Customer c ON w.BillTo = c.Number
            WHERE w.WONo = %s
            """
            
            wo_result = db.execute_query(wo_query, [wo_number])
            if not wo_result:
                return jsonify({'error': 'Work order not found'}), 404
            
            wo_data = dict(wo_result[0])
            
            # Get labor details
            labor_query = """
            SELECT 
                MechanicName,
                DateOfLabor,
                Hours,
                Cost,
                Sell
            FROM ben002.WOLabor
            WHERE WONo = %s
            ORDER BY DateOfLabor
            """
            labor_details = db.execute_query(labor_query, [wo_number])
            
            # Debug: Check if flat rate labor might be in WOMisc or other tables
            # First, let's get all columns from WO to see what's available
            wo_columns_query = """
            SELECT TOP 1 * FROM ben002.WO WHERE WONo = %s
            """
            wo_full_data = db.execute_query(wo_columns_query, [wo_number])
            
            # Extract any labor-related fields from WO table
            labor_fields = {}
            if wo_full_data:
                wo_dict = dict(wo_full_data[0])
                for key, value in wo_dict.items():
                    if key and isinstance(key, str) and ('labor' in key.lower() or 'flat' in key.lower() or 'rate' in key.lower()):
                        labor_fields[key] = value
            
            # Also check if flat rate labor might be stored as a misc charge
            flat_rate_check_query = """
            SELECT * FROM ben002.WOMisc 
            WHERE WONo = %s 
            AND (UPPER(Description) LIKE '%LABOR%' 
                 OR UPPER(Description) LIKE '%FLAT%' 
                 OR UPPER(Description) LIKE '%RATE%'
                 OR Sell = 270)  -- Look for the exact $270 amount
            """
            flat_rate_misc = db.execute_query(flat_rate_check_query, [wo_number])
            
            # Get parts details
            parts_query = """
            SELECT 
                PartNo,
                Description,
                Qty,
                Cost,
                Sell,
                Cost * Qty as ExtendedCost,
                Sell * Qty as ExtendedSell
            FROM ben002.WOParts
            WHERE WONo = %s
            ORDER BY PartNo
            """
            parts_details = db.execute_query(parts_query, [wo_number])
            
            # Get misc details - let's see ALL misc items
            misc_query = """
            SELECT 
                Description,
                Cost,
                Sell,
                Taxable
            FROM ben002.WOMisc
            WHERE WONo = %s
            ORDER BY Description
            """
            misc_details = db.execute_query(misc_query, [wo_number])
            
            # Let's also check if there's a separate labor estimate or quote table
            # Check WOQuote for labor items
            quote_query = """
            SELECT 
                QuoteLine,
                Type,
                Description,
                Amount
            FROM ben002.WOQuote
            WHERE WONo = %s
            ORDER BY QuoteLine
            """
            quote_details = db.execute_query(quote_query, [wo_number])
            
            # Calculate totals
            labor_cost_total = sum(float(row.get('Cost', 0) or 0) for row in labor_details)
            labor_sell_total = sum(float(row.get('Sell', 0) or 0) for row in labor_details)
            
            # Add labor quotes to the labor sell total
            labor_quote_total = sum(float(row.get('Amount', 0) or 0) for row in quote_details if row.get('Type') == 'L')
            
            parts_cost_total = sum(float(row.get('ExtendedCost', 0) or 0) for row in parts_details)
            parts_sell_total = sum(float(row.get('ExtendedSell', 0) or 0) for row in parts_details)
            
            misc_cost_total = sum(float(row.get('Cost', 0) or 0) for row in misc_details)
            misc_sell_total = sum(float(row.get('Sell', 0) or 0) for row in misc_details)
            
            # Check invoice if exists
            # Note: InvoiceSales table doesn't exist, so we'll just search by Comments field
            invoice_query = """
            SELECT 
                InvoiceNo,
                InvoiceDate,
                GrandTotal,
                LaborTaxable + LaborNonTax as LaborTotal,
                PartsTaxable + PartsNonTax as PartsTotal,
                MiscTaxable + MiscNonTax as MiscTotal,
                EquipmentTaxable + EquipmentNonTax as EquipmentTotal,
                TotalTax
            FROM ben002.InvoiceReg
            WHERE Comments LIKE %s
            """
            
            invoice_data = db.execute_query(invoice_query, [f'%{wo_number}%'])
            
            return jsonify({
                'workOrder': {
                    'number': wo_number,
                    'billTo': wo_data.get('BillTo'),
                    'customerName': wo_data.get('CustomerName'),
                    'unitNo': wo_data.get('UnitNo'),
                    'serialNo': wo_data.get('SerialNo'),
                    'make': wo_data.get('Make'),
                    'model': wo_data.get('Model'),
                    'openDate': wo_data.get('OpenDate').isoformat() if wo_data.get('OpenDate') else None,
                    'status': wo_data.get('Status'),
                    'type': wo_data.get('Type'),
                    'saleCode': wo_data.get('SaleCode'),
                    'saleDept': wo_data.get('SaleDept')
                },
                'labor': {
                    'details': [dict(row) for row in labor_details],
                    'quoteItems': [dict(row) for row in quote_details if row.get('Type') == 'L'],
                    'costTotal': labor_cost_total,
                    'sellTotal': labor_sell_total + labor_quote_total,
                    'quoteTotal': labor_quote_total
                },
                'parts': {
                    'details': [dict(row) for row in parts_details],
                    'costTotal': parts_cost_total,
                    'sellTotal': parts_sell_total
                },
                'misc': {
                    'details': [dict(row) for row in misc_details],
                    'costTotal': misc_cost_total,
                    'sellTotal': misc_sell_total
                },
                'totals': {
                    'totalCost': labor_cost_total + parts_cost_total + misc_cost_total,
                    'totalSell': labor_sell_total + labor_quote_total + parts_sell_total + misc_sell_total
                },
                'invoice': [dict(row) for row in invoice_data] if invoice_data else None
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'wo_detail_error'
            }), 500


    @reports_bp.route('/departments/accounting-old', methods=['GET'])
    @jwt_required()
    def get_accounting_department_report_old():
        """Get Accounting Department report data"""
        try:
            db = get_db()
            
            # Get current year start
            today = datetime.now()
            year_start = datetime(today.year, 1, 1)
            month_start = today.replace(day=1)
            
            # 1. Summary metrics
            summary_query = f"""
            SELECT 
                -- Total Revenue YTD
                (SELECT SUM(GrandTotal) FROM ben002.InvoiceReg 
                 WHERE InvoiceDate >= '{year_start.strftime('%Y-%m-%d')}' 
                 AND InvoiceDate < '{today.strftime('%Y-%m-%d')}') as totalRevenue,
                 
                -- Total Expenses (expense data not available)
                0 as totalExpenses,
                
                -- Accounts Receivable
                (SELECT SUM(Balance) FROM ben002.Customer WHERE Balance > 0) as accountsReceivable,
                
                -- Overdue Invoices
                (SELECT COUNT(*) FROM ben002.InvoiceReg 
                 WHERE InvoiceStatus = 'Open' 
                 AND DATEDIFF(day, InvoiceDate, GETDATE()) > 30) as overdueInvoices,
                 
                -- Monthly Cash Flow
                (SELECT SUM(GrandTotal) FROM ben002.InvoiceReg 
                 WHERE InvoiceDate >= '{month_start.strftime('%Y-%m-%d')}'
                 AND InvoiceDate < '{today.strftime('%Y-%m-%d')}') as cashFlow
            """
            
            summary_result = db.execute_query(summary_query)
            
            total_revenue = float(summary_result[0][0] or 0)
            total_expenses = 0  # Expense data not available
            net_profit = total_revenue - total_expenses
            
            summary = {
                'totalRevenue': total_revenue,
                'totalExpenses': total_expenses,
                'netProfit': net_profit,
                'profitMargin': round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 1),
                'accountsReceivable': float(summary_result[0][2] or 0),
                'accountsPayable': 0,  # Would need payables table
                'cashFlow': float(summary_result[0][4] or 0),
                'overdueInvoices': summary_result[0][3] or 0
            }
            
            # 2. Revenue by Department
            dept_query = f"""
            SELECT 
                Department,
                SUM(GrandTotal) as revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= '{year_start.strftime('%Y-%m-%d')}'
            AND Department IS NOT NULL
            GROUP BY Department
            ORDER BY revenue DESC
            """
            
            dept_result = db.execute_query(dept_query)
            
            revenueByDepartment = []
            total_dept_revenue = sum(float(row[1] or 0) for row in dept_result)
            
            for row in dept_result:
                revenue = float(row[1] or 0)
                revenueByDepartment.append({
                    'department': row[0],
                    'revenue': revenue,
                    'percentage': round((revenue / total_dept_revenue * 100) if total_dept_revenue > 0 else 0, 1)
                })
            
            # 3. Monthly Financial Trend
            financial_trend_query = """
            SELECT 
                DATENAME(month, InvoiceDate) as month,
                SUM(GrandTotal) as revenue,
                COUNT(*) as invoiceCount
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
            GROUP BY DATENAME(month, InvoiceDate), MONTH(InvoiceDate), YEAR(InvoiceDate)
            ORDER BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            """
            
            financial_trend_result = db.execute_query(financial_trend_query)
            
            monthlyFinancials = []
            for row in financial_trend_result:
                revenue = float(row[1] or 0)
                expenses = 0  # Expense data not available
                monthlyFinancials.append({
                    'month': row[0][:3],
                    'revenue': revenue,
                    'expenses': expenses,
                    'profit': revenue - expenses
                })
            
            # 4. Outstanding Invoices
            invoices_query = """
            SELECT TOP 5
                InvoiceNo,
                CustomerName,
                GrandTotal,
                DATEDIFF(day, InvoiceDate, GETDATE()) as daysOverdue,
                CASE 
                    WHEN DATEDIFF(day, InvoiceDate, GETDATE()) > 60 THEN 'Overdue'
                    WHEN DATEDIFF(day, InvoiceDate, GETDATE()) > 30 THEN 'Late'
                    ELSE 'Current'
                END as status
            FROM ben002.InvoiceReg
            WHERE InvoiceStatus = 'Open'
            ORDER BY InvoiceDate ASC
            """
            
            invoices_result = db.execute_query(invoices_query)
            
            outstandingInvoices = []
            for row in invoices_result:
                outstandingInvoices.append({
                    'invoiceNumber': f'INV-{row[0]}',
                    'customer': row[1] or 'Unknown',
                    'amount': float(row[2] or 0),
                    'daysOverdue': max(0, row[3]),
                    'status': row[4]
                })
            
            # Expense categories data not available yet
            expenseCategories = []
            
            cashFlowTrend = []
            pendingPayables = []
            
            return jsonify({
                'summary': summary,
                'revenueByDepartment': revenueByDepartment,
                'expenseCategories': expenseCategories,
                'monthlyFinancials': monthlyFinancials,
                'cashFlowTrend': cashFlowTrend,
                'outstandingInvoices': outstandingInvoices,
                'pendingPayables': pendingPayables
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'accounting_report_error'
            }), 500

    @reports_bp.route('/departments/accounting', methods=['GET'])
    @require_permission('view_accounting')
    def get_accounting_report():
        """Get accounting department report data with expenses over time"""
        try:
            db = get_db()
            
            # Get G&A expenses over time since March 2025
            # Note: This query needs to be updated based on your actual G&A expense tables
            # Common tables might include: APInvoice, GLTransaction, ExpenseReport, etc.
            # For now, returning mock data to demonstrate the structure
            
            # Get G&A expenses from GLDetail table (which has the actual expense transactions)
            # Use trailing 13 months to match other dashboard charts
            expenses_query = """
            WITH MonthlyExpenses AS (
                SELECT
                    YEAR(gld.EffectiveDate) as year,
                    MONTH(gld.EffectiveDate) as month,
                    SUM(gld.Amount) as total_expenses
                FROM ben002.GLDetail gld
                WHERE gld.AccountNo LIKE '6%'  -- Expense accounts start with 6
                    AND gld.EffectiveDate >= DATEADD(month, -13, GETDATE())
                    AND gld.EffectiveDate < DATEADD(DAY, 1, GETDATE())
                GROUP BY YEAR(gld.EffectiveDate), MONTH(gld.EffectiveDate)
            ),
            ExpenseCategories AS (
                SELECT 
                    CASE 
                        WHEN gld.AccountNo LIKE '600%' THEN 'Advertising & Marketing'
                        WHEN gld.AccountNo LIKE '601%' THEN 'Payroll & Benefits'
                        WHEN gld.AccountNo LIKE '602%' THEN 'Facilities & Rent'
                        WHEN gld.AccountNo LIKE '603%' THEN 'Insurance'
                        WHEN gld.AccountNo LIKE '604%' THEN 'Professional Services'
                        WHEN gld.AccountNo LIKE '605%' THEN 'IT & Computer'
                        WHEN gld.AccountNo LIKE '606%' THEN 'Depreciation'
                        WHEN gld.AccountNo LIKE '607%' THEN 'Interest & Finance'
                        WHEN gld.AccountNo LIKE '608%' THEN 'Travel & Entertainment'
                        WHEN gld.AccountNo LIKE '609%' THEN 'Office & Admin'
                        ELSE 'Other Expenses'
                    END as category,
                    SUM(gld.Amount) as amount
                FROM ben002.GLDetail gld
                WHERE gld.AccountNo LIKE '6%'
                    AND gld.EffectiveDate >= DATEADD(MONTH, -6, GETDATE())
                GROUP BY 
                    CASE 
                        WHEN gld.AccountNo LIKE '600%' THEN 'Advertising & Marketing'
                        WHEN gld.AccountNo LIKE '601%' THEN 'Payroll & Benefits'
                        WHEN gld.AccountNo LIKE '602%' THEN 'Facilities & Rent'
                        WHEN gld.AccountNo LIKE '603%' THEN 'Insurance'
                        WHEN gld.AccountNo LIKE '604%' THEN 'Professional Services'
                        WHEN gld.AccountNo LIKE '605%' THEN 'IT & Computer'
                        WHEN gld.AccountNo LIKE '606%' THEN 'Depreciation'
                        WHEN gld.AccountNo LIKE '607%' THEN 'Interest & Finance'
                        WHEN gld.AccountNo LIKE '608%' THEN 'Travel & Entertainment'
                        WHEN gld.AccountNo LIKE '609%' THEN 'Office & Admin'
                        ELSE 'Other Expenses'
                    END
                HAVING SUM(gld.Amount) != 0
            )
            SELECT 
                (SELECT year, month, total_expenses 
                 FROM MonthlyExpenses 
                 ORDER BY year, month 
                 FOR JSON AUTO) as monthly_data,
                (SELECT category, amount 
                 FROM ExpenseCategories 
                 WHERE amount > 0
                 ORDER BY amount DESC
                 FOR JSON AUTO) as category_data
            """
            
            expenses_results = db.execute_query(expenses_query)
            monthly_expenses = []
            expense_categories = []
            
            if expenses_results and len(expenses_results) > 0:
                result = expenses_results[0]
                
                # Parse monthly data
                import json
                monthly_data = json.loads(result.get('monthly_data', '[]'))
                for row in monthly_data:
                    monthly_expenses.append({
                        'year': row['year'],
                        'month_num': row['month'],  # Keep month as number for proper matching
                        'expenses': float(row['total_expenses'] or 0)
                    })
                
                # Parse category data
                category_data = json.loads(result.get('category_data', '[]'))
                expense_categories = [{
                    'category': cat['category'],
                    'amount': float(cat['amount'] or 0)
                } for cat in category_data]
            
            # Use trailing 13 months to match other dashboard charts
            current_date = datetime.now()

            # Generate 13-month list ending with current month
            all_months = []
            for i in range(12, -1, -1):
                month_date = current_date - timedelta(days=i * 30)  # Approximate
                # More accurate: go back i months
                year = current_date.year
                month = current_date.month - i
                while month <= 0:
                    month += 12
                    year -= 1
                month_date = datetime(year, month, 1)
                all_months.append({
                    'month': month_date.strftime("%b"),
                    'month_label': month_date.strftime("%b '%y"),
                    'year': year,
                    'month_num': month
                })

            # Match existing data by year and month number
            existing_data = {(item['year'], item['month_num']): item['expenses'] for item in monthly_expenses if 'year' in item and 'month_num' in item}

            monthly_expenses = []
            for m in all_months:
                expenses = existing_data.get((m['year'], m['month_num']), 0)
                monthly_expenses.append({
                    'month': m['month_label'],
                    'year': m['year'],
                    'expenses': expenses
                })
            
            # Calculate summary metrics (exclude current month from average since it's incomplete)
            total_expenses = sum(item['expenses'] for item in monthly_expenses)
            # Exclude last month (current month) from average calculation
            complete_months = monthly_expenses[:-1] if len(monthly_expenses) > 1 else monthly_expenses
            avg_expenses = sum(item['expenses'] for item in complete_months) / len(complete_months) if complete_months else 0
            
            # Return structure with real expense data from GL
            return jsonify({
                'monthly_expenses': monthly_expenses,
                'debug_info': {
                    'data_source': 'GLDetail table',
                    'account_filter': 'AccountNo LIKE 6%'
                },
                'summary': {
                    'total_expenses': round(total_expenses, 2),
                    'average_monthly': round(avg_expenses, 2),
                    'expense_categories': expense_categories,
                    'totalRevenue': 0,
                    'totalExpenses': total_expenses,
                    'netProfit': 0,
                    'profitMargin': 0,
                    'accountsReceivable': 0,
                    'accountsPayable': 0,
                    'cashFlow': 0,
                    'overdueInvoices': 0
                },
                'revenueByDepartment': [],
                'expenseCategories': expense_categories,
                'monthlyFinancials': [],
                'cashFlowTrend': [],
                'outstandingInvoices': [],
                'pendingPayables': []
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'accounting_report_error'
            }), 500

    @reports_bp.route('/departments/accounting/professional-services', methods=['GET'])
    @jwt_required()
    @require_permission('view_accounting')
    def get_professional_services_expenses():
        """Get Professional Services (603000) expenses over time"""
        try:
            db = get_db()

            # Get Professional Services expenses from GLDetail table
            # Account 603000 is Professional Services
            expenses_query = """
            WITH MonthlyExpenses AS (
                SELECT
                    YEAR(gld.EffectiveDate) as year,
                    MONTH(gld.EffectiveDate) as month,
                    SUM(gld.Amount) as total_expenses
                FROM ben002.GLDetail gld
                WHERE gld.AccountNo = '603000'
                    AND gld.EffectiveDate >= DATEADD(month, -13, GETDATE())
                    AND gld.EffectiveDate < DATEADD(DAY, 1, GETDATE())
                GROUP BY YEAR(gld.EffectiveDate), MONTH(gld.EffectiveDate)
            )
            SELECT year, month, total_expenses
            FROM MonthlyExpenses
            ORDER BY year, month
            FOR JSON AUTO
            """

            expenses_results = db.execute_query(expenses_query)
            monthly_expenses = []

            if expenses_results and len(expenses_results) > 0:
                result = expenses_results[0]

                # Parse monthly data - result might be a dict with JSON or direct JSON string
                import json
                monthly_data_raw = result.get('') if isinstance(result, dict) else result
                if isinstance(monthly_data_raw, str):
                    monthly_data = json.loads(monthly_data_raw)
                elif isinstance(monthly_data_raw, list):
                    monthly_data = monthly_data_raw
                else:
                    # Try to get the first value from the dict
                    monthly_data = json.loads(list(result.values())[0]) if result else []

                for row in monthly_data:
                    monthly_expenses.append({
                        'year': row['year'],
                        'month_num': row['month'],
                        'expenses': float(row['total_expenses'] or 0)
                    })

            # Generate 13-month list ending with current month
            current_date = datetime.now()
            all_months = []
            for i in range(12, -1, -1):
                year = current_date.year
                month = current_date.month - i
                while month <= 0:
                    month += 12
                    year -= 1
                month_date = datetime(year, month, 1)
                all_months.append({
                    'month': month_date.strftime("%b"),
                    'month_label': month_date.strftime("%b '%y"),
                    'year': year,
                    'month_num': month
                })

            # Match existing data by year and month number
            existing_data = {(item['year'], item['month_num']): item['expenses'] for item in monthly_expenses if 'year' in item and 'month_num' in item}

            monthly_expenses = []
            for m in all_months:
                expenses = existing_data.get((m['year'], m['month_num']), 0)
                monthly_expenses.append({
                    'month': m['month_label'],
                    'year': m['year'],
                    'expenses': expenses
                })

            # Calculate summary metrics (exclude current month from average since it's incomplete)
            total_expenses = sum(item['expenses'] for item in monthly_expenses)
            complete_months = monthly_expenses[:-1] if len(monthly_expenses) > 1 else monthly_expenses
            avg_expenses = sum(item['expenses'] for item in complete_months) / len(complete_months) if complete_months else 0

            return jsonify({
                'monthly_expenses': monthly_expenses,
                'summary': {
                    'total_expenses': round(total_expenses, 2),
                    'average_monthly': round(avg_expenses, 2)
                }
            })

        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'professional_services_error'
            }), 500

    @reports_bp.route('/departments/accounting/professional-services/details', methods=['GET'])
    @jwt_required()
    @require_permission('view_accounting')
    def get_professional_services_details():
        """Get Professional Services (603000) invoice details for a specific month"""
        try:
            db = get_db()

            # Get year and month from query params
            year = request.args.get('year', type=int)
            month = request.args.get('month', type=int)

            if not year or not month:
                return jsonify({'error': 'Year and month parameters are required'}), 400

            # Get invoice details from GLDetail table for the specified month
            # Only use verified columns: AccountNo, EffectiveDate, Amount, Description
            details_query = f"""
            SELECT
                EffectiveDate,
                Amount,
                Description
            FROM ben002.GLDetail
            WHERE AccountNo = '603000'
                AND YEAR(EffectiveDate) = {year}
                AND MONTH(EffectiveDate) = {month}
            ORDER BY EffectiveDate DESC, Amount DESC
            """

            results = db.execute_query(details_query)

            invoices = []
            for row in results:
                # Use Description as the vendor/description
                desc = row.get('Description') or ''

                # Handle date formatting safely
                effective_date = row.get('EffectiveDate')
                if effective_date:
                    try:
                        date_str = effective_date.strftime('%Y-%m-%d')
                    except AttributeError:
                        # If it's already a string or other format
                        date_str = str(effective_date)[:10] if effective_date else None
                else:
                    date_str = None

                invoices.append({
                    'date': date_str,
                    'amount': float(row.get('Amount') or 0),
                    'description': desc,
                    'vendor_name': desc.split(' - ')[0] if ' - ' in desc else desc[:50] if desc else 'Unknown'
                })

            # Calculate total
            total = sum(inv['amount'] for inv in invoices)

            return jsonify({
                'year': year,
                'month': month,
                'invoices': invoices,
                'total': round(total, 2),
                'count': len(invoices)
            })

        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'professional_services_details_error'
            }), 500

    @reports_bp.route('/departments/accounting/ap-total', methods=['GET'])
    @jwt_required()
    def get_ap_total():
        """Get total accounts payable balance"""
        try:
            db = get_db()
            
            # Get total AP balance - sum all unpaid AP amounts
            # AP amounts are stored as negative values, so we need to negate them
            query = """
            SELECT 
                SUM(Amount) as total_ap
            FROM ben002.APDetail
            WHERE (CheckNo IS NULL OR CheckNo = 0)
                AND (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            
            result = db.execute_query(query)
            total_ap = float(result[0]['total_ap']) if result and result[0]['total_ap'] else 0
            
            # If AP is negative, make it positive (AP is a liability, should show as positive)
            if total_ap < 0:
                total_ap = -total_ap
            
            return jsonify({
                'total_ap': total_ap,
                'formatted': f"${total_ap/1000000:.3f}M" if total_ap >= 1000000 else f"${total_ap/1000:.0f}k"
            })
            
        except Exception as e:
            logger.error(f"Error fetching AP total: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/ap-report', methods=['GET'])
    @jwt_required()
    def get_ap_report():
        """Get comprehensive accounts payable report with aging and details"""
        try:
            db = get_db()
            
            # Get all unpaid AP invoices with vendor info
            ap_detail_query = """
            WITH APInvoices AS (
                SELECT 
                    ap.APInvoiceNo,
                    ap.VendorNo,
                    v.Name as VendorName,
                    ap.APInvoiceDate,
                    ap.DueDate,
                    SUM(ap.Amount) as InvoiceAmount,
                    COUNT(*) as LineItems,
                    DATEDIFF(day, ap.DueDate, GETDATE()) as DaysOverdue,
                    CASE 
                        WHEN ap.DueDate IS NULL THEN 'No Due Date'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) < 0 THEN 'Not Due'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 0 AND 30 THEN '0-30'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) > 90 THEN 'Over 90'
                    END as AgingBucket
                FROM ben002.APDetail ap
                LEFT JOIN ben002.Vendor v ON ap.VendorNo = v.VendorNo
                WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                    AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                    AND ap.DeletionTime IS NULL
                GROUP BY ap.APInvoiceNo, ap.VendorNo, v.Name, ap.APInvoiceDate, ap.DueDate
            )
            SELECT 
                APInvoiceNo,
                VendorNo,
                VendorName,
                APInvoiceDate,
                DueDate,
                -- Convert negative amounts to positive for display
                ABS(InvoiceAmount) as InvoiceAmount,
                LineItems,
                DaysOverdue,
                AgingBucket
            FROM APInvoices
            ORDER BY DaysOverdue DESC, InvoiceAmount DESC
            """
            
            ap_results = db.execute_query(ap_detail_query)
            
            # Get aging summary - calculate based on net invoice amounts
            aging_query = """
            WITH APInvoices AS (
                SELECT 
                    ap.APInvoiceNo,
                    ap.DueDate,
                    SUM(ap.Amount) as InvoiceAmount,
                    CASE 
                        WHEN ap.DueDate IS NULL THEN 'No Due Date'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) < 0 THEN 'Not Due'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 0 AND 30 THEN '0-30'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 31 AND 60 THEN '31-60'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) BETWEEN 61 AND 90 THEN '61-90'
                        WHEN DATEDIFF(day, ap.DueDate, GETDATE()) > 90 THEN 'Over 90'
                    END as AgingBucket
                FROM ben002.APDetail ap
                WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                    AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                    AND ap.DeletionTime IS NULL
                GROUP BY ap.APInvoiceNo, ap.DueDate
                HAVING SUM(ap.Amount) != 0  -- Exclude zero balance invoices
            )
            SELECT 
                AgingBucket,
                COUNT(*) as InvoiceCount,
                -- Sum the already-netted invoice amounts, then take absolute value
                ABS(SUM(InvoiceAmount)) as TotalAmount
            FROM APInvoices
            GROUP BY AgingBucket
            """
            
            aging_results = db.execute_query(aging_query)
            
            # Get top vendors by amount owed - calculate net amounts per vendor like main total
            vendor_query = """
            SELECT TOP 10
                ap.VendorNo,
                v.Name as VendorName,
                COUNT(DISTINCT ap.APInvoiceNo) as InvoiceCount,
                ABS(SUM(ap.Amount)) as TotalOwed,
                MIN(ap.DueDate) as OldestDueDate,
                DATEDIFF(day, MIN(ap.DueDate), GETDATE()) as OldestDaysOverdue
            FROM ben002.APDetail ap
            LEFT JOIN ben002.Vendor v ON ap.VendorNo = v.VendorNo
            WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                AND ap.DeletionTime IS NULL
            GROUP BY ap.VendorNo, v.Name
            ORDER BY ABS(SUM(ap.Amount)) DESC
            """
            
            vendor_results = db.execute_query(vendor_query)
            
            # Calculate summary metrics - get the real total from raw sum like ap-total endpoint
            total_query = """
            SELECT SUM(Amount) as raw_total
            FROM ben002.APDetail
            WHERE (CheckNo IS NULL OR CheckNo = 0)
                AND (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            total_result = db.execute_query(total_query)
            raw_total = float(total_result[0]['raw_total']) if total_result and total_result[0]['raw_total'] else 0
            
            # Convert to positive if negative (AP is a liability)
            total_ap = abs(raw_total)
            
            # Calculate overdue will be done after we scale the aging buckets
            # This ensures consistency with the displayed values
            
            # Format invoice details
            invoices = []
            for row in ap_results:
                invoices.append({
                    'invoice_no': row['APInvoiceNo'],
                    'vendor_no': row['VendorNo'],
                    'vendor_name': row['VendorName'] or 'Unknown Vendor',
                    'invoice_date': row['APInvoiceDate'].strftime('%Y-%m-%d') if row['APInvoiceDate'] else None,
                    'due_date': row['DueDate'].strftime('%Y-%m-%d') if row['DueDate'] else None,
                    'amount': float(row['InvoiceAmount']),
                    'days_overdue': row['DaysOverdue'] if row['DaysOverdue'] and row['DaysOverdue'] >= 0 else 0,
                    'aging_bucket': row['AgingBucket']
                })
            
            # Format aging summary
            aging_summary = []
            bucket_order = ['Not Due', '0-30', '31-60', '61-90', 'Over 90', 'No Due Date']
            
            # Calculate the total from aging buckets to ensure consistency
            aging_total = sum(float(row['TotalAmount']) for row in aging_results) if aging_results else 0
            
            # If aging total doesn't match our calculated total, use proportional amounts
            scale_factor = total_ap / aging_total if aging_total > 0 else 1
            
            for bucket in bucket_order:
                bucket_data = next((row for row in aging_results if row['AgingBucket'] == bucket), None)
                if bucket_data:
                    # Scale the amount to ensure it's proportional to the actual total
                    aging_summary.append({
                        'bucket': bucket,
                        'count': bucket_data['InvoiceCount'],
                        'amount': float(bucket_data['TotalAmount']) * scale_factor
                    })
                else:
                    aging_summary.append({
                        'bucket': bucket,
                        'count': 0,
                        'amount': 0
                    })
            
            # Now calculate overdue amount from the scaled aging summary
            overdue_amount = sum(bucket['amount'] for bucket in aging_summary 
                               if bucket['bucket'] not in ['Not Due', 'No Due Date'])
            overdue_percentage = (overdue_amount / total_ap * 100) if total_ap > 0 else 0
            
            # Format top vendors
            top_vendors = []
            for row in vendor_results:
                top_vendors.append({
                    'vendor_no': row['VendorNo'],
                    'vendor_name': row['VendorName'] or 'Unknown Vendor',
                    'invoice_count': row['InvoiceCount'],
                    'total_owed': float(row['TotalOwed']),
                    'oldest_days_overdue': row['OldestDaysOverdue'] if row['OldestDaysOverdue'] and row['OldestDaysOverdue'] >= 0 else 0
                })
            
            return jsonify({
                'total_ap': total_ap,
                'overdue_amount': overdue_amount,
                'overdue_percentage': round(overdue_percentage, 1),
                'aging_summary': aging_summary,
                'top_vendors': top_vendors,
                'invoices': invoices,
                'invoice_count': len(invoices)
            })
            
        except Exception as e:
            logger.error(f"Error fetching AP report: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/ap-validation', methods=['GET'])
    @jwt_required()
    def get_ap_validation():
        """Get AP validation data to verify accuracy"""
        try:
            db = get_db()
            
            # Get total AP by different methods to cross-check
            validation_queries = {
                'total_unpaid_ap': """
                    SELECT COUNT(DISTINCT APInvoiceNo) as invoice_count,
                           SUM(Amount) as total_amount_raw,
                           SUM(ABS(Amount)) as total_amount_abs
                    FROM ben002.APDetail
                    WHERE (CheckNo IS NULL OR CheckNo = 0)
                        AND (HistoryFlag IS NULL OR HistoryFlag = 0)
                        AND DeletionTime IS NULL
                """,
                
                'by_entry_type': """
                    SELECT EntryType, 
                           COUNT(*) as record_count,
                           SUM(Amount) as total_amount
                    FROM ben002.APDetail
                    WHERE (CheckNo IS NULL OR CheckNo = 0)
                        AND (HistoryFlag IS NULL OR HistoryFlag = 0)
                        AND DeletionTime IS NULL
                    GROUP BY EntryType
                """,
                
                'sample_invoices': """
                    SELECT TOP 10 
                        ap.APInvoiceNo,
                        ap.VendorNo,
                        v.Name as VendorName,
                        ap.APInvoiceDate,
                        ap.DueDate,
                        ap.Amount,
                        ap.EntryType,
                        ap.Comments
                    FROM ben002.APDetail ap
                    LEFT JOIN ben002.Vendor v ON ap.VendorNo = v.VendorNo
                    WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                        AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                        AND ap.DeletionTime IS NULL
                    ORDER BY ABS(ap.Amount) DESC
                """,
                
                'vendors_with_balances': """
                    SELECT COUNT(DISTINCT ap.VendorNo) as vendor_count
                    FROM ben002.APDetail ap
                    WHERE (ap.CheckNo IS NULL OR ap.CheckNo = 0)
                        AND (ap.HistoryFlag IS NULL OR ap.HistoryFlag = 0)
                        AND ap.DeletionTime IS NULL
                """
            }
            
            results = {}
            for key, query in validation_queries.items():
                results[key] = db.execute_query(query)
            
            return jsonify({
                'validation_results': results,
                'summary': {
                    'total_ap_raw': float(results['total_unpaid_ap'][0]['total_amount_raw']) if results['total_unpaid_ap'] else 0,
                    'total_ap_absolute': float(results['total_unpaid_ap'][0]['total_amount_abs']) if results['total_unpaid_ap'] else 0,
                    'invoice_count': results['total_unpaid_ap'][0]['invoice_count'] if results['total_unpaid_ap'] else 0,
                    'vendor_count': results['vendors_with_balances'][0]['vendor_count'] if results['vendors_with_balances'] else 0
                }
            })
            
        except Exception as e:
            logger.error(f"Error in AP validation: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/ar-report', methods=['GET'])
    @jwt_required()
    def get_ar_report():
        """Get accounts receivable aging report"""
        try:
            db = get_db()
            
            # First get the total AR amount
            total_ar_query = """
            SELECT SUM(Amount) as total_ar
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            
            total_ar_result = db.execute_query(total_ar_query)
            total_ar = float(total_ar_result[0]['total_ar']) if total_ar_result and total_ar_result[0]['total_ar'] else 0
            
            # Get AR aging buckets by invoice balance (not individual records)
            # Using source system bucket structure: Current (0-29), 30-60, 60-90, 90-120, 120+
            ar_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,  -- Use earliest due date for the invoice
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL  -- Exclude non-invoice transactions
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01  -- Only invoices with outstanding balance
            )
            SELECT 
                CASE 
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) < 30 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 30 AND 59 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 60 AND 89 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 90 AND 120 THEN '90-120'
                    WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
                END as AgingBucket,
                COUNT(*) as RecordCount,
                SUM(NetBalance) as TotalAmount
            FROM InvoiceBalances
            GROUP BY 
                CASE 
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) < 30 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 30 AND 59 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 60 AND 89 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 90 AND 120 THEN '90-120'
                    WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
                END
            """
            
            ar_results = db.execute_query(ar_query)
            
            # Calculate over 90 days directly from the data
            # Get a direct calculation of invoices over 90 days
            over_90_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL
                GROUP BY ar.InvoiceNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT SUM(NetBalance) as total_over_90
            FROM InvoiceBalances
            WHERE DATEDIFF(day, Due, GETDATE()) >= 90
            """
            
            over_90_result = db.execute_query(over_90_query)
            over_90_amount = float(over_90_result[0]['total_over_90']) if over_90_result and over_90_result[0]['total_over_90'] else 0
            over_90_percentage = (over_90_amount / total_ar * 100) if total_ar > 0 else 0
            
            # Get specific customer AR over 90 days
            customer_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance  -- Amounts already have correct signs
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                CASE 
                    WHEN c.Name = 'POLARIS INDUSTRIES' OR c.Name = 'POLARIS' OR c.Name = 'POLARIS INJECT MOLDING'
                    THEN 'POLARIS INDUSTRIES'
                    ELSE c.Name
                END as CustomerName,
                COUNT(ib.InvoiceNo) as InvoiceCount,
                SUM(ib.NetBalance) as TotalAmount,
                MIN(ib.Due) as OldestDueDate,
                MAX(DATEDIFF(day, ib.Due, GETDATE())) as MaxDaysOverdue
            FROM InvoiceBalances ib
            INNER JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90  -- 90 days and over
                AND (
                    UPPER(c.Name) LIKE '%POLARIS%' OR
                    UPPER(c.Name) LIKE '%GREDE%' OR
                    UPPER(c.Name) LIKE '%OWENS%'
                )
            GROUP BY CASE 
                WHEN c.Name = 'POLARIS INDUSTRIES' OR c.Name = 'POLARIS' OR c.Name = 'POLARIS INJECT MOLDING'
                THEN 'POLARIS INDUSTRIES'
                ELSE c.Name
            END
            ORDER BY SUM(ib.NetBalance) DESC
            """
            
            customer_results = db.execute_query(customer_query)
            
            # Get aging breakdown for visualization - matching our actual buckets
            aging_summary = []
            for bucket in ['Current', '30-60', '60-90', '90-120', '120+']:
                row = next((r for r in ar_results if r['AgingBucket'] == bucket), None)
                aging_summary.append({
                    'bucket': bucket,
                    'amount': float(row['TotalAmount']) if row else 0,
                    'count': row['RecordCount'] if row else 0
                })
            
            # Add debug info to see what's in ar_results
            debug_buckets = {}
            for row in ar_results:
                debug_buckets[row['AgingBucket']] = float(row['TotalAmount'])
            
            return jsonify({
                'total_ar': float(total_ar),
                'over_90_amount': float(over_90_amount),
                'over_90_percentage': round(over_90_percentage, 1),
                'aging_summary': aging_summary,
                'debug_buckets': debug_buckets,  # Temporary debug info
                'specific_customers': [
                    {
                        'name': row['CustomerName'],
                        'amount': float(row['TotalAmount']),
                        'invoice_count': row['InvoiceCount'],
                        'oldest_due_date': row['OldestDueDate'].isoformat() if row['OldestDueDate'] else None,
                        'max_days_overdue': row['MaxDaysOverdue']
                    }
                    for row in customer_results
                ]
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'ar_report_error'
            }), 500

    @reports_bp.route('/departments/accounting/version', methods=['GET'])
    @jwt_required()
    def get_version():
        """Get version info to verify deployment"""
        return jsonify({
            'version': '2024-12-04-fix-ar-calculations',
            'ar_calculation': 'using SUM(Amount) directly',
            'polaris_merge': 'enabled',
            'timestamp': datetime.utcnow().isoformat()
        })
    
    @reports_bp.route('/departments/accounting/ar-debug', methods=['GET'])
    @jwt_required()
    def get_ar_debug():
        """Debug endpoint to analyze AR calculations"""
        try:
            db = get_db()
            
            # Get raw AR totals and check EntryType values
            raw_query = """
            SELECT 
                COUNT(*) as total_records,
                SUM(Amount) as raw_total,
                SUM(CASE WHEN EntryType = 'Invoice' THEN Amount ELSE 0 END) as invoice_total,
                SUM(CASE WHEN EntryType = 'Payment' THEN Amount ELSE 0 END) as payment_total,
                SUM(CASE WHEN EntryType = 'Voucher' THEN Amount ELSE 0 END) as voucher_total,
                SUM(CASE WHEN EntryType = 'Journal' THEN Amount ELSE 0 END) as journal_total,
                SUM(CASE WHEN EntryType = 'AR Journal' THEN Amount ELSE 0 END) as ar_journal_total,
                COUNT(DISTINCT InvoiceNo) as unique_invoices
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            
            # Get EntryType distribution
            entry_type_query = """
            SELECT 
                EntryType,
                COUNT(*) as count,
                SUM(Amount) as total_amount
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            GROUP BY EntryType
            ORDER BY COUNT(*) DESC
            """
            
            raw_results = db.execute_query(raw_query)
            raw_data = dict(raw_results[0]) if raw_results else {}
            
            entry_type_results = db.execute_query(entry_type_query)
            entry_types = [dict(row) for row in entry_type_results]
            
            # Get net AR using the same logic as the main query
            net_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    ar.Due,
                    SUM(ar.Amount) as NetBalance  -- Amounts already have correct signs
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo, ar.Due
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                COUNT(*) as open_invoices,
                SUM(NetBalance) as total_ar
            FROM InvoiceBalances
            """
            
            net_results = db.execute_query(net_query)
            net_data = dict(net_results[0]) if net_results else {}
            
            # Get sample of largest open balances
            sample_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    ar.Due,
                    SUM(ar.Amount) as NetBalance  -- Amounts already have correct signs
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo, ar.Due
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT TOP 10
                ib.CustomerNo,
                c.Name as CustomerName,
                ib.InvoiceNo,
                ib.NetBalance,
                ib.Due
            FROM InvoiceBalances ib
            LEFT JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            ORDER BY ib.NetBalance DESC
            """
            
            sample_results = db.execute_query(sample_query)
            
            return jsonify({
                'raw_totals': raw_data,
                'entry_types': entry_types,
                'net_ar': net_data,
                'calculated_net': float(raw_data.get('raw_total', 0)),  # Just use the raw total since amounts have correct signs
                'largest_open_balances': [dict(row) for row in sample_results],
                'message': 'AR Debug Information'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'ar_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/customer-ar-debug', methods=['GET'])
    @jwt_required()
    def get_customer_ar_debug():
        """Debug specific customer AR over 90 days"""
        try:
            db = get_db()
            
            # Get all customers matching our criteria
            customer_list_query = """
            SELECT DISTINCT c.Number, c.Name
            FROM ben002.Customer c
            WHERE UPPER(c.Name) LIKE '%POLARIS%' 
               OR UPPER(c.Name) LIKE '%GREDE%' 
               OR UPPER(c.Name) LIKE '%OWENS%'
            ORDER BY c.Name
            """
            
            customers = db.execute_query(customer_list_query)
            
            # Get AR balances for these customers
            balance_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                c.Name as CustomerName,
                COUNT(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) >= 90 THEN 1 END) as InvoicesOver90,
                SUM(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) >= 90 THEN ib.NetBalance ELSE 0 END) as AmountOver90,
                COUNT(*) as TotalOpenInvoices,
                SUM(ib.NetBalance) as TotalARBalance
            FROM InvoiceBalances ib
            INNER JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE UPPER(c.Name) LIKE '%POLARIS%' 
               OR UPPER(c.Name) LIKE '%GREDE%' 
               OR UPPER(c.Name) LIKE '%OWENS%'
            GROUP BY c.Name
            ORDER BY SUM(CASE WHEN DATEDIFF(day, ib.Due, GETDATE()) > 90 THEN ib.NetBalance ELSE 0 END) DESC
            """
            
            balances = db.execute_query(balance_query)
            
            # Get specific invoices over 90 days
            detail_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.CustomerNo,
                    ar.InvoiceNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                GROUP BY ar.CustomerNo, ar.InvoiceNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT TOP 30
                c.Name as CustomerName,
                ib.InvoiceNo,
                ib.Due,
                DATEDIFF(day, ib.Due, GETDATE()) as DaysOverdue,
                ib.NetBalance
            FROM InvoiceBalances ib
            INNER JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90
                AND (UPPER(c.Name) LIKE '%POLARIS%' 
                     OR UPPER(c.Name) LIKE '%GREDE%' 
                     OR UPPER(c.Name) LIKE '%OWENS%')
            ORDER BY ib.NetBalance DESC
            """
            
            details = db.execute_query(detail_query)
            
            return jsonify({
                'customer_list': [dict(row) for row in customers],
                'customer_balances': [dict(row) for row in balances],
                'invoice_details': [dict(row) for row in details]
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'customer_ar_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/ar-over90-full', methods=['GET'])
    @jwt_required()
    def get_ar_over90_full():
        """Get ALL invoices over 90 days for detailed analysis"""
        try:
            db = get_db()
            
            # Get all invoices over 90 days with details
            query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                ib.InvoiceNo,
                ib.CustomerNo,
                c.Name as CustomerName,
                ib.Due,
                DATEDIFF(day, ib.Due, GETDATE()) as DaysOld,
                ib.NetBalance
            FROM InvoiceBalances ib
            LEFT JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90
            ORDER BY DATEDIFF(day, ib.Due, GETDATE()) DESC, ib.NetBalance DESC
            """
            
            results = db.execute_query(query)
            
            # Calculate totals by days old ranges
            totals = {
                '90-120': 0,
                '120+': 0,
                'total': 0
            }
            
            invoices = []
            for row in results:
                invoice = dict(row)
                amount = float(invoice.get('NetBalance', 0))
                days = int(invoice.get('DaysOld', 0))
                
                if 90 <= days <= 120:
                    totals['90-120'] += amount
                elif days > 120:
                    totals['120+'] += amount
                totals['total'] += amount
                
                invoices.append(invoice)
            
            return jsonify({
                'invoices': invoices,  # Return ALL invoices
                'totals': totals,
                'total_count': len(results)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'ar_over90_full_error'
            }), 500

    @reports_bp.route('/departments/accounting/over90-debug', methods=['GET'])
    @jwt_required()
    def get_over90_debug():
        """Debug over 90 days AR calculation"""
        try:
            db = get_db()
            
            # Get all invoices over 90 days with details
            query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01
            )
            SELECT 
                ib.InvoiceNo,
                ib.CustomerNo,
                c.Name as CustomerName,
                ib.Due,
                DATEDIFF(day, ib.Due, GETDATE()) as DaysOld,
                ib.NetBalance
            FROM InvoiceBalances ib
            LEFT JOIN ben002.Customer c ON ib.CustomerNo = c.Number
            WHERE DATEDIFF(day, ib.Due, GETDATE()) >= 90
            ORDER BY ib.NetBalance DESC
            """
            
            results = db.execute_query(query)
            
            # Calculate totals by days old ranges
            totals = {
                '90-120': 0,
                '120+': 0,
                'total': 0
            }
            
            invoices = []
            for row in results:
                invoice = dict(row)
                amount = float(invoice.get('NetBalance', 0))
                days = int(invoice.get('DaysOld', 0))
                
                if 90 <= days <= 120:
                    totals['90-120'] += amount
                elif days > 120:
                    totals['120+'] += amount
                totals['total'] += amount
                
                invoices.append(invoice)
            
            return jsonify({
                'invoices': invoices[:100],  # Return top 100
                'totals': totals,
                'total_count': len(results)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'over90_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/ar-aging-debug', methods=['GET'])
    @jwt_required()
    def get_ar_aging_debug():
        """Comprehensive AR aging debug endpoint"""
        try:
            db = get_db()
            
            # 1. Get total AR same way as main report
            total_query = """
            SELECT SUM(Amount) as total_ar
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            """
            total_result = db.execute_query(total_query)
            total_ar = float(total_result[0]['total_ar']) if total_result and total_result[0]['total_ar'] else 0
            
            # 2. Get aging buckets by invoice balance (matching main report)
            buckets_query = """
            WITH InvoiceBalances AS (
                SELECT 
                    ar.InvoiceNo,
                    ar.CustomerNo,
                    MIN(ar.Due) as Due,  -- Use earliest due date for the invoice
                    SUM(ar.Amount) as NetBalance
                FROM ben002.ARDetail ar
                WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
                    AND ar.DeletionTime IS NULL
                    AND ar.InvoiceNo IS NOT NULL  -- Exclude non-invoice transactions
                GROUP BY ar.InvoiceNo, ar.CustomerNo
                HAVING SUM(ar.Amount) > 0.01  -- Only invoices with outstanding balance
            )
            SELECT 
                CASE 
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 91 AND 120 THEN '90-120'
                    WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
                END as AgingBucket,
                COUNT(*) as RecordCount,
                SUM(NetBalance) as TotalAmount
            FROM InvoiceBalances
            GROUP BY 
                CASE 
                    WHEN Due IS NULL THEN 'No Due Date'
                    WHEN DATEDIFF(day, Due, GETDATE()) <= 0 THEN 'Current'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 1 AND 30 THEN '1-30'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 31 AND 60 THEN '30-60'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 61 AND 90 THEN '60-90'
                    WHEN DATEDIFF(day, Due, GETDATE()) BETWEEN 91 AND 120 THEN '90-120'
                    WHEN DATEDIFF(day, Due, GETDATE()) > 120 THEN '120+'
                END
            """
            bucket_results = db.execute_query(buckets_query)
            
            # Calculate bucket totals
            buckets = {}
            bucket_sum = 0
            for row in bucket_results:
                buckets[row['AgingBucket']] = {
                    'amount': float(row['TotalAmount']),
                    'count': row['RecordCount']
                }
                bucket_sum += float(row['TotalAmount'])
            
            # Calculate over 90 days
            over_90 = sum(buckets.get(b, {}).get('amount', 0) for b in ['90-120', '120+'])
            
            # 3. Check for NULL due dates
            null_due_query = """
            SELECT COUNT(*) as count, SUM(Amount) as amount
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
                AND Due IS NULL
            """
            null_due_result = db.execute_query(null_due_query)
            null_due_data = dict(null_due_result[0]) if null_due_result else {}
            
            # 4. Get EntryType breakdown
            entry_type_query = """
            SELECT EntryType, COUNT(*) as count, SUM(Amount) as amount
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
            GROUP BY EntryType
            ORDER BY ABS(SUM(Amount)) DESC
            """
            entry_type_results = db.execute_query(entry_type_query)
            entry_types = [dict(row) for row in entry_type_results]
            
            # 5. Sample records around 90 days
            sample_90_query = """
            SELECT TOP 20
                InvoiceNo,
                CustomerNo,
                EntryType,
                Amount,
                Due,
                DATEDIFF(day, Due, GETDATE()) as DaysOld
            FROM ben002.ARDetail
            WHERE (HistoryFlag IS NULL OR HistoryFlag = 0)
                AND DeletionTime IS NULL
                AND DATEDIFF(day, Due, GETDATE()) BETWEEN 85 AND 95
            ORDER BY Amount DESC
            """
            sample_90_results = db.execute_query(sample_90_query)
            
            # 6. Your expected values from database pull
            expected_total = 1697050.59
            expected_current = 389448.08
            expected_1_30 = 312764.25
            expected_31_60 = 173548.60
            expected_61_90 = 27931.75
            expected_over_90 = 201479.00  # Your actual database pull value
            
            return jsonify({
                'calculated': {
                    'total_ar': total_ar,
                    'bucket_sum': bucket_sum,
                    'difference': total_ar - bucket_sum,
                    'over_90_amount': over_90,
                    'over_90_percentage': round((over_90 / total_ar * 100), 1) if total_ar > 0 else 0
                },
                'buckets': buckets,
                'null_due_dates': null_due_data,
                'entry_types': entry_types,
                'sample_90_days': [dict(row) for row in sample_90_results],
                'expected': {
                    'total_ar': expected_total,
                    'current': expected_current,
                    '1-30': expected_1_30,
                    '31-60': expected_31_60,
                    '61-90': expected_61_90,
                    'over_90': expected_over_90,
                    'over_90_percentage': round((expected_over_90 / expected_total * 100), 1)
                },
                'differences': {
                    'total_ar_diff': total_ar - expected_total,
                    'current_diff': buckets.get('Current', {}).get('amount', 0) - expected_current,
                    '1-30_diff': buckets.get('1-30', {}).get('amount', 0) - expected_1_30,
                    '30-60_diff': buckets.get('30-60', {}).get('amount', 0) - expected_31_60,
                    '60-90_diff': buckets.get('60-90', {}).get('amount', 0) - expected_61_90,
                    'over_90_diff': over_90 - expected_over_90
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'ar_aging_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/expense-debug', methods=['GET'])
    @jwt_required()
    def get_expense_debug():
        """Debug endpoint to analyze expense calculations"""
        try:
            db = get_db()
            
            # Get detailed breakdown for a specific month
            month = request.args.get('month', '2025-07')  # Default to July 2025
            
            # Get expense breakdown by category
            breakdown_query = f"""
            SELECT 
                COUNT(*) as invoice_count,
                SUM(COALESCE(PartsCost, 0)) as parts_cost,
                SUM(COALESCE(LaborCost, 0)) as labor_cost,
                SUM(COALESCE(EquipmentCost, 0)) as equipment_cost,
                SUM(COALESCE(RentalCost, 0)) as rental_cost,
                SUM(COALESCE(MiscCost, 0)) as misc_cost,
                SUM(COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + 
                    COALESCE(EquipmentCost, 0) + COALESCE(RentalCost, 0) + 
                    COALESCE(MiscCost, 0)) as total_cost,
                -- Also check revenue fields for comparison
                SUM(GrandTotal) as total_revenue,
                SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue,
                SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as labor_revenue
            FROM ben002.InvoiceReg
            WHERE FORMAT(InvoiceDate, 'yyyy-MM') = '{month}'
            """
            
            result = db.execute_query(breakdown_query)
            
            if result:
                breakdown = result[0]
                
                # Get sample invoices with high costs
                sample_query = f"""
                SELECT TOP 10
                    InvoiceNo,
                    InvoiceDate,
                    BillToName,
                    SaleDept,
                    SaleCode,
                    PartsCost,
                    LaborCost,
                    EquipmentCost,
                    RentalCost,
                    MiscCost,
                    (COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + 
                     COALESCE(EquipmentCost, 0) + COALESCE(RentalCost, 0) + 
                     COALESCE(MiscCost, 0)) as total_cost,
                    GrandTotal as revenue
                FROM ben002.InvoiceReg
                WHERE FORMAT(InvoiceDate, 'yyyy-MM') = '{month}'
                ORDER BY (COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + 
                         COALESCE(EquipmentCost, 0) + COALESCE(RentalCost, 0) + 
                         COALESCE(MiscCost, 0)) DESC
                """
                
                samples = db.execute_query(sample_query)
                
                # Get monthly trend with breakdown
                trend_query = """
                SELECT 
                    FORMAT(InvoiceDate, 'yyyy-MM') as month,
                    COUNT(*) as invoices,
                    SUM(COALESCE(PartsCost, 0)) as parts,
                    SUM(COALESCE(LaborCost, 0)) as labor,
                    SUM(COALESCE(EquipmentCost, 0)) as equipment,
                    SUM(COALESCE(RentalCost, 0)) as rental,
                    SUM(COALESCE(MiscCost, 0)) as misc,
                    SUM(COALESCE(PartsCost, 0) + COALESCE(LaborCost, 0) + 
                        COALESCE(EquipmentCost, 0) + COALESCE(RentalCost, 0) + 
                        COALESCE(MiscCost, 0)) as total
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= '2025-03-01'
                GROUP BY FORMAT(InvoiceDate, 'yyyy-MM')
                ORDER BY FORMAT(InvoiceDate, 'yyyy-MM')
                """
                
                trend = db.execute_query(trend_query)
                
                return jsonify({
                    'month': month,
                    'summary': {
                        'invoice_count': int(breakdown['invoice_count']),
                        'parts_cost': float(breakdown['parts_cost'] or 0),
                        'labor_cost': float(breakdown['labor_cost'] or 0),
                        'equipment_cost': float(breakdown['equipment_cost'] or 0),
                        'rental_cost': float(breakdown['rental_cost'] or 0),
                        'misc_cost': float(breakdown['misc_cost'] or 0),
                        'total_cost': float(breakdown['total_cost'] or 0),
                        'total_revenue': float(breakdown['total_revenue'] or 0),
                        'parts_revenue': float(breakdown['parts_revenue'] or 0),
                        'labor_revenue': float(breakdown['labor_revenue'] or 0)
                    },
                    'sample_invoices': [{
                        'invoice_no': row['InvoiceNo'],
                        'date': row['InvoiceDate'].strftime('%Y-%m-%d') if row['InvoiceDate'] else None,
                        'customer': row['BillToName'],
                        'department': row['SaleDept'],
                        'sale_code': row['SaleCode'],
                        'parts_cost': float(row['PartsCost'] or 0),
                        'labor_cost': float(row['LaborCost'] or 0),
                        'equipment_cost': float(row['EquipmentCost'] or 0),
                        'rental_cost': float(row['RentalCost'] or 0),
                        'misc_cost': float(row['MiscCost'] or 0),
                        'total_cost': float(row['total_cost'] or 0),
                        'revenue': float(row['revenue'] or 0)
                    } for row in samples],
                    'monthly_trend': [{
                        'month': row['month'],
                        'invoices': int(row['invoices']),
                        'parts': float(row['parts'] or 0),
                        'labor': float(row['labor'] or 0),
                        'equipment': float(row['equipment'] or 0),
                        'rental': float(row['rental'] or 0),
                        'misc': float(row['misc'] or 0),
                        'total': float(row['total'] or 0)
                    } for row in trend]
                })
            
            return jsonify({
                'error': 'No data found for the specified month'
            }), 404
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'expense_debug_error'
            }), 500

    @reports_bp.route('/departments/accounting/find-expense-tables', methods=['GET'])
    @jwt_required()
    def find_expense_tables():
        """Help identify G&A expense tables in the database"""
        try:
            db = get_db()
            
            # Query to find potential expense-related tables
            table_query = """
            SELECT 
                TABLE_NAME,
                TABLE_TYPE
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ben002'
            AND (
                TABLE_NAME LIKE '%expense%'
                OR TABLE_NAME LIKE '%payable%'
                OR TABLE_NAME LIKE '%AP%'
                OR TABLE_NAME LIKE '%GL%'
                OR TABLE_NAME LIKE '%ledger%'
                OR TABLE_NAME LIKE '%vendor%'
                OR TABLE_NAME LIKE '%payroll%'
                OR TABLE_NAME LIKE '%salary%'
                OR TABLE_NAME LIKE '%wage%'
                OR TABLE_NAME LIKE '%payment%'
                OR TABLE_NAME LIKE '%disbursement%'
                OR TABLE_NAME LIKE '%purchase%'
                OR TABLE_NAME LIKE '%journal%'
                OR TABLE_NAME LIKE '%transaction%'
            )
            ORDER BY TABLE_NAME
            """
            
            tables = db.execute_query(table_query)
            
            # For each table, get column information
            table_details = []
            for table in tables[:20]:  # Limit to first 20 tables
                table_name = table['TABLE_NAME']
                
                column_query = f"""
                SELECT TOP 10
                    COLUMN_NAME,
                    DATA_TYPE,
                    CHARACTER_MAXIMUM_LENGTH,
                    IS_NULLABLE
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = '{table_name}'
                ORDER BY ORDINAL_POSITION
                """
                
                columns = db.execute_query(column_query)
                
                # Try to get row count
                try:
                    count_query = f"SELECT COUNT(*) as row_count FROM ben002.{table_name}"
                    count_result = db.execute_query(count_query)
                    row_count = count_result[0]['row_count'] if count_result else 0
                except:
                    row_count = -1
                
                table_details.append({
                    'table_name': table_name,
                    'row_count': row_count,
                    'columns': [{
                        'name': col['COLUMN_NAME'],
                        'type': col['DATA_TYPE'],
                        'nullable': col['IS_NULLABLE'] == 'YES'
                    } for col in columns]
                })
            
            return jsonify({
                'potential_tables': table_details,
                'message': 'Found potential G&A expense tables'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'table_discovery_error'
            }), 500

    @reports_bp.route('/departments/rental/monthly-revenue', methods=['GET'])
    @jwt_required()
    def get_rental_monthly_revenue():
        """Get monthly rental revenue with gross margin"""
        try:
            db = get_db()
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            # Get monthly rental revenue and cost data from GLDetail
            # Using same GL accounts as Currie report for consistency
            # Revenue: 411001, 419000, 420000, 421000, 434012, 410008
            # Cost: 510008, 511001, 519000, 520000, 521008, 537001, 539000, 534014, 545000
            query = """
            SELECT 
                YEAR(EffectiveDate) as year,
                MONTH(EffectiveDate) as month,
                -- Rental revenue (credit accounts, stored as negative)
                ABS(SUM(CASE WHEN AccountNo IN ('411001', '419000', '420000', '421000', '434012', '410008') 
                             THEN Amount ELSE 0 END)) as rental_revenue,
                -- Rental cost (debit accounts, stored as positive)
                ABS(SUM(CASE WHEN AccountNo IN ('510008', '511001', '519000', '520000', '521008', '537001', '539000', '534014', '545000') 
                             THEN Amount ELSE 0 END)) as rental_cost
            FROM ben002.GLDetail
            WHERE AccountNo IN ('411001', '419000', '420000', '421000', '434012', '410008',
                                '510008', '511001', '519000', '520000', '521008', '537001', '539000', '534014', '545000')
                AND EffectiveDate >= DATEADD(month, -13, GETDATE())
                AND Posted = 1
            GROUP BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            ORDER BY YEAR(EffectiveDate), MONTH(EffectiveDate)
            """
            
            results = db.execute_query(query)
            
            # Convert results to dictionary for easy lookup
            data_by_month = {}
            for row in results:
                year = row['year']
                month = row['month']
                rental_revenue = float(row['rental_revenue'] or 0)
                rental_cost = float(row['rental_cost'] or 0)
                
                # Check if this is current month or future
                is_current_or_future = (year > current_year) or (year == current_year and month >= current_month)
                
                # Calculate gross margin percentage only for historical months
                margin_percentage = None
                if not is_current_or_future and rental_revenue > 0:
                    margin_percentage = round(((rental_revenue - rental_cost) / rental_revenue) * 100, 1)
                
                month_key = (year, month)
                data_by_month[month_key] = {
                    'rental_revenue': rental_revenue,
                    'rental_cost': rental_cost,
                    'margin_percentage': margin_percentage
                }
            
            # Get fiscal year months (12 consecutive months starting with fiscal year start)
            fiscal_year_months = get_fiscal_year_months()
            
            # Generate data for each fiscal year month
            monthly_data = []
            for year, month in fiscal_year_months:
                month_date = datetime(year, month, 1)
                # Include year in label if spanning multiple calendar years
                if fiscal_year_months[0][0] != fiscal_year_months[-1][0]:
                    month_str = month_date.strftime("%b '%y")
                else:
                    month_str = month_date.strftime("%b")
                
                year_month_key = (year, month)
                prior_year_key = (year - 1, month)  # Same month, previous year
                
                # Get current year data
                if year_month_key in data_by_month:
                    data = data_by_month[year_month_key]
                    rental_revenue = data['rental_revenue']
                    rental_cost = data['rental_cost']
                    margin = data['margin_percentage']
                else:
                    rental_revenue = 0
                    rental_cost = 0
                    margin = None
                
                # Get prior year data for comparison
                if prior_year_key in data_by_month:
                    prior_data = data_by_month[prior_year_key]
                    prior_rental_revenue = prior_data['rental_revenue']
                else:
                    prior_rental_revenue = 0
                
                monthly_data.append({
                    'month': month_str,
                    'amount': rental_revenue,
                    'cost': rental_cost,
                    'margin': margin,
                    'prior_year_amount': prior_rental_revenue
                })
            
            return jsonify({
                'monthlyRentalRevenue': monthly_data
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_monthly_revenue_error'
            }), 500

    @reports_bp.route('/departments/rental/debug-revenue', methods=['GET'])
    @jwt_required()
    def debug_rental_revenue():
        """Debug endpoint to check rental revenue data"""
        try:
            db = get_db()
            
            # First check what columns exist in InvoiceReg
            columns_query = """
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'InvoiceReg' 
            AND TABLE_SCHEMA = 'ben002'
            AND (COLUMN_NAME LIKE '%dept%' OR COLUMN_NAME LIKE '%Dept%' OR COLUMN_NAME = 'SaleCode')
            ORDER BY COLUMN_NAME
            """
            
            columns_result = db.execute_query(columns_query)
            column_names = [row['COLUMN_NAME'] for row in columns_result]
            
            # Check SaleCodes
            dept_query = """
            SELECT DISTINCT SaleCode, COUNT(*) as count
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -12, GETDATE())
            GROUP BY SaleCode
            ORDER BY SaleCode
            """
            
            dept_results = db.execute_query(dept_query)
            departments = [{'salecode': row['SaleCode'], 'count': row['count']} for row in dept_results]
            
            # Check rental data with different approaches
            rental_queries = {
                
                'by_salecode': """
                SELECT 
                    YEAR(InvoiceDate) as year,
                    MONTH(InvoiceDate) as month,
                    SaleCode,
                    COUNT(*) as invoice_count,
                    SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as rental_revenue
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(month, -6, GETDATE())
                    AND SaleCode IN ('RENTR', 'RENTRS', 'RENTPM')
                GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate), SaleCode
                ORDER BY year, month, SaleCode
                """,
                
                'any_rental_revenue': """
                SELECT TOP 10
                    InvoiceDate,
                    Department,
                    SaleCode,
                    RentalTaxable,
                    RentalNonTax,
                    RentalCost,
                    GrandTotal
                FROM ben002.InvoiceReg
                WHERE (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
                ORDER BY InvoiceDate DESC
                """,
                
                'sample_invoices': """
                SELECT TOP 10
                    InvoiceDate,
                    Department,
                    SaleCode,
                    LaborTaxable,
                    LaborNonTax,
                    PartsTaxable,
                    PartsNonTax,
                    RentalTaxable,
                    RentalNonTax,
                    EquipmentTaxable,
                    EquipmentNonTax,
                    GrandTotal
                FROM ben002.InvoiceReg
                WHERE InvoiceDate >= DATEADD(month, -1, GETDATE())
                ORDER BY InvoiceDate DESC
                """
            }
            
            results = {}
            for key, query in rental_queries.items():
                try:
                    result = db.execute_query(query)
                    if key in ['by_department', 'by_salecode']:
                        results[key] = [dict(row) for row in result]
                    else:
                        results[key] = [dict(row) for row in result]
                except Exception as e:
                    results[key] = f"Error: {str(e)}"
            
            return jsonify({
                'columns': column_names,
                'salecodes': departments,
                'rental_data': results,
                'message': 'Debug data for rental revenue troubleshooting'
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'debug_error'
            }), 500

    @reports_bp.route('/departments/rental/top-customers', methods=['GET'])
    @jwt_required()
    def get_rental_top_customers():
        """Get top 10 rental customers by revenue"""
        try:
            db = get_db()
            
            # Get top 10 rental customers by total revenue with current rental count
            # Combine POLARIS INDUSTRIES and POLARIS as one customer
            query = """
            WITH RentalRevenue AS (
                SELECT 
                    CASE 
                        WHEN BillToName = 'POLARIS INDUSTRIES' OR BillToName = 'POLARIS' 
                        THEN 'POLARIS INDUSTRIES'
                        ELSE BillToName
                    END as customer_name,
                    COUNT(DISTINCT InvoiceNo) as invoice_count,
                    SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as total_revenue,
                    MAX(InvoiceDate) as last_invoice_date
                FROM ben002.InvoiceReg
                WHERE (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
                    AND BillToName IS NOT NULL
                    AND BillToName != ''
                    AND BillToName NOT LIKE '%RENTAL FLEET%'
                    AND BillToName NOT LIKE '%EXPENSE%'
                    AND BillToName NOT LIKE '%INTERNAL%'
                    AND YEAR(InvoiceDate) = YEAR(GETDATE())  -- YTD filter
                GROUP BY CASE 
                    WHEN BillToName = 'POLARIS INDUSTRIES' OR BillToName = 'POLARIS' 
                    THEN 'POLARIS INDUSTRIES'
                    ELSE BillToName
                END
            ),
            RankedCustomers AS (
                SELECT 
                    customer_name,
                    invoice_count,
                    total_revenue,
                    last_invoice_date,
                    ROW_NUMBER() OVER (ORDER BY total_revenue DESC) as rank
                FROM RentalRevenue
                WHERE total_revenue > 0
            ),
            -- Get current rental counts from RentalHistory for current month
            CurrentRentals AS (
                SELECT 
                    CASE 
                        WHEN c.Name = 'POLARIS INDUSTRIES' OR c.Name = 'POLARIS' 
                        THEN 'POLARIS INDUSTRIES'
                        ELSE c.Name
                    END as customer_name,
                    COUNT(DISTINCT rh.SerialNo) as units_on_rent
                FROM ben002.RentalHistory rh
                INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
                INNER JOIN ben002.Customer c ON e.CustomerNo = c.Number
                WHERE rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                    AND rh.DaysRented > 0
                    AND e.CustomerNo IS NOT NULL
                    AND e.CustomerNo != ''
                GROUP BY CASE 
                    WHEN c.Name = 'POLARIS INDUSTRIES' OR c.Name = 'POLARIS' 
                    THEN 'POLARIS INDUSTRIES'
                    ELSE c.Name
                END
            )
            SELECT TOP 10
                rc.rank,
                rc.customer_name,
                rc.invoice_count,
                rc.total_revenue,
                rc.last_invoice_date,
                DATEDIFF(day, rc.last_invoice_date, GETDATE()) as days_since_last_invoice,
                COALESCE(cr.units_on_rent, 0) as units_on_rent
            FROM RankedCustomers rc
            LEFT JOIN CurrentRentals cr ON rc.customer_name = cr.customer_name
            ORDER BY rc.rank
            """
            
            results = db.execute_query(query)
            
            # Calculate total YTD revenue for percentage calculation
            total_query = """
            SELECT SUM(COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) as total
            FROM ben002.InvoiceReg
            WHERE (COALESCE(RentalTaxable, 0) + COALESCE(RentalNonTax, 0)) > 0
                AND BillToName NOT LIKE '%RENTAL FLEET%'
                AND BillToName NOT LIKE '%EXPENSE%'
                AND BillToName NOT LIKE '%INTERNAL%'
                AND YEAR(InvoiceDate) = YEAR(GETDATE())  -- YTD filter
            """
            
            total_result = db.execute_query(total_query)
            total_revenue = float(total_result[0]['total'] or 0)
            
            top_customers = []
            for row in results:
                revenue = float(row['total_revenue'] or 0)
                percentage = (revenue / total_revenue * 100) if total_revenue > 0 else 0
                
                top_customers.append({
                    'rank': row['rank'],
                    'name': row['customer_name'],
                    'invoice_count': row['invoice_count'],
                    'revenue': revenue,
                    'percentage': round(percentage, 1),
                    'last_invoice_date': row['last_invoice_date'].strftime('%Y-%m-%d') if row['last_invoice_date'] else None,
                    'days_since_last': row['days_since_last_invoice'],
                    'units_on_rent': row['units_on_rent']
                })
            
            return jsonify({
                'top_customers': top_customers,
                'total_revenue': total_revenue
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_top_customers_error'
            }), 500

    @reports_bp.route('/departments/rental/units-on-rent', methods=['GET'])
    @jwt_required()
    def get_units_on_rent():
        """Get count of units currently on rent based on RentalHistory"""
        try:
            db = get_db()
            
            # Count distinct units with rental activity in current month
            # This directly shows what's on rent regardless of ownership
            query = """
            SELECT COUNT(DISTINCT SerialNo) as units_on_rent
            FROM ben002.RentalHistory
            WHERE Year = YEAR(GETDATE()) 
                AND Month = MONTH(GETDATE())
                AND DaysRented > 0
                AND RentAmount > 0
                AND DeletionTime IS NULL
            """
            
            result = db.execute_query(query)
            units_on_rent = result[0]['units_on_rent'] if result else 0
            
            return jsonify({
                'units_on_rent': units_on_rent
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_on_rent_error'
            }), 500
    
    @reports_bp.route('/departments/rental/units-on-rent-detail', methods=['GET'])
    @jwt_required()
    def get_units_on_rent_detail():
        """Get detailed list of units currently on rent with customer information"""
        try:
            db = get_db()
            
            # Get units on rent from RentalHistory with equipment details
            query = """
            SELECT 
                rh.SerialNo,
                rh.DaysRented,
                rh.RentAmount,
                e.UnitNo,
                e.Make,
                e.Model,
                e.ModelYear,
                e.Location,
                e.DayRent,
                e.WeekRent,
                e.MonthRent,
                e.CustomerNo,
                c.Name as CustomerName
            FROM ben002.RentalHistory rh
            INNER JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
                AND rh.RentAmount > 0
                AND rh.DeletionTime IS NULL
            ORDER BY c.Name, e.Make, e.Model, e.UnitNo
            """
            
            results = db.execute_query(query)
            
            units_detail = []
            for row in results:
                # Handle customer info - could be from Equipment owner or from rental activity
                customer_name = row['CustomerName']
                if not customer_name or customer_name == 'RENTAL FLEET - EXPENSE':
                    customer_name = 'Rental Customer'
                    
                units_detail.append({
                    'customer_name': customer_name,
                    'customer_no': row['CustomerNo'] or '',
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'make': row['Make'],
                    'model': row['Model'],
                    'model_year': row['ModelYear'],
                    'location': row['Location'],
                    'days_rented': row['DaysRented'],
                    'rent_amount': float(row['RentAmount'] or 0),
                    'day_rent': float(row['DayRent'] or 0),
                    'week_rent': float(row['WeekRent'] or 0),
                    'month_rent': float(row['MonthRent'] or 0)
                })
            
            return jsonify({
                'units': units_detail,
                'count': len(units_detail)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_on_rent_detail_error'
            }), 500

    @reports_bp.route('/departments/rental/units-on-hold', methods=['GET'])
    @jwt_required()
    def get_units_on_hold():
        """Get count of units currently on hold"""
        try:
            db = get_db()
            
            # Count units with RentalStatus = 'Hold'
            query = """
            SELECT COUNT(*) as units_on_hold
            FROM ben002.Equipment
            WHERE RentalStatus = 'Hold'
            """
            
            result = db.execute_query(query)
            units_on_hold = result[0]['units_on_hold'] if result else 0
            
            return jsonify({
                'units_on_hold': units_on_hold
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_on_hold_error'
            }), 500

    @reports_bp.route('/departments/rental/units-on-hold-detail', methods=['GET'])
    @jwt_required()
    def get_units_on_hold_detail():
        """Get detailed list of units currently on hold"""
        try:
            db = get_db()
            
            # Get detailed information for units on hold
            query = """
            SELECT 
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.ModelYear,
                e.Location,
                e.Cost,
                e.Sell as ListPrice,
                e.DayRent,
                e.WeekRent,
                e.MonthRent,
                e.RentalStatus,
                -- Get customer info if assigned
                e.CustomerNo,
                c.Name as CustomerName
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE e.RentalStatus = 'Hold'
            ORDER BY e.Make, e.Model, e.UnitNo
            """
            
            results = db.execute_query(query)
            
            units_detail = []
            for row in results:
                units_detail.append({
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'make': row['Make'],
                    'model': row['Model'],
                    'model_year': row['ModelYear'],
                    'location': row['Location'],
                    'cost': float(row['Cost'] or 0),
                    'list_price': float(row['ListPrice'] or 0),
                    'day_rent': float(row['DayRent'] or 0),
                    'week_rent': float(row['WeekRent'] or 0),
                    'month_rent': float(row['MonthRent'] or 0),
                    'rental_status': row['RentalStatus'],
                    'customer_no': row['CustomerNo'] or '',
                    'customer_name': row['CustomerName'] or 'No Customer Assigned'
                })
            
            return jsonify({
                'units': units_detail,
                'count': len(units_detail)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_on_hold_detail_error'
            }), 500
    
    @reports_bp.route('/departments/rental/equipment-report', methods=['GET'])
    @jwt_required()
    def get_rental_equipment_report():
        """Get all equipment associated with the rental department"""
        try:
            db = get_db()
            
            # Get equipment owned by rental department (900006)
            query = """
            WITH RentalEquipment AS (
                SELECT 
                    e.UnitNo,
                    e.SerialNo,
                    e.Make,
                    e.Model,
                    e.ModelYear,
                    e.RentalStatus,
                    e.Location,
                    e.Cost,
                    e.Retail as ListPrice,
                    e.DayRent,
                    e.WeekRent,
                    e.MonthRent,
                    e.CustomerNo,
                    e.Customer as CustomerFlag,
                    e.LastHourMeter,
                    e.LastHourMeterDate,
                    e.RentalYTD,
                    e.RentalITD,
                    c.Name as CurrentCustomer,
                    -- Check if currently on rent
                    CASE 
                        WHEN rh.SerialNo IS NOT NULL THEN 'On Rent'
                        WHEN e.RentalStatus = 'On Hold' THEN 'On Hold'
                        WHEN e.RentalStatus = 'Ready To Rent' THEN 'Available'
                        ELSE COALESCE(e.RentalStatus, 'Unknown')
                    END as CurrentStatus,
                    rh.DaysRented as CurrentMonthDays,
                    rh.RentAmount as CurrentMonthRevenue
                FROM ben002.Equipment e
                LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
                LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                    AND rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                    AND rh.DaysRented > 0
                    AND rh.DeletionTime IS NULL
                WHERE EXISTS (
                    SELECT 1 FROM ben002.RentalHistory rh 
                    WHERE rh.SerialNo = e.SerialNo 
                    AND rh.DaysRented > 0
                )
            )
            SELECT 
                UnitNo,
                SerialNo,
                Make,
                Model,
                ModelYear,
                CurrentStatus,
                RentalStatus,
                Location,
                Cost,
                ListPrice,
                DayRent,
                WeekRent,
                MonthRent,
                CustomerNo,
                CurrentCustomer,
                LastHourMeter,
                LastHourMeterDate,
                RentalYTD,
                RentalITD,
                CurrentMonthDays,
                CurrentMonthRevenue,
                -- Calculate utilization
                CASE 
                    WHEN CurrentStatus = 'On Rent' THEN 100
                    WHEN CurrentStatus = 'Available' THEN 0
                    ELSE NULL
                END as UtilizationPercent
            FROM RentalEquipment
            ORDER BY CurrentStatus DESC, UnitNo
            """
            
            results = db.execute_query(query)
            
            # Get summary statistics
            summary_query = """
            SELECT 
                COUNT(*) as total_units,
                COUNT(CASE WHEN e.CustomerNo = '900006' THEN 1 END) as fleet_owned_units,
                COUNT(CASE WHEN rh.SerialNo IS NOT NULL THEN 1 END) as units_on_rent,
                COUNT(CASE WHEN e.RentalStatus = 'Ready To Rent' THEN 1 END) as available_units,
                COUNT(CASE WHEN e.RentalStatus = 'On Hold' THEN 1 END) as on_hold_units,
                SUM(e.Cost) as total_fleet_value,
                SUM(e.RentalYTD) as total_ytd_revenue,
                SUM(rh.RentAmount) as current_month_revenue
            FROM ben002.Equipment e
            LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                AND rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
                AND rh.DeletionTime IS NULL
            WHERE (e.CustomerNo = '900006'
                OR e.InventoryDept = 40
                OR e.RentalStatus IS NOT NULL)
                AND UPPER(e.Make) IN ('LINDE', 'KOMATSU', 'BENDI', 'CLARK', 'CROWN', 'UNICARRIERS')
            """
            
            summary_result = db.execute_query(summary_query)
            summary = summary_result[0] if summary_result else {}
            
            # Get breakdown by make
            make_breakdown_query = """
            SELECT 
                e.Make,
                COUNT(*) as unit_count,
                COUNT(CASE WHEN rh.SerialNo IS NOT NULL THEN 1 END) as on_rent_count,
                SUM(e.Cost) as total_value,
                SUM(e.RentalYTD) as ytd_revenue
            FROM ben002.Equipment e
            LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                AND rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
                AND rh.DeletionTime IS NULL
            WHERE (e.CustomerNo = '900006' OR e.InventoryDept = 40 OR e.RentalStatus IS NOT NULL)
                AND UPPER(e.Make) IN ('LINDE', 'KOMATSU', 'BENDI', 'CLARK', 'CROWN', 'UNICARRIERS')
            GROUP BY e.Make
            ORDER BY unit_count DESC
            """
            
            make_breakdown = db.execute_query(make_breakdown_query)
            
            return jsonify({
                'equipment': results,
                'summary': summary,
                'make_breakdown': make_breakdown
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_equipment_report_error'
            }), 500

    @reports_bp.route('/departments/rental/rental-fleet-diagnostic', methods=['GET'])
    @jwt_required()
    def get_rental_fleet_diagnostic():
        """Diagnostic to understand the rental fleet ownership"""
        try:
            db = get_db()
            
            diagnostics = {}
            
            # 1. Count total equipment owned by RENTAL FLEET (900006)
            query1 = """
            SELECT 
                COUNT(*) as total_fleet_units,
                COUNT(CASE WHEN RentalStatus = 'Ready To Rent' THEN 1 END) as ready_to_rent,
                COUNT(CASE WHEN RentalStatus = 'Hold' THEN 1 END) as on_hold,
                COUNT(CASE WHEN RentalStatus IS NULL THEN 1 END) as null_status
            FROM ben002.Equipment
            WHERE CustomerNo = '900006'
            """
            diagnostics['rental_fleet_owned'] = db.execute_query(query1)
            
            # 2. Get rental activity for fleet equipment
            query2 = """
            SELECT 
                COUNT(DISTINCT e.SerialNo) as units_with_activity,
                COUNT(DISTINCT CASE WHEN rh.SerialNo IS NOT NULL THEN e.SerialNo END) as units_in_rental_history
            FROM ben002.Equipment e
            LEFT JOIN (
                SELECT DISTINCT SerialNo 
                FROM ben002.RentalHistory 
                WHERE Year = YEAR(GETDATE()) 
                AND Month = MONTH(GETDATE())
                AND DaysRented > 0
            ) rh ON e.SerialNo = rh.SerialNo
            WHERE e.CustomerNo = '900006'
            """
            diagnostics['fleet_rental_activity'] = db.execute_query(query2)
            
            # 3. Sample of rental fleet equipment
            query3 = """
            SELECT TOP 10
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.RentalStatus,
                e.DayRent,
                e.WeekRent,
                e.MonthRent
            FROM ben002.Equipment e
            WHERE e.CustomerNo = '900006'
            ORDER BY e.UnitNo
            """
            diagnostics['fleet_sample'] = db.execute_query(query3)
            
            # 4. Check RentalContract structure
            query4 = """
            SELECT 
                COUNT(*) as total_contracts
            FROM ben002.RentalContract
            WHERE DeletionTime IS NULL
            """
            diagnostics['rental_contract_summary'] = db.execute_query(query4)
            
            # 5. Get count of all equipment by CustomerNo to see the big picture
            query5 = """
            SELECT 
                CustomerNo,
                c.Name as CustomerName,
                COUNT(*) as equipment_count
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE CustomerNo IN ('900006', '900007', '900008', '900009')
            GROUP BY CustomerNo, c.Name
            ORDER BY equipment_count DESC
            """
            diagnostics['internal_customer_equipment'] = db.execute_query(query5)
            
            return jsonify(diagnostics)
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_fleet_diagnostic_error'
            }), 500

    @reports_bp.route('/departments/rental/rental-vs-sales-diagnostic', methods=['GET'])
    @jwt_required()
    def get_rental_vs_sales_diagnostic():
        """Diagnostic to determine if CustomerNo means rental or sale"""
        try:
            db = get_db()
            
            diagnostics = {}
            
            # 1. Check Equipment with CustomerNo and their Customer flag
            query1 = """
            SELECT 
                CASE 
                    WHEN Customer = 1 THEN 'Customer Flag = 1'
                    WHEN Customer = 0 THEN 'Customer Flag = 0'
                    ELSE 'Customer Flag NULL'
                END as customer_flag_status,
                COUNT(*) as count,
                COUNT(CASE WHEN CustomerNo IS NOT NULL AND CustomerNo != '' THEN 1 END) as has_customer_no
            FROM ben002.Equipment
            GROUP BY Customer
            """
            diagnostics['customer_flag_analysis'] = db.execute_query(query1)
            
            # 2. Sample equipment with CustomerNo to see patterns
            query2 = """
            SELECT TOP 20
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.Customer as CustomerFlag,
                e.CustomerNo,
                c.Name as CustomerName,
                e.RentalStatus,
                e.DayRent,
                e.WeekRent,
                e.MonthRent,
                -- Check if this equipment has rental history
                CASE WHEN rh.SerialNo IS NOT NULL THEN 'Has Rental History' ELSE 'No Rental History' END as rental_history_status,
                -- Check if sold through invoice
                CASE WHEN inv.SerialNo IS NOT NULL THEN 'Found in Invoice' ELSE 'Not in Invoice' END as invoice_status
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            LEFT JOIN (
                SELECT DISTINCT SerialNo 
                FROM ben002.RentalHistory 
                WHERE Year >= 2024
            ) rh ON e.SerialNo = rh.SerialNo
            LEFT JOIN (
                SELECT DISTINCT SerialNo 
                FROM ben002.InvoiceReg 
                WHERE SerialNo IS NOT NULL
            ) inv ON e.SerialNo = inv.SerialNo
            WHERE e.CustomerNo IS NOT NULL 
                AND e.CustomerNo != ''
                AND e.CustomerNo != '0'
            ORDER BY e.UnitNo
            """
            diagnostics['sample_equipment_with_customer'] = db.execute_query(query2)
            
            # 3. Check RentalContract to see if it links to Equipment
            query3 = """
            SELECT TOP 10
                rc.RentalContractNo,
                rc.CustomerNo,
                c.Name as CustomerName,
                rc.StartDate,
                rc.EndDate,
                rc.DeliveryCharge,
                rc.PickupCharge
            FROM ben002.RentalContract rc
            LEFT JOIN ben002.Customer c ON rc.CustomerNo = c.Number
            WHERE rc.DeletionTime IS NULL
            ORDER BY rc.RentalContractNo DESC
            """
            diagnostics['rental_contracts_sample'] = db.execute_query(query3)
            
            # 4. Check if there's a RentalContractEquipment table
            query4 = """
            SELECT TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ben002'
            AND TABLE_NAME LIKE '%Rental%Equipment%'
            """
            diagnostics['rental_equipment_tables'] = db.execute_query(query4)
            
            return jsonify(diagnostics)
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_vs_sales_diagnostic_error'
            }), 500

    @reports_bp.route('/departments/rental/units-diagnostic', methods=['GET'])
    @jwt_required()
    def get_units_diagnostic():
        """Diagnostic to find where the 400 units on rent are tracked"""
        try:
            db = get_db()
            
            diagnostics = {}
            
            # 1. Check Equipment table RentalStatus values
            status_query = """
            SELECT RentalStatus, COUNT(*) as count
            FROM ben002.Equipment
            GROUP BY RentalStatus
            ORDER BY count DESC
            """
            diagnostics['equipment_rental_status'] = db.execute_query(status_query)
            
            # 2. Check Equipment table for units with CustomerNo
            customer_query = """
            SELECT 
                CASE 
                    WHEN CustomerNo IS NULL OR CustomerNo = '' THEN 'No Customer'
                    WHEN Customer = 1 THEN 'Has Customer Flag'
                    ELSE 'Has CustomerNo Only'
                END as status,
                COUNT(*) as count
            FROM ben002.Equipment
            GROUP BY 
                CASE 
                    WHEN CustomerNo IS NULL OR CustomerNo = '' THEN 'No Customer'
                    WHEN Customer = 1 THEN 'Has Customer Flag'
                    ELSE 'Has CustomerNo Only'
                END
            """
            diagnostics['equipment_customer_status'] = db.execute_query(customer_query)
            
            # 3. Count Equipment with CustomerNo that are likely on rent
            on_rent_query = """
            SELECT COUNT(*) as count
            FROM ben002.Equipment
            WHERE CustomerNo IS NOT NULL 
                AND CustomerNo != ''
                AND CustomerNo != '0'
            """
            diagnostics['equipment_with_customer'] = db.execute_query(on_rent_query)
            
            # 4. Sample of equipment with customers
            sample_query = """
            SELECT TOP 10
                e.UnitNo,
                e.SerialNo,
                e.Make,
                e.Model,
                e.RentalStatus,
                e.CustomerNo,
                e.Customer as CustomerFlag,
                c.Name as CustomerName
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE e.CustomerNo IS NOT NULL 
                AND e.CustomerNo != ''
                AND e.CustomerNo != '0'
            ORDER BY e.UnitNo
            """
            diagnostics['sample_equipment_with_customer'] = db.execute_query(sample_query)
            
            # 5. Check RentalContract table
            contract_query = """
            SELECT COUNT(*) as active_contracts
            FROM ben002.RentalContract
            WHERE DeletionTime IS NULL
            """
            diagnostics['rental_contracts'] = db.execute_query(contract_query)
            
            # 6. Check RentalHistory current month total
            history_query = """
            SELECT 
                COUNT(DISTINCT SerialNo) as unique_units,
                COUNT(*) as total_records
            FROM ben002.RentalHistory
            WHERE Year = YEAR(GETDATE()) AND Month = MONTH(GETDATE())
            """
            diagnostics['rental_history_current_month'] = db.execute_query(history_query)
            
            return jsonify(diagnostics)
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'units_diagnostic_error'
            }), 500

    @reports_bp.route('/departments/rental/available-forklifts', methods=['GET'])
    @jwt_required()
    def get_available_forklifts():
        """Get list of all available rental equipment (Ready To Rent status)"""
        try:
            db = get_db()
            
            # Get ALL equipment that is Ready To Rent (matches the inventory count logic)
            query = """
            SELECT 
                UnitNo,
                SerialNo,
                Make,
                Model,
                ModelYear,
                Cost,
                Sell as ListPrice,
                RentalStatus,
                Location,
                DayRent,
                WeekRent,
                MonthRent
            FROM ben002.Equipment
            WHERE RentalStatus = 'Ready To Rent'
            ORDER BY Make, Model, UnitNo
            """
            
            results = db.execute_query(query)
            
            forklifts = []
            for row in results:
                forklifts.append({
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'make': row['Make'],
                    'model': row['Model'],
                    'model_year': row['ModelYear'],
                    'cost': float(row['Cost'] or 0),
                    'list_price': float(row['ListPrice'] or 0),
                    'rental_status': row['RentalStatus'],
                    'location': row['Location'],
                    'day_rent': float(row['DayRent'] or 0),
                    'week_rent': float(row['WeekRent'] or 0),
                    'month_rent': float(row['MonthRent'] or 0)
                })
            
            return jsonify({
                'forklifts': forklifts,
                'count': len(forklifts)
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'available_forklifts_error'
            }), 500

    @reports_bp.route('/departments/rental/forklift-query-diagnostic', methods=['GET'])
    @jwt_required()
    def get_forklift_query_diagnostic():
        """Diagnostic to understand what the forklift query actually returns"""
        try:
            db = get_db()
            
            # Test the exact query from available-forklifts endpoint
            query = """
            SELECT 
                UnitNo,
                SerialNo,
                Make,
                Model,
                ModelYear,
                Cost,
                Sell as ListPrice,
                COALESCE(RentalStatus, 'On Rent') as RentalStatus,
                -- Additional debug fields
                UPPER(Make) as UpperMake,
                UPPER(Model) as UpperModel,
                CASE 
                    WHEN UPPER(Model) LIKE '%FORK%' THEN 'Model contains FORK'
                    WHEN UPPER(Make) LIKE '%FORK%' THEN 'Make contains FORK'
                    ELSE 'No match'
                END as MatchReason
            FROM ben002.Equipment
            WHERE UPPER(Model) LIKE '%FORK%' OR UPPER(Make) LIKE '%FORK%'
            ORDER BY Make, Model, UnitNo
            """
            
            results = db.execute_query(query)
            
            # Count total equipment
            count_query = "SELECT COUNT(*) as total_equipment FROM ben002.Equipment"
            count_result = db.execute_query(count_query)
            total_equipment = count_result[0]['total_equipment'] if count_result else 0
            
            # Get some sample equipment records to understand the data better
            sample_query = """
            SELECT TOP 10
                UnitNo,
                SerialNo,
                Make,
                Model,
                UPPER(Make) as UpperMake,
                UPPER(Model) as UpperModel
            FROM ben002.Equipment
            WHERE Make IS NOT NULL AND Model IS NOT NULL
            ORDER BY UnitNo
            """
            
            sample_results = db.execute_query(sample_query)
            
            # Test alternative forklift queries
            alt_queries = {}
            
            # Query 1: More specific forklift matching
            alt1_query = """
            SELECT COUNT(*) as count FROM ben002.Equipment
            WHERE (UPPER(Model) LIKE '%FORKLIFT%' 
                   OR UPPER(Model) LIKE 'FORK%'
                   OR UPPER(Make) IN ('YALE', 'HYSTER', 'TOYOTA', 'CROWN', 'CLARK', 'LINDE')
                   OR UPPER(Model) LIKE '%LIFT TRUCK%')
            """
            alt1_result = db.execute_query(alt1_query)
            alt_queries['specific_forklift_terms'] = alt1_result[0]['count'] if alt1_result else 0
            
            # Query 2: Just looking for FORKLIFT in model
            alt2_query = """
            SELECT COUNT(*) as count FROM ben002.Equipment
            WHERE UPPER(Model) LIKE '%FORKLIFT%'
            """
            alt2_result = db.execute_query(alt2_query)
            alt_queries['model_contains_forklift'] = alt2_result[0]['count'] if alt2_result else 0
            
            # Query 3: Common forklift manufacturers
            alt3_query = """
            SELECT COUNT(*) as count FROM ben002.Equipment
            WHERE UPPER(Make) IN ('YALE', 'HYSTER', 'TOYOTA', 'CROWN', 'CLARK', 'LINDE', 'CATERPILLAR', 'KOMATSU')
            """
            alt3_result = db.execute_query(alt3_query)
            alt_queries['known_forklift_makes'] = alt3_result[0]['count'] if alt3_result else 0
            
            return jsonify({
                'forklift_results': results,
                'forklift_count': len(results),
                'total_equipment_count': total_equipment,
                'sample_equipment': sample_results,
                'alternative_queries': alt_queries,
                'query_used': query
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'forklift_diagnostic_error'
            }), 500
    
    @reports_bp.route('/departments/rental/customer-units-diagnostic', methods=['GET'])
    @jwt_required()
    def get_customer_units_diagnostic():
        """Diagnostic to understand customer rental units"""
        try:
            db = get_db()
            
            # Check RentalHistory for current month
            query = """
            SELECT 
                COUNT(*) as total_records,
                COUNT(DISTINCT SerialNo) as unique_units,
                MIN(Year) as min_year,
                MAX(Year) as max_year,
                MIN(Month) as min_month,
                MAX(Month) as max_month
            FROM ben002.RentalHistory
            WHERE Year = YEAR(GETDATE()) AND Month = MONTH(GETDATE())
            """
            
            results = db.execute_query(query)
            
            # Get sample rental history with customer info
            sample_query = """
            SELECT TOP 10
                rh.SerialNo,
                rh.Year,
                rh.Month,
                rh.DaysRented,
                rh.RentAmount,
                e.UnitNo,
                e.CustomerNo,
                c.Name as CustomerName
            FROM ben002.RentalHistory rh
            LEFT JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
            ORDER BY rh.RentAmount DESC
            """
            
            sample_results = db.execute_query(sample_query)
            
            # Count by customer
            customer_query = """
            SELECT 
                COALESCE(c.Name, 'No Customer') as customer_name,
                COUNT(DISTINCT rh.SerialNo) as units_on_rent,
                SUM(rh.RentAmount) as total_rent
            FROM ben002.RentalHistory rh
            LEFT JOIN ben002.Equipment e ON rh.SerialNo = e.SerialNo
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
            GROUP BY c.Name
            ORDER BY COUNT(DISTINCT rh.SerialNo) DESC
            """
            
            customer_results = db.execute_query(customer_query)
            
            return jsonify({
                'current_month_summary': results[0] if results else {},
                'sample_rentals': [dict(row) for row in sample_results] if sample_results else [],
                'customers_with_units': [dict(row) for row in customer_results] if customer_results else []
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'customer_units_diagnostic_error'
            }), 500
    
    @reports_bp.route('/departments/rental/rental-status-diagnostic', methods=['GET'])
    @jwt_required()
    def get_rental_status_diagnostic():
        """Diagnostic endpoint to check rental indicators"""
        try:
            db = get_db()
            
            # Check rental contracts - this is the real answer!
            rental_contract_query = """
            SELECT 
                COUNT(DISTINCT rc.RentalContractNo) as active_contracts,
                COUNT(DISTINCT re.SerialNo) as units_on_contract
            FROM ben002.RentalContract rc
            LEFT JOIN ben002.RentalContractEquipment re ON rc.RentalContractNo = re.RentalContractNo
            WHERE rc.DeletionTime IS NULL
                AND (rc.EndDate IS NULL OR rc.EndDate >= GETDATE() OR rc.OpenEndedContract = 1)
            """
            
            # If RentalContractEquipment doesn't exist, try simpler query
            try:
                contract_results = db.execute_query(rental_contract_query)
            except:
                # Fallback if join table doesn't exist
                rental_contract_query = """
                SELECT COUNT(*) as active_contracts
                FROM ben002.RentalContract
                WHERE DeletionTime IS NULL
                    AND (EndDate IS NULL OR EndDate >= GETDATE() OR OpenEndedContract = 1)
                """
                contract_results = db.execute_query(rental_contract_query)
            
            # Check various rental indicators in Equipment table
            query = """
            SELECT 
                -- Unit types
                COUNT(*) as total_equipment,
                COUNT(CASE WHEN UnitType = 'Rental' OR UnitType LIKE '%Rent%' THEN 1 END) as rental_unit_type,
                COUNT(CASE WHEN WebRentalFlag = 1 THEN 1 END) as web_rental_flag,
                COUNT(CASE WHEN RentalRateCode IS NOT NULL AND RentalRateCode != '' THEN 1 END) as has_rental_rate,
                
                -- Current rental status
                COUNT(CASE WHEN CustomerNo IS NOT NULL AND CustomerNo != '' THEN 1 END) as has_customer,
                COUNT(CASE WHEN RentalStatus = 'Ready To Rent' THEN 1 END) as ready_to_rent,
                COUNT(CASE WHEN RentalStatus IS NULL OR RentalStatus = '' THEN 1 END) as null_status,
                
                -- Combinations
                COUNT(CASE WHEN (UnitType = 'Rental' OR WebRentalFlag = 1) AND CustomerNo IS NOT NULL AND CustomerNo != '' THEN 1 END) as rental_units_with_customer,
                COUNT(CASE WHEN (UnitType = 'Rental' OR WebRentalFlag = 1) AND (RentalStatus = 'Ready To Rent' OR RentalStatus = 'Hold') THEN 1 END) as rental_units_available
            FROM ben002.Equipment
            """
            
            results = db.execute_query(query)
            
            # Check UnitType values
            unit_type_query = """
            SELECT DISTINCT UnitType, COUNT(*) as count
            FROM ben002.Equipment
            WHERE UnitType IS NOT NULL
            GROUP BY UnitType
            ORDER BY count DESC
            """
            
            unit_type_results = db.execute_query(unit_type_query)
            
            # Sample rental units with customer info
            sample_query = """
            SELECT TOP 10
                e.UnitNo, e.Make, e.Model, e.UnitType, e.WebRentalFlag, e.RentalStatus, 
                e.CustomerNo, c.Name as CustomerName,
                e.RentalRateCode, e.DayRent, e.WeekRent, e.MonthRent
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE (e.UnitType = 'Rental' OR e.WebRentalFlag = 1 OR e.RentalRateCode IS NOT NULL)
                AND e.CustomerNo IS NOT NULL AND e.CustomerNo != ''
            """
            
            sample_results = db.execute_query(sample_query)
            
            # Check if RentalContractEquipment or similar table exists to link contracts to equipment/customers
            contract_link_query = """
            SELECT TOP 5 
                rc.RentalContractNo,
                rc.StartDate,
                rc.EndDate,
                e.SerialNo,
                e.UnitNo,
                e.CustomerNo,
                c.Name as CustomerName
            FROM ben002.RentalContract rc
            INNER JOIN ben002.Equipment e ON e.CustomerNo IS NOT NULL
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            WHERE rc.DeletionTime IS NULL
                AND (rc.EndDate IS NULL OR rc.EndDate >= GETDATE() OR rc.OpenEndedContract = 1)
                AND EXISTS (
                    SELECT 1 FROM ben002.RentalHistory rh 
                    WHERE rh.SerialNo = e.SerialNo 
                    AND rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                )
            """
            
            try:
                contract_link_results = db.execute_query(contract_link_query)
            except:
                contract_link_results = []
            
            return jsonify({
                'rental_contracts': contract_results[0] if contract_results else {},
                'rental_indicators': results[0] if results else {},
                'unit_types': [{'type': row['UnitType'], 'count': row['count']} for row in unit_type_results] if unit_type_results else [],
                'sample_rental_units': [dict(row) for row in sample_results] if sample_results else [],
                'contract_equipment_links': [dict(row) for row in contract_link_results] if contract_link_results else []
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'rental_status_diagnostic_error'
            }), 500

    @reports_bp.route('/departments/accounting/sales-commissions', methods=['GET'])
    @require_permission('view_commissions')
    def get_sales_commissions():
        """Get sales commission report for a specific month"""
        try:
            db = get_db()
            
            # Get month parameter (format: YYYY-MM)
            month_param = request.args.get('month')
            if not month_param:
                # Default to previous month
                today = datetime.today()
                prev_month = today.replace(day=1) - timedelta(days=1)
                month_param = prev_month.strftime('%Y-%m')
            
            # Parse month parameter
            year, month = map(int, month_param.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Query to get sales by salesman and category
            # Use WO.Salesman field directly - join on WONo = InvoiceNo
            sales_query = """
            SELECT 
                COALESCE(wo.Salesman, 'Unassigned') as SalesRep,
                -- Rental sales and costs
                SUM(CASE 
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)
                    ELSE 0 
                END) as RentalSales,
                SUM(CASE 
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN COALESCE(ir.RentalCost, 0)
                    ELSE 0 
                END) as RentalCost,
                -- Used equipment sales and costs
                SUM(CASE 
                    -- USEDEQ is used equipment, RNTSALE is selling used rental units
                    -- USED K, USED L, USED SL are additional used equipment codes
                    -- Note: USEDEQP is equipment prep, not sales; USEDCAP is not commissionable
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as UsedEquipmentSales,
                SUM(CASE 
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL')
                    THEN COALESCE(ir.EquipmentCost, 0)
                    ELSE 0 
                END) as UsedEquipmentCost,
                -- Allied equipment sales and costs
                SUM(CASE 
                    WHEN ir.SaleCode = 'ALLIED'
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as AlliedEquipmentSales,
                SUM(CASE 
                    WHEN ir.SaleCode = 'ALLIED'
                    THEN COALESCE(ir.EquipmentCost, 0)
                    ELSE 0 
                END) as AlliedEquipmentCost,
                -- New equipment sales and costs
                SUM(CASE 
                    -- LINDE is new Linde equipment, NEWEQ/NEWEQP-R are other new equipment, KOM is Komatsu
                    WHEN ir.SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as NewEquipmentSales,
                SUM(CASE 
                    WHEN ir.SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                    THEN COALESCE(ir.EquipmentCost, 0)
                    ELSE 0 
                END) as NewEquipmentCost
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.WO wo ON ir.InvoiceNo = wo.WONo
            WHERE ir.InvoiceDate >= %s
                AND ir.InvoiceDate <= %s
                AND COALESCE(wo.Salesman, 'Unassigned') != 'Unassigned'
                AND COALESCE(wo.Salesman, 'Unassigned') IS NOT NULL
                AND COALESCE(wo.Salesman, 'Unassigned') != ''
                AND UPPER(COALESCE(wo.Salesman, 'Unassigned')) != 'HOUSE'
            GROUP BY COALESCE(wo.Salesman, 'Unassigned')
            ORDER BY SUM(
                COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0) +
                COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
            ) DESC
            """
            
            results = db.execute_query(sales_query, [start_date, end_date, start_date, end_date])
            
            # SIMPLIFIED Commission structure (Proposed):
            # - Equipment Sales (All types): 15% of gross profit, $75 minimum per invoice
            # - Rentals: 8% of revenue (unlimited duration, no 12-month cap)
            # Note: House accounts excluded from rental commissions

            # Use dictionary to combine salespeople with aliased names
            salespeople_dict = {}
            totals = {
                'rental': 0,
                'used_equipment': 0,
                'allied_equipment': 0,
                'new_equipment': 0,
                'total_sales': 0,
                'total_commissions': 0
            }

            for row in results:
                # Normalize salesman name to combine aliases (e.g., "Tod Auge" -> "Todd Auge")
                salesman_name = normalize_salesman_name(row['SalesRep'])

                rental = float(row['RentalSales'] or 0)
                rental_cost = float(row['RentalCost'] or 0)
                used = float(row['UsedEquipmentSales'] or 0)
                used_cost = float(row['UsedEquipmentCost'] or 0)
                allied = float(row['AlliedEquipmentSales'] or 0)
                allied_cost = float(row['AlliedEquipmentCost'] or 0)
                new = float(row['NewEquipmentSales'] or 0)
                new_cost = float(row['NewEquipmentCost'] or 0)

                total_sales = rental + used + allied + new

                # Commission Calculations:
                # Rental: 8% of revenue (no limits, no tracking needed)
                rental_commission = rental * 0.08

                # New Equipment: 20% of gross profit
                new_gp = new - new_cost
                new_commission = new_gp * 0.20 if new_gp > 0 else 0

                # Allied Equipment: 20% of gross profit
                allied_gp = allied - allied_cost
                allied_commission = allied_gp * 0.20 if allied_gp > 0 else 0

                # Used Equipment: 5% of sale price
                used_commission = used * 0.05

                commission_amount = rental_commission + new_commission + allied_commission + used_commission

                # Check if this salesman already exists (combining aliased entries)
                if salesman_name in salespeople_dict:
                    # Add to existing entry
                    existing = salespeople_dict[salesman_name]
                    existing['rental'] += rental
                    existing['used_equipment'] += used
                    existing['allied_equipment'] += allied
                    existing['new_equipment'] += new
                    existing['total_sales'] += total_sales
                    existing['commission_amount'] += commission_amount
                else:
                    # Create new entry
                    salespeople_dict[salesman_name] = {
                        'name': salesman_name,
                        'rental': rental,
                        'used_equipment': used,
                        'allied_equipment': allied,
                        'new_equipment': new,
                        'total_sales': total_sales,
                        'commission_amount': commission_amount
                    }

                # Update totals - keep individual categories for display
                totals['rental'] += rental
                totals['used_equipment'] += used
                totals['allied_equipment'] += allied
                totals['new_equipment'] += new
                totals['total_sales'] += total_sales
                totals['total_commissions'] += commission_amount

            # Convert dict to list and calculate effective commission rates
            salespeople = []
            for sp in salespeople_dict.values():
                sp['commission_rate'] = sp['commission_amount'] / sp['total_sales'] if sp['total_sales'] > 0 else 0
                salespeople.append(sp)

            # Sort by total sales descending
            salespeople.sort(key=lambda x: x['total_sales'], reverse=True)

            return jsonify({
                'month': month_param,
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'salespeople': salespeople,
                'totals': totals
            })
            
        except Exception as e:
            logger.error(f"Error fetching sales commissions: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/sales-commission-diagnostic', methods=['GET'])
    @jwt_required()
    def get_sales_commission_diagnostic():
        """Diagnostic endpoint to understand sales data structure"""
        try:
            db = get_db()
            
            # Get month parameter
            month_param = request.args.get('month')
            if not month_param:
                today = datetime.today()
                prev_month = today.replace(day=1) - timedelta(days=1)
                month_param = prev_month.strftime('%Y-%m')
            
            year, month = map(int, month_param.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # 1. Check what SaleCodes exist
            sale_codes_query = """
            SELECT 
                ir.SaleCode,
                COUNT(*) as InvoiceCount,
                SUM(COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)) as RentalRevenue,
                SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) as EquipmentRevenue,
                SUM(ir.GrandTotal) as TotalRevenue
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
            GROUP BY ir.SaleCode
            ORDER BY COUNT(*) DESC
            """
            
            sale_codes = db.execute_query(sale_codes_query, [start_date, end_date])
            
            # 2. Check sample invoices with equipment sales
            equipment_sample_query = """
            SELECT TOP 20
                ir.InvoiceNo,
                ir.SaleCode,
                ir.BillToName,
                c.Salesman1,
                ir.Comments,
                ir.EquipmentTaxable,
                ir.EquipmentNonTax,
                ir.RentalTaxable,
                ir.RentalNonTax
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
                AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
            ORDER BY ir.InvoiceDate DESC
            """
            
            equipment_samples = db.execute_query(equipment_sample_query, [start_date, end_date])
            
            # 3. Check salesmen distribution
            salesmen_query = """
            SELECT 
                c.Salesman1,
                COUNT(DISTINCT ir.InvoiceNo) as InvoiceCount,
                SUM(ir.GrandTotal) as TotalSales
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
                AND c.Salesman1 IS NOT NULL
            GROUP BY c.Salesman1
            ORDER BY SUM(ir.GrandTotal) DESC
            """
            
            salesmen = db.execute_query(salesmen_query, [start_date, end_date])
            
            # 4. Check rental invoices
            rental_check_query = """
            SELECT 
                COUNT(*) as RentalInvoiceCount,
                SUM(ir.RentalTaxable + ir.RentalNonTax) as TotalRentalRevenue
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
                AND (ir.RentalTaxable > 0 OR ir.RentalNonTax > 0)
            """
            
            rental_check = db.execute_query(rental_check_query, [start_date, end_date])
            
            return jsonify({
                'month': month_param,
                'date_range': {
                    'start': start_date.isoformat(),
                    'end': end_date.isoformat()
                },
                'sale_codes': [dict(row) for row in sale_codes],
                'equipment_samples': [dict(row) for row in equipment_samples],
                'salesmen_summary': [dict(row) for row in salesmen],
                'rental_summary': dict(rental_check[0]) if rental_check else {},
                'diagnostic_info': {
                    'total_sale_codes': len(sale_codes),
                    'total_salesmen': len(salesmen),
                    'has_equipment_sales': any(row['EquipmentRevenue'] > 0 for row in sale_codes) if sale_codes else False,
                    'has_rental_sales': rental_check[0]['TotalRentalRevenue'] > 0 if rental_check and rental_check[0]['TotalRentalRevenue'] else False
                }
            })
            
        except Exception as e:
            logger.error(f"Error in sales commission diagnostic: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/find-missing-invoices', methods=['GET'])
    @jwt_required()
    def find_missing_invoices():
        """Find invoices by invoice number to diagnose missing commission entries"""
        try:
            db = get_db()

            # Get invoice numbers from query parameter (comma-separated)
            invoice_numbers = request.args.get('invoices', '')

            if not invoice_numbers:
                return jsonify({'error': 'Please provide invoice numbers as comma-separated list'}), 400

            # Parse invoice numbers
            invoice_list = [inv.strip() for inv in invoice_numbers.split(',') if inv.strip()]

            if not invoice_list:
                return jsonify({'error': 'No valid invoice numbers provided'}), 400

            # Build query to find these specific invoices
            placeholders = ','.join(['%s'] * len(invoice_list))

            query = f"""
            SELECT
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillTo,
                ir.BillToName as CustomerName,
                ir.SaleCode,
                c.Salesman1,
                ir.GrandTotal,
                ir.EquipmentTaxable,
                ir.EquipmentNonTax,
                ir.EquipmentCost,
                ir.RentalTaxable,
                ir.RentalNonTax,
                ir.RentalCost,
                ir.PartsTaxable,
                ir.PartsNonTax,
                ir.LaborTaxable,
                ir.LaborNonTax,
                ir.Comments
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceNo IN ({placeholders})
            ORDER BY ir.InvoiceNo
            """

            results = db.execute_query(query, invoice_list)

            # Also get all unique sale codes for reference
            sale_codes_query = """
            SELECT DISTINCT SaleCode, COUNT(*) as Count
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= DATEADD(month, -3, GETDATE())
            GROUP BY SaleCode
            ORDER BY COUNT(*) DESC
            """
            all_sale_codes = db.execute_query(sale_codes_query, [])

            # Current filter list for comparison
            current_filter = ['RENTAL', 'USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL',
                            'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM']

            return jsonify({
                'searched_invoices': invoice_list,
                'found_invoices': [dict(row) for row in results],
                'found_count': len(results),
                'missing_count': len(invoice_list) - len(results),
                'all_recent_sale_codes': [dict(row) for row in all_sale_codes],
                'current_commission_filter': current_filter,
                'analysis': {
                    'found_sale_codes': list(set(row['SaleCode'] for row in results if row['SaleCode'])),
                    'codes_not_in_filter': [row['SaleCode'] for row in results if row['SaleCode'] and row['SaleCode'] not in current_filter]
                }
            })

        except Exception as e:
            logger.error(f"Error finding missing invoices: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/invoice-lookup', methods=['GET'])
    @jwt_required()
    def invoice_lookup():
        """Look up a specific invoice to determine its commission status"""
        try:
            db = get_db()

            invoice_no = request.args.get('invoice_no', '').strip()
            if not invoice_no:
                return jsonify({'error': 'Please provide an invoice number'}), 400

            # Commission-eligible sale codes
            commission_sale_codes = ['RENTAL', 'USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL',
                                    'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM']

            # Query to find the invoice with all relevant details
            # Use WO.Salesman field directly - join on WONo = InvoiceNo
            query = """
            SELECT
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillTo,
                ir.BillToName as CustomerName,
                ir.SaleCode,
                wo.Salesman as Salesman1,
                ir.GrandTotal,
                COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0) as EquipmentAmount,
                COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0) as RentalAmount,
                COALESCE(ir.EquipmentCost, 0) as EquipmentCost,
                COALESCE(ir.RentalCost, 0) as RentalCost
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.WO wo ON ir.InvoiceNo = wo.WONo
            WHERE ir.InvoiceNo = %s
            """

            results = db.execute_query(query, [invoice_no])

            if not results:
                return jsonify({
                    'found': False,
                    'invoice_no': invoice_no,
                    'status': 'not_found',
                    'status_message': 'Invoice not found in the database',
                    'status_color': 'red'
                })

            row = results[0]
            invoice_data = {
                'invoice_no': row['InvoiceNo'],
                'invoice_date': row['InvoiceDate'].isoformat() if row['InvoiceDate'] else None,
                'bill_to': row['BillTo'],
                'customer_name': row['CustomerName'],
                'sale_code': row['SaleCode'],
                'salesman': row['Salesman1'],
                'grand_total': float(row['GrandTotal'] or 0),
                'equipment_amount': float(row['EquipmentAmount'] or 0),
                'rental_amount': float(row['RentalAmount'] or 0),
                'equipment_cost': float(row['EquipmentCost'] or 0),
                'rental_cost': float(row['RentalCost'] or 0)
            }

            # Determine the category
            sale_code = row['SaleCode']
            if sale_code == 'RENTAL':
                category = 'Rental'
                amount = invoice_data['rental_amount']
            elif sale_code in ['USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL']:
                category = 'Used Equipment'
                amount = invoice_data['equipment_amount']
            elif sale_code == 'ALLIED':
                category = 'Allied Equipment'
                amount = invoice_data['equipment_amount']
            elif sale_code in ['LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM']:
                category = 'New Equipment'
                amount = invoice_data['equipment_amount']
            else:
                category = 'Other'
                amount = invoice_data['grand_total']

            invoice_data['category'] = category
            invoice_data['category_amount'] = amount

            # Determine status
            salesman = row['Salesman1']

            if sale_code not in commission_sale_codes:
                status = 'not_in_filter'
                status_message = f"Sale code '{sale_code}' is not commission-eligible"
                status_color = 'orange'
            elif salesman is None or salesman == '':
                status = 'unassigned'
                status_message = 'No salesman assigned to this customer'
                status_color = 'yellow'
            elif salesman.upper() == 'HOUSE':
                status = 'house'
                status_message = 'Assigned to House account (excluded from commissions)'
                status_color = 'yellow'
            elif amount <= 0:
                status = 'zero_amount'
                status_message = f'No {category.lower()} amount on this invoice'
                status_color = 'orange'
            else:
                status = 'commission_eligible'
                status_message = f'Assigned to {salesman}'
                status_color = 'green'

            return jsonify({
                'found': True,
                'invoice': invoice_data,
                'status': status,
                'status_message': status_message,
                'status_color': status_color,
                'commission_sale_codes': commission_sale_codes
            })

        except Exception as e:
            logger.error(f"Error in invoice lookup: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/sales-commission-buckets', methods=['GET'])
    @jwt_required()
    def get_sales_commission_buckets():
        """Get detailed bucket diagnostics with sample invoices for each category"""
        try:
            db = get_db()
            
            # Get month parameter
            month_param = request.args.get('month')
            if not month_param:
                today = datetime.today()
                prev_month = today.replace(day=1) - timedelta(days=1)
                month_param = prev_month.strftime('%Y-%m')
            
            year, month = map(int, month_param.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            buckets = {
                'rental': {
                    'name': 'Rental',
                    'sale_codes': ['RENTAL'],
                    'field': 'Rental',
                    'sample_invoices': []
                },
                'used_equipment': {
                    'name': 'Used Equipment', 
                    'sale_codes': ['USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL'],
                    'field': 'Equipment',
                    'sample_invoices': []
                },
                'allied_equipment': {
                    'name': 'Allied Equipment',
                    'sale_codes': ['ALLIED'],
                    'field': 'Equipment',
                    'sample_invoices': []
                },
                'new_equipment': {
                    'name': 'New Equipment',
                    'sale_codes': ['LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM'],
                    'field': 'Equipment',
                    'sample_invoices': []
                }
            }
            
            # Get sample invoices for each bucket
            for bucket_key, bucket_info in buckets.items():
                # Skip buckets with no sale codes
                if not bucket_info['sale_codes']:
                    bucket_info['sample_invoices'] = []
                    continue
                    
                sale_codes_str = "','".join(bucket_info['sale_codes'])
                
                if bucket_info['field'] == 'Rental':
                    amount_condition = "(ir.RentalTaxable > 0 OR ir.RentalNonTax > 0)"
                else:  # Equipment
                    amount_condition = "(ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)"
                
                # Get ALL invoices, not just samples
                # Updated to find salesman from ANY customer record with matching name
                sample_query = f"""
                WITH SalesmanLookup AS (
                    SELECT 
                        InvoiceNo,
                        BillToName,
                        Salesman1
                    FROM (
                        SELECT 
                            InvoiceNo,
                            BillToName,
                            Salesman1,
                            ROW_NUMBER() OVER (PARTITION BY InvoiceNo ORDER BY Priority) as rn
                        FROM (
                            SELECT DISTINCT
                                ir.InvoiceNo,
                                ir.BillToName,
                                CASE 
                                    WHEN c1.Salesman1 IS NOT NULL THEN c1.Salesman1
                                    WHEN c2.Salesman1 IS NOT NULL THEN c2.Salesman1
                                    WHEN c3.Salesman1 IS NOT NULL THEN c3.Salesman1
                                    ELSE NULL
                                END as Salesman1,
                                CASE 
                                    WHEN c1.Salesman1 IS NOT NULL THEN 1
                                    WHEN c2.Salesman1 IS NOT NULL THEN 2
                                    WHEN c3.Salesman1 IS NOT NULL THEN 3
                                    ELSE 4
                                END as Priority
                            FROM ben002.InvoiceReg ir
                            LEFT JOIN ben002.Customer c1 ON ir.BillTo = c1.Number
                            LEFT JOIN ben002.Customer c2 ON ir.BillToName = c2.Name AND c2.Salesman1 IS NOT NULL
                            -- Try matching on first word of company name (e.g., SIMONSON)
                            LEFT JOIN ben002.Customer c3 ON 
                                c3.Salesman1 IS NOT NULL
                                AND LEN(ir.BillToName) >= 4
                                AND LEN(c3.Name) >= 4
                                AND UPPER(
                                    CASE 
                                        WHEN CHARINDEX(' ', ir.BillToName) > 0 
                                        THEN LEFT(ir.BillToName, CHARINDEX(' ', ir.BillToName) - 1)
                                        ELSE ir.BillToName
                                    END
                                ) = UPPER(
                                    CASE 
                                        WHEN CHARINDEX(' ', c3.Name) > 0 
                                        THEN LEFT(c3.Name, CHARINDEX(' ', c3.Name) - 1)
                                        ELSE c3.Name
                                    END
                                )
                            WHERE ir.InvoiceDate >= %s 
                                AND ir.InvoiceDate <= %s
                        ) AS SalesmanMatches
                    ) AS RankedMatches
                    WHERE rn = 1
                )
                SELECT 
                    ir.InvoiceNo,
                    ir.InvoiceDate,
                    ir.SaleCode,
                    ir.BillToName,
                    sl.Salesman1,
                    ir.Comments,
                    ir.RentalTaxable,
                    ir.RentalNonTax,
                    ir.EquipmentTaxable,
                    ir.EquipmentNonTax,
                    ir.GrandTotal,
                    CASE 
                        WHEN '{bucket_info['field']}' = 'Rental'
                        THEN COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)
                        ELSE COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    END as CategoryAmount
                FROM ben002.InvoiceReg ir
                LEFT JOIN SalesmanLookup sl ON ir.InvoiceNo = sl.InvoiceNo
                WHERE ir.InvoiceDate >= %s 
                    AND ir.InvoiceDate <= %s
                    AND ir.SaleCode IN ('{sale_codes_str}')
                    AND {amount_condition}
                ORDER BY ir.InvoiceDate DESC
                """
                
                samples = db.execute_query(sample_query, [start_date, end_date, start_date, end_date])
                # Convert to dict and ensure CategoryAmount is float
                bucket_info['sample_invoices'] = []
                for row in samples:
                    invoice = dict(row)
                    # Ensure CategoryAmount is a float
                    invoice['CategoryAmount'] = float(invoice.get('CategoryAmount', 0) or 0)
                    bucket_info['sample_invoices'].append(invoice)
            
            # Get summary statistics for each bucket
            summary_query = """
            SELECT 
                SUM(CASE 
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)
                    ELSE 0 
                END) as RentalTotal,
                COUNT(CASE WHEN ir.SaleCode = 'RENTAL' THEN 1 ELSE NULL END) as RentalCount,
                
                SUM(CASE 
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as UsedTotal,
                COUNT(CASE WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL') THEN 1 ELSE NULL END) as UsedCount,
                
                SUM(CASE 
                    WHEN ir.SaleCode = 'ALLIED'
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as AlliedTotal,
                COUNT(CASE WHEN ir.SaleCode = 'ALLIED' THEN 1 ELSE NULL END) as AlliedCount,
                
                SUM(CASE 
                    WHEN ir.SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0 
                END) as NewTotal,
                COUNT(CASE WHEN ir.SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM') THEN 1 ELSE NULL END) as NewCount
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s AND ir.InvoiceDate <= %s
            """
            
            summary = db.execute_query(summary_query, [start_date, end_date])
            summary_data = dict(summary[0]) if summary else {}
            
            # Check all SaleCodes that have equipment revenue but aren't mapped
            unmapped_query = """
            SELECT 
                ir.SaleCode,
                COUNT(*) as InvoiceCount,
                SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) as EquipmentRevenue
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s 
                AND ir.InvoiceDate <= %s
                AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
                AND ir.SaleCode NOT IN ('USEDEQ', 'USEDEQP', 'RNTSALE', 'USED K', 'USED L', 'USED SL', 'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
            GROUP BY ir.SaleCode
            ORDER BY SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) DESC
            """
            
            unmapped = db.execute_query(unmapped_query, [start_date, end_date])
            
            # Get ALL OTHER invoices that don't fall into our defined categories
            all_other_query = """
            SELECT 
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillTo,
                ir.BillToName,
                c.Salesman1,
                ir.SaleCode,
                ir.SaleDept,
                ir.Comments,
                COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0) as RentalAmount,
                COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0) as EquipmentAmount,
                COALESCE(ir.PartsTaxable, 0) + COALESCE(ir.PartsNonTax, 0) as PartsAmount,
                COALESCE(ir.LaborTaxable, 0) + COALESCE(ir.LaborNonTax, 0) as LaborAmount,
                COALESCE(ir.MiscTaxable, 0) + COALESCE(ir.MiscNonTax, 0) as MiscAmount,
                ir.GrandTotal
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= %s 
                AND ir.InvoiceDate <= %s
                AND NOT (
                    -- Exclude invoices that fall into our defined categories
                    (ir.SaleCode = 'RENTAL' AND (ir.RentalTaxable > 0 OR ir.RentalNonTax > 0))
                    OR
                    (ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL', 
                                     'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM') 
                     AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0))
                )
                AND ir.GrandTotal > 0  -- Only show invoices with actual amounts
            ORDER BY ir.GrandTotal DESC
            """
            
            all_other_invoices = db.execute_query(all_other_query, [start_date, end_date])
            
            # Format all other invoices for display
            all_other_bucket = {
                'name': 'All Other Invoices',
                'sale_codes': ['Various'],
                'field': 'Mixed',
                'sample_invoices': [{
                    'InvoiceNo': row['InvoiceNo'],
                    'InvoiceDate': row['InvoiceDate'],
                    'BillTo': row['BillTo'],
                    'BillToName': row['BillToName'],
                    'Salesman1': row['Salesman1'],
                    'SaleCode': row['SaleCode'],
                    'SaleDept': row['SaleDept'],
                    'Comments': row['Comments'],
                    'RentalAmount': float(row['RentalAmount'] or 0),
                    'EquipmentAmount': float(row['EquipmentAmount'] or 0),
                    'PartsAmount': float(row['PartsAmount'] or 0),
                    'LaborAmount': float(row['LaborAmount'] or 0),
                    'MiscAmount': float(row['MiscAmount'] or 0),
                    'CategoryAmount': float(row['GrandTotal'] or 0),  # Use GrandTotal for consistency
                    'GrandTotal': float(row['GrandTotal'] or 0)
                } for row in all_other_invoices]
            }
            
            # Add to buckets
            buckets['all_other'] = all_other_bucket
            
            return jsonify({
                'month': month_param,
                'buckets': buckets,
                'summary': {
                    'rental': {
                        'total': float(summary_data.get('RentalTotal', 0)),
                        'count': int(summary_data.get('RentalCount', 0))
                    },
                    'used_equipment': {
                        'total': float(summary_data.get('UsedTotal', 0)),
                        'count': int(summary_data.get('UsedCount', 0))
                    },
                    'allied_equipment': {
                        'total': float(summary_data.get('AlliedTotal', 0)),
                        'count': int(summary_data.get('AlliedCount', 0))
                    },
                    'new_equipment': {
                        'total': float(summary_data.get('NewTotal', 0)),
                        'count': int(summary_data.get('NewCount', 0))
                    }
                },
                'unmapped_equipment_codes': [dict(row) for row in unmapped] if unmapped else []
            })
            
        except Exception as e:
            logger.error(f"Error in sales commission buckets: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/sales-commission-details', methods=['GET'])
    @jwt_required()
    def get_sales_commission_details():
        """Get detailed commission invoices by salesman"""
        try:
            db = get_db()
            
            # Get month parameter
            month_param = request.args.get('month')
            if not month_param:
                today = datetime.today()
                prev_month = today.replace(day=1) - timedelta(days=1)
                month_param = prev_month.strftime('%Y-%m')
            
            year, month = map(int, month_param.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Query to get all commission-eligible invoices with details
            # Use WO.Salesman field directly - join on WONo = InvoiceNo
            details_query = """
            SELECT 
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillTo,
                ir.BillToName as CustomerName,
                COALESCE(wo.Salesman, 'House') as Salesman1,
                ir.SaleCode,
                CASE
                    WHEN ir.SaleCode = 'RENTAL' THEN 'Rental'
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL') THEN 'Used Equipment'
                    WHEN ir.SaleCode = 'ALLIED' THEN 'Allied Equipment'
                    WHEN ir.SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM') THEN 'New Equipment'
                    ELSE 'Other'
                END as Category,
                -- Revenue amounts
                CASE 
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL', 
                                         'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0
                END as CategoryAmount,
                -- Cost amounts for gross profit calculation
                CASE 
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN COALESCE(ir.RentalCost, 0)
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL', 
                                         'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                    THEN COALESCE(ir.EquipmentCost, 0)
                    ELSE 0
                END as CategoryCost,
                -- Commission calculation
                CASE 
                    -- Rental: 8% of revenue (unlimited duration)
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN (COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)) * 0.08
                    
                    -- New Equipment and Allied: 20% of gross profit
                    WHEN ir.SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM', 'ALLIED')
                    THEN CASE 
                        WHEN (COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0) - COALESCE(ir.EquipmentCost, 0)) > 0
                        THEN (COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0) - COALESCE(ir.EquipmentCost, 0)) * 0.20
                        ELSE 0
                    END
                    
                    -- Used Equipment: 5% of sale price
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL')
                    THEN (COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) * 0.05
                    
                    ELSE 0
                END as Commission
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.WO wo ON ir.InvoiceNo = wo.WONo
            WHERE ir.InvoiceDate >= %s
                AND ir.InvoiceDate <= %s
                AND COALESCE(wo.Salesman, 'House') IS NOT NULL
                AND COALESCE(wo.Salesman, 'House') != ''
                AND UPPER(COALESCE(wo.Salesman, 'House')) != 'HOUSE'
                AND ir.SaleCode IN ('RENTAL', 'USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL',
                                    'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                AND (
                    (ir.SaleCode = 'RENTAL' AND (ir.RentalTaxable > 0 OR ir.RentalNonTax > 0))
                    OR
                    (ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL',
                                     'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                     AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0))
                )
            ORDER BY COALESCE(wo.Salesman, 'House'), ir.InvoiceDate, ir.InvoiceNo
            """
            
            results = db.execute_query(details_query, [start_date, end_date, start_date, end_date])
            
            # Fetch commission settings from PostgreSQL
            commission_settings = {}
            try:
                from src.services.postgres_service import PostgreSQLService
                from src.routes.commission_settings import ensure_commission_settings_table
                pg_service = PostgreSQLService()
                with pg_service.get_connection() as conn:
                    cursor = conn.cursor()
                    # Ensure the table and columns exist before querying
                    ensure_commission_settings_table(cursor)
                    conn.commit()
                    cursor.execute("""
                        SELECT invoice_no, sale_code, category, is_commissionable, commission_rate, cost_override, extra_commission
                        FROM commission_settings
                    """)
                    settings_results = cursor.fetchall()
                    for row in settings_results:
                        # Row is a dict due to RealDictCursor
                        key = f"{row['invoice_no']}_{row['sale_code']}_{row['category']}"
                        commission_settings[key] = {
                            'is_commissionable': row['is_commissionable'],
                            'commission_rate': row['commission_rate'],
                            'cost_override': row['cost_override'],
                            'extra_commission': float(row['extra_commission']) if row['extra_commission'] else 0
                        }
            except Exception as e:
                logger.warning(f"Could not fetch commission settings: {str(e)}")
                # If we can't fetch settings, default to all commissionable
                commission_settings = {}
            
            # Group by salesman (normalize names to combine aliases like "Tod Auge" -> "Todd Auge")
            salesmen_details = {}
            for row in results:
                salesman = normalize_salesman_name(row['Salesman1'])
                if salesman not in salesmen_details:
                    salesmen_details[salesman] = {
                        'name': salesman,
                        'invoices': [],
                        'total_sales': 0,
                        'total_commission': 0
                    }
                
                invoice_no = row['InvoiceNo']
                sale_code = row['SaleCode']
                category = row['Category']
                
                # Check if this invoice is commissionable and get custom settings
                settings_key = f"{invoice_no}_{sale_code}_{category}"
                settings = commission_settings.get(settings_key, {})
                is_commissionable = settings.get('is_commissionable', True) if isinstance(settings, dict) else settings
                custom_rate = settings.get('commission_rate') if isinstance(settings, dict) else None
                cost_override = settings.get('cost_override') if isinstance(settings, dict) else None
                extra_commission = settings.get('extra_commission', 0) if isinstance(settings, dict) else 0
                
                # Get original values
                category_amount = float(row['CategoryAmount'] or 0)
                original_cost = float(row.get('CategoryCost', 0) or 0)
                
                # Use cost override if provided, otherwise use original cost
                actual_cost = float(cost_override) if cost_override is not None else original_cost
                
                # Calculate commission based on category
                if not is_commissionable:
                    actual_commission = 0
                elif category == 'Rental' and custom_rate is not None:
                    # Rental: use custom rate
                    actual_commission = category_amount * float(custom_rate)
                elif category in ['New Equipment', 'Allied Equipment']:
                    # New/Allied: 20% of profit (using potentially overridden cost)
                    profit = category_amount - actual_cost
                    actual_commission = profit * 0.20 if profit > 0 else 0
                elif category == 'Used Equipment':
                    # Used: 5% of sale price
                    actual_commission = category_amount * 0.05
                else:
                    # Default to base calculation
                    actual_commission = float(row['Commission'] or 0) if is_commissionable else 0
                
                # Add extra commission to the calculated commission
                total_commission = actual_commission + float(extra_commission)
                
                invoice = {
                    'invoice_no': invoice_no,
                    'invoice_date': row['InvoiceDate'].isoformat() if row['InvoiceDate'] else None,
                    'bill_to': row['BillTo'],
                    'customer_name': row['CustomerName'],
                    'sale_code': sale_code,
                    'category': category,
                    'category_amount': category_amount,
                    'category_cost': original_cost,  # Original cost from database
                    'cost_override': cost_override,  # User's override if any
                    'actual_cost': actual_cost,  # The cost being used for calculation
                    'profit': category_amount - actual_cost if category in ['New Equipment', 'Allied Equipment'] else None,
                    'commission': actual_commission,  # Base calculated commission
                    'extra_commission': extra_commission,  # User-added extra commission
                    'total_commission': total_commission,  # Total including extra
                    'is_commissionable': is_commissionable,
                    'commission_rate': custom_rate
                }
                
                salesmen_details[salesman]['invoices'].append(invoice)
                salesmen_details[salesman]['total_sales'] += invoice['category_amount']
                salesmen_details[salesman]['total_commission'] += total_commission
            
            # Convert to list and sort by total sales
            salesmen_list = list(salesmen_details.values())
            salesmen_list.sort(key=lambda x: x['total_sales'], reverse=True)
            
            # Calculate grand totals
            grand_total_sales = sum(s['total_sales'] for s in salesmen_list)
            grand_total_commission = sum(s['total_commission'] for s in salesmen_list)
            
            # Query for unassigned invoices
            # Use WO.Salesman field directly - join on WONo = InvoiceNo
            unassigned_query = """
            SELECT 
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillTo,
                ir.BillToName as CustomerName,
                COALESCE(wo.Salesman, 'Unassigned') as Salesman,
                ir.SaleCode,
                CASE
                    WHEN ir.SaleCode = 'RENTAL' THEN 'Rental'
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL') THEN 'Used Equipment'
                    WHEN ir.SaleCode = 'ALLIED' THEN 'Allied Equipment'
                    WHEN ir.SaleCode IN ('LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM') THEN 'New Equipment'
                    ELSE 'Other'
                END as Category,
                CASE 
                    WHEN ir.SaleCode = 'RENTAL'
                    THEN COALESCE(ir.RentalTaxable, 0) + COALESCE(ir.RentalNonTax, 0)
                    WHEN ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL', 
                                         'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                    THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
                    ELSE 0
                END as CategoryAmount,
                ir.GrandTotal
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.WO wo ON ir.InvoiceNo = wo.WONo
            WHERE ir.InvoiceDate >= %s
                AND ir.InvoiceDate <= %s
                AND (wo.Salesman IS NULL OR wo.Salesman = '' OR UPPER(wo.Salesman) = 'HOUSE')
                AND ir.SaleCode IN ('RENTAL', 'USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL',
                                    'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM')
                AND (
                    (ir.SaleCode = 'RENTAL' AND (ir.RentalTaxable > 0 OR ir.RentalNonTax > 0))
                    OR
                    (ir.SaleCode IN ('USEDEQ', 'RNTSALE', 'USED K', 'USED L', 'USED SL', 
                                     'ALLIED', 'LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM') 
                     AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0))
                )
            ORDER BY ir.InvoiceDate, ir.InvoiceNo
            """
            
            unassigned_results = db.execute_query(unassigned_query, [start_date, end_date, start_date, end_date])
            
            # Format unassigned invoices
            unassigned_invoices = []
            unassigned_total = 0
            for row in unassigned_results:
                invoice = {
                    'invoice_no': row['InvoiceNo'],
                    'invoice_date': row['InvoiceDate'].isoformat() if row['InvoiceDate'] else None,
                    'bill_to': row['BillTo'],
                    'customer_name': row['CustomerName'],
                    'salesman': row['Salesman'],
                    'sale_code': row['SaleCode'],
                    'category': row['Category'],
                    'category_amount': float(row['CategoryAmount'] or 0),
                    'grand_total': float(row['GrandTotal'] or 0)
                }
                unassigned_invoices.append(invoice)
                unassigned_total += invoice['category_amount']
            
            return jsonify({
                'month': month_param,
                'salesmen': salesmen_list,
                'grand_totals': {
                    'sales': grand_total_sales,
                    'commission': grand_total_commission
                },
                'unassigned': {
                    'invoices': unassigned_invoices,
                    'total': unassigned_total,
                    'count': len(unassigned_invoices)
                },
                'commission_structure': {
                    'rental': '10% of sales',
                    'new_equipment': '20% of gross profit (est. 20% margin)',
                    'allied_equipment': '20% of gross profit (est. 20% margin)',
                    'used_equipment': '5% of selling price',
                    'rental_sale': '5% of gross profit (est. 25% margin)'
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching commission details: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/invoice-sales-diagnostic', methods=['GET'])
    @jwt_required()
    def get_invoice_sales_diagnostic():
        """Diagnostic endpoint to explore InvoiceSales table for cost data"""
        try:
            db = get_db()
            
            # First, get column info
            columns_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002' 
                AND TABLE_NAME = 'InvoiceSales'
            ORDER BY ORDINAL_POSITION
            """
            
            columns = db.execute_query(columns_query)
            
            # Get sample data
            sample_query = """
            SELECT TOP 10 *
            FROM ben002.InvoiceSales
            WHERE InvoiceNo IN (
                SELECT TOP 10 InvoiceNo 
                FROM ben002.InvoiceReg
                WHERE SaleCode IN ('LINDEN', 'NEWEQ', 'USEDEQ', 'RNTSALE')
                AND InvoiceDate >= '2025-01-01'
                ORDER BY InvoiceDate DESC
            )
            """
            
            samples = db.execute_query(sample_query)
            
            # Check if we have cost-related columns
            cost_columns = [col for col in columns if 'cost' in col['COLUMN_NAME'].lower() or 'cos' in col['COLUMN_NAME'].lower()]
            
            return jsonify({
                'columns': [dict(col) for col in columns],
                'cost_columns': [dict(col) for col in cost_columns],
                'sample_data': [dict(row) for row in samples] if samples else [],
                'table_exists': len(columns) > 0
            })
            
        except Exception as e:
            logger.error(f"Error in invoice sales diagnostic: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/accounting/equipment-sales-diagnostic', methods=['GET'])
    @jwt_required()
    def get_equipment_sales_diagnostic():
        """Diagnostic to find all equipment sale codes for a specific month"""
        try:
            db = get_db()
            
            month_param = request.args.get('month', '2025-03')
            year, month = map(int, month_param.split('-'))
            start_date = datetime(year, month, 1)
            if month == 12:
                end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                end_date = datetime(year, month + 1, 1) - timedelta(days=1)
            
            # Find all sale codes with equipment revenue
            equipment_codes_query = """
            SELECT 
                ir.SaleCode,
                COUNT(*) as InvoiceCount,
                SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) as EquipmentRevenue,
                SUM(ir.GrandTotal) as TotalRevenue,
                MIN(ir.InvoiceDate) as FirstInvoice,
                MAX(ir.InvoiceDate) as LastInvoice
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s 
                AND ir.InvoiceDate <= %s
                AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
            GROUP BY ir.SaleCode
            ORDER BY SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) DESC
            """
            
            equipment_codes = db.execute_query(equipment_codes_query, [start_date, end_date])
            
            # Check specific codes that might be new equipment
            new_equipment_check_query = """
            SELECT 
                ir.SaleCode,
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillToName,
                ir.Comments,
                COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0) as EquipmentAmount,
                ir.GrandTotal
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s 
                AND ir.InvoiceDate <= %s
                AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
                AND ir.SaleCode IN ('NEW', 'NEWEQ', 'NEWEQP', 'LINDE', 'LINDEN', 'KOM', 'KOMATSU', 'ALLIED')
            ORDER BY ir.InvoiceDate DESC
            """
            
            new_equipment_invoices = db.execute_query(new_equipment_check_query, [start_date, end_date])
            
            # Look for codes containing 'NEW' or 'LINDE'
            pattern_check_query = """
            SELECT DISTINCT 
                ir.SaleCode,
                COUNT(*) as InvoiceCount,
                SUM(COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)) as EquipmentRevenue
            FROM ben002.InvoiceReg ir
            WHERE ir.InvoiceDate >= %s 
                AND ir.InvoiceDate <= %s
                AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
                AND (ir.SaleCode LIKE '%NEW%' OR ir.SaleCode LIKE '%LIND%' OR ir.SaleCode LIKE '%KOM%')
            GROUP BY ir.SaleCode
            ORDER BY ir.SaleCode
            """
            
            pattern_matches = db.execute_query(pattern_check_query, [start_date, end_date])
            
            # Summary of configured vs actual
            configured_new = ['LINDE', 'LINDEN', 'NEWEQ', 'NEWEQP-R', 'KOM']
            
            return jsonify({
                'month': month_param,
                'all_equipment_codes': [dict(row) for row in equipment_codes],
                'new_equipment_invoices': [dict(row) for row in new_equipment_invoices],
                'pattern_matches': [dict(row) for row in pattern_matches],
                'configured_new_codes': configured_new,
                'summary': {
                    'total_equipment_codes': len(equipment_codes),
                    'codes_with_new_pattern': len(pattern_matches)
                }
            })
            
        except Exception as e:
            logger.error(f"Error in equipment sales diagnostic: {str(e)}")
            return jsonify({'error': str(e)}), 500


    @reports_bp.route('/departments/accounting/find-linde-invoice', methods=['GET'])
    @jwt_required()
    def find_linde_invoice():
        """Find specific LINDE invoice around $113K"""
        try:
            db = get_db()
            
            # Search for LINDE invoices in March 2025 around $113K
            query = """
            SELECT 
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillTo,
                ir.BillToName,
                c.Salesman1,
                c.Salesman2,
                c.Salesman3,
                ir.SaleCode,
                ir.SaleDept,
                COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0) as EquipmentAmount,
                ir.GrandTotal,
                ir.Comments
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= '2025-03-01' 
                AND ir.InvoiceDate < '2025-04-01'
                AND ir.SaleCode = 'LINDE'
                AND ir.GrandTotal > 100000  -- Looking for invoices over $100K
            ORDER BY ir.GrandTotal DESC
            """
            
            results = db.execute_query(query)
            
            # Also search for any equipment invoice around $113K in March
            broad_query = """
            SELECT 
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillTo,
                ir.BillToName,
                c.Salesman1,
                c.Salesman2,
                c.Salesman3,
                ir.SaleCode,
                ir.SaleDept,
                COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0) as EquipmentAmount,
                ir.GrandTotal,
                ir.Comments
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= '2025-03-01' 
                AND ir.InvoiceDate < '2025-04-01'
                AND (ir.EquipmentTaxable > 0 OR ir.EquipmentNonTax > 0)
                AND ir.GrandTotal BETWEEN 110000 AND 115000  -- Looking around $113K
            ORDER BY ir.GrandTotal DESC
            """
            
            broad_results = db.execute_query(broad_query)
            
            # Get ALL LINDE invoices for March to see what we have
            all_linde_query = """
            SELECT 
                ir.InvoiceNo,
                ir.InvoiceDate,
                ir.BillTo,
                ir.BillToName,
                c.Salesman1,
                ir.SaleCode,
                COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0) as EquipmentAmount,
                ir.GrandTotal
            FROM ben002.InvoiceReg ir
            LEFT JOIN ben002.Customer c ON ir.BillTo = c.Number
            WHERE ir.InvoiceDate >= '2025-03-01' 
                AND ir.InvoiceDate < '2025-04-01'
                AND ir.SaleCode = 'LINDE'
            ORDER BY ir.GrandTotal DESC
            """
            
            all_linde = db.execute_query(all_linde_query)
            
            return jsonify({
                'linde_over_100k': [dict(row) for row in results],
                'equipment_around_113k': [dict(row) for row in broad_results],
                'all_linde_march': [dict(row) for row in all_linde],
                'total_linde_march': sum(row['EquipmentAmount'] for row in all_linde)
            })
            
        except Exception as e:
            logger.error(f"Error finding LINDE invoice: {str(e)}")
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/service/invoice-billing', methods=['GET'])
    @jwt_required()
    def get_service_invoice_billing():
        """Get invoice billing report for Service department"""
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            customer_no = request.args.get('customer_no', '')
            
            if not start_date or not end_date:
                return jsonify({'error': 'Start date and end date are required'}), 400
                
            # Query - removed unreliable work order matching since there's no direct link
            query = """
            SELECT 
                -- Customer info
                i.BillTo,
                i.BillToName,
                c.Salesman1 as Salesman,
                
                -- Invoice info
                i.InvoiceNo,
                i.InvoiceDate,
                
                -- Equipment info from Equipment table via SerialNo
                COALESCE(e.UnitNo, '') as UnitNo,
                CAST(i.InvoiceNo AS VARCHAR(20)) as AssociatedWONo,  -- Use InvoiceNo as WO#
                COALESCE(e.Make, '') as Make,
                COALESCE(e.Model, '') as Model,
                COALESCE(i.SerialNo, e.SerialNo, '') as SerialNo,
                COALESCE(i.HourMeter, 0) as HourMeter,
                
                -- PO and other fields
                COALESCE(i.PONo, '') as PONo,
                i.PartsTaxable,
                i.LaborTaxable,
                i.LaborNonTax,
                i.MiscTaxable,
                COALESCE(i.MiscNonTax, 0) as Freight,  -- Using MiscNonTax as Freight proxy
                i.TotalTax,
                i.GrandTotal,
                
                -- Comments
                i.Comments
                
            FROM ben002.InvoiceReg i
            LEFT JOIN ben002.Customer c ON i.BillTo = c.Number
            LEFT JOIN ben002.Equipment e ON i.SerialNo = e.SerialNo
            WHERE i.InvoiceDate >= %s
              AND i.InvoiceDate <= %s
              AND i.DeletionTime IS NULL
              -- Exclude parts invoices (those starting with 130)
              AND CAST(i.InvoiceNo AS VARCHAR(20)) NOT LIKE '130%'
              -- Include all invoices with service-related revenue
              AND (i.LaborTaxable > 0 OR i.LaborNonTax > 0 
                   OR i.MiscTaxable > 0 OR i.MiscNonTax > 0
                   OR i.PartsTaxable > 0 OR i.PartsNonTax > 0)
              AND i.GrandTotal > 0
            """
            
            # Add customer filter if specified
            params = [start_date, end_date]
            if customer_no and customer_no != 'ALL':
                # Check both BillTo and BillToName fields for the customer
                query += " AND (i.BillTo = %s OR i.BillToName = %s)"
                params.append(customer_no)
                params.append(customer_no)
                
            query += " ORDER BY i.InvoiceDate, i.InvoiceNo"
            
            db = get_db()
            invoices = db.execute_query(query, params)
                
            # Calculate totals
            totals = {
                'parts_taxable': sum(inv['PartsTaxable'] or 0 for inv in invoices),
                'labor_taxable': sum(inv['LaborTaxable'] or 0 for inv in invoices),
                'labor_non_tax': sum(inv['LaborNonTax'] or 0 for inv in invoices),
                'misc_taxable': sum(inv['MiscTaxable'] or 0 for inv in invoices),
                'freight': sum(inv['Freight'] or 0 for inv in invoices),
                'total_tax': sum(inv['TotalTax'] or 0 for inv in invoices),
                'grand_total': sum(inv['GrandTotal'] or 0 for inv in invoices),
                'invoice_count': len(invoices)
            }
            
            result = {
                'invoices': invoices,
                'totals': totals,
                'start_date': start_date,
                'end_date': end_date
            }
                
            return jsonify(result)
        except Exception as e:
            logger.error(f"Error in service invoice billing: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/service/customers', methods=['GET'])
    @jwt_required()
    def get_service_customers():
        """Get list of customers with service invoices in date range"""
        try:
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            if not start_date or not end_date:
                return jsonify({'error': 'Start date and end date are required'}), 400
            
            # Get customers with service invoices in the specified date range
            query = """
            SELECT 
                c.Number as CustomerNo,
                c.Name as CustomerName,
                COUNT(DISTINCT i.InvoiceNo) as InvoiceCount,
                SUM(i.GrandTotal) as TotalRevenue
            FROM ben002.Customer c
            INNER JOIN ben002.InvoiceReg i ON c.Number = i.BillTo
            WHERE i.DeletionTime IS NULL
              AND i.InvoiceDate >= %s
              AND i.InvoiceDate <= %s
              -- Include all invoices with service-related revenue
              AND (i.LaborTaxable > 0 OR i.LaborNonTax > 0 
                   OR i.MiscTaxable > 0 OR i.MiscNonTax > 0
                   OR i.PartsTaxable > 0 OR i.PartsNonTax > 0)
              AND i.GrandTotal > 0
            GROUP BY c.Number, c.Name
            HAVING COUNT(DISTINCT i.InvoiceNo) > 0
            ORDER BY c.Name
            """
            
            db = get_db()
            customers = db.execute_query(query, [start_date, end_date])
            
            # Format the response
            customer_list = [
                {
                    'value': 'ALL',
                    'label': 'All Customers',
                    'invoiceCount': sum(c['InvoiceCount'] for c in customers),
                    'totalRevenue': sum(c['TotalRevenue'] for c in customers)
                }
            ]
            
            for customer in customers:
                customer_list.append({
                    'value': customer['CustomerNo'],
                    'label': customer['CustomerName'] or f"Customer {customer['CustomerNo']}",
                    'invoiceCount': customer['InvoiceCount'],
                    'totalRevenue': float(customer['TotalRevenue'])
                })
            
            return jsonify(customer_list)
        except Exception as e:
            logger.error(f"Error fetching service customers: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/service/invoice-diagnostic', methods=['GET'])
    @jwt_required()
    def get_invoice_diagnostic():
        """Diagnostic endpoint to check invoice counts by department"""
        try:
            start_date = request.args.get('start_date', '2025-07-29')
            end_date = request.args.get('end_date', '2025-08-01')
            
            db = get_db()
            
            # Check total invoices in date range
            total_query = """
            SELECT 
                COUNT(*) as total_invoices,
                COUNT(DISTINCT BillTo) as unique_customers,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= %s
              AND InvoiceDate <= %s
              AND DeletionTime IS NULL
              AND GrandTotal > 0
            """
            
            total_results = db.execute_query(total_query, [start_date, end_date])
            
            # Check service department invoices (using broader criteria)
            # The third-party appears to include all service-related work regardless of SaleCode
            service_query = """
            SELECT 
                COUNT(*) as service_invoices,
                COUNT(DISTINCT BillTo) as service_customers,
                SUM(GrandTotal) as service_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= %s
              AND InvoiceDate <= %s
              AND DeletionTime IS NULL
              AND GrandTotal > 0
              -- Include all invoices that have service components
              AND (LaborTaxable > 0 OR LaborNonTax > 0 
                   OR MiscTaxable > 0 OR MiscNonTax > 0
                   OR PartsTaxable > 0 OR PartsNonTax > 0)
            """
            
            service_results = db.execute_query(service_query, [start_date, end_date])
            
            # Get breakdown by SaleCode
            breakdown_query = """
            SELECT 
                SaleCode,
                SaleDept,
                COUNT(*) as invoice_count,
                COUNT(DISTINCT BillTo) as customer_count,
                SUM(GrandTotal) as total_revenue
            FROM ben002.InvoiceReg
            WHERE InvoiceDate >= %s
              AND InvoiceDate <= %s
              AND DeletionTime IS NULL
              AND GrandTotal > 0
            GROUP BY SaleCode, SaleDept
            ORDER BY invoice_count DESC
            """
            
            breakdown_results = db.execute_query(breakdown_query, [start_date, end_date])
            
            # Get list of Service customers with their invoices
            service_customers_query = """
            SELECT 
                i.BillTo,
                i.BillToName,
                COUNT(*) as invoice_count,
                MIN(i.InvoiceNo) as first_invoice,
                MAX(i.InvoiceNo) as last_invoice,
                SUM(i.GrandTotal) as total_revenue
            FROM ben002.InvoiceReg i
            WHERE i.InvoiceDate >= %s
              AND i.InvoiceDate <= %s
              AND i.DeletionTime IS NULL
              -- Exclude parts invoices (those starting with 130)
              AND CAST(i.InvoiceNo AS VARCHAR(20)) NOT LIKE '130%'
              -- Include all invoices with service-related revenue
              AND (i.LaborTaxable > 0 OR i.LaborNonTax > 0 
                   OR i.MiscTaxable > 0 OR i.MiscNonTax > 0
                   OR i.PartsTaxable > 0 OR i.PartsNonTax > 0)
              AND i.GrandTotal > 0
            GROUP BY i.BillTo, i.BillToName
            ORDER BY total_revenue DESC
            """
            
            service_customers = db.execute_query(service_customers_query, [start_date, end_date])
            
            return jsonify({
                'date_range': {'start': start_date, 'end': end_date},
                'total_all_departments': total_results[0] if total_results else None,
                'total_service_only': service_results[0] if service_results else None,
                'breakdown_by_sale_code': breakdown_results,
                'service_customers_list': service_customers,
                'service_customer_count': len(service_customers)
            })
            
        except Exception as e:
            logger.error(f"Error in invoice diagnostic: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/service/invoice-schema', methods=['GET'])
    @jwt_required()
    def get_invoice_schema():
        """Diagnostic endpoint to explore InvoiceReg table structure"""
        try:
            db = get_db()
            
            # Get column information
            schema_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE,
                CHARACTER_MAXIMUM_LENGTH,
                IS_NULLABLE,
                COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = 'InvoiceReg'
            ORDER BY ORDINAL_POSITION
            """
            
            columns = db.execute_query(schema_query)
            
            # Get a sample invoice with all fields
            sample_query = """
            SELECT TOP 1 * 
            FROM ben002.InvoiceReg 
            WHERE InvoiceDate >= '2025-07-01'
                AND GrandTotal > 1000
                AND (SaleCode IN ('SVE', 'SVES', 'SVEW', 'SVER', 'SVE-STL', 'FREIG') 
                     OR SaleDept IN (20, 25, 29))
            ORDER BY InvoiceDate DESC
            """
            
            sample = db.execute_query(sample_query)
            
            # Look for any freight-related or PO-related fields
            search_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = 'InvoiceReg'
                AND (COLUMN_NAME LIKE '%freight%' 
                     OR COLUMN_NAME LIKE '%ship%'
                     OR COLUMN_NAME LIKE '%PO%'
                     OR COLUMN_NAME LIKE '%purchase%'
                     OR COLUMN_NAME LIKE '%order%'
                     OR COLUMN_NAME LIKE '%comment%'
                     OR COLUMN_NAME LIKE '%note%'
                     OR COLUMN_NAME LIKE '%salesman%'
                     OR COLUMN_NAME LIKE '%sales%')
            """
            
            related_fields = db.execute_query(search_query)
            
            # Check for invoice-related tables that might have work order links
            related_tables_query = """
            SELECT DISTINCT 
                t.TABLE_NAME,
                c.COLUMN_NAME
            FROM INFORMATION_SCHEMA.TABLES t
            JOIN INFORMATION_SCHEMA.COLUMNS c 
                ON t.TABLE_SCHEMA = c.TABLE_SCHEMA 
                AND t.TABLE_NAME = c.TABLE_NAME
            WHERE t.TABLE_SCHEMA = 'ben002'
                AND (t.TABLE_NAME LIKE '%Invoice%' OR c.COLUMN_NAME LIKE '%Invoice%')
                AND c.COLUMN_NAME IN ('InvoiceNo', 'WONo', 'WorkOrderNo', 'Freight', 'ShipCharge')
            ORDER BY t.TABLE_NAME, c.COLUMN_NAME
            """
            
            related_tables = db.execute_query(related_tables_query)
            
            # Look for InvoiceSales or InvoiceDetail table
            invoice_detail_query = """
            SELECT 
                TABLE_NAME
            FROM INFORMATION_SCHEMA.TABLES
            WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME IN ('InvoiceSales', 'InvoiceDetail', 'InvoiceLines', 'InvoiceArchive')
            """
            
            detail_tables = db.execute_query(invoice_detail_query)
            
            return jsonify({
                'all_columns': columns,
                'sample_invoice': sample[0] if sample else None,
                'freight_po_related_fields': related_fields,
                'total_columns': len(columns),
                'related_tables': related_tables,
                'detail_tables': detail_tables
            })
            
        except Exception as e:
            logger.error(f"Error exploring invoice schema: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/service/wo-invoice-link', methods=['GET'])
    @jwt_required()
    def find_wo_invoice_link():
        """Find how work orders are linked to invoices"""
        try:
            db = get_db()
            
            # Check WO table for invoice fields
            wo_invoice_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = 'WO'
                AND COLUMN_NAME LIKE '%Invoice%'
            """
            
            wo_invoice_fields = db.execute_query(wo_invoice_query)
            
            # Get a sample of closed work orders with their invoice info
            sample_query = """
            SELECT TOP 10
                w.WONo,
                w.Type,
                w.ClosedDate,
                w.BillTo,
                w.UnitNo,
                w.WorkPerformed,
                w.*
            FROM ben002.WO w
            WHERE w.ClosedDate IS NOT NULL
                AND w.ClosedDate >= '2025-07-01'
                AND w.Type = 'S'
            ORDER BY w.ClosedDate DESC
            """
            
            closed_wos = db.execute_query(sample_query)
            
            # Check if there's a freight field in WOMisc
            misc_query = """
            SELECT TOP 10
                m.*,
                w.WONo,
                w.ClosedDate
            FROM ben002.WOMisc m
            JOIN ben002.WO w ON m.WONo = w.WONo
            WHERE w.ClosedDate >= '2025-07-01'
                AND (UPPER(m.Description) LIKE '%FREIGHT%' 
                     OR UPPER(m.Description) LIKE '%SHIP%'
                     OR UPPER(m.Description) LIKE '%DELIVERY%')
            ORDER BY w.ClosedDate DESC
            """
            
            freight_charges = db.execute_query(misc_query)
            
            # Check all WO columns
            wo_columns_query = """
            SELECT 
                COLUMN_NAME,
                DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_SCHEMA = 'ben002'
                AND TABLE_NAME = 'WO'
            ORDER BY ORDINAL_POSITION
            """
            
            wo_columns = db.execute_query(wo_columns_query)
            
            return jsonify({
                'wo_invoice_fields': wo_invoice_fields,
                'closed_work_orders_sample': closed_wos,
                'freight_misc_charges': freight_charges,
                'all_wo_columns': wo_columns
            })
            
        except Exception as e:
            logger.error(f"Error finding WO-Invoice link: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500

    @reports_bp.route('/departments/rental/availability', methods=['GET'])
    @jwt_required()
    def get_rental_availability():
        """Get rental availability report showing all equipment status and customer info"""
        try:
            logger.info("Starting rental availability report")
            db = get_db()
            
            # UPDATED LOGIC: Check for OPEN rental work orders (Type='R' and ClosedDate IS NULL)
            # This matches what the Rental Manager sees in Softbase under "Open Rental Orders"
            combined_query = """
            SELECT DISTINCT
                e.UnitNo, 
                e.SerialNo, 
                e.Make, 
                e.Model, 
                e.Location,
                e.CustomerNo,
                -- Show rental customer when on rent, otherwise show equipment owner
                CASE 
                    WHEN open_rental.WONo IS NOT NULL THEN open_rental.CustomerName
                    ELSE c.Name
                END as CustomerName,
                CASE 
                    WHEN open_rental.WONo IS NOT NULL THEN open_rental.CustomerAddress
                    ELSE c.Address
                END as CustomerAddress,
                CASE 
                    WHEN open_rental.WONo IS NOT NULL THEN open_rental.CustomerCity
                    ELSE c.City
                END as CustomerCity,
                CASE 
                    WHEN open_rental.WONo IS NOT NULL THEN open_rental.CustomerState
                    ELSE c.State
                END as CustomerState,
                CASE 
                    WHEN open_rental.WONo IS NOT NULL THEN open_rental.CustomerZip
                    ELSE c.ZipCode
                END as CustomerZip,
                CASE 
                    WHEN open_rental.WONo IS NOT NULL THEN 'On Rent'
                    ELSE 'Available'  -- Includes NULL, 'Ready To Rent', and 'Hold'
                END as Status,
                e.RentalStatus as OriginalStatus,
                e.WebRentalFlag,
                e.RentalYTD,
                e.RentalITD,
                open_rental.WONo as OpenRentalWO,
                open_rental.OpenDate as RentalStartDate,
                open_rental.RentalContractNo,
                e.DayRent,
                e.WeekRent,
                e.MonthRent
            FROM ben002.Equipment e
            LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
            -- Check for OPEN rental work orders (matching Softbase "Open Rental Orders")
            LEFT JOIN (
                SELECT DISTINCT
                    wr.SerialNo,
                    wr.UnitNo,
                    wo.WONo,
                    wo.OpenDate,
                    wo.RentalContractNo,
                    wo.BillTo,
                    wo.ShipTo,
                    -- Use Ship To customer info when available, fall back to Bill To
                    COALESCE(ship_cust.Name, bill_cust.Name) as CustomerName,
                    COALESCE(ship_cust.Address, bill_cust.Address) as CustomerAddress,
                    COALESCE(ship_cust.City, bill_cust.City) as CustomerCity,
                    COALESCE(ship_cust.State, bill_cust.State) as CustomerState,
                    COALESCE(ship_cust.ZipCode, bill_cust.ZipCode) as CustomerZip
                FROM ben002.WORental wr
                INNER JOIN ben002.WO wo ON wr.WONo = wo.WONo
                LEFT JOIN ben002.Customer bill_cust ON wo.BillTo = bill_cust.Number
                LEFT JOIN ben002.Customer ship_cust ON wo.ShipTo = ship_cust.Number
                WHERE wo.Type = 'R'
                AND wo.ClosedDate IS NULL  -- This is the key: OPEN rental orders only
                AND wo.DeletionTime IS NULL
                -- Exclude quotes (WO numbers starting with 9)
                AND wo.WONo NOT LIKE '9%'
                -- Ensure we have valid unit/serial matches
                AND (wr.UnitNo IS NOT NULL AND wr.UnitNo != '' 
                     OR wr.SerialNo IS NOT NULL AND wr.SerialNo != '')
            ) open_rental ON (
                (e.UnitNo IS NOT NULL AND e.UnitNo != '' AND e.UnitNo = open_rental.UnitNo)
                OR (e.SerialNo IS NOT NULL AND e.SerialNo != '' AND e.SerialNo = open_rental.SerialNo)
            )
            WHERE 
            -- PRIMARY FILTER: Units owned by Rental Department
            e.InventoryDept = 60
            -- Exclude customer-owned equipment
            AND (e.Customer = 0 OR e.Customer IS NULL)
            """
            
            # Try the enhanced query, but fall back to simple query if it fails
            try:
                logger.info("Executing combined query for InventoryDept = 60")
                simple_result = db.execute_query(combined_query)
                logger.info(f"Combined query found {len(simple_result) if simple_result else 0} records from Dept 60")
            except Exception as query_error:
                logger.warning(f"Enhanced rental query failed: {str(query_error)}. Falling back to simple query.")
                # Fallback to simpler query without full customer info
                fallback_query = """
                SELECT DISTINCT
                    e.UnitNo, 
                    e.SerialNo, 
                    e.Make, 
                    e.Model, 
                    e.Location,
                    e.CustomerNo,
                    -- Show rental customer when on rent, otherwise show equipment owner
                    CASE 
                        WHEN open_rental.WONo IS NOT NULL THEN COALESCE(ship_cust.Name, bill_cust.Name)
                        ELSE c.Name
                    END as CustomerName,
                    CASE 
                        WHEN open_rental.WONo IS NOT NULL THEN COALESCE(ship_cust.Address, bill_cust.Address)
                        ELSE c.Address
                    END as CustomerAddress,
                    CASE 
                        WHEN open_rental.WONo IS NOT NULL THEN COALESCE(ship_cust.City, bill_cust.City)
                        ELSE c.City
                    END as CustomerCity,
                    CASE 
                        WHEN open_rental.WONo IS NOT NULL THEN COALESCE(ship_cust.State, bill_cust.State)
                        ELSE c.State
                    END as CustomerState,
                    CASE 
                        WHEN open_rental.WONo IS NOT NULL THEN COALESCE(ship_cust.ZipCode, bill_cust.ZipCode)
                        ELSE c.ZipCode
                    END as CustomerZip,
                    CASE 
                        WHEN open_rental.WONo IS NOT NULL THEN 'On Rent'
                        ELSE 'Available'  -- Includes NULL, 'Ready To Rent', and 'Hold'
                    END as Status,
                    e.RentalStatus as OriginalStatus,
                    e.WebRentalFlag,
                    e.RentalYTD,
                    e.RentalITD,
                    open_rental.WONo as OpenRentalWO,
                    open_rental.OpenDate as RentalStartDate,
                    open_rental.RentalContractNo,
                    e.DayRent,
                    e.WeekRent,
                    e.MonthRent
                FROM ben002.Equipment e
                LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
                -- Check for OPEN rental work orders
                LEFT JOIN (
                    SELECT DISTINCT
                        wr.SerialNo,
                        wr.UnitNo,
                        wo.WONo,
                        wo.OpenDate,
                        wo.RentalContractNo,
                        wo.BillTo,
                        wo.ShipTo
                    FROM ben002.WORental wr
                    INNER JOIN ben002.WO wo ON wr.WONo = wo.WONo
                    WHERE wo.Type = 'R'
                    AND wo.ClosedDate IS NULL  -- OPEN rental orders only
                    AND wo.DeletionTime IS NULL
                    -- Exclude quotes (WO numbers starting with 9)
                    AND wo.WONo NOT LIKE '9%'
                    -- Ensure we have valid unit/serial matches
                    AND (wr.UnitNo IS NOT NULL AND wr.UnitNo != '' 
                         OR wr.SerialNo IS NOT NULL AND wr.SerialNo != '')
                ) open_rental ON (
                    (e.UnitNo IS NOT NULL AND e.UnitNo != '' AND e.UnitNo = open_rental.UnitNo)
                    OR (e.SerialNo IS NOT NULL AND e.SerialNo != '' AND e.SerialNo = open_rental.SerialNo)
                )
                -- Join to get Ship To customer info first, fall back to Bill To
                LEFT JOIN ben002.Customer ship_cust ON open_rental.ShipTo = ship_cust.Number
                LEFT JOIN ben002.Customer bill_cust ON open_rental.BillTo = bill_cust.Number
                WHERE 
                -- PRIMARY FILTER: Units owned by Rental Department
                e.InventoryDept = 60
                -- Exclude customer-owned equipment
                AND (e.Customer = 0 OR e.Customer IS NULL)
                """
                simple_result = db.execute_query(fallback_query)
                logger.info(f"Fallback query found {len(simple_result) if simple_result else 0} records")
            
            # Log what we got
            logger.info(f"Query returned {len(simple_result) if simple_result else 0} records")
            
            # If we found equipment, return it directly for now
            if simple_result and len(simple_result) > 0:
                equipment = []
                for row in simple_result:
                    status = row.get('Status', '')
                    # Show just customer name for on rent equipment (no address to avoid cutoff)
                    ship_info = ''
                    if status == 'On Rent':
                        # Just show customer name
                        if row.get('CustomerName'):
                            ship_info = row.get('CustomerName')
                    
                    equipment.append({
                        'make': row.get('Make', ''),
                        'model': row.get('Model', ''),
                        'unitNo': row.get('UnitNo', ''),
                        'serialNo': row.get('SerialNo', ''),
                        'status': status,
                        'rentalStatus': row.get('OriginalStatus', ''),
                        'billTo': row.get('CustomerName', '') if status == 'On Rent' else '',
                        'shipTo': '',  # Deprecated - using shipAddress instead
                        'shipAddress': ship_info,
                        'shipState': row.get('CustomerState', '') if status == 'On Rent' else '',
                        'shipContact': '',
                        'location': row.get('Location', ''),
                        'dayRate': float(row.get('DayRent', 0) or 0),
                        'weekRate': float(row.get('WeekRent', 0) or 0),
                        'monthRate': float(row.get('MonthRent', 0) or 0),
                        'modelYear': '',
                        'cost': 0
                    })
                
                total_units = len(equipment)
                on_rent = sum(1 for e in equipment if e['status'] == 'On Rent')
                available = sum(1 for e in equipment if e['status'].lower() == 'available')
                on_hold = sum(1 for e in equipment if e['status'].lower() == 'hold')
                
                return jsonify({
                    'equipment': equipment,
                    'summary': {
                        'totalUnits': total_units,
                        'availableUnits': available,
                        'onRentUnits': on_rent,
                        'onHoldUnits': on_hold,
                        'utilizationRate': round((on_rent / total_units * 100), 1) if total_units > 0 else 0
                    }
                })
            
            logger.info("No equipment found with simple query, trying complex query...")
            
            # Use the SAME working query from equipment-report
            query = """
            WITH RentalEquipment AS (
                SELECT 
                    e.UnitNo,
                    e.SerialNo,
                    e.Make,
                    e.Model,
                    e.ModelYear,
                    e.RentalStatus,
                    e.Location,
                    e.Cost,
                    e.DayRent,
                    e.WeekRent,
                    e.MonthRent,
                    e.CustomerNo,
                    c.Name as CurrentCustomer,
                    COALESCE(c.Contact, c.Phone1, '') as CustomerContact,
                    -- Check if currently on rent
                    CASE 
                        WHEN rh.SerialNo IS NOT NULL THEN 'On Rent'
                        WHEN e.RentalStatus = 'On Hold' THEN 'On Hold'
                        WHEN e.RentalStatus = 'Ready To Rent' THEN 'Available'
                        ELSE COALESCE(e.RentalStatus, 'Unknown')
                    END as CurrentStatus,
                    rh.DaysRented as CurrentMonthDays
                FROM ben002.Equipment e
                LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
                LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                    AND rh.Year = YEAR(GETDATE()) 
                    AND rh.Month = MONTH(GETDATE())
                    AND rh.DaysRented > 0
                    AND rh.DeletionTime IS NULL
                WHERE EXISTS (
                    SELECT 1 FROM ben002.RentalHistory rh 
                    WHERE rh.SerialNo = e.SerialNo 
                    AND rh.DaysRented > 0
                )
            )
            SELECT 
                Make,
                Model,
                UnitNo,
                SerialNo,
                CurrentStatus as Status,
                RentalStatus,
                Location,
                Cost,
                DayRent,
                WeekRent,
                MonthRent,
                ModelYear,
                -- Only show customer info if on rent
                CASE 
                    WHEN CurrentStatus = 'On Rent' THEN CurrentCustomer
                    ELSE NULL 
                END as ShipTo,
                CASE 
                    WHEN CurrentStatus = 'On Rent' THEN CustomerContact
                    ELSE NULL 
                END as ShipContact
            FROM RentalEquipment
            ORDER BY 
                CASE CurrentStatus
                    WHEN 'On Rent' THEN 1
                    WHEN 'Available' THEN 2
                    WHEN 'On Hold' THEN 3
                    ELSE 4
                END,
                Make,
                Model,
                UnitNo
            """
            
            logger.info("Executing main equipment query")
            results = db.execute_query(query)
            logger.info(f"Found {len(results) if results else 0} equipment records")
            
            # Get summary counts - EXACT same as equipment-report
            summary_query = """
            SELECT 
                COUNT(*) as total_units,
                COUNT(CASE WHEN e.RentalStatus = 'Ready To Rent' THEN 1 END) as available_units,
                COUNT(CASE WHEN rh.SerialNo IS NOT NULL AND rh.DaysRented > 0 THEN 1 END) as on_rent_units,
                COUNT(CASE WHEN e.RentalStatus = 'On Hold' THEN 1 END) as on_hold_units
            FROM ben002.Equipment e
            LEFT JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo 
                AND rh.Year = YEAR(GETDATE()) 
                AND rh.Month = MONTH(GETDATE())
                AND rh.DaysRented > 0
                AND rh.DeletionTime IS NULL
            WHERE (e.CustomerNo = '900006'
                OR e.InventoryDept = 40
                OR e.RentalStatus IS NOT NULL)
                AND UPPER(e.Make) IN ('LINDE', 'KOMATSU', 'BENDI', 'CLARK', 'CROWN', 'UNICARRIERS')
            """
            
            logger.info("Executing summary query")
            summary_result = db.execute_query(summary_query)
            
            # Parse results
            equipment = []
            if results:
                for row in results:
                    equipment.append({
                        'make': row.get('Make', ''),
                        'model': row.get('Model', ''),
                        'unitNo': row.get('UnitNo', ''),
                        'serialNo': row.get('SerialNo', ''),
                        'rentalStatus': row.get('RentalStatus', ''),
                        'status': row.get('Status', ''),
                        'shipTo': row.get('ShipTo', ''),
                        'shipContact': row.get('ShipContact', ''),
                        'location': row.get('Location', ''),
                        'dayRate': float(row.get('DayRent', 0)) if row.get('DayRent') else 0,
                        'weekRate': float(row.get('WeekRent', 0)) if row.get('WeekRent') else 0,
                        'monthRate': float(row.get('MonthRent', 0)) if row.get('MonthRent') else 0,
                        'modelYear': row.get('ModelYear', ''),
                        'cost': float(row.get('Cost', 0)) if row.get('Cost') else 0
                    })
            
            # Parse summary
            summary = {
                'totalUnits': 0,
                'availableUnits': 0,
                'onRentUnits': 0,
                'onHoldUnits': 0,
                'otherStatusUnits': 0,
                'utilizationRate': 0
            }
            
            if summary_result and len(summary_result) > 0:
                row = summary_result[0]
                summary['totalUnits'] = row.get('total_units', 0)
                summary['availableUnits'] = row.get('available_units', 0)
                summary['onRentUnits'] = row.get('on_rent_units', 0)
                summary['onHoldUnits'] = row.get('on_hold_units', 0)
                summary['otherStatusUnits'] = row.get('other_status_units', 0)
                
                if summary['totalUnits'] > 0:
                    summary['utilizationRate'] = round((summary['onRentUnits'] / summary['totalUnits']) * 100, 1)
            
            logger.info(f"Returning {len(equipment)} equipment records with summary: {summary}")
            
            return jsonify({
                'equipment': equipment,
                'summary': summary
            })
            
        except Exception as e:
            logger.error(f"Error in rental availability report: {str(e)}", exc_info=True)
            return jsonify({'error': str(e)}), 500
    
    @reports_bp.route('/departments/rental/availability-debug', methods=['GET'])
    @jwt_required()
    def debug_rental_availability():
        """Debug endpoint to troubleshoot rental availability data"""
        try:
            db = get_db()
            debug_info = {}
            
            # Test 0: Direct query of what availability endpoint would return
            try:
                test0 = """
                SELECT TOP 100 
                    e.UnitNo,
                    e.SerialNo,
                    e.Make,
                    e.Model,
                    e.RentalStatus,
                    e.DayRent,
                    e.WeekRent,
                    e.MonthRent
                FROM ben002.Equipment e
                WHERE EXISTS (
                    SELECT 1 FROM ben002.RentalHistory rh 
                    WHERE rh.SerialNo = e.SerialNo 
                    AND rh.DaysRented > 0
                )
                """
                result0 = db.execute_query(test0)
                debug_info['availability_query_results'] = len(result0) if result0 else 0
                debug_info['availability_query_sample'] = result0[:3] if result0 else []
            except Exception as e:
                debug_info['availability_query_error'] = str(e)
            
            # Test 1: Check if Equipment table is accessible
            try:
                test1 = "SELECT COUNT(*) as total FROM ben002.Equipment"
                result1 = db.execute_query(test1)
                debug_info['equipment_table_count'] = result1[0]['total'] if result1 else 0
            except Exception as e:
                debug_info['equipment_table_error'] = str(e)
            
            # Test 2: Check Equipment table columns
            try:
                test2 = """
                SELECT TOP 1 * FROM ben002.Equipment
                """
                result2 = db.execute_query(test2)
                if result2:
                    debug_info['equipment_columns'] = list(result2[0].keys())
                    debug_info['sample_equipment'] = result2[0]
            except Exception as e:
                debug_info['equipment_columns_error'] = str(e)
            
            # Test 3: Check RentalStatus values
            try:
                test3 = """
                SELECT RentalStatus, COUNT(*) as count
                FROM ben002.Equipment
                GROUP BY RentalStatus
                ORDER BY count DESC
                """
                result3 = db.execute_query(test3)
                debug_info['rental_status_values'] = result3 if result3 else []
            except Exception as e:
                debug_info['rental_status_error'] = str(e)
            
            # Test 4: Check equipment with rental rates
            try:
                test4 = """
                SELECT COUNT(*) as count
                FROM ben002.Equipment
                WHERE DayRent > 0 OR WeekRent > 0 OR MonthRent > 0
                """
                result4 = db.execute_query(test4)
                debug_info['equipment_with_rates'] = result4[0]['count'] if result4 else 0
            except Exception as e:
                debug_info['rental_rates_error'] = str(e)
            
            # Test 5: Check equipment with Make/Model
            try:
                test5 = """
                SELECT COUNT(*) as count
                FROM ben002.Equipment
                WHERE Make IS NOT NULL AND Make != ''
                """
                result5 = db.execute_query(test5)
                debug_info['equipment_with_make'] = result5[0]['count'] if result5 else 0
            except Exception as e:
                debug_info['make_model_error'] = str(e)
            
            # Test 6: Sample of rental equipment
            try:
                test6 = """
                SELECT TOP 10 
                    Make, Model, UnitNo, SerialNo, RentalStatus,
                    CustomerNo, DayRent, WeekRent, MonthRent
                FROM ben002.Equipment
                WHERE (DayRent > 0 OR WeekRent > 0 OR MonthRent > 0)
                    AND Make IS NOT NULL AND Make != ''
                """
                result6 = db.execute_query(test6)
                debug_info['sample_rental_equipment'] = result6 if result6 else []
            except Exception as e:
                debug_info['sample_rental_error'] = str(e)
            
            # Test 7: Check Customer table join
            try:
                test7 = """
                SELECT TOP 5
                    e.UnitNo, e.CustomerNo, c.Name as CustomerName
                FROM ben002.Equipment e
                LEFT JOIN ben002.Customer c ON e.CustomerNo = c.Number
                WHERE e.CustomerNo IS NOT NULL AND e.CustomerNo != ''
                """
                result7 = db.execute_query(test7)
                debug_info['customer_join_test'] = result7 if result7 else []
            except Exception as e:
                debug_info['customer_join_error'] = str(e)
            
            # Test 8: Main query test (simplified)
            try:
                test8 = """
                SELECT TOP 20
                    e.Make,
                    e.Model,
                    e.UnitNo,
                    e.SerialNo,
                    e.RentalStatus,
                    e.CustomerNo,
                    e.DayRent,
                    e.WeekRent,
                    e.MonthRent
                FROM ben002.Equipment e
                WHERE e.Make IS NOT NULL 
                    AND e.Make != ''
                ORDER BY e.UnitNo
                """
                result8 = db.execute_query(test8)
                debug_info['simplified_query_results'] = len(result8) if result8 else 0
                debug_info['simplified_query_sample'] = result8[:5] if result8 else []
            except Exception as e:
                debug_info['simplified_query_error'] = str(e)
            
            # Test 9: Find actual rental equipment - CHECK ALL RENTAL HISTORY
            try:
                test9 = """
                SELECT TOP 10
                    e.UnitNo,
                    e.Make,
                    e.Model,
                    e.CustomerNo,
                    e.InventoryDept,
                    e.RentalStatus,
                    e.RentalYTD,
                    e.RentalITD,
                    rh.Year,
                    rh.Month,
                    rh.DaysRented,
                    rh.RentAmount
                FROM ben002.Equipment e
                INNER JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo
                WHERE rh.DaysRented > 0
                ORDER BY rh.Year DESC, rh.Month DESC
                """
                result9 = db.execute_query(test9)
                debug_info['equipment_with_rental_history'] = result9 if result9 else []
                
                # Count total equipment with ANY rental history
                count_query = """
                SELECT COUNT(DISTINCT e.SerialNo) as count
                FROM ben002.Equipment e
                INNER JOIN ben002.RentalHistory rh ON e.SerialNo = rh.SerialNo
                WHERE rh.DaysRented > 0
                """
                count_result = db.execute_query(count_query)
                debug_info['total_equipment_with_rental_history'] = count_result[0]['count'] if count_result else 0
            except Exception as e:
                debug_info['rental_history_error'] = str(e)
            
            # Test 10: Check what InventoryDept values exist
            try:
                test10 = """
                SELECT InventoryDept, COUNT(*) as count
                FROM ben002.Equipment
                WHERE InventoryDept IS NOT NULL
                GROUP BY InventoryDept
                ORDER BY count DESC
                """
                result10 = db.execute_query(test10)
                debug_info['inventory_dept_values'] = result10 if result10 else []
            except Exception as e:
                debug_info['inventory_dept_error'] = str(e)
            
            # Test 11: Find equipment by specific makes that Equipment Report uses
            try:
                test11 = """
                SELECT COUNT(*) as count,
                    COUNT(CASE WHEN CustomerNo = '900006' THEN 1 END) as with_900006,
                    COUNT(CASE WHEN InventoryDept = 40 THEN 1 END) as with_dept_40,
                    COUNT(CASE WHEN RentalStatus IS NOT NULL THEN 1 END) as with_rental_status
                FROM ben002.Equipment
                WHERE UPPER(Make) IN ('LINDE', 'KOMATSU', 'BENDI', 'CLARK', 'CROWN', 'UNICARRIERS')
                """
                result11 = db.execute_query(test11)
                debug_info['equipment_by_makes'] = result11[0] if result11 else {}
            except Exception as e:
                debug_info['makes_error'] = str(e)
            
            return jsonify(debug_info)

        except Exception as e:
            return jsonify({'error': str(e), 'type': 'main_exception'}), 500


    @reports_bp.route('/departments/rental/depreciation-rolloff', methods=['GET'])
    @jwt_required()
    def get_depreciation_rolloff():
        """
        Get depreciation roll-off schedule for rental trucks.
        Shows when each truck's depreciation ends and monthly cost roll-off.
        """
        try:
            db = get_db()

            # Get all active depreciation records with remaining months
            # Join with Equipment to get unit info
            query = """
            SELECT
                d.SerialNo,
                e.UnitNo,
                e.Make,
                e.Model,
                e.ModelYear,
                d.StartingValue,
                d.NetBookValue,
                d.LastUpdatedAmount as MonthlyDepreciation,
                d.TotalMonths,
                d.RemainingMonths,
                d.ResidualValue,
                d.LastUpdated,
                d.DepreciationGroup,
                d.Method,
                -- Calculate depreciation end date (LastUpdated + RemainingMonths)
                DATEADD(month, COALESCE(d.RemainingMonths, 0), d.LastUpdated) as DepreciationEndDate
            FROM ben002.Depreciation d
            LEFT JOIN ben002.Equipment e ON d.SerialNo = e.SerialNo
            WHERE d.Inactive = 0  -- Only active depreciation
                AND d.RemainingMonths > 0  -- Only items still depreciating
                AND d.LastUpdatedAmount > 0  -- Only items with depreciation amount
            ORDER BY DATEADD(month, COALESCE(d.RemainingMonths, 0), d.LastUpdated) ASC
            """

            result = db.execute_query(query)

            if not result:
                return jsonify({
                    'success': True,
                    'equipment': [],
                    'monthlyRolloff': [],
                    'summary': {
                        'totalActiveItems': 0,
                        'totalMonthlyDepreciation': 0,
                        'totalRemainingBookValue': 0
                    }
                })

            # Process equipment list
            equipment = []
            total_monthly_depreciation = 0
            total_remaining_book_value = 0

            for row in result:
                monthly_dep = float(row['MonthlyDepreciation'] or 0)
                net_book = float(row['NetBookValue'] or 0)
                total_monthly_depreciation += monthly_dep
                total_remaining_book_value += net_book

                equipment.append({
                    'serialNo': row['SerialNo'],
                    'unitNo': row['UnitNo'],
                    'make': row['Make'],
                    'model': row['Model'],
                    'modelYear': row['ModelYear'],
                    'startingValue': float(row['StartingValue'] or 0),
                    'netBookValue': net_book,
                    'monthlyDepreciation': monthly_dep,
                    'totalMonths': row['TotalMonths'],
                    'remainingMonths': row['RemainingMonths'],
                    'residualValue': float(row['ResidualValue'] or 0),
                    'lastUpdated': row['LastUpdated'].isoformat() if row['LastUpdated'] else None,
                    'depreciationEndDate': row['DepreciationEndDate'].isoformat() if row['DepreciationEndDate'] else None,
                    'depreciationGroup': row['DepreciationGroup'],
                    'method': row['Method']
                })

            # Calculate monthly roll-off (aggregate by month)
            rolloff_by_month = {}
            for item in equipment:
                if item['depreciationEndDate']:
                    # Extract year-month from end date
                    end_date = datetime.fromisoformat(item['depreciationEndDate'])
                    month_key = end_date.strftime('%Y-%m')

                    if month_key not in rolloff_by_month:
                        rolloff_by_month[month_key] = {
                            'month': month_key,
                            'monthLabel': end_date.strftime('%b %Y'),
                            'rolloffAmount': 0,
                            'itemCount': 0,
                            'items': []
                        }

                    rolloff_by_month[month_key]['rolloffAmount'] += item['monthlyDepreciation']
                    rolloff_by_month[month_key]['itemCount'] += 1
                    rolloff_by_month[month_key]['items'].append({
                        'unitNo': item['unitNo'],
                        'serialNo': item['serialNo'],
                        'monthlyDepreciation': item['monthlyDepreciation']
                    })

            # Sort by month and convert to list
            monthly_rolloff = sorted(rolloff_by_month.values(), key=lambda x: x['month'])

            # Calculate cumulative roll-off (running total of cost reduction)
            cumulative = 0
            for month in monthly_rolloff:
                cumulative += month['rolloffAmount']
                month['cumulativeRolloff'] = round(cumulative, 2)
                month['rolloffAmount'] = round(month['rolloffAmount'], 2)

            return jsonify({
                'success': True,
                'equipment': equipment,
                'monthlyRolloff': monthly_rolloff,
                'summary': {
                    'totalActiveItems': len(equipment),
                    'totalMonthlyDepreciation': round(total_monthly_depreciation, 2),
                    'totalRemainingBookValue': round(total_remaining_book_value, 2)
                }
            })

        except Exception as e:
            logger.error(f"Error getting depreciation rolloff: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @reports_bp.route('/departments/guaranteed-maintenance/profitability', methods=['GET'])
    @jwt_required()
    def get_maintenance_contract_profitability():
        """
        Get Maintenance Contract (FMBILL) profitability analysis.
        Compares contract revenue (from FMBILL invoices) to actual service costs
        from Work Orders (WOLabor + WOParts + WOMisc).

        True profitability = Contract Revenue - Actual Service Costs
        """
        try:
            db = get_db()

            # Get FMBILL revenue by year/month (contract billing)
            revenue_query = """
            SELECT
                YEAR(InvoiceDate) as year,
                MONTH(InvoiceDate) as month,
                COUNT(*) as invoice_count,
                SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0)) as labor_revenue,
                SUM(COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0)) as parts_revenue,
                SUM(COALESCE(MiscTaxable, 0) + COALESCE(MiscNonTax, 0)) as misc_revenue,
                SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0) +
                    COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0) +
                    COALESCE(MiscTaxable, 0) + COALESCE(MiscNonTax, 0)) as total_revenue
            FROM [ben002].InvoiceReg
            WHERE SaleCode = 'FMBILL'
                AND BillTo NOT IN ('78960', '89410')  -- Exclude Wells Fargo and US Bank
            GROUP BY YEAR(InvoiceDate), MONTH(InvoiceDate)
            ORDER BY YEAR(InvoiceDate) DESC, MONTH(InvoiceDate) DESC
            """

            revenue_results = db.execute_query(revenue_query)

            # Get list of ShipTo locations that have work orders for FMBILL customers
            # This finds actual service locations, not billing entities like leasing companies
            fmbill_customers_query = """
            SELECT DISTINCT w.ShipTo as customer_number
            FROM [ben002].WO w
            WHERE w.BillTo IN (
                SELECT DISTINCT BillTo
                FROM [ben002].InvoiceReg
                WHERE SaleCode = 'FMBILL'
            )
            AND w.Type IN ('S', 'SH', 'PM')
            AND w.ShipTo IS NOT NULL
            AND w.ShipTo != ''
            AND w.ShipTo NOT IN ('78960', '89410')  -- Exclude Wells Fargo and US Bank
            """
            fmbill_customers = db.execute_query(fmbill_customers_query)
            customer_numbers = [row['customer_number'] for row in fmbill_customers]

            # Get actual service costs from Work Orders for FMBILL customers
            # This includes all service WOs (Type S, SH, PM) for these customers
            if customer_numbers:
                # Build quoted list of customer numbers for IN clause
                # pymssql doesn't support ? placeholders well with IN clauses
                quoted_customers = ','.join([f"'{c}'" for c in customer_numbers])

                # Service costs by year/month
                service_costs_query = f"""
                WITH ServiceWOs AS (
                    SELECT
                        w.WONo,
                        w.ShipTo,
                        YEAR(COALESCE(w.ClosedDate, w.CompletedDate, w.OpenDate)) as year,
                        MONTH(COALESCE(w.ClosedDate, w.CompletedDate, w.OpenDate)) as month
                    FROM [ben002].WO w
                    WHERE w.ShipTo IN ({quoted_customers})
                    AND w.Type IN ('S', 'SH', 'PM')  -- Service, Shop, PM work orders
                ),
                LaborCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as labor_cost
                    FROM [ben002].WOLabor
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                ),
                PartsCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as parts_cost
                    FROM [ben002].WOParts
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                ),
                MiscCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as misc_cost
                    FROM [ben002].WOMisc
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                )
                SELECT
                    sw.year,
                    sw.month,
                    COUNT(DISTINCT sw.WONo) as wo_count,
                    SUM(COALESCE(l.labor_cost, 0)) as labor_cost,
                    SUM(COALESCE(p.parts_cost, 0)) as parts_cost,
                    SUM(COALESCE(m.misc_cost, 0)) as misc_cost,
                    SUM(COALESCE(l.labor_cost, 0) + COALESCE(p.parts_cost, 0) + COALESCE(m.misc_cost, 0)) as total_cost
                FROM ServiceWOs sw
                LEFT JOIN LaborCosts l ON sw.WONo = l.WONo
                LEFT JOIN PartsCosts p ON sw.WONo = p.WONo
                LEFT JOIN MiscCosts m ON sw.WONo = m.WONo
                GROUP BY sw.year, sw.month
                ORDER BY sw.year DESC, sw.month DESC
                """

                service_costs_results = db.execute_query(service_costs_query)

                # Service costs by customer
                service_costs_by_customer_query = f"""
                WITH ServiceWOs AS (
                    SELECT
                        w.WONo,
                        w.ShipTo
                    FROM [ben002].WO w
                    WHERE w.ShipTo IN ({quoted_customers})
                    AND w.Type IN ('S', 'SH', 'PM')
                ),
                LaborCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as labor_cost
                    FROM [ben002].WOLabor
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                ),
                PartsCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as parts_cost
                    FROM [ben002].WOParts
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                ),
                MiscCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as misc_cost
                    FROM [ben002].WOMisc
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                )
                SELECT
                    sw.ShipTo as customer_number,
                    c.Name as customer_name,
                    COUNT(DISTINCT sw.WONo) as wo_count,
                    SUM(COALESCE(l.labor_cost, 0)) as labor_cost,
                    SUM(COALESCE(p.parts_cost, 0)) as parts_cost,
                    SUM(COALESCE(m.misc_cost, 0)) as misc_cost,
                    SUM(COALESCE(l.labor_cost, 0) + COALESCE(p.parts_cost, 0) + COALESCE(m.misc_cost, 0)) as total_cost
                FROM ServiceWOs sw
                LEFT JOIN [ben002].Customer c ON sw.ShipTo = c.Number
                LEFT JOIN LaborCosts l ON sw.WONo = l.WONo
                LEFT JOIN PartsCosts p ON sw.WONo = p.WONo
                LEFT JOIN MiscCosts m ON sw.WONo = m.WONo
                GROUP BY sw.ShipTo, c.Name
                ORDER BY total_cost DESC
                """

                service_costs_by_customer = db.execute_query(service_costs_by_customer_query)

                # Total service costs summary
                total_service_costs_query = f"""
                WITH ServiceWOs AS (
                    SELECT w.WONo, w.ShipTo
                    FROM [ben002].WO w
                    WHERE w.ShipTo IN ({quoted_customers})
                    AND w.Type IN ('S', 'SH', 'PM')
                ),
                LaborCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as labor_cost
                    FROM [ben002].WOLabor
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                ),
                PartsCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as parts_cost
                    FROM [ben002].WOParts
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                ),
                MiscCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as misc_cost
                    FROM [ben002].WOMisc
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                )
                SELECT
                    COUNT(DISTINCT sw.WONo) as total_work_orders,
                    SUM(COALESCE(l.labor_cost, 0)) as total_labor_cost,
                    SUM(COALESCE(p.parts_cost, 0)) as total_parts_cost,
                    SUM(COALESCE(m.misc_cost, 0)) as total_misc_cost,
                    SUM(COALESCE(l.labor_cost, 0) + COALESCE(p.parts_cost, 0) + COALESCE(m.misc_cost, 0)) as total_service_cost
                FROM ServiceWOs sw
                LEFT JOIN LaborCosts l ON sw.WONo = l.WONo
                LEFT JOIN PartsCosts p ON sw.WONo = p.WONo
                LEFT JOIN MiscCosts m ON sw.WONo = m.WONo
                """

                total_service_costs = db.execute_query(total_service_costs_query)

                # Service costs by equipment/serial for each customer
                equipment_costs_query = f"""
                WITH ServiceWOs AS (
                    SELECT
                        w.WONo,
                        w.ShipTo,
                        w.SerialNo,
                        w.UnitNo,
                        w.Make,
                        w.Model,
                        w.Type as wo_type
                    FROM [ben002].WO w
                    WHERE w.ShipTo IN ({quoted_customers})
                    AND w.Type IN ('S', 'SH', 'PM')
                    AND w.SerialNo IS NOT NULL
                    AND w.SerialNo != ''
                ),
                LaborCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as labor_cost
                    FROM [ben002].WOLabor
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                ),
                PartsCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as parts_cost
                    FROM [ben002].WOParts
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                ),
                MiscCosts AS (
                    SELECT WONo, SUM(COALESCE(Cost, 0)) as misc_cost
                    FROM [ben002].WOMisc
                    WHERE WONo IN (SELECT WONo FROM ServiceWOs)
                    GROUP BY WONo
                )
                SELECT
                    sw.ShipTo as customer_number,
                    c.Name as customer_name,
                    sw.SerialNo as serial_no,
                    MAX(sw.UnitNo) as unit_no,
                    MAX(sw.Make) as make,
                    MAX(sw.Model) as model,
                    COUNT(DISTINCT sw.WONo) as wo_count,
                    SUM(CASE WHEN sw.wo_type = 'PM' THEN 1 ELSE 0 END) as pm_count,
                    SUM(CASE WHEN sw.wo_type IN ('S', 'SH') THEN 1 ELSE 0 END) as service_count,
                    SUM(COALESCE(l.labor_cost, 0)) as labor_cost,
                    SUM(COALESCE(p.parts_cost, 0)) as parts_cost,
                    SUM(COALESCE(m.misc_cost, 0)) as misc_cost,
                    SUM(COALESCE(l.labor_cost, 0) + COALESCE(p.parts_cost, 0) + COALESCE(m.misc_cost, 0)) as total_cost
                FROM ServiceWOs sw
                LEFT JOIN [ben002].Customer c ON sw.ShipTo = c.Number
                LEFT JOIN LaborCosts l ON sw.WONo = l.WONo
                LEFT JOIN PartsCosts p ON sw.WONo = p.WONo
                LEFT JOIN MiscCosts m ON sw.WONo = m.WONo
                GROUP BY sw.ShipTo, c.Name, sw.SerialNo
                ORDER BY total_cost DESC
                """

                equipment_costs_results = db.execute_query(equipment_costs_query)
            else:
                service_costs_results = []
                service_costs_by_customer = []
                total_service_costs = []
                equipment_costs_results = []

            # Get FMBILL revenue by customer
            customer_query = """
            SELECT
                i.BillTo as customer_number,
                c.Name as customer_name,
                COUNT(*) as invoice_count,
                SUM(COALESCE(i.LaborTaxable, 0) + COALESCE(i.LaborNonTax, 0) +
                    COALESCE(i.PartsTaxable, 0) + COALESCE(i.PartsNonTax, 0) +
                    COALESCE(i.MiscTaxable, 0) + COALESCE(i.MiscNonTax, 0)) as total_revenue,
                MIN(i.InvoiceDate) as first_invoice,
                MAX(i.InvoiceDate) as last_invoice
            FROM [ben002].InvoiceReg i
            LEFT JOIN [ben002].Customer c ON i.BillTo = c.Number
            WHERE i.SaleCode = 'FMBILL'
                AND i.BillTo NOT IN ('78960', '89410')  -- Exclude Wells Fargo and US Bank
            GROUP BY i.BillTo, c.Name
            ORDER BY total_revenue DESC
            """

            customer_results = db.execute_query(customer_query)

            # Get overall summary
            summary_query = """
            SELECT
                COUNT(*) as total_invoices,
                COUNT(DISTINCT BillTo) as unique_customers,
                SUM(COALESCE(LaborTaxable, 0) + COALESCE(LaborNonTax, 0) +
                    COALESCE(PartsTaxable, 0) + COALESCE(PartsNonTax, 0) +
                    COALESCE(MiscTaxable, 0) + COALESCE(MiscNonTax, 0)) as total_revenue,
                MIN(InvoiceDate) as earliest_invoice,
                MAX(InvoiceDate) as latest_invoice
            FROM [ben002].InvoiceReg
            WHERE SaleCode = 'FMBILL'
                AND BillTo NOT IN ('78960', '89410')  -- Exclude Wells Fargo and US Bank
            """

            summary_results = db.execute_query(summary_query)

            # Build service costs lookup by month
            service_costs_by_month = {}
            for row in service_costs_results:
                key = (int(row['year']), int(row['month']))
                service_costs_by_month[key] = {
                    'wo_count': int(row['wo_count'] or 0),
                    'labor_cost': float(row['labor_cost'] or 0),
                    'parts_cost': float(row['parts_cost'] or 0),
                    'misc_cost': float(row['misc_cost'] or 0),
                    'total_cost': float(row['total_cost'] or 0)
                }

            # Build service costs lookup by customer
            service_costs_by_cust = {}
            for row in service_costs_by_customer:
                service_costs_by_cust[row['customer_number']] = {
                    'wo_count': int(row['wo_count'] or 0),
                    'labor_cost': float(row['labor_cost'] or 0),
                    'parts_cost': float(row['parts_cost'] or 0),
                    'misc_cost': float(row['misc_cost'] or 0),
                    'total_cost': float(row['total_cost'] or 0)
                }

            # Format monthly data with TRUE profitability (revenue - service costs)
            monthly_data = []
            for row in revenue_results:
                year = int(row['year'])
                month = int(row['month'])
                revenue = float(row['total_revenue'] or 0)

                # Get actual service costs for this month
                service_data = service_costs_by_month.get((year, month), {})
                service_cost = service_data.get('total_cost', 0)
                wo_count = service_data.get('wo_count', 0)

                # True profitability
                true_profit = revenue - service_cost
                margin = (true_profit / revenue * 100) if revenue > 0 else 0

                monthly_data.append({
                    'year': year,
                    'month': month,
                    'month_name': datetime(year, month, 1).strftime('%b %Y'),
                    'invoice_count': int(row['invoice_count']),
                    'contract_revenue': revenue,
                    'labor_revenue': float(row['labor_revenue'] or 0),
                    'parts_revenue': float(row['parts_revenue'] or 0),
                    'misc_revenue': float(row['misc_revenue'] or 0),
                    'service_wo_count': wo_count,
                    'service_labor_cost': service_data.get('labor_cost', 0),
                    'service_parts_cost': service_data.get('parts_cost', 0),
                    'service_misc_cost': service_data.get('misc_cost', 0),
                    'service_total_cost': service_cost,
                    'true_profit': true_profit,
                    'margin_percent': round(margin, 1)
                })

            # Format customer data with TRUE profitability
            customer_data = []
            for row in customer_results:
                cust_num = row['customer_number']
                revenue = float(row['total_revenue'] or 0)

                # Get actual service costs for this customer
                service_data = service_costs_by_cust.get(cust_num, {})
                service_cost = service_data.get('total_cost', 0)
                wo_count = service_data.get('wo_count', 0)

                # True profitability
                true_profit = revenue - service_cost
                margin = (true_profit / revenue * 100) if revenue > 0 else 0

                customer_data.append({
                    'customer_number': cust_num,
                    'customer_name': row['customer_name'] or 'Unknown',
                    'invoice_count': int(row['invoice_count']),
                    'contract_revenue': revenue,
                    'service_wo_count': wo_count,
                    'service_labor_cost': service_data.get('labor_cost', 0),
                    'service_parts_cost': service_data.get('parts_cost', 0),
                    'service_misc_cost': service_data.get('misc_cost', 0),
                    'service_total_cost': service_cost,
                    'true_profit': true_profit,
                    'margin_percent': round(margin, 1),
                    'profitable': true_profit > 0,
                    'first_invoice': row['first_invoice'].strftime('%Y-%m-%d') if row['first_invoice'] else None,
                    'last_invoice': row['last_invoice'].strftime('%Y-%m-%d') if row['last_invoice'] else None
                })

            # Format summary with TRUE profitability
            summary = {}
            if summary_results and len(summary_results) > 0:
                row = summary_results[0]
                revenue = float(row['total_revenue'] or 0)

                # Get total service costs
                total_service_cost = 0
                total_work_orders = 0
                total_labor_cost = 0
                total_parts_cost = 0
                total_misc_cost = 0

                if total_service_costs and len(total_service_costs) > 0:
                    sc = total_service_costs[0]
                    total_service_cost = float(sc['total_service_cost'] or 0)
                    total_work_orders = int(sc['total_work_orders'] or 0)
                    total_labor_cost = float(sc['total_labor_cost'] or 0)
                    total_parts_cost = float(sc['total_parts_cost'] or 0)
                    total_misc_cost = float(sc['total_misc_cost'] or 0)

                true_profit = revenue - total_service_cost
                margin = (true_profit / revenue * 100) if revenue > 0 else 0

                # Count profitable vs unprofitable customers
                profitable_count = sum(1 for c in customer_data if c['profitable'])
                unprofitable_count = len(customer_data) - profitable_count

                summary = {
                    'total_invoices': int(row['total_invoices'] or 0),
                    'unique_customers': int(row['unique_customers'] or 0),
                    'total_contract_revenue': revenue,
                    'total_work_orders': total_work_orders,
                    'total_labor_cost': total_labor_cost,
                    'total_parts_cost': total_parts_cost,
                    'total_misc_cost': total_misc_cost,
                    'total_service_cost': total_service_cost,
                    'true_profit': true_profit,
                    'margin_percent': round(margin, 1),
                    'profitable_customers': profitable_count,
                    'unprofitable_customers': unprofitable_count,
                    'overall_profitable': true_profit > 0,
                    'earliest_invoice': row['earliest_invoice'].strftime('%Y-%m-%d') if row['earliest_invoice'] else None,
                    'latest_invoice': row['latest_invoice'].strftime('%Y-%m-%d') if row['latest_invoice'] else None
                }

            # Format equipment data
            equipment_data = []
            for row in equipment_costs_results:
                equipment_data.append({
                    'customer_number': row['customer_number'],
                    'customer_name': row['customer_name'] or 'Unknown',
                    'serial_no': row['serial_no'],
                    'unit_no': row['unit_no'] or '',
                    'make': row['make'] or '',
                    'model': row['model'] or '',
                    'wo_count': int(row['wo_count'] or 0),
                    'pm_count': int(row['pm_count'] or 0),
                    'service_count': int(row['service_count'] or 0),
                    'labor_cost': float(row['labor_cost'] or 0),
                    'parts_cost': float(row['parts_cost'] or 0),
                    'misc_cost': float(row['misc_cost'] or 0),
                    'total_cost': float(row['total_cost'] or 0)
                })

            return jsonify({
                'success': True,
                'monthly': monthly_data,
                'by_customer': customer_data,
                'by_equipment': equipment_data,
                'summary': summary,
                'notes': {
                    'contract_revenue': 'Monthly billing from FMBILL invoices',
                    'service_costs': 'Actual costs from Work Orders (Labor + Parts + Misc) for contract customers',
                    'true_profit': 'Contract Revenue - Actual Service Costs',
                    'wo_types_included': 'S (Service), SH (Shop), PM (Preventive Maintenance)'
                }
            })

        except Exception as e:
            logger.error(f"Error getting maintenance contract profitability: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

