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

@database_query_bp.route('/api/database/test-gl-query', methods=['POST'])
@jwt_required()
def test_gl_query():
    """
    Test GLDetail query performance with different parameters
    """
    try:
        import time
        data = request.get_json()
        
        # Parameters
        gl_accounts = data.get('gl_accounts', ['410003', '410004', '410005', '410012'])
        months_back = data.get('months_back', 1)  # Default to 1 month
        
        db = AzureSQLService()
        
        # Build query
        account_list = "', '".join(gl_accounts)
        query = f"""
        SELECT 
            AccountNo,
            YEAR(EffectiveDate) as year,
            MONTH(EffectiveDate) as month,
            COUNT(*) as transaction_count,
            SUM(Amount) as total_amount
        FROM ben002.GLDetail
        WHERE AccountNo IN ('{account_list}')
            AND EffectiveDate >= DATEADD(month, -{months_back}, GETDATE())
            AND Posted = 1
        GROUP BY AccountNo, YEAR(EffectiveDate), MONTH(EffectiveDate)
        ORDER BY AccountNo, YEAR(EffectiveDate), MONTH(EffectiveDate)
        """
        
        # Time the query
        start_time = time.time()
        results = db.execute_query(query)
        end_time = time.time()
        
        execution_time = round((end_time - start_time) * 1000, 2)  # Convert to milliseconds
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append({
                'account': row['AccountNo'],
                'year': row['year'],
                'month': row['month'],
                'transaction_count': row['transaction_count'],
                'total_amount': float(row['total_amount'] or 0)
            })
        
        return jsonify({
            'success': True,
            'execution_time_ms': execution_time,
            'months_queried': months_back,
            'gl_accounts': gl_accounts,
            'result_count': len(formatted_results),
            'results': formatted_results,
            'query': query
        })
        
    except Exception as e:
        logger.error(f"GL query test failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
