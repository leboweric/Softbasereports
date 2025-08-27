"""User management routes for admin users"""
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import db, User, Organization
from src.models.rbac import Role, Permission, Department

user_management_bp = Blueprint('user_management', __name__)

@user_management_bp.route('/users', methods=['GET'])
@cross_origin()
@jwt_required()
def get_all_users():
    """Get all users in the system"""
    try:
        # Just return all users - bypass the organization check for now
        users = User.query.all()
        
        # Add debug info
        current_user_id = get_jwt_identity()
        
        return jsonify({
            'users': [u.to_dict() for u in users],
            'debug': {
                'jwt_user_id': current_user_id,
                'total_users': len(users),
                'user_ids': [u.id for u in users]
            }
        }), 200
    except Exception as e:
        # Return the actual error for debugging
        import traceback
        return jsonify({
            'users': [],
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 200  # Return 200 even on error so we can see the error in frontend

@user_management_bp.route('/users/<int:user_id>', methods=['GET'])
@cross_origin()
@jwt_required()
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
@cross_origin()
@jwt_required()
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
        # Commenting out department_id as it's not currently in use
        # if 'department_id' in data:
        #     user.department_id = data['department_id']
        
        db.session.commit()
        return jsonify({
            'message': 'User updated successfully',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error updating user: {str(e)}'}), 500

@user_management_bp.route('/users/<int:user_id>/roles', methods=['POST'])
@cross_origin()
@jwt_required()
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
@jwt_required()
def remove_user_role(user_id, role_name):
    """Remove a role from a user"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
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