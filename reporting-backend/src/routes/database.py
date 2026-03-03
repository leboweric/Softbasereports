from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.softbase_service import SoftbaseService
from ..models.user import User, Organization
import logging
import os

logger = logging.getLogger(__name__)

database_bp = Blueprint('database', __name__)

@database_bp.route('/api/database/test', methods=['GET'])
@jwt_required()
def test_endpoint():
    """Simple test endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Database routes are working',
        'azure_configured': bool(os.environ.get('AZURE_SQL_PASSWORD'))
    }), 200

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
        
        # Support org_id override for multi-org Super Admins
        org_id_override = data.get('org_id') or request.args.get('org_id', type=int)
        target_org = user.organization
        if org_id_override:
            org_id_override = int(org_id_override)
            if org_id_override != user.organization_id:
                super_admin_roles = [r for r in user.roles if r.name == 'Super Admin']
                if len(super_admin_roles) > 1:
                    override_org = Organization.query.get(org_id_override)
                    if override_org:
                        target_org = override_org
                        logger.info(f"Database query: org override to {override_org.name} (id={org_id_override})")
        
        service = SoftbaseService(target_org)
        result = service.execute_custom_query(query)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        return jsonify({'error': 'Query execution failed', 'message': str(e)}), 500