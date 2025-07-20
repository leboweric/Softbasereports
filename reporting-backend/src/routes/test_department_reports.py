# Simplified department report endpoints for testing
from flask import jsonify
from flask_jwt_extended import jwt_required
import datetime
from src.services.azure_sql_service import AzureSQLService


def get_db():
    """Get database connection"""
    return AzureSQLService()


def register_department_routes(reports_bp):
    """Register department report routes with the reports blueprint"""
    
    @reports_bp.route('/departments/service', methods=['GET'])
    @jwt_required()
    def get_service_department_report():
        """Get Service Department report data"""
        try:
            db = get_db()
            
            # Get current date info for month calculations
            today = datetime.now()
            current_month_start = today.replace(day=1)
            last_month_end = current_month_start - datetime.timedelta(days=1)
            last_month_start = last_month_end.replace(day=1)
            
            # Count open and recently closed work orders
            test_query = f"""
            SELECT 
                COUNT(*) as total_service,
                SUM(CASE WHEN ClosedDate IS NULL THEN 1 ELSE 0 END) as open_service,
                SUM(CASE 
                    WHEN ClosedDate >= '{current_month_start.strftime('%Y-%m-%d')}' 
                    THEN 1 ELSE 0 
                END) as closed_this_month,
                SUM(CASE 
                    WHEN ClosedDate >= '{last_month_start.strftime('%Y-%m-%d')}' 
                    AND ClosedDate < '{current_month_start.strftime('%Y-%m-%d')}'
                    THEN 1 ELSE 0 
                END) as closed_last_month
            FROM ben002.WO 
            WHERE Type = 'S'
            """
            
            test_result = db.execute_query(test_query)
            
            # Return minimal data structure for testing
            if test_result and len(test_result) > 0:
                row = test_result[0]
                open_count = row.get('open_service', 0) or 0
                total_count = row.get('total_service', 0) or 0
                closed_this_month = row.get('closed_this_month', 0) or 0
                closed_last_month = row.get('closed_last_month', 0) or 0
            else:
                open_count = 0
                total_count = 0
                closed_this_month = 0
                closed_last_month = 0
                
            # Get month names for labels
            current_month_name = today.strftime('%B')  # e.g., "July"
            last_month_name = last_month_end.strftime('%B')  # e.g., "June"
                
            return jsonify({
                'summary': {
                    'openWorkOrders': open_count,
                    'completedToday': 0,
                    'averageRepairTime': 0,
                    'technicianEfficiency': 87,
                    'revenue': 0,
                    'customersServed': 0
                },
                'workOrdersByStatus': [
                    {'name': 'Open', 'status': 'Open', 'count': open_count, 'color': '#f59e0b'},
                    {'name': f'Closed {current_month_name}', 'status': 'Closed This Month', 'count': closed_this_month, 'color': '#10b981'},
                    {'name': f'Closed {last_month_name}', 'status': 'Closed Last Month', 'count': closed_last_month, 'color': '#3b82f6'}
                ],
                'recentWorkOrders': [],
                'monthlyTrend': [],
                'technicianPerformance': [],
                'debug': {
                    'total_service_orders': total_count,
                    'open_service_orders': open_count,
                    'closed_this_month': closed_this_month,
                    'closed_last_month': closed_last_month,
                    'current_month': current_month_name,
                    'last_month': last_month_name
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'service_report_error',
                'details': f"Query failed: {str(e)}"
            }), 500