"""
GL Account Mapping API
Provides CRUD endpoints for managing GL account mappings per tenant,
plus a trigger for auto-discovery.
"""

from flask import Blueprint, request, jsonify
from functools import wraps
import jwt
import os
import logging

logger = logging.getLogger(__name__)

gl_mapping_bp = Blueprint('gl_mapping', __name__)


def require_auth(f):
    """Decorator to require JWT authentication and extract user info."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Authentication required'}), 401
        try:
            secret = os.environ.get('JWT_SECRET_KEY', os.environ.get('SECRET_KEY', 'dev-secret'))
            payload = jwt.decode(token, secret, algorithms=['HS256'])
            request.user_org_id = payload.get('organization_id')
            request.user_role = payload.get('role', '')
            request.user_schema = payload.get('schema', '')
            if not request.user_org_id:
                return jsonify({'error': 'No organization found in token'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated


def require_admin(f):
    """Decorator to require admin role. Checks JWT first, falls back to DB lookup."""
    @wraps(f)
    @require_auth
    def decorated(*args, **kwargs):
        role = request.user_role
        admin_roles = ('super_admin', 'admin', 'Super Admin', 'Admin')
        
        # If JWT role is missing or None, look up from database
        if not role or role == 'None':
            try:
                from src.services.postgres_service import PostgreSQLService
                pg = PostgreSQLService()
                user_id = getattr(request, 'user_id', None)
                if not user_id:
                    # Try to get user_id from JWT payload
                    token = request.headers.get('Authorization', '').replace('Bearer ', '')
                    secret = os.environ.get('JWT_SECRET_KEY', os.environ.get('SECRET_KEY', 'dev-secret'))
                    payload = jwt.decode(token, secret, algorithms=['HS256'])
                    user_id = payload.get('user_id')
                
                if user_id:
                    result = pg.execute_query("""
                        SELECT r.name as role_name 
                        FROM user_roles ur 
                        JOIN role r ON ur.role_id = r.id 
                        WHERE ur.user_id = %s
                    """, (user_id,))
                    if result:
                        role = result[0].get('role_name', '')
                        request.user_role = role
            except Exception as e:
                logger.warning(f"Failed to look up role from DB: {e}")
        
        if role not in admin_roles:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated


# ============================================================
# GL Account Endpoints
# ============================================================

@gl_mapping_bp.route('/accounts', methods=['GET'])
@require_auth
def get_gl_accounts():
    """
    Get all GL accounts for the current tenant.
    Query params: account_type, department_code, expense_category, is_active, search
    """
    try:
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        
        org_id = request.user_org_id
        
        # Build query with filters
        conditions = ["organization_id = %s"]
        params = [org_id]
        
        account_type = request.args.get('account_type')
        if account_type:
            conditions.append("account_type = %s")
            params.append(account_type)
        
        dept_code = request.args.get('department_code')
        if dept_code:
            conditions.append("department_code = %s")
            params.append(dept_code)
        
        expense_cat = request.args.get('expense_category')
        if expense_cat:
            conditions.append("expense_category = %s")
            params.append(expense_cat)
        
        is_active = request.args.get('is_active')
        if is_active is not None:
            conditions.append("is_active = %s")
            params.append(is_active.lower() == 'true')
        
        search = request.args.get('search')
        if search:
            conditions.append("(account_no ILIKE %s OR description ILIKE %s)")
            params.extend([f'%{search}%', f'%{search}%'])
        
        where_clause = " AND ".join(conditions)
        
        query = f"""
            SELECT id, account_no, account_type, department_code, department_name,
                   expense_category, description, is_active, is_auto_discovered,
                   last_seen_date, created_at, updated_at
            FROM tenant_gl_accounts
            WHERE {where_clause}
            ORDER BY account_no
        """
        
        accounts = pg.execute_query(query, tuple(params))
        
        # Get summary counts
        summary_query = """
            SELECT 
                account_type,
                COUNT(*) as count,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END) as active_count
            FROM tenant_gl_accounts
            WHERE organization_id = %s
            GROUP BY account_type
            ORDER BY account_type
        """
        summary = pg.execute_query(summary_query, (org_id,))
        
        return jsonify({
            'accounts': accounts,
            'summary': summary,
            'total': len(accounts),
        })
        
    except Exception as e:
        logger.error(f"Error fetching GL accounts: {e}")
        return jsonify({'error': str(e)}), 500


@gl_mapping_bp.route('/accounts/<int:account_id>', methods=['PUT'])
@require_admin
def update_gl_account(account_id):
    """Update a GL account mapping (department, category, description, active status)."""
    try:
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        
        org_id = request.user_org_id
        data = request.get_json()
        
        # Build update fields
        updates = []
        params = []
        
        allowed_fields = {
            'account_type': 'account_type',
            'department_code': 'department_code',
            'department_name': 'department_name',
            'expense_category': 'expense_category',
            'description': 'description',
            'is_active': 'is_active',
        }
        
        for field, column in allowed_fields.items():
            if field in data:
                updates.append(f"{column} = %s")
                params.append(data[field])
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        # Mark as manually edited
        updates.append("is_auto_discovered = FALSE")
        updates.append("updated_at = CURRENT_TIMESTAMP")
        
        params.extend([org_id, account_id])
        
        query = f"""
            UPDATE tenant_gl_accounts
            SET {', '.join(updates)}
            WHERE organization_id = %s AND id = %s
            RETURNING id, account_no, account_type, department_code, department_name,
                      expense_category, description, is_active, is_auto_discovered
        """
        
        with pg.get_connection() as conn:
            with conn.cursor() as cursor:
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute(query, tuple(params))
                result = cursor.fetchone()
                conn.commit()
        
        if not result:
            return jsonify({'error': 'Account not found'}), 404
        
        return jsonify({'account': dict(result)})
        
    except Exception as e:
        logger.error(f"Error updating GL account: {e}")
        return jsonify({'error': str(e)}), 500


@gl_mapping_bp.route('/accounts/bulk-update', methods=['PUT'])
@require_admin
def bulk_update_gl_accounts():
    """Bulk update multiple GL accounts at once."""
    try:
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        
        org_id = request.user_org_id
        data = request.get_json()
        
        account_ids = data.get('account_ids', [])
        updates = data.get('updates', {})
        
        if not account_ids or not updates:
            return jsonify({'error': 'account_ids and updates required'}), 400
        
        set_clauses = []
        params = []
        
        allowed_fields = ['account_type', 'department_code', 'department_name', 
                         'expense_category', 'is_active']
        
        for field in allowed_fields:
            if field in updates:
                set_clauses.append(f"{field} = %s")
                params.append(updates[field])
        
        if not set_clauses:
            return jsonify({'error': 'No valid fields to update'}), 400
        
        set_clauses.append("is_auto_discovered = FALSE")
        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        
        placeholders = ','.join(['%s'] * len(account_ids))
        params.extend([org_id])
        params.extend(account_ids)
        
        query = f"""
            UPDATE tenant_gl_accounts
            SET {', '.join(set_clauses)}
            WHERE organization_id = %s AND id IN ({placeholders})
        """
        
        with pg.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                updated_count = cursor.rowcount
                conn.commit()
        
        return jsonify({'updated': updated_count})
        
    except Exception as e:
        logger.error(f"Error bulk updating GL accounts: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Department Endpoints
# ============================================================

@gl_mapping_bp.route('/departments', methods=['GET'])
@require_auth
def get_departments():
    """Get all departments for the current tenant."""
    try:
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        
        query = """
            SELECT d.id, d.dept_code, d.dept_name, d.display_order, d.is_active,
                   COUNT(g.id) as account_count,
                   SUM(CASE WHEN g.account_type = 'revenue' THEN 1 ELSE 0 END) as revenue_accounts,
                   SUM(CASE WHEN g.account_type = 'cogs' THEN 1 ELSE 0 END) as cogs_accounts,
                   SUM(CASE WHEN g.account_type = 'expense' THEN 1 ELSE 0 END) as expense_accounts
            FROM tenant_departments d
            LEFT JOIN tenant_gl_accounts g ON d.organization_id = g.organization_id 
                AND d.dept_code = g.department_code AND g.is_active = TRUE
            WHERE d.organization_id = %s
            GROUP BY d.id, d.dept_code, d.dept_name, d.display_order, d.is_active
            ORDER BY d.display_order, d.dept_code
        """
        
        departments = pg.execute_query(query, (request.user_org_id,))
        return jsonify({'departments': departments})
        
    except Exception as e:
        logger.error(f"Error fetching departments: {e}")
        return jsonify({'error': str(e)}), 500


@gl_mapping_bp.route('/departments/<int:dept_id>', methods=['PUT'])
@require_admin
def update_department(dept_id):
    """Update a department name or display order."""
    try:
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        
        data = request.get_json()
        updates = []
        params = []
        
        if 'dept_name' in data:
            updates.append("dept_name = %s")
            params.append(data['dept_name'])
        if 'display_order' in data:
            updates.append("display_order = %s")
            params.append(data['display_order'])
        if 'is_active' in data:
            updates.append("is_active = %s")
            params.append(data['is_active'])
        
        if not updates:
            return jsonify({'error': 'No fields to update'}), 400
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([request.user_org_id, dept_id])
        
        query = f"""
            UPDATE tenant_departments
            SET {', '.join(updates)}
            WHERE organization_id = %s AND id = %s
        """
        
        with pg.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, tuple(params))
                conn.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Error updating department: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Expense Category Endpoints
# ============================================================

@gl_mapping_bp.route('/expense-categories', methods=['GET'])
@require_auth
def get_expense_categories():
    """Get all expense categories for the current tenant."""
    try:
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        
        query = """
            SELECT ec.id, ec.category_key, ec.category_name, ec.display_order, ec.is_active,
                   COUNT(g.id) as account_count
            FROM tenant_expense_categories ec
            LEFT JOIN tenant_gl_accounts g ON ec.organization_id = g.organization_id 
                AND ec.category_key = g.expense_category AND g.is_active = TRUE
            WHERE ec.organization_id = %s
            GROUP BY ec.id, ec.category_key, ec.category_name, ec.display_order, ec.is_active
            ORDER BY ec.display_order, ec.category_key
        """
        
        categories = pg.execute_query(query, (request.user_org_id,))
        return jsonify({'categories': categories})
        
    except Exception as e:
        logger.error(f"Error fetching expense categories: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Discovery Endpoints
# ============================================================

@gl_mapping_bp.route('/discover', methods=['POST'])
@require_admin
def trigger_discovery():
    """Trigger GL account auto-discovery for the current tenant."""
    try:
        from src.etl.etl_gl_discovery import run_gl_discovery_etl
        
        org_id = request.user_org_id
        
        # Look up schema from Organization table (not in JWT)
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        org_result = pg.execute_query(
            "SELECT database_schema FROM organization WHERE id = %s", (org_id,)
        )
        if not org_result or not org_result[0].get('database_schema'):
            return jsonify({'error': 'No database schema found for this organization'}), 400
        schema = org_result[0]['database_schema']
        
        logger.info(f"[GL Mapping] Triggering discovery for org_id={org_id}, schema={schema}")
        run_gl_discovery_etl(org_id=org_id, schema=schema)
        
        # Return updated counts
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        
        count_query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN account_type = 'revenue' THEN 1 ELSE 0 END) as revenue,
                SUM(CASE WHEN account_type = 'cogs' THEN 1 ELSE 0 END) as cogs,
                SUM(CASE WHEN account_type = 'expense' THEN 1 ELSE 0 END) as expense,
                SUM(CASE WHEN account_type = 'other_income' THEN 1 ELSE 0 END) as other_income,
                SUM(CASE WHEN account_type = 'other' THEN 1 ELSE 0 END) as other
            FROM tenant_gl_accounts
            WHERE organization_id = %s AND is_active = TRUE
        """
        counts = pg.execute_query(count_query, (org_id,))
        
        return jsonify({
            'success': True,
            'message': 'GL account discovery completed',
            'counts': counts[0] if counts else {},
        })
        
    except Exception as e:
        logger.error(f"Error triggering GL discovery: {e}")
        return jsonify({'error': str(e)}), 500


