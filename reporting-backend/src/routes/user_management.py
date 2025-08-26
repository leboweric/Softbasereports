"""User management routes for admin users"""
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from src.models.user import db, User, Organization
from src.models.rbac import Role, Permission, Department
from src.utils.auth_decorators import require_permission, admin_required
from src.utils.init_rbac import assign_role_to_user, remove_role_from_user

user_management_bp = Blueprint('user_management', __name__)

@user_management_bp.route('/users', methods=['GET'])
@require_permission('view_users')
def get_all_users():
    """Get all users in the system"""
    try:
        users = User.query.all()
        return jsonify({
            'users': [u.to_dict() for u in users]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching users: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>', methods=['GET'])
@require_permission('view_users')
def get_user(user_id):
    """Get a specific user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        return jsonify({
            'user': user.to_dict(),
            'permissions': [p.name for role in user.roles for p in role.permissions]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching user: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>', methods=['PUT'])
@require_permission('edit_users')
def update_user(user_id):
    """Update user information"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update basic info
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        if 'is_active' in data:
            user.is_active = data['is_active']
        if 'department_id' in data:
            user.department_id = data['department_id']
        
        db.session.commit()
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating user: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@require_permission('manage_roles')
def assign_user_role(user_id):
    """Assign a role to a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        role_name = data.get('role_name')
        
        if not role_name:
            return jsonify({'message': 'Role name is required'}), 400
        
        success = assign_role_to_user(user, role_name)
        if success:
            return jsonify({
                'message': f'Role {role_name} assigned to user',
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'message': 'User already has this role'}), 400
            
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': f'Error assigning role: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>/roles/<role_name>', methods=['DELETE'])
@require_permission('manage_roles')
def remove_user_role(user_id, role_name):
    """Remove a role from a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        success = remove_role_from_user(user, role_name)
        if success:
            return jsonify({
                'message': f'Role {role_name} removed from user',
                'user': user.to_dict()
            }), 200
        else:
            return jsonify({'message': 'User does not have this role'}), 400
            
    except ValueError as e:
        return jsonify({'message': str(e)}), 400
    except Exception as e:
        return jsonify({'message': f'Error removing role: {str(e)}'}), 500

@user_management_bp.route('/roles', methods=['GET'])
@require_permission('view_users')
def get_all_roles():
    """Get all available roles"""
    try:
        roles = Role.query.filter_by(is_active=True).all()
        return jsonify({
            'roles': [r.to_dict() for r in roles]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching roles: {str(e)}'}), 500

@user_management_bp.route('/permissions', methods=['GET'])
@admin_required
def get_all_permissions():
    """Get all available permissions"""
    try:
        permissions = Permission.query.all()
        return jsonify({
            'permissions': [p.to_dict() for p in permissions]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching permissions: {str(e)}'}), 500

@user_management_bp.route('/departments', methods=['GET'])
@require_permission('view_users')
def get_all_departments():
    """Get all departments"""
    try:
        departments = Department.query.filter_by(is_active=True).all()
        return jsonify({
            'departments': [d.to_dict() for d in departments]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching departments: {str(e)}'}), 500