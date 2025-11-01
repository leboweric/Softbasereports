from flask import Blueprint, request, jsonify, g
from src.middleware.tenant_middleware import TenantMiddleware
from src.models.user import Organization, User, db
from src.services.credential_manager import get_credential_manager
from src.services.platform_service_factory import PlatformServiceFactory
import logging

logger = logging.getLogger(__name__)

tenant_admin_bp = Blueprint('tenant_admin', __name__)

# ============================================================================
# LIST ALL ORGANIZATIONS
# ============================================================================

@tenant_admin_bp.route('/organizations', methods=['GET'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def list_organizations():
    """
    Get list of all organizations.
    Only accessible by Super Admins.
    """
    try:
        organizations = Organization.query.all()
        
        result = []
        for org in organizations:
            # Count users in this organization
            user_count = User.query.filter_by(organization_id=org.id).count()
            
            result.append({
                'id': org.id,
                'name': org.name,
                'platform_type': org.platform_type or 'evolution',
                'subscription_tier': org.subscription_tier or 'basic',
                'max_users': org.max_users or 5,
                'user_count': user_count,
                'is_active': org.is_active if org.is_active is not None else True,
                'created_at': org.created_at.isoformat() if org.created_at else None,
                'has_custom_db': bool(org.db_server)
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error listing organizations: {str(e)}")
        return jsonify({'message': 'Failed to list organizations', 'error': str(e)}), 500


# ============================================================================
# GET SINGLE ORGANIZATION
# ============================================================================

@tenant_admin_bp.route('/organizations/<int:org_id>', methods=['GET'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def get_organization(org_id):
    """
    Get details of a specific organization.
    Does NOT return the decrypted password for security.
    """
    try:
        org = Organization.query.get(org_id)
        
        if not org:
            return jsonify({'message': 'Organization not found'}), 404
        
        # Count users
        user_count = User.query.filter_by(organization_id=org.id).count()
        
        return jsonify({
            'id': org.id,
            'name': org.name,
            'platform_type': org.platform_type or 'evolution',
            'db_server': org.db_server,
            'db_name': org.db_name,
            'db_username': org.db_username,
            # NEVER return decrypted password
            'has_password': bool(org.db_password_encrypted),
            'subscription_tier': org.subscription_tier or 'basic',
            'max_users': org.max_users or 5,
            'user_count': user_count,
            'is_active': org.is_active if org.is_active is not None else True,
            'created_at': org.created_at.isoformat() if org.created_at else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting organization {org_id}: {str(e)}")
        return jsonify({'message': 'Failed to get organization', 'error': str(e)}), 500


# ============================================================================
# CREATE NEW ORGANIZATION
# ============================================================================

@tenant_admin_bp.route('/organizations', methods=['POST'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def create_organization():
    """
    Create a new organization with database credentials.
    Encrypts the password before storing.
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'platform_type']
        for field in required_fields:
            if field not in data:
                return jsonify({'message': f'Missing required field: {field}'}), 400
        
        # Check if organization name already exists
        existing = Organization.query.filter_by(name=data['name']).first()
        if existing:
            return jsonify({'message': 'Organization with this name already exists'}), 409
        
        # Create new organization
        new_org = Organization(
            name=data['name'],
            platform_type=data['platform_type'],
            db_server=data.get('db_server'),
            db_name=data.get('db_name'),
            db_username=data.get('db_username'),
            subscription_tier=data.get('subscription_tier', 'basic'),
            max_users=data.get('max_users', 5),
            is_active=True
        )
        
        # Encrypt password if provided
        if data.get('db_password'):
            credential_manager = get_credential_manager()
            new_org.db_password_encrypted = credential_manager.encrypt_password(data['db_password'])
        
        db.session.add(new_org)
        db.session.commit()
        
        logger.info(f"Created new organization: {new_org.name} (ID: {new_org.id})")
        
        return jsonify({
            'id': new_org.id,
            'name': new_org.name,
            'message': 'Organization created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating organization: {str(e)}")
        return jsonify({'message': 'Failed to create organization', 'error': str(e)}), 500


# ============================================================================
# UPDATE ORGANIZATION
# ============================================================================

@tenant_admin_bp.route('/organizations/<int:org_id>', methods=['PUT'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def update_organization(org_id):
    """
    Update an existing organization.
    Can update credentials, subscription tier, etc.
    """
    try:
        org = Organization.query.get(org_id)
        
        if not org:
            return jsonify({'message': 'Organization not found'}), 404
        
        data = request.get_json()
        
        # Update fields if provided
        if 'name' in data:
            # Check if new name conflicts with another org
            existing = Organization.query.filter(
                Organization.name == data['name'],
                Organization.id != org_id
            ).first()
            if existing:
                return jsonify({'message': 'Organization name already exists'}), 409
            org.name = data['name']
        
        if 'platform_type' in data:
            org.platform_type = data['platform_type']
        
        if 'db_server' in data:
            org.db_server = data['db_server']
        
        if 'db_name' in data:
            org.db_name = data['db_name']
        
        if 'db_username' in data:
            org.db_username = data['db_username']
        
        # Encrypt new password if provided
        if 'db_password' in data and data['db_password']:
            credential_manager = get_credential_manager()
            org.db_password_encrypted = credential_manager.encrypt_password(data['db_password'])
        
        if 'subscription_tier' in data:
            org.subscription_tier = data['subscription_tier']
        
        if 'max_users' in data:
            org.max_users = data['max_users']
        
        if 'is_active' in data:
            org.is_active = data['is_active']
        
        db.session.commit()
        
        logger.info(f"Updated organization: {org.name} (ID: {org.id})")
        
        return jsonify({
            'id': org.id,
            'name': org.name,
            'message': 'Organization updated successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating organization {org_id}: {str(e)}")
        return jsonify({'message': 'Failed to update organization', 'error': str(e)}), 500


# ============================================================================
# DELETE/DEACTIVATE ORGANIZATION
# ============================================================================

@tenant_admin_bp.route('/organizations/<int:org_id>', methods=['DELETE'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def delete_organization(org_id):
    """
    Soft delete (deactivate) an organization.
    Does not actually delete from database to preserve data integrity.
    """
    try:
        org = Organization.query.get(org_id)
        
        if not org:
            return jsonify({'message': 'Organization not found'}), 404
        
        # Soft delete by setting is_active to False
        org.is_active = False
        db.session.commit()
        
        logger.info(f"Deactivated organization: {org.name} (ID: {org.id})")
        
        return jsonify({
            'message': 'Organization deactivated successfully',
            'id': org.id,
            'name': org.name
        }), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deactivating organization {org_id}: {str(e)}")
        return jsonify({'message': 'Failed to deactivate organization', 'error': str(e)}), 500


# ============================================================================
# TEST DATABASE CONNECTION
# ============================================================================

@tenant_admin_bp.route('/organizations/<int:org_id>/test-connection', methods=['POST'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def test_connection(org_id):
    """
    Test if the database credentials for an organization work.
    Attempts to connect and run a simple query.
    """
    try:
        org = Organization.query.get(org_id)
        
        if not org:
            return jsonify({'message': 'Organization not found'}), 404
        
        # Check if organization has database credentials
        if not org.db_server or not org.db_username or not org.db_password_encrypted:
            return jsonify({
                'success': False,
                'message': 'Organization does not have database credentials configured'
            }), 400
        
        # Get platform service for this organization
        import time
        start_time = time.time()
        
        try:
            service = PlatformServiceFactory.get_service(org)
            
            # Try to execute a simple query
            result = service.get_monthly_sales(months=1)
            
            latency_ms = int((time.time() - start_time) * 1000)
            
            if result is not None:
                return jsonify({
                    'success': True,
                    'message': 'Connection successful',
                    'details': {
                        'server': org.db_server,
                        'database': org.db_name,
                        'latency_ms': latency_ms,
                        'test_query_results': len(result) if isinstance(result, list) else 'N/A'
                    }
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'message': 'Connection established but query returned no results'
                }), 500
                
        except Exception as conn_error:
            return jsonify({
                'success': False,
                'message': 'Connection failed',
                'error': str(conn_error)
            }), 500
        
    except Exception as e:
        logger.error(f"Error testing connection for organization {org_id}: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to test connection',
            'error': str(e)
        }), 500


# ============================================================================
# GET ORGANIZATION USERS
# ============================================================================

@tenant_admin_bp.route('/organizations/<int:org_id>/users', methods=['GET'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def get_organization_users(org_id):
    """
    Get list of all users in a specific organization.
    """
    try:
        org = Organization.query.get(org_id)
        
        if not org:
            return jsonify({'message': 'Organization not found'}), 404
        
        users = User.query.filter_by(organization_id=org_id).all()
        
        result = []
        for user in users:
            roles = [role.name for role in user.roles]
            
            result.append({
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'roles': roles,
                'is_active': user.is_active if hasattr(user, 'is_active') else True,
                'last_login': user.last_login.isoformat() if hasattr(user, 'last_login') and user.last_login else None
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"Error getting users for organization {org_id}: {str(e)}")
        return jsonify({'message': 'Failed to get organization users', 'error': str(e)}), 500


# ============================================================================
# GET SUPPORTED PLATFORMS
# ============================================================================

@tenant_admin_bp.route('/platforms', methods=['GET'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_super_admin
def get_supported_platforms():
    """
    Get list of supported platform types.
    """
    try:
        platforms = PlatformServiceFactory.get_supported_platforms()
        
        return jsonify({
            'platforms': platforms,
            'default': 'evolution'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting supported platforms: {str(e)}")
        return jsonify({'message': 'Failed to get supported platforms', 'error': str(e)}), 500