@gl_mapping_bp.route('/discovery-log', methods=['GET'])
@require_auth
def get_discovery_log():
    """Get the discovery run history for the current tenant."""
    try:
        from src.services.postgres_service import PostgreSQLService
        pg = PostgreSQLService()
        
        query = """
            SELECT id, discovery_type, accounts_found, accounts_new, accounts_updated,
                   status, error_message, started_at, completed_at
            FROM gl_discovery_log
            WHERE organization_id = %s
            ORDER BY started_at DESC
            LIMIT 20
        """
        
        logs = pg.execute_query(query, (request.user_org_id,))
        return jsonify({'logs': logs})
        
    except Exception as e:
        logger.error(f"Error fetching discovery log: {e}")
        return jsonify({'error': str(e)}), 500


# ============================================================
# Migration Endpoint (run once)
# ============================================================

@gl_mapping_bp.route('/migrate', methods=['POST'])
@require_admin
def run_migration():
    """Run the GL mapping tables migration (idempotent)."""
    try:
        from src.services.postgres_service import PostgreSQLService
        import os
        
        pg = PostgreSQLService()
        
        migration_file = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'migrations', 'create_gl_mapping_tables.sql'
        )
        
        with open(migration_file, 'r') as f:
            sql_content = f.read()
        
        with pg.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(sql_content)
            conn.commit()
        
        return jsonify({
            'success': True,
            'message': 'GL mapping tables created/verified successfully'
        })
        
    except Exception as e:
        logger.error(f"Error running migration: {e}")
        return jsonify({'error': str(e)}), 500
