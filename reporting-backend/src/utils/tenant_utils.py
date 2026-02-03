"""
Tenant utility functions for multi-tenant data isolation.
"""
from flask import g
from flask_jwt_extended import get_jwt_identity
from src.models.user import User
import logging

logger = logging.getLogger(__name__)

def get_tenant_schema():
    """
    Get the database schema for the current authenticated user's organization.
    
    Returns:
        str: The database schema name (e.g., 'ben002', 'ind004')
        
    Raises:
        ValueError: If user, organization, or schema is not found/configured
    """
    user_id = get_jwt_identity()
    if not user_id:
        raise ValueError("No authenticated user found")
    
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    
    if not user.organization:
        raise ValueError("User not associated with an organization")
    
    schema = user.organization.database_schema
    if not schema:
        raise ValueError(f"Database schema not configured for organization: {user.organization.name}")
    
    logger.debug(f"Tenant schema resolved: {schema} for user {user_id} in org {user.organization.name}")
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
    
    This is the primary method for getting a database connection in multi-tenant routes.
    It uses the current authenticated user's organization to determine which database
    credentials to use.
    
    Returns:
        AzureSQLService: Database service configured with tenant-specific credentials
        
    Raises:
        ValueError: If user or organization is not found/configured
    """
    from src.services.azure_sql_service import AzureSQLService
    from src.services.credential_manager import get_credential_manager
    
    user_id = get_jwt_identity()
    if not user_id:
        raise ValueError("No authenticated user found")
    
    user = User.query.get(user_id)
    if not user:
        raise ValueError("User not found")
    
    if not user.organization:
        raise ValueError("User not associated with an organization")
    
    org = user.organization
    
    # Create AzureSQLService instance
    service = AzureSQLService()
    
    # If organization has custom database credentials, use them
    if org.db_server and org.db_username and org.db_password_encrypted:
        try:
            credential_manager = get_credential_manager()
            decrypted_password = credential_manager.decrypt_password(org.db_password_encrypted)
            
            # Override the default credentials with tenant-specific ones
            service.server = org.db_server
            service.database = org.db_name or 'evo'  # Default to 'evo' if not specified
            service.username = org.db_username
            service.password = decrypted_password
            
            logger.info(f"Using tenant-specific database credentials for {org.name}")
            logger.info(f"  Server: {service.server}")
            logger.info(f"  Database: {service.database}")
            logger.info(f"  Username: {service.username}")
        except Exception as e:
            logger.error(f"Failed to decrypt credentials for {org.name}: {str(e)}")
            # Fall back to default credentials
            logger.warning(f"Falling back to default credentials for {org.name}")
    else:
        logger.debug(f"Using default database credentials for {org.name} (no custom credentials configured)")
    
    return service


def get_db():
    """
    Alias for get_tenant_db() for backward compatibility.
    
    Returns:
        AzureSQLService: Database service configured with tenant-specific credentials
    """
    return get_tenant_db()
