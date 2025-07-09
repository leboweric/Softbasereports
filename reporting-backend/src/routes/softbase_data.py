from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.azure_sql_service import AzureSQLService
from ..services.softbase_mock_service import SoftbaseMockService
from ..models.user import User
import logging

logger = logging.getLogger(__name__)

softbase_bp = Blueprint('softbase', __name__)

def get_db_service():
    """Get database service - Azure SQL or mock fallback"""
    try:
        db = AzureSQLService()
        if db.test_connection():
            return db, 'live'
    except Exception as e:
        logger.warning(f"Using mock service: {str(e)}")
    
    return SoftbaseMockService(), 'mock'

@softbase_bp.route('/api/softbase/customers', methods=['GET'])
@jwt_required()
def get_customers():
    """Get customer data"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db, status = get_db_service()
        
        if isinstance(db, SoftbaseMockService):
            customers = db.get_customers_sample()
        else:
            # Real query for Azure SQL
            customers = db.execute_query("""
                SELECT TOP 100 * FROM CustomerMaster 
                ORDER BY CompanyName
            """)
        
        return jsonify({
            'data': customers,
            'count': len(customers),
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching customers: {str(e)}")
        return jsonify({'error': str(e)}), 500

@softbase_bp.route('/api/softbase/equipment', methods=['GET'])
@jwt_required()
def get_equipment():
    """Get equipment/forklift data"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db, status = get_db_service()
        
        if isinstance(db, SoftbaseMockService):
            equipment = db.get_equipment_sample()
        else:
            # Real query for Azure SQL
            equipment = db.execute_query("""
                SELECT TOP 100 * FROM EquipmentMaster 
                ORDER BY SerialNumber
            """)
        
        return jsonify({
            'data': equipment,
            'count': len(equipment),
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching equipment: {str(e)}")
        return jsonify({'error': str(e)}), 500

@softbase_bp.route('/api/softbase/service-history', methods=['GET'])
@jwt_required()
def get_service_history():
    """Get service history data"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db, status = get_db_service()
        
        if isinstance(db, SoftbaseMockService):
            services = db.get_service_history_sample()
        else:
            # Real query for Azure SQL
            services = db.execute_query("""
                SELECT TOP 100 * FROM ServiceHistory 
                ORDER BY ServiceDate DESC
            """)
        
        return jsonify({
            'data': services,
            'count': len(services),
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching service history: {str(e)}")
        return jsonify({'error': str(e)}), 500

@softbase_bp.route('/api/softbase/sales', methods=['GET'])
@jwt_required()
def get_sales():
    """Get sales data"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db, status = get_db_service()
        
        if isinstance(db, SoftbaseMockService):
            sales = db.get_sales_data_sample()
        else:
            # Real query for Azure SQL
            sales = db.execute_query("""
                SELECT TOP 100 * FROM SalesOrders 
                ORDER BY OrderDate DESC
            """)
        
        return jsonify({
            'data': sales,
            'count': len(sales),
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching sales: {str(e)}")
        return jsonify({'error': str(e)}), 500

@softbase_bp.route('/api/softbase/dashboard-stats', methods=['GET'])
@jwt_required()
def get_dashboard_stats():
    """Get dashboard statistics"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(int(current_user_id))
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        db, status = get_db_service()
        
        if isinstance(db, SoftbaseMockService):
            # Mock statistics
            stats = {
                'total_customers': 6,
                'active_equipment': 14,
                'service_calls_this_month': 12,
                'sales_this_month': 5,
                'revenue_this_month': 285000,
                'open_work_orders': 3
            }
        else:
            # Real queries would go here
            stats = {
                'total_customers': 0,
                'active_equipment': 0,
                'service_calls_this_month': 0,
                'sales_this_month': 0,
                'revenue_this_month': 0,
                'open_work_orders': 0
            }
        
        return jsonify({
            'stats': stats,
            'status': status
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching dashboard stats: {str(e)}")
        return jsonify({'error': str(e)}), 500