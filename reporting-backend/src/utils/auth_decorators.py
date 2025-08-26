"""
Authentication and authorization decorators for route protection
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from src.models.user import User

def require_permission(*permissions):
    """
    Decorator to require specific permissions for a route
    Usage: @require_permission('view_parts', 'edit_parts')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'message': 'Account is disabled'}), 403
            
            # Check if user has any of the required permissions
            if not user.has_any_permission(*permissions):
                return jsonify({
                    'message': 'Insufficient permissions',
                    'required': list(permissions),
                    'user_permissions': [p.name for role in user.roles for p in role.permissions]
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_all_permissions(*permissions):
    """
    Decorator to require ALL specified permissions for a route
    Usage: @require_all_permissions('view_parts', 'edit_parts')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'message': 'Account is disabled'}), 403
            
            # Check if user has ALL required permissions
            if not user.has_all_permissions(*permissions):
                return jsonify({
                    'message': 'Insufficient permissions',
                    'required': list(permissions),
                    'user_permissions': [p.name for role in user.roles for p in role.permissions]
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_role(*role_names):
    """
    Decorator to require specific roles for a route
    Usage: @require_role('Parts Manager', 'Super Admin')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'message': 'Account is disabled'}), 403
            
            # Check if user has any of the required roles
            if not any(user.has_role(role) for role in role_names):
                return jsonify({
                    'message': 'Insufficient role privileges',
                    'required_roles': list(role_names),
                    'user_roles': [r.name for r in user.roles]
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_department(*department_names):
    """
    Decorator to require access to specific departments
    Usage: @require_department('Parts', 'Service')
    """
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return jsonify({'message': 'User not found'}), 404
            
            if not user.is_active:
                return jsonify({'message': 'Account is disabled'}), 403
            
            # Check if user can access any of the required departments
            if not any(user.can_access_department(dept) for dept in department_names):
                return jsonify({
                    'message': 'Department access denied',
                    'required_departments': list(department_names),
                    'accessible_departments': user.get_accessible_departments()
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def admin_required(f):
    """
    Decorator to require admin privileges
    Usage: @admin_required
    """
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        if not user.is_active:
            return jsonify({'message': 'Account is disabled'}), 403
        
        if not user.is_admin:
            return jsonify({'message': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """
    Helper function to get the current user object
    Must be called within a route protected by @jwt_required()
    """
    user_id = get_jwt_identity()
    return User.query.get(user_id) if user_id else None