from functools import wraps
from flask import request, jsonify, g
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from src.models.user import User, Organization

class TenantMiddleware:
    """Middleware to handle multi-tenant organization isolation"""
    
    @staticmethod
    def require_organization(f):
        """Decorator to ensure user belongs to an organization and set tenant context"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Verify JWT token
                verify_jwt_in_request()
                user_id = get_jwt_identity()
                
                # Get user and organization
                user = User.query.get(user_id)
                if not user:
                    return jsonify({"error": "User not found"}), 404
                
                if not user.organization_id:
                    return jsonify({"error": "User not associated with an organization"}), 403
                
                organization = Organization.query.get(user.organization_id)
                if not organization:
                    return jsonify({"error": "Organization not found"}), 404
                
                if not organization.is_active:
                    return jsonify({"error": "Organization is inactive"}), 403
                
                # Set tenant context in Flask's g object
                g.current_user = user
                g.current_organization = organization
                g.tenant_id = organization.id
                
                return f(*args, **kwargs)
                
            except Exception as e:
                return jsonify({"error": f"Authentication error: {str(e)}"}), 401
        
        return decorated_function
    
    @staticmethod
    def get_tenant_filter():
        """Get SQL filter for current tenant"""
        if hasattr(g, 'tenant_id'):
            return f"organization_id = {g.tenant_id}"
        return None
    
    @staticmethod
    def apply_tenant_filter(query, model_class):
        """Apply tenant filter to SQLAlchemy query"""
        if hasattr(g, 'tenant_id') and hasattr(model_class, 'organization_id'):
            return query.filter(model_class.organization_id == g.tenant_id)
        return query
    
    @staticmethod
    def get_organization_context():
        """Get current organization context"""
        if hasattr(g, 'current_organization'):
            return {
                "id": g.current_organization.id,
                "name": g.current_organization.name,
                "subscription_tier": g.current_organization.subscription_tier,
                "max_users": g.current_organization.max_users,
                "is_active": g.current_organization.is_active
            }
        return None
    
    @staticmethod
    def check_feature_access(feature_name):
        """Check if current organization has access to a feature"""
        if not hasattr(g, 'current_organization'):
            return False
        
        org = g.current_organization
        
        # Define feature access by subscription tier
        feature_matrix = {
            "basic": [
                "dashboard", "basic_reports", "csv_export"
            ],
            "professional": [
                "dashboard", "basic_reports", "advanced_reports", 
                "csv_export", "excel_export", "pdf_export", "ai_queries_limited"
            ],
            "enterprise": [
                "dashboard", "basic_reports", "advanced_reports",
                "csv_export", "excel_export", "pdf_export", 
                "ai_queries_unlimited", "custom_reports", "api_access",
                "advanced_analytics", "white_label"
            ]
        }
        
        tier_features = feature_matrix.get(org.subscription_tier, [])
        return feature_name in tier_features
    
    @staticmethod
    def require_feature(feature_name):
        """Decorator to require specific feature access"""
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not TenantMiddleware.check_feature_access(feature_name):
                    return jsonify({
                        "error": f"Feature '{feature_name}' not available in your subscription tier",
                        "current_tier": g.current_organization.subscription_tier if hasattr(g, 'current_organization') else None,
                        "upgrade_required": True
                    }), 403
                
                return f(*args, **kwargs)
            return decorated_function
        return decorator
    
    @staticmethod
    def get_usage_limits():
        """Get usage limits for current organization"""
        if not hasattr(g, 'current_organization'):
            return {}
        
        org = g.current_organization
        
        limits = {
            "basic": {
                "max_users": 5,
                "max_reports_per_month": 100,
                "max_ai_queries_per_month": 50,
                "max_data_export_size_mb": 10
            },
            "professional": {
                "max_users": 25,
                "max_reports_per_month": 1000,
                "max_ai_queries_per_month": 500,
                "max_data_export_size_mb": 100
            },
            "enterprise": {
                "max_users": -1,  # Unlimited
                "max_reports_per_month": -1,  # Unlimited
                "max_ai_queries_per_month": -1,  # Unlimited
                "max_data_export_size_mb": 1000
            }
        }
        
        return limits.get(org.subscription_tier, limits["basic"])
    
    @staticmethod
    def check_usage_limit(limit_type, current_usage=0):
        """Check if usage is within limits"""
        limits = TenantMiddleware.get_usage_limits()
        limit_value = limits.get(limit_type, 0)
        
        # -1 means unlimited
        if limit_value == -1:
            return True
        
        return current_usage < limit_value
    
    @staticmethod
    def get_tenant_database_config():
        """Get database configuration for current tenant"""
        if not hasattr(g, 'current_organization'):
            return None
        
        org = g.current_organization
        
        # For now, all tenants use the same database with organization_id filtering
        # In the future, this could be extended to support separate databases per tenant
        return {
            "type": "shared",
            "organization_id": org.id,
            "schema_prefix": f"org_{org.id}_",
            "isolation_level": "row_level"
        }
    
    @staticmethod
    def require_super_admin(f):
        """
        Decorator to require Super Admin role for accessing an endpoint.
        Must be used after @require_organization decorator.
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify JWT is present
            verify_jwt_in_request()

            # Get current user from context (set by @require_organization)
            current_user = g.get('current_user')

            if not current_user:
                return jsonify({'message': 'User not found'}), 401

            # Check if user has Super Admin role
            user_roles = [role.name for role in current_user.roles]

            if 'Super Admin' not in user_roles:
                return jsonify({
                    'message': 'Access denied. Super Admin role required.',
                    'required_role': 'Super Admin',
                    'your_roles': user_roles
                }), 403

            return f(*args, **kwargs)

        return decorated_function

    @staticmethod
    def require_active_subscription(f):
        """
        Decorator to require an active subscription (paid or trial).
        Must be used after @require_organization decorator or @jwt_required.
        """
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Verify JWT is present
            verify_jwt_in_request()

            # Get user and organization
            user_id = get_jwt_identity()
            user = User.query.get(user_id)

            if not user:
                return jsonify({'message': 'User not found'}), 401

            organization = Organization.query.get(user.organization_id)
            if not organization:
                return jsonify({'message': 'Organization not found'}), 404

            # Check subscription status
            if not organization.has_active_subscription():
                return jsonify({
                    'error': 'subscription_required',
                    'message': 'Your subscription has expired or is inactive. Please subscribe to continue using the application.',
                    'subscription_status': organization.subscription_status,
                    'subscription_ends_at': organization.subscription_ends_at.isoformat() if organization.subscription_ends_at else None
                }), 402  # 402 Payment Required

            return f(*args, **kwargs)

        return decorated_function

