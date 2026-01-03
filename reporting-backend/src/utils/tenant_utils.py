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
        str: The database schema name (e.g., 'ben002', 'vital001')
        
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
