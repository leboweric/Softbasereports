from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.softbase_service import SoftbaseService
from ..models.user import User
import logging

logger = logging.getLogger(__name__)

database_bp = Blueprint('database', __name__)

@database_bp.route('/api/database/test-connection', methods=['GET'])
@jwt_required()
def test_connection():
    """Test the Azure SQL database connection"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        service = SoftbaseService(user.organization)
        result = service.test_connection()
        
        return jsonify(result), 200 if result['status'] == 'connected' else 500
        
    except Exception as e:
        logger.error(f"Connection test failed: {str(e)}")
        return jsonify({'error': 'Connection test failed', 'message': str(e)}), 500

@database_bp.route('/api/database/tables', methods=['GET'])
@jwt_required()
def get_tables():
    """Get list of all available tables"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        service = SoftbaseService(user.organization)
        tables = service.get_available_tables()
        
        return jsonify({
            'tables': tables,
            'total_count': len(tables)
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get tables: {str(e)}")
        return jsonify({'error': 'Failed to get tables', 'message': str(e)}), 500

@database_bp.route('/api/database/table/<table_name>/info', methods=['GET'])
@jwt_required()
def get_table_info(table_name):
    """Get column information for a specific table"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        service = SoftbaseService(user.organization)
        columns = service.get_table_info(table_name)
        
        return jsonify({
            'table_name': table_name,
            'columns': columns
        }), 200
        
    except Exception as e:
        logger.error(f"Failed to get table info: {str(e)}")
        return jsonify({'error': 'Failed to get table info', 'message': str(e)}), 500

@database_bp.route('/api/database/query', methods=['POST'])
@jwt_required()
def execute_query():
    """Execute a custom SQL query (SELECT only)"""
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        query = data.get('query', '')
        
        if not query:
            return jsonify({'error': 'Query is required'}), 400
        
        service = SoftbaseService(user.organization)
        result = service.execute_custom_query(query)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        return jsonify({'error': 'Query execution failed', 'message': str(e)}), 500