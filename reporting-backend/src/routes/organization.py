from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.models.user import User, Organization, db
from src.middleware.tenant_middleware import TenantMiddleware
from datetime import datetime

organization_bp = Blueprint('organization', __name__)

@organization_bp.route('/info', methods=['GET'])
@TenantMiddleware.require_organization
def get_organization_info():
    """Get current organization information"""
    try:
        org_context = TenantMiddleware.get_organization_context()
        usage_limits = TenantMiddleware.get_usage_limits()
        
        # Get user count for the organization
        user_count = User.query.filter_by(organization_id=org_context['id']).count()
        
        # Get additional organization stats
        org_stats = {
            "current_users": user_count,
            "created_date": g.current_organization.created_at.isoformat() if hasattr(g.current_organization, 'created_at') else None,
            "last_activity": datetime.now().isoformat(),  # This would come from actual activity tracking
            "features_enabled": _get_enabled_features(org_context['subscription_tier'])
        }
        
        return jsonify({
            "success": True,
            "organization": org_context,
            "usage_limits": usage_limits,
            "stats": org_stats
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@organization_bp.route('/users', methods=['GET'])
@TenantMiddleware.require_organization
def get_organization_users():
    """Get all users in the current organization"""
    try:
        users = User.query.filter_by(organization_id=g.tenant_id).all()
        
        user_list = []
        for user in users:
            user_list.append({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "last_login": user.last_login.isoformat() if user.last_login else None
            })
        
        return jsonify({
            "success": True,
            "users": user_list,
            "total_count": len(user_list)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@organization_bp.route('/users', methods=['POST'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_feature('user_management')
def create_organization_user():
    """Create a new user in the current organization"""
    try:
        data = request.get_json()
        
        # Check user limit
        current_user_count = User.query.filter_by(organization_id=g.tenant_id).count()
        if not TenantMiddleware.check_usage_limit('max_users', current_user_count):
            return jsonify({
                "success": False,
                "error": "User limit reached for your subscription tier",
                "upgrade_required": True
            }), 403
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Check if username or email already exists
        existing_user = User.query.filter(
            (User.username == data['username']) | (User.email == data['email'])
        ).first()
        
        if existing_user:
            return jsonify({
                "success": False,
                "error": "Username or email already exists"
            }), 400
        
        # Create new user
        new_user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data.get('role', 'user'),
            organization_id=g.tenant_id,
            is_active=True,
            created_at=datetime.now()
        )
        new_user.set_password(data['password'])
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "User created successfully",
            "user_id": new_user.id
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@organization_bp.route('/users/<int:user_id>', methods=['PUT'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_feature('user_management')
def update_organization_user(user_id):
    """Update a user in the current organization"""
    try:
        user = User.query.filter_by(id=user_id, organization_id=g.tenant_id).first()
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        data = request.get_json()
        
        # Update allowed fields
        allowed_fields = ['first_name', 'last_name', 'email', 'role', 'is_active']
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # Handle password update separately
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "User updated successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@organization_bp.route('/users/<int:user_id>', methods=['DELETE'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_feature('user_management')
def delete_organization_user(user_id):
    """Delete a user from the current organization"""
    try:
        user = User.query.filter_by(id=user_id, organization_id=g.tenant_id).first()
        if not user:
            return jsonify({
                "success": False,
                "error": "User not found"
            }), 404
        
        # Prevent deleting the last admin user
        if user.role == 'admin':
            admin_count = User.query.filter_by(
                organization_id=g.tenant_id, 
                role='admin', 
                is_active=True
            ).count()
            if admin_count <= 1:
                return jsonify({
                    "success": False,
                    "error": "Cannot delete the last admin user"
                }), 400
        
        # Soft delete - just deactivate the user
        user.is_active = False
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "User deactivated successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@organization_bp.route('/settings', methods=['GET'])
@TenantMiddleware.require_organization
def get_organization_settings():
    """Get organization settings"""
    try:
        org = g.current_organization
        
        settings = {
            "name": org.name,
            "subscription_tier": org.subscription_tier,
            "max_users": org.max_users,
            "features": _get_enabled_features(org.subscription_tier),
            "usage_limits": TenantMiddleware.get_usage_limits(),
            "api_settings": {
                "softbase_api_enabled": False,  # This would be configurable
                "openai_integration_enabled": TenantMiddleware.check_feature_access('ai_queries_limited') or TenantMiddleware.check_feature_access('ai_queries_unlimited')
            }
        }
        
        return jsonify({
            "success": True,
            "settings": settings
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@organization_bp.route('/settings', methods=['PUT'])
@TenantMiddleware.require_organization
@TenantMiddleware.require_feature('organization_settings')
def update_organization_settings():
    """Update organization settings"""
    try:
        data = request.get_json()
        org = g.current_organization
        
        # Update allowed settings
        if 'name' in data:
            org.name = data['name']
        
        # Only allow subscription tier changes through proper upgrade process
        # This would typically be handled by a billing system
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Settings updated successfully"
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@organization_bp.route('/usage', methods=['GET'])
@TenantMiddleware.require_organization
def get_organization_usage():
    """Get organization usage statistics"""
    try:
        # This would typically come from a usage tracking system
        # For now, return mock data
        usage_data = {
            "current_period": {
                "reports_generated": 45,
                "ai_queries_used": 23,
                "data_exported_mb": 156,
                "active_users": User.query.filter_by(organization_id=g.tenant_id, is_active=True).count()
            },
            "limits": TenantMiddleware.get_usage_limits(),
            "period_start": "2024-01-01T00:00:00Z",
            "period_end": "2024-01-31T23:59:59Z"
        }
        
        return jsonify({
            "success": True,
            "usage": usage_data
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def _get_enabled_features(subscription_tier):
    """Get list of enabled features for subscription tier"""
    feature_matrix = {
        "basic": [
            "dashboard", "basic_reports", "csv_export", "user_management"
        ],
        "professional": [
            "dashboard", "basic_reports", "advanced_reports", 
            "csv_export", "excel_export", "pdf_export", "ai_queries_limited",
            "user_management", "organization_settings"
        ],
        "enterprise": [
            "dashboard", "basic_reports", "advanced_reports",
            "csv_export", "excel_export", "pdf_export", 
            "ai_queries_unlimited", "custom_reports", "api_access",
            "advanced_analytics", "white_label", "user_management",
            "organization_settings", "audit_logs", "sso"
        ]
    }
    
    return feature_matrix.get(subscription_tier, feature_matrix["basic"])

