"""Diagnostic endpoint to check users in database"""
from flask import Blueprint, jsonify
from flask_cors import cross_origin
from flask_jwt_extended import jwt_required
from src.models.user import db, User, Organization
from src.models.rbac import Role, user_roles

user_diagnostic_bp = Blueprint('user_diagnostic', __name__)

@user_diagnostic_bp.route('/api/diagnostic/users', methods=['GET'])
@cross_origin()
@jwt_required()
def diagnose_users():
    """Check what users exist in the database"""
    try:
        # Get ALL users without any filtering
        all_users = User.query.all()
        
        # Get organizations
        all_orgs = Organization.query.all()
        
        # Check user_roles table
        user_role_count = db.session.execute(db.text('SELECT COUNT(*) FROM user_roles')).scalar()
        
        # Check specific users
        elebow = User.query.filter_by(username='elebow@bmhmn.com').first()
        jchristensen = User.query.filter_by(username='jchristensen@bmhmn.com').first()
        
        # Check if there's an elebow without full email
        elebow_short = User.query.filter_by(username='elebow').first()
        
        return jsonify({
            'total_users': len(all_users),
            'users': [
                {
                    'id': u.id,
                    'username': u.username,
                    'email': u.email,
                    'organization_id': u.organization_id,
                    'roles': [r.name for r in u.roles] if u.roles else []
                } for u in all_users
            ],
            'organizations': [
                {
                    'id': o.id,
                    'name': o.name
                } for o in all_orgs
            ],
            'user_roles_count': user_role_count,
            'specific_users': {
                'elebow@bmhmn.com': elebow.username if elebow else 'NOT FOUND',
                'jchristensen@bmhmn.com': jchristensen.username if jchristensen else 'NOT FOUND',
                'elebow': elebow_short.username if elebow_short else 'NOT FOUND'
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500