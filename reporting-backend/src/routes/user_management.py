"""User management routes for admin users"""
from flask import Blueprint, request, jsonify, g
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash
from datetime import datetime
from src.models.user import db, User, Organization
from src.models.rbac import Role, Permission, Department
from src.middleware.tenant_middleware import TenantMiddleware

user_management_bp = Blueprint('user_management', __name__)


def verify_user_in_organization(user_id):
    """
    Helper to verify a user belongs to the current organization.
    Returns (user, error_response) tuple. If user is valid, error_response is None.
    """
    user = User.query.get(user_id)
    if not user:
        return None, (jsonify({'message': 'User not found'}), 404)

    if user.organization_id != g.current_organization.id:
        return None, (jsonify({'message': 'Access denied: User belongs to a different organization'}), 403)

    return user, None

@user_management_bp.route('/users', methods=['GET'])
@cross_origin()
@TenantMiddleware.require_organization
def get_all_users():
    """Get all users in the current organization"""
    try:
        # Filter users by current organization - MULTI-TENANT SECURITY
        users = User.query.filter_by(organization_id=g.current_organization.id).all()

        return jsonify({
            'users': [u.to_dict() for u in users],
            'organization': {
                'id': g.current_organization.id,
                'name': g.current_organization.name
            },
            'total_users': len(users)
        }), 200
    except Exception as e:
        import traceback
        return jsonify({
            'users': [],
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@user_management_bp.route('/users/<int:user_id>', methods=['GET'])
@cross_origin()
@TenantMiddleware.require_organization
def get_user(user_id):
    """Get a specific user (must belong to current organization)"""
    try:
        # Verify user belongs to current organization - MULTI-TENANT SECURITY
        user, error = verify_user_in_organization(user_id)
        if error:
            return error

        return jsonify({
            'user': user.to_dict(),
            'permissions': [p.name for role in user.roles for p in role.permissions]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching user: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>', methods=['PUT', 'OPTIONS'])
@cross_origin()
def update_user(user_id):
    """Update user information (must belong to current organization)"""
    if request.method == 'OPTIONS':
        return '', 204

    # Manually apply tenant middleware for non-OPTIONS requests
    verify_jwt_in_request()
    current_user_id = get_jwt_identity()
    current_user = User.query.get(current_user_id)
    if not current_user or not current_user.organization_id:
        return jsonify({'message': 'Authentication error'}), 401

    try:
        # Verify target user belongs to same organization - MULTI-TENANT SECURITY
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        if user.organization_id != current_user.organization_id:
            return jsonify({'message': 'Access denied: User belongs to a different organization'}), 403

        data = request.get_json()

        # Update basic info
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        if 'username' in data:
            user.username = data['username']
        if 'is_active' in data:
            user.is_active = data['is_active']

        db.session.commit()

        # Force a new query to get the updated data
        db.session.expire(user)
        updated_user = User.query.get(user_id)

        return jsonify(updated_user.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        import traceback
        traceback.print_exc()
        return jsonify({'message': f'Error updating user: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@cross_origin()
@TenantMiddleware.require_organization
def assign_user_role(user_id):
    """Assign a role to a user (must belong to current organization)"""
    try:
        # Verify user belongs to current organization - MULTI-TENANT SECURITY
        user, error = verify_user_in_organization(user_id)
        if error:
            return error

        data = request.get_json()
        role_name = data.get('role_name')

        if not role_name:
            return jsonify({'message': 'Role name is required'}), 400

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'message': f'Role {role_name} not found'}), 404

        # Check if user already has this role
        if role in user.roles:
            return jsonify({'message': 'User already has this role'}), 400

        user.roles.append(role)
        db.session.commit()

        return jsonify({
            'message': f'Role {role_name} assigned to user',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error assigning role: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>/roles/<role_name>', methods=['DELETE'])
@cross_origin()
@TenantMiddleware.require_organization
def remove_user_role(user_id, role_name):
    """Remove a role from a user (must belong to current organization)"""
    try:
        # Verify user belongs to current organization - MULTI-TENANT SECURITY
        user, error = verify_user_in_organization(user_id)
        if error:
            return error

        role = Role.query.filter_by(name=role_name).first()
        if not role:
            return jsonify({'message': f'Role {role_name} not found'}), 404

        if role not in user.roles:
            return jsonify({'message': 'User does not have this role'}), 400

        user.roles.remove(role)
        db.session.commit()

        return jsonify({
            'message': f'Role {role_name} removed from user',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error removing role: {str(e)}'}), 500

@user_management_bp.route('/roles', methods=['GET'])
@cross_origin()
@jwt_required()
def get_all_roles():
    """Get all available roles"""
    try:
        roles = Role.query.all()
        return jsonify({
            'roles': [
                {
                    'id': r.id,
                    'name': r.name,
                    'description': r.description,
                    'department': r.department,
                    'level': r.level,
                    'is_active': r.is_active,
                    'permissions': [p.name for p in r.permissions] if r.permissions else []
                } for r in roles
            ]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching roles: {str(e)}'}), 500

@user_management_bp.route('/permissions', methods=['GET'])
@cross_origin()
@jwt_required()
def get_all_permissions():
    """Get all available permissions"""
    try:
        permissions = Permission.query.all()
        return jsonify({
            'permissions': [
                {
                    'id': p.id,
                    'name': p.name,
                    'description': p.description
                } for p in permissions
            ]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching permissions: {str(e)}'}), 500

@user_management_bp.route('/departments', methods=['GET'])
@cross_origin()
@jwt_required()
def get_all_departments():
    """Get all departments"""
    try:
        departments = Department.query.all()
        return jsonify({
            'departments': [
                {
                    'id': d.id,
                    'name': d.name,
                    'description': d.description,
                    'is_active': d.is_active
                } for d in departments
            ]
        }), 200
    except Exception as e:
        return jsonify({'message': f'Error fetching departments: {str(e)}'}), 500

@user_management_bp.route('/users/create', methods=['POST'])
@cross_origin()
@TenantMiddleware.require_organization
def create_user():
    """Create a new user in the current organization"""
    try:
        data = request.get_json()

        # Check if username already exists (globally unique)
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400

        # Check if email already exists (globally unique)
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400

        # Create new user in current organization - MULTI-TENANT SECURITY
        new_user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            organization_id=g.current_organization.id,
            is_active=True,
            created_at=datetime.utcnow()
        )

        # Set password
        new_user.set_password(data['password'])

        # Add to database
        db.session.add(new_user)
        db.session.commit()

        # Assign initial role if provided
        if data.get('role'):
            role = Role.query.filter_by(name=data['role']).first()
            if role:
                new_user.roles.append(role)
                db.session.commit()

        return jsonify({
            'message': 'User created successfully',
            'user': new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@cross_origin()
@TenantMiddleware.require_organization
def reset_user_password(user_id):
    """Reset a user's password (must belong to current organization)"""
    try:
        # Verify user belongs to current organization - MULTI-TENANT SECURITY
        user, error = verify_user_in_organization(user_id)
        if error:
            return error

        data = request.get_json()
        new_password = data.get('password')

        if not new_password:
            return jsonify({'message': 'Password is required'}), 400

        # Set new password
        user.set_password(new_password)
        db.session.commit()

        return jsonify({'message': 'Password reset successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error resetting password: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>', methods=['DELETE'])
@cross_origin()
@TenantMiddleware.require_organization
def delete_user(user_id):
    """Delete a user (must belong to current organization)"""
    try:
        # Verify user belongs to current organization - MULTI-TENANT SECURITY
        user, error = verify_user_in_organization(user_id)
        if error:
            return error

        # Don't allow deleting yourself
        if g.current_user.id == user_id:
            return jsonify({'message': 'Cannot delete your own account'}), 400

        # Delete user
        db.session.delete(user)
        db.session.commit()

        return jsonify({'message': 'User deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error deleting user: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>/update-info', methods=['POST'])
@cross_origin()
@TenantMiddleware.require_organization
def update_user_info(user_id):
    """Alternative update endpoint using POST (must belong to current organization)"""
    try:
        # Verify user belongs to current organization - MULTI-TENANT SECURITY
        user, error = verify_user_in_organization(user_id)
        if error:
            return error

        data = request.get_json()

        # Update fields
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        if 'email' in data:
            user.email = data['email']
        if 'username' in data:
            user.username = data['username']

        db.session.commit()

        # Force a new query to get the updated data
        db.session.expire(user)
        updated_user = User.query.get(user_id)

        return jsonify({
            'success': True,
            'message': 'User updated successfully',
            'user': {
                'id': updated_user.id,
                'username': updated_user.username,
                'email': updated_user.email,
                'first_name': updated_user.first_name,
                'last_name': updated_user.last_name
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500