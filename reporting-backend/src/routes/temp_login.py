"""Temporary login bypass for testing"""
from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import create_access_token
from datetime import datetime, timedelta
from src.models.user import db, User

temp_login_bp = Blueprint('temp_login', __name__)

@temp_login_bp.route('/api/auth/temp-login', methods=['POST'])
@cross_origin()
def temp_login():
    """Temporary login that bypasses password check"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        # Check if it's one of our users and the password is abc123
        if username in ['elebow@bmhmn.com', 'jchristensen@bmhmn.com'] and password == 'abc123':
            user = User.query.filter_by(username=username).first()
            
            if user and user.is_active:
                # Update last login
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                # Generate JWT token
                access_token = create_access_token(
                    identity=str(user.id),
                    expires_delta=timedelta(hours=24),
                    additional_claims={
                        'user_id': user.id,
                        'organization_id': user.organization_id,
                        'role': user.role
                    }
                )
                
                # Get permissions and departments
                permissions = []
                
                # Check if user is Super Admin - if so, give all permissions
                is_super_admin = any(r.name == 'Super Admin' for r in user.roles)
                if is_super_admin:
                    # Super Admin gets all permissions
                    permissions = ['*', 'manage_users', 'view_dashboard', 'view_service', 
                                 'view_parts', 'view_rental', 'view_accounting', 
                                 'view_minitrac', 'use_ai_query', 'use_report_creator',
                                 'view_database_explorer', 'view_users']
                else:
                    # Regular users get permissions from their roles
                    for role in user.roles:
                        for permission in role.permissions:
                            if permission.name not in permissions:
                                permissions.append(permission.name)
                
                accessible_departments = user.get_accessible_departments()
                
                return jsonify({
                    'token': access_token,
                    'user': user.to_dict(),
                    'organization': user.organization.to_dict() if user.organization else None,
                    'permissions': permissions,
                    'accessible_departments': accessible_departments
                }), 200
        
        return jsonify({'message': 'Invalid credentials'}), 401
        
    except Exception as e:
        return jsonify({'message': f'Login error: {str(e)}'}), 500