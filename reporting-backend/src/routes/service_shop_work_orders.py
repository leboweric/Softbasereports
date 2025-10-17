from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

service_shop_bp = Blueprint('service_shop', __name__)

@service_shop_bp.route('/api/reports/departments/service/shop-work-orders', methods=['GET'])
@jwt_required()
def get_shop_work_orders():
    """
    Get open shop work orders with cost overrun alerts.
    Compares actual labor hours vs quoted hours to prevent budget overruns.
    """
    try:
        db = AzureSQLService()
        
        query = """
        SELECT 
            w.WONo,
            w.BillTo as CustomerNo,
            c.Name as CustomerName,
            w.UnitNo,
            w.SerialNo,
            w.OpenDate,
            w.Status,
            
            -- Quoted labor
            COALESCE(quoted.QuotedAmount, 0) as QuotedAmount,
            CASE 
                WHEN quoted.QuotedAmount > 0 THEN quoted.QuotedAmount / 189.0
                ELSE 0
            END as QuotedHours,
            
            -- Actual labor hours
            COALESCE(SUM(l.Hours), 0) as ActualHours,
            
            -- Percentage used
            CASE 
                WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN 0
                ELSE (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100
            END as PercentUsed,
            
            -- Alert level
            CASE 
                WHEN quoted.QuotedAmount IS NULL OR quoted.QuotedAmount = 0 THEN 'NO_QUOTE'
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 100 THEN 'CRITICAL'
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 90 THEN 'RED'
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 80 THEN 'YELLOW'
                ELSE 'GREEN'
            END as AlertLevel

        FROM [ben002].WO w
        
        LEFT JOIN [ben002].Customer c ON w.BillTo = c.Number
        
        LEFT JOIN (
            SELECT 
                WONo,
                SUM(Sell) as QuotedAmount
            FROM [ben002].WOMisc
            WHERE Description LIKE '%SHOP%LABOR%' 
               OR Description LIKE '%REPAIR%LABOR%'
               OR Description LIKE '%SHOP REPAIR LABOR%'
            GROUP BY WONo
        ) quoted ON w.WONo = quoted.WONo
        
        LEFT JOIN [ben002].WOLabor l ON w.WONo = l.WONo
        
        WHERE w.Type IN ('S', 'SH', 'PM')
          AND w.ClosedDate IS NULL
        
        GROUP BY 
            w.WONo, w.BillTo, c.Name, w.UnitNo, w.SerialNo, 
            w.OpenDate, w.Status, quoted.QuotedAmount
        
        ORDER BY 
            CASE 
                WHEN quoted.QuotedAmount IS NULL THEN 4
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 100 THEN 1
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 90 THEN 2
                WHEN (COALESCE(SUM(l.Hours), 0) / (quoted.QuotedAmount / 189.0)) * 100 >= 80 THEN 3
                ELSE 5
            END,
            w.OpenDate
        """
        
        results = db.execute_query(query)
        
        work_orders = []
        if results:
            for row in results:
                work_orders.append({
                    'wo_number': row['WONo'],
                    'customer_no': row['CustomerNo'],
                    'customer_name': row['CustomerName'] or 'Unknown',
                    'unit_no': row['UnitNo'],
                    'serial_no': row['SerialNo'],
                    'open_date': row['OpenDate'].isoformat() if row['OpenDate'] else None,
                    'status': row['Status'],
                    'quoted_amount': float(row['QuotedAmount']) if row['QuotedAmount'] else 0,
                    'quoted_hours': float(row['QuotedHours']) if row['QuotedHours'] else 0,
                    'actual_hours': float(row['ActualHours']) if row['ActualHours'] else 0,
                    'percent_used': float(row['PercentUsed']) if row['PercentUsed'] else 0,
                    'alert_level': row['AlertLevel']
                })
        
        # Calculate summary stats
        total_work_orders = len(work_orders)
        critical_count = len([wo for wo in work_orders if wo['alert_level'] == 'CRITICAL'])
        red_count = len([wo for wo in work_orders if wo['alert_level'] == 'RED'])
        yellow_count = len([wo for wo in work_orders if wo['alert_level'] == 'YELLOW'])
        warning_count = red_count + yellow_count
        
        # Calculate hours at risk (RED + CRITICAL)
        hours_at_risk = sum(wo['actual_hours'] for wo in work_orders 
                          if wo['alert_level'] in ['RED', 'CRITICAL'])
        
        return jsonify({
            'work_orders': work_orders,
            'summary': {
                'total_work_orders': total_work_orders,
                'critical_count': critical_count,
                'red_count': red_count,
                'yellow_count': yellow_count,
                'warning_count': warning_count,
                'hours_at_risk': hours_at_risk
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching shop work orders: {str(e)}")
        return jsonify({'error': str(e)}), 500