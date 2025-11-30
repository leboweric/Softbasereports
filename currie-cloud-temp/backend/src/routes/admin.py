"""
Admin Routes

Currie corporate administration endpoints.
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from src.models.database import db
from src.models.core import Dealer, User, Role, DataSyncJob
from src.adapters.adapter_factory import AdapterFactory

admin_bp = Blueprint('admin', __name__)


def require_currie_admin(f):
    """Decorator to require Currie admin role."""
    from functools import wraps

    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.user_type != 'currie_admin':
            return jsonify({'error': 'Currie admin access required'}), 403

        return f(*args, **kwargs)

    return decorated


@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@require_currie_admin
def get_admin_dashboard():
    """Get admin dashboard statistics."""
    total_dealers = Dealer.query.filter_by(is_active=True).count()
    total_users = User.query.filter_by(is_active=True).count()

    # Subscription breakdown
    subscription_counts = db.session.query(
        Dealer.subscription_tier,
        db.func.count(Dealer.id)
    ).filter_by(is_active=True).group_by(Dealer.subscription_tier).all()

    # Recent sync jobs
    recent_syncs = DataSyncJob.query.order_by(
        DataSyncJob.created_at.desc()
    ).limit(10).all()

    return jsonify({
        'stats': {
            'total_dealers': total_dealers,
            'total_users': total_users,
            'subscriptions': {tier: count for tier, count in subscription_counts}
        },
        'recent_syncs': [s.to_dict() for s in recent_syncs]
    }), 200


@admin_bp.route('/dealers', methods=['GET'])
@jwt_required()
@require_currie_admin
def get_all_dealers():
    """Get all dealers with detailed info."""
    dealers = Dealer.query.all()

    result = []
    for dealer in dealers:
        dealer_dict = dealer.to_dict()
        dealer_dict['user_count'] = dealer.users.count()
        dealer_dict['last_sync'] = None

        # Get last sync
        last_sync = DataSyncJob.query.filter_by(
            dealer_id=dealer.id
        ).order_by(DataSyncJob.created_at.desc()).first()

        if last_sync:
            dealer_dict['last_sync'] = last_sync.to_dict()

        result.append(dealer_dict)

    return jsonify({'dealers': result}), 200


@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@require_currie_admin
def get_all_users():
    """Get all users across all dealers."""
    users = User.query.all()
    return jsonify({
        'users': [u.to_dict() for u in users]
    }), 200


@admin_bp.route('/roles', methods=['GET'])
@jwt_required()
@require_currie_admin
def get_roles():
    """Get all available roles."""
    roles = Role.query.all()
    return jsonify({
        'roles': [r.to_dict() for r in roles]
    }), 200


@admin_bp.route('/roles', methods=['POST'])
@jwt_required()
@require_currie_admin
def create_role():
    """Create a new role."""
    data = request.get_json()

    if not data.get('name'):
        return jsonify({'error': 'Role name is required'}), 400

    if Role.query.filter_by(name=data['name']).first():
        return jsonify({'error': 'Role name already exists'}), 400

    role = Role(
        name=data['name'],
        description=data.get('description', ''),
        permissions=data.get('permissions', [])
    )

    db.session.add(role)
    db.session.commit()

    return jsonify({
        'message': 'Role created',
        'role': role.to_dict()
    }), 201


@admin_bp.route('/erp-types', methods=['GET'])
@jwt_required()
@require_currie_admin
def get_supported_erp_types():
    """Get list of supported ERP system types."""
    return jsonify({
        'erp_types': AdapterFactory.get_supported_types()
    }), 200


@admin_bp.route('/test-connection', methods=['POST'])
@jwt_required()
@require_currie_admin
def test_erp_connection():
    """Test an ERP connection configuration."""
    data = request.get_json()

    required = ['erp_type', 'server', 'database', 'username', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    try:
        adapter = AdapterFactory.get_adapter(
            data['erp_type'],
            {
                'server': data['server'],
                'database': data['database'],
                'username': data['username'],
                'password': data['password'],
                'schema': data.get('schema', 'ben002')
            }
        )

        result = adapter.test_connection()
        adapter.close()

        return jsonify(result), 200 if result['success'] else 400

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': f'Connection test failed: {str(e)}'}), 500
