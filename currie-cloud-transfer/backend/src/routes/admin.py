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


@admin_bp.route('/setup-dealer', methods=['POST'])
@jwt_required()
@require_currie_admin
def setup_dealer_with_erp():
    """
    Quick setup: Create a dealer with ERP connection in one call.
    Used for initial platform setup and testing.
    """
    data = request.get_json()

    # Validate required fields
    required = ['name', 'code', 'erp_type', 'server', 'database', 'username', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400

    # Check if dealer already exists
    existing = Dealer.query.filter_by(code=data['code']).first()
    if existing:
        return jsonify({'error': f"Dealer with code '{data['code']}' already exists", 'dealer_id': existing.id}), 400

    try:
        # Create dealer
        dealer = Dealer(
            name=data['name'],
            code=data['code'],
            contact_name=data.get('contact_name'),
            contact_email=data.get('contact_email'),
            erp_system=data['erp_type'],
            subscription_tier=data.get('subscription_tier', 'professional'),
            subscription_status='active',
            is_active=True
        )
        db.session.add(dealer)
        db.session.flush()  # Get dealer ID

        # Create ERP connection
        from src.models.core import ERPConnection
        connection = ERPConnection(
            dealer_id=dealer.id,
            erp_type=data['erp_type'],
            connection_method='direct_db',
            server=data['server'],
            database=data['database'],
            username=data['username'],
            password_encrypted=data['password'],  # TODO: Encrypt in production
            is_active=True
        )
        db.session.add(connection)
        db.session.commit()

        # Test connection
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
            test_result = adapter.test_connection()
            adapter.close()
            connection_status = test_result
        except Exception as e:
            connection_status = {'success': False, 'message': str(e)}

        return jsonify({
            'message': 'Dealer created successfully',
            'dealer': dealer.to_dict(),
            'connection_id': connection.id,
            'connection_test': connection_status
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create dealer: {str(e)}'}), 500


@admin_bp.route('/setup-bennett', methods=['POST'])
@jwt_required()
@require_currie_admin
def setup_bennett_quick():
    """
    Quick setup for Bennett Material Handling with pre-configured credentials.
    For testing the Currie Financial Model integration.
    """
    # Pre-configured Bennett credentials (same as Softbase Reports)
    bennett_config = {
        'name': 'Bennett Material Handling',
        'code': 'BENNETT',
        'erp_type': 'softbase_evolution',
        'server': 'evo1-sql-replica.database.windows.net',
        'database': 'evo',
        'username': 'ben002user',
        'password': 'g6O8CE5mT83mDYOW',
        'schema': 'ben002',
        'subscription_tier': 'professional'
    }

    # Check if already exists
    existing = Dealer.query.filter_by(code='BENNETT').first()
    if existing:
        # Return existing dealer info
        from src.models.core import ERPConnection
        connection = ERPConnection.query.filter_by(dealer_id=existing.id, is_active=True).first()
        return jsonify({
            'message': 'Bennett already configured',
            'dealer': existing.to_dict(),
            'connection_id': connection.id if connection else None
        }), 200

    try:
        # Create dealer
        dealer = Dealer(
            name=bennett_config['name'],
            code=bennett_config['code'],
            erp_system=bennett_config['erp_type'],
            subscription_tier=bennett_config['subscription_tier'],
            subscription_status='active',
            is_active=True
        )
        db.session.add(dealer)
        db.session.flush()

        # Create ERP connection
        from src.models.core import ERPConnection
        connection = ERPConnection(
            dealer_id=dealer.id,
            erp_type=bennett_config['erp_type'],
            connection_method='direct_db',
            server=bennett_config['server'],
            database=bennett_config['database'],
            username=bennett_config['username'],
            password_encrypted=bennett_config['password'],
            is_active=True
        )
        db.session.add(connection)
        db.session.commit()

        # Test connection
        try:
            adapter = AdapterFactory.get_adapter(
                bennett_config['erp_type'],
                {
                    'server': bennett_config['server'],
                    'database': bennett_config['database'],
                    'username': bennett_config['username'],
                    'password': bennett_config['password'],
                    'schema': bennett_config['schema']
                }
            )
            test_result = adapter.test_connection()
            adapter.close()
        except Exception as e:
            test_result = {'success': False, 'message': str(e)}

        return jsonify({
            'message': 'Bennett Material Handling configured successfully',
            'dealer': dealer.to_dict(),
            'connection_id': connection.id,
            'connection_test': test_result
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to setup Bennett: {str(e)}'}), 500
