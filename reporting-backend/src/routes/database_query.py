from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.services.azure_sql_service import AzureSQLService
import logging

logger = logging.getLogger(__name__)

database_query_bp = Blueprint('database_query', __name__)

@database_query_bp.route('/api/database/execute-query', methods=['POST'])
@jwt_required()
def execute_query():
    """
    Execute a custom SQL query for database exploration
    """
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({'error': 'Query cannot be empty'}), 400
        
        # Security: Only allow SELECT statements
        if not query.upper().startswith('SELECT'):
            return jsonify({'error': 'Only SELECT queries are allowed'}), 400
        
        db = AzureSQLService()
        results = db.execute_query(query)
        
        # Get column names
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        # Convert results to list of dicts
        result_list = []
        for row in results:
            row_dict = {}
            for i, col in enumerate(columns):
                val = row[i]
                # Convert to JSON-safe types
                if val is None:
                    row_dict[col] = None
                else:
                    row_dict[col] = str(val)
            result_list.append(row_dict)
        
        return jsonify({
            'success': True,
            'columns': columns,
            'results': result_list,
            'row_count': len(result_list)
        })
        
    except Exception as e:
        logger.error(f"Query execution failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@database_query_bp.route('/api/debug/navigation', methods=['GET'])
@jwt_required()
def debug_navigation():
    """
    Debug endpoint to check user navigation
    """
    try:
        from flask_jwt_extended import get_jwt_identity
        from src.models.user import User
        from src.services.permission_service import PermissionService
        
        current_user_id = get_jwt_identity()
        current_user = User.query.get(int(current_user_id))
        
        if not current_user:
            return jsonify({'error': 'User not found'}), 404
        
        navigation = PermissionService.get_user_navigation(current_user)
        resources = PermissionService.get_user_resources(current_user)
        
        return jsonify({
            'user_email': current_user.email,
            'user_roles': [r.name for r in current_user.roles],
            'legacy_role': current_user.role,
            'navigation_items': list(navigation.keys()),
            'all_resources': resources,
            'has_database_explorer': 'database_explorer' in resources,
            'database_explorer_in_nav': 'database-explorer' in navigation,
            'full_navigation': navigation
        })
        
    except Exception as e:
        logger.error(f"Navigation debug failed: {str(e)}")
        return jsonify({'error': str(e)}), 500