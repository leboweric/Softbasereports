# Simplified department report endpoints for testing
from flask import jsonify
from flask_jwt_extended import jwt_required
from datetime import datetime
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
            
            # Test with a simple query first - count OPEN service work orders
            test_query = """
            SELECT 
                COUNT(*) as total_service,
                SUM(CASE WHEN ClosedDate IS NULL THEN 1 ELSE 0 END) as open_service,
                SUM(CASE WHEN ClosedDate IS NOT NULL THEN 1 ELSE 0 END) as closed_service
            FROM ben002.WO 
            WHERE Type = 'S'
            """
            
            test_result = db.execute_query(test_query)
            
            # Return minimal data structure for testing
            if test_result and len(test_result) > 0:
                row = test_result[0]
                open_count = row.get('open_service', 0) or 0
                total_count = row.get('total_service', 0) or 0
                closed_count = row.get('closed_service', 0) or 0
            else:
                open_count = 0
                total_count = 0
                closed_count = 0
                
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
                    {'name': 'Closed', 'status': 'Closed', 'count': closed_count, 'color': '#10b981'}
                ],
                'recentWorkOrders': [],
                'monthlyTrend': [],
                'technicianPerformance': [],
                'debug': {
                    'total_service_orders': total_count,
                    'open_service_orders': open_count,
                    'closed_service_orders': closed_count
                }
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'service_report_error',
                'details': f"Query failed: {str(e)}"
            }), 500