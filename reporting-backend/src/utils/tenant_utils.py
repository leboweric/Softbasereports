"""
Tenant utility functions for multi-tenant data isolation.

Super Admin users with roles in multiple organizations can pass ?org_id=<id>
on any tenant-scoped endpoint to override the default tenant context.  This
enables the AIOP Support Bot (and human Super Admins) to test and validate
data for any organization without needing to log in as that org's user.
"""
from flask import g, request
from flask_jwt_extended import get_jwt_identity
from src.models.user import User
import logging

logger = logging.getLogger(__name__)


def _resolve_org_for_request():
    """
    Determine which Organization object to use for the current request.

    1. If the request has an ``org_id`` query-parameter **and** the
       authenticated user holds a Super Admin role in multiple orgs,
       look up and return that organization instead of the user's own.
    2. Otherwise fall back to the user's own organization.

    Returns:
        (User, Organization) tuple

    Raises:
        ValueError: on auth / lookup failures
    """
    user_id = get_jwt_identity()
    if not user_id:
        raise ValueError("No authenticated user found")

    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")

    # Check for org_id override in query params
    requested_org_id = request.args.get('org_id', type=int) if request else None

    if requested_org_id and requested_org_id != getattr(user.organization, 'id', None):
        # Verify the user is a multi-org Super Admin
        super_admin_roles = [r for r in user.roles if r.name == 'Super Admin']
        if len(super_admin_roles) > 1:
            from src.models.user import Organization
            target_org = Organization.query.get(requested_org_id)
            if target_org:
                logger.info(
                    f"Tenant override: user {user_id} switching context "
                    f"from org {getattr(user.organization, 'id', '?')} "
                    f"to org {target_org.id} ({target_org.name})"
                )
                return user, target_org
            else:
                logger.warning(f"Tenant override requested org_id={requested_org_id} not found, using default")
        else:
            logger.warning(
                f"User {user_id} requested org_id={requested_org_id} "
                f"but is not a multi-org Super Admin — ignoring override"
            )

    if not user.organization:
        raise ValueError("User not associated with an organization")

    return user, user.organization


def get_tenant_schema():
    """
    Get the database schema for the current request's organization.

    Supports ``?org_id=`` override for multi-org Super Admins.

    Returns:
        str: The database schema name (e.g., 'ben002', 'ind004')

    Raises:
        ValueError: If user, organization, or schema is not found/configured
    """
    user, org = _resolve_org_for_request()

    schema = org.database_schema
    if not schema:
        raise ValueError(f"Database schema not configured for organization: {org.name}")

    logger.debug(f"Tenant schema resolved: {schema} for user {user.id} in org {org.name}")
    return schema


def get_tenant_schema_safe(default='ben002'):
    """
    Get the database schema with a fallback default.
    Use this only for backward compatibility during migration.

    Args:
        default: Default schema to use if not configured

    Returns:
        str: The database schema name
    """
    try:
        return get_tenant_schema()
    except ValueError as e:
        logger.warning(f"Using default schema '{default}': {str(e)}")
        return default


def get_tenant_db():
    """
    Get a database service configured with the current tenant's credentials.

    Supports ``?org_id=`` override for multi-org Super Admins so the bot
    can query any tenant's Azure SQL data.

    Returns:
        AzureSQLService: Database service configured with tenant-specific credentials

    Raises:
        ValueError: If user or organization is not found/configured
    """
    from src.services.azure_sql_service import AzureSQLService
    from src.services.credential_manager import get_credential_manager

    user, org = _resolve_org_for_request()

    # Create AzureSQLService instance
    service = AzureSQLService()

    # If organization has custom database credentials, use them
    logger.debug(f"[TENANT_DB] Org: {org.name}, db_server: {org.db_server}, db_username: {org.db_username}, has_password: {bool(org.db_password_encrypted)}")

    if org.db_server and org.db_username and org.db_password_encrypted:
        try:
            credential_manager = get_credential_manager()
            decrypted_password = credential_manager.decrypt_password(org.db_password_encrypted)

            # Override the default credentials with tenant-specific ones
            service.server = org.db_server
            service.database = org.db_name or 'evo'
            service.username = org.db_username
            service.password = decrypted_password

            logger.debug(f"[TENANT_DB] Using tenant credentials - Server: {service.server}, DB: {service.database}, User: {service.username}")
        except Exception as e:
            logger.error(f"[TENANT_DB] ERROR decrypting credentials for {org.name}: {str(e)}")
            logger.warning(f"[TENANT_DB] Falling back to default credentials")
    else:
        logger.debug(f"[TENANT_DB] Using default credentials for {org.name} (missing: server={not org.db_server}, user={not org.db_username}, pass={not org.db_password_encrypted})")

    return service


def get_db():
    """
    Alias for get_tenant_db() for backward compatibility.

    Returns:
        AzureSQLService: Database service configured with tenant-specific credentials
    """
    return get_tenant_db()
