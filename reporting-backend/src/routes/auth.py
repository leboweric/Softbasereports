from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from src.models.user import db, User, Organization

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
@cross_origin()
def register():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'organization_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'message': f'{field} is required'}), 400
        
        # Check if user already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'message': 'Username already exists'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'message': 'Email already exists'}), 400
        
        # Create or get organization
        organization = Organization.query.filter_by(name=data['organization_name']).first()
        if not organization:
            organization = Organization(name=data['organization_name'])
            db.session.add(organization)
            db.session.flush()  # Get the ID
        
        # Create user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data.get('first_name', ''),
            last_name=data.get('last_name', ''),
            organization_id=organization.id,
            role='admin' if not organization.users else 'user'  # First user is admin
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error creating user: {str(e)}'}), 500

@auth_bp.route('/login', methods=['POST'])
@cross_origin()
def login():
    try:
        data = request.get_json()
        
        if not data.get('username') or not data.get('password'):
            return jsonify({'message': 'Username and password are required'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']) or not user.is_active:
            return jsonify({'message': 'Invalid credentials'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        # Generate JWT token using Flask-JWT-Extended
        access_token = create_access_token(
            identity=str(user.id),  # Flask-JWT-Extended requires string identity
            expires_delta=timedelta(hours=24),
            additional_claims={
                'user_id': user.id,
                'organization_id': user.organization_id,
                'role': user.role
            }
        )
        
        return jsonify({
            'token': access_token,
            'user': user.to_dict(),
            'organization': user.organization.to_dict(),
            'permissions': [p.name for role in user.roles for p in role.permissions],
            'accessible_departments': user.get_accessible_departments()
        }), 200
        
    except Exception as e:
        return jsonify({'message': f'Login error: {str(e)}'}), 500

@auth_bp.route('/me', methods=['GET'])
@cross_origin()
@jwt_required()
def get_current_user():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(int(current_user_id))
    
    if not current_user or not current_user.is_active:
        return jsonify({'message': 'User not found'}), 404
    
    return jsonify({
        'user': current_user.to_dict(),
        'organization': current_user.organization.to_dict()
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
@cross_origin()
@jwt_required()
def refresh_token():
    current_user_id = get_jwt_identity()
    current_user = User.query.get(int(current_user_id))
    
    if not current_user or not current_user.is_active:
        return jsonify({'message': 'User not found'}), 404
    
    # Generate new token using Flask-JWT-Extended
    access_token = create_access_token(
        identity=str(current_user.id),  # Flask-JWT-Extended requires string identity
        expires_delta=timedelta(hours=24),
        additional_claims={
            'user_id': current_user.id,
            'organization_id': current_user.organization_id,
            'role': current_user.role
        }
    )
    
    return jsonify({'token': access_token}), 200

