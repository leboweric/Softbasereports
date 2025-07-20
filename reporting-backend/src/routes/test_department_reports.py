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
            
            # Test with a simple query first
            test_query = """
            SELECT COUNT(*) as count FROM ben002.WO WHERE Type = 'S'
            """
            
            test_result = db.execute_query(test_query)
            
            # Return minimal data structure for testing
            return jsonify({
                'summary': {
                    'openWorkOrders': test_result[0]['count'] if test_result else 0,
                    'completedToday': 0,
                    'averageRepairTime': 0,
                    'technicianEfficiency': 87,
                    'revenue': 0,
                    'customersServed': 0
                },
                'workOrdersByStatus': [],
                'recentWorkOrders': [],
                'monthlyTrend': [],
                'technicianPerformance': []
            })
            
        except Exception as e:
            return jsonify({
                'error': str(e),
                'type': 'service_report_error',
                'details': f"Query failed: {str(e)}"
            }), 500