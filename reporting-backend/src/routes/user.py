from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required
from src.models.user import User, db
from src.models.rbac import Role
from src.utils.auth_decorators import require_permission

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.to_dict() for user in users])

@user_bp.route('/users', methods=['POST'])
def create_user():
    
    data = request.json
    user = User(username=data['username'], email=data['email'])
    db.session.add(user)
    db.session.commit()
    return jsonify(user.to_dict()), 201

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.json
    user.username = data.get('username', user.username)
    user.email = data.get('email', user.email)
    db.session.commit()
    return jsonify(user.to_dict())

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@require_permission('manage_users')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return '', 204

@user_bp.route('/users/<int:user_id>/roles', methods=['GET'])
@require_permission('manage_roles', 'view_users')
def get_user_roles(user_id):
    """Get all roles assigned to a user"""
    user = User.query.get_or_404(user_id)
    return jsonify({
        'user_id': user.id,
        'username': user.username,
        'roles': [role.to_dict() for role in user.roles]
    })

@user_bp.route('/users/<int:user_id>/roles/<int:role_id>', methods=['POST'])
@require_permission('manage_roles')
def assign_role_to_user(user_id, role_id):
    """Assign a role to a user"""
    user = User.query.get_or_404(user_id)
    role = Role.query.get_or_404(role_id)
    
    if role not in user.roles:
        user.roles.append(role)
        db.session.commit()
        return jsonify({
            'message': f'Role {role.name} assigned to user {user.username}',
            'user': user.to_dict()
        })
    else:
        return jsonify({
            'message': f'User {user.username} already has role {role.name}'
        }), 400

@user_bp.route('/users/<int:user_id>/roles/<int:role_id>', methods=['DELETE'])
@require_permission('manage_roles')
def remove_role_from_user(user_id, role_id):
    """Remove a role from a user"""
    user = User.query.get_or_404(user_id)
    role = Role.query.get_or_404(role_id)
    
    if role in user.roles:
        user.roles.remove(role)
        db.session.commit()
        return jsonify({
            'message': f'Role {role.name} removed from user {user.username}',
            'user': user.to_dict()
        })
    else:
        return jsonify({
            'message': f'User {user.username} does not have role {role.name}'
        }), 400

@user_bp.route('/roles', methods=['GET'])
@require_permission('manage_roles', 'view_users')
def get_all_roles():
    """Get all available roles"""
    roles = Role.query.all()
    return jsonify([role.to_dict() for role in roles])

@user_bp.route('/users/parts-users', methods=['GET'])
@require_permission('manage_roles', 'view_users')
def get_parts_users():
    """Get all users with Parts User role"""
    parts_role = Role.query.filter_by(name='Parts User').first()
    if not parts_role:
        return jsonify({'message': 'Parts User role not found'}), 404
    
    parts_users = User.query.filter(User.roles.contains(parts_role)).all()
    return jsonify({
        'role': parts_role.to_dict(),
        'users': [user.to_dict() for user in parts_users],
        'count': len(parts_users)
    })

@user_bp.route('/users/<int:user_id>/assign-parts-user', methods=['POST'])
@require_permission('manage_roles')
def assign_parts_user_role(user_id):
    """Convenience endpoint to assign Parts User role"""
    user = User.query.get_or_404(user_id)
    parts_role = Role.query.filter_by(name='Parts User').first()
    
    if not parts_role:
        return jsonify({'message': 'Parts User role not found'}), 404
    
    if parts_role not in user.roles:
        user.roles.append(parts_role)
        db.session.commit()
        return jsonify({
            'message': f'Parts User role assigned to {user.username}',
            'user': user.to_dict()
        })
    else:
        return jsonify({
            'message': f'User {user.username} already has Parts User role'
        }), 400
