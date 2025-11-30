"""
Dealer Management Routes

Handles dealer CRUD operations and user management within dealers.
"""
from flask import Blueprint, request, jsonify, g
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

from src.models.database import db
from src.models.core import Dealer, User, ERPConnection

dealers_bp = Blueprint('dealers', __name__)


def get_current_user():
    """Helper to get current user from JWT."""
    user_id = get_jwt_identity()
    return User.query.get(user_id)


def require_dealer_access(f):
    """Decorator to ensure user has access to the dealer."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        dealer_id = kwargs.get('dealer_id')

        # Currie admins can access any dealer
        if user.user_type in ('currie_admin', 'currie_analyst'):
            return f(*args, **kwargs)

        # Dealer users can only access their own dealer
        if user.dealer_id != dealer_id:
            return jsonify({'error': 'Access denied'}), 403

        return f(*args, **kwargs)

    return decorated


@dealers_bp.route('', methods=['GET'])
@jwt_required()
def get_dealers():
    """
    Get list of dealers.
    Currie users see all dealers, dealer users see only their dealer.
    """
    user = get_current_user()

    if user.user_type in ('currie_admin', 'currie_analyst'):
        dealers = Dealer.query.filter_by(is_active=True).all()
    else:
        dealers = [user.dealer] if user.dealer else []

    return jsonify({
        'dealers': [d.to_dict() for d in dealers]
    }), 200


@dealers_bp.route('/<int:dealer_id>', methods=['GET'])
@jwt_required()
@require_dealer_access
def get_dealer(dealer_id):
    """Get dealer details."""
    dealer = Dealer.query.get_or_404(dealer_id)
    return jsonify({'dealer': dealer.to_dict()}), 200


@dealers_bp.route('', methods=['POST'])
@jwt_required()
def create_dealer():
    """Create a new dealer. Currie admin only."""
    user = get_current_user()
    if user.user_type != 'currie_admin':
        return jsonify({'error': 'Only Currie admins can create dealers'}), 403

    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Dealer name is required'}), 400

    # Check for duplicate code
    if data.get('code') and Dealer.query.filter_by(code=data['code']).first():
        return jsonify({'error': 'Dealer code already exists'}), 400

    dealer = Dealer(
        name=data['name'],
        code=data.get('code'),
        contact_name=data.get('contact_name'),
        contact_email=data.get('contact_email'),
        contact_phone=data.get('contact_phone'),
        address=data.get('address'),
        city=data.get('city'),
        state=data.get('state'),
        zip_code=data.get('zip_code'),
        erp_system=data.get('erp_system', 'softbase_evolution'),
        subscription_tier=data.get('subscription_tier', 'basic'),
        subscription_start=datetime.utcnow()
    )

    db.session.add(dealer)
    db.session.commit()

    return jsonify({
        'message': 'Dealer created successfully',
        'dealer': dealer.to_dict()
    }), 201


@dealers_bp.route('/<int:dealer_id>', methods=['PUT'])
@jwt_required()
@require_dealer_access
def update_dealer(dealer_id):
    """Update dealer information."""
    user = get_current_user()

    # Only Currie admins or dealer admins can update
    if user.user_type not in ('currie_admin',) and user.dealer_id != dealer_id:
        return jsonify({'error': 'Access denied'}), 403

    dealer = Dealer.query.get_or_404(dealer_id)
    data = request.get_json()

    # Update fields
    for field in ['name', 'contact_name', 'contact_email', 'contact_phone',
                  'address', 'city', 'state', 'zip_code', 'erp_system']:
        if field in data:
            setattr(dealer, field, data[field])

    dealer.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({'dealer': dealer.to_dict()}), 200


@dealers_bp.route('/<int:dealer_id>/users', methods=['GET'])
@jwt_required()
@require_dealer_access
def get_dealer_users(dealer_id):
    """Get users belonging to a dealer."""
    users = User.query.filter_by(dealer_id=dealer_id).all()
    return jsonify({
        'users': [u.to_dict() for u in users]
    }), 200


@dealers_bp.route('/<int:dealer_id>/connections', methods=['GET'])
@jwt_required()
@require_dealer_access
def get_dealer_connections(dealer_id):
    """Get ERP connections for a dealer."""
    connections = ERPConnection.query.filter_by(dealer_id=dealer_id).all()
    return jsonify({
        'connections': [c.to_dict() for c in connections]
    }), 200


@dealers_bp.route('/<int:dealer_id>/connections', methods=['POST'])
@jwt_required()
@require_dealer_access
def create_erp_connection(dealer_id):
    """Create a new ERP connection for a dealer."""
    user = get_current_user()
    if user.user_type != 'currie_admin':
        return jsonify({'error': 'Only Currie admins can create connections'}), 403

    data = request.get_json()

    connection = ERPConnection(
        dealer_id=dealer_id,
        erp_type=data.get('erp_type', 'softbase_evolution'),
        connection_method=data.get('connection_method', 'direct_db'),
        server=data.get('server'),
        database=data.get('database'),
        username=data.get('username'),
        # Note: Password should be encrypted before storing
        password_encrypted=data.get('password'),  # TODO: Encrypt this
        api_endpoint=data.get('api_endpoint'),
        sftp_host=data.get('sftp_host'),
        sftp_path=data.get('sftp_path')
    )

    db.session.add(connection)
    db.session.commit()

    return jsonify({
        'message': 'Connection created successfully',
        'connection': connection.to_dict()
    }), 201
