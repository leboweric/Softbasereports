"""
Authentication Routes

Handles user login, registration, and token management.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity
)
from datetime import datetime

from src.models.database import db
from src.models.core import User, Dealer

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    data = request.get_json()

    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400

    user = User.query.filter_by(email=data['email']).first()

    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401

    if not user.is_active:
        return jsonify({'error': 'Account is disabled'}), 403

    # Update last login
    user.last_login = datetime.utcnow()
    db.session.commit()

    # Create tokens
    access_token = create_access_token(identity=user.id)
    refresh_token = create_refresh_token(identity=user.id)

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'user': user.to_dict(),
        'dealer': user.dealer.to_dict() if user.dealer else None
    }), 200


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User registration endpoint.
    For dealer users, requires dealer_code to associate with existing dealer.
    """
    data = request.get_json()

    required_fields = ['email', 'username', 'password']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Check for existing user
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already taken'}), 400

    # Handle dealer association
    dealer_id = None
    if data.get('dealer_code'):
        dealer = Dealer.query.filter_by(code=data['dealer_code']).first()
        if not dealer:
            return jsonify({'error': 'Invalid dealer code'}), 400
        dealer_id = dealer.id

    # Create user
    user = User(
        email=data['email'],
        username=data['username'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
        dealer_id=dealer_id,
        user_type='dealer' if dealer_id else 'currie_admin'
    )
    user.set_password(data['password'])

    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    current_user_id = get_jwt_identity()
    access_token = create_access_token(identity=current_user_id)

    return jsonify({'access_token': access_token}), 200


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current authenticated user."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({'error': 'User not found'}), 404

    return jsonify({
        'user': user.to_dict(),
        'dealer': user.dealer.to_dict() if user.dealer else None
    }), 200
