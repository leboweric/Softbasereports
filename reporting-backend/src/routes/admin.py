"""
Admin endpoints for user and role management
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from functools import wraps
from src.models.user import User, db
from src.models.rbac import Role
from src.services.permission_service import PermissionService
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)

def require_admin():
    """Decorator to require admin permissions"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def wrapper(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(int(current_user_id))
            
            if not PermissionService.user_has_permission(user, 'user_management', 'view'):
                return jsonify({'error': 'Admin access required'}), 403
            
            return f(*args, **kwargs)
        return wrapper
    return decorator

@admin_bp.route('/users', methods=['GET'])
@require_admin()
def get_users():
    """Get all users"""
    try:
        users = User.query.all()
        return jsonify([{
            'id': u.id,
            'email': u.email,
            'username': u.username,
            'first_name': u.first_name,
            'last_name': u.last_name,
            'is_active': u.is_active,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_login': u.last_login.isoformat() if u.last_login else None,
            'organization_id': u.organization_id,
            'roles': [{'id': r.id, 'name': r.name, 'department': r.department} for r in u.roles]
        } for u in users])
    except Exception as e:
        return jsonify({'error': f'Failed to fetch users: {str(e)}'}), 500

@admin_bp.route('/users', methods=['POST'])
@require_admin()
def create_user():
    """Create new user"""
    try:
        data = request.json
        
        # Validate required fields
        required_fields = ['email', 'first_name', 'last_name', 'password']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if user exists
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': 'User with this email already exists'}), 400
        
        # Create user
        user = User(
            email=data['email'],
            username=data.get('username', data['email']),
            first_name=data['first_name'],
            last_name=data['last_name'],
            password_hash=generate_password_hash(data['password']),
            is_active=data.get('is_active', True),
            organization_id=data.get('organization_id', 4),  # Default to Bennett Material Handling
            role='user'  # Legacy field
        )
        
        # Assign roles
        if 'role_ids' in data:
            for role_id in data['role_ids']:
                role = Role.query.get(role_id)
                if role:
                    user.roles.append(role)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'id': user.id,
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'roles': [{'id': r.id, 'name': r.name} for r in user.roles]
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create user: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_admin()
def update_user(user_id):
    """Update user"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.json
        
        # Update basic fields
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.is_active = data.get('is_active', user.is_active)
        
        # Update username if provided
        if 'username' in data and data['username']:
            user.username = data['username']
        
        # Update password if provided
        if 'password' in data and data['password']:
            user.password_hash = generate_password_hash(data['password'])
        
        # Update roles
        if 'role_ids' in data:
            user.roles.clear()
            for role_id in data['role_ids']:
                role = Role.query.get(role_id)
                if role:
                    user.roles.append(role)
        
        db.session.commit()
        
        return jsonify({
            'message': 'User updated successfully',
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'roles': [{'id': r.id, 'name': r.name} for r in user.roles]
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to update user: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_admin()
def delete_user(user_id):
    """Delete/deactivate user"""
    try:
        user = User.query.get_or_404(user_id)
        
        # Don't actually delete, just deactivate
        user.is_active = False
        db.session.commit()
        
        return jsonify({'message': 'User deactivated successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to deactivate user: {str(e)}'}), 500

@admin_bp.route('/roles', methods=['GET'])
@require_admin()
def get_roles():
    """Get all roles"""
    try:
        roles = Role.query.filter_by(is_active=True).all()
        return jsonify([{
            'id': r.id,
            'name': r.name,
            'description': r.description,
            'department': r.department,
            'level': r.level,
            'user_count': len(r.users)
        } for r in roles])
    except Exception as e:
        return jsonify({'error': f'Failed to fetch roles: {str(e)}'}), 500

@admin_bp.route('/permissions/config', methods=['GET'])
@require_admin()
def get_permission_config():
    """Get permission configuration"""
    try:
        from src.config.rbac_config import ROLE_PERMISSIONS, RESOURCES, NAVIGATION_CONFIG
        return jsonify({
            'resources': RESOURCES,
            'role_permissions': ROLE_PERMISSIONS,
            'navigation_config': NAVIGATION_CONFIG
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch config: {str(e)}'}), 500

@admin_bp.route('/users/<int:user_id>/permissions', methods=['GET'])
@require_admin()
def get_user_permissions(user_id):
    """Get detailed permissions for a specific user"""
    try:
        user = User.query.get_or_404(user_id)
        permissions = PermissionService.get_user_permissions_summary(user)
        
        return jsonify({
            'user_id': user_id,
            'permissions': permissions
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch user permissions: {str(e)}'}), 500

@admin_bp.route('/stats', methods=['GET'])
@require_admin()
def get_admin_stats():
    """Get admin dashboard statistics"""
    try:
        total_users = User.query.count()
        active_users = User.query.filter_by(is_active=True).count()
        total_roles = Role.query.filter_by(is_active=True).count()
        
        # Role distribution
        role_distribution = {}
        roles = Role.query.filter_by(is_active=True).all()
        for role in roles:
            role_distribution[role.name] = len(role.users)
        
        return jsonify({
            'total_users': total_users,
            'active_users': active_users,
            'inactive_users': total_users - active_users,
            'total_roles': total_roles,
            'role_distribution': role_distribution
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to fetch stats: {str(e)}'}), 500