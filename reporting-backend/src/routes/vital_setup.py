"""
One-time setup route for VITAL Worklife tenant
This can be called once to set up the organization and users, then removed.
"""
from flask import Blueprint, jsonify
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from src.models.user import db, Organization, User
from src.models.rbac import Role

vital_setup_bp = Blueprint('vital_setup', __name__)

@vital_setup_bp.route('/setup-vital-worklife', methods=['POST'])
def setup_vital_worklife():
    """
    One-time setup for VITAL Worklife organization and users.
    Call this endpoint once to create the tenant.
    """
    try:
        # Check if VITAL Worklife already exists
        existing_org = Organization.query.filter_by(name='VITAL Worklife').first()
        if existing_org:
            return jsonify({
                'message': 'VITAL Worklife organization already exists',
                'organization_id': existing_org.id
            }), 200
        
        # Create VITAL Worklife organization
        org = Organization(
            name='VITAL Worklife',
            platform_type='demo',  # Demo mode - no external DB connection needed
            subscription_status='trialing',
            trial_ends_at=datetime.utcnow() + timedelta(days=30),
            fiscal_year_start_month=1,  # January fiscal year
            is_active=True
        )
        db.session.add(org)
        db.session.flush()  # Get the org ID
        
        # Get or create Leadership role (for VITAL users)
        leadership_role = Role.query.filter_by(name='Leadership').first()
        super_admin_role = Role.query.filter_by(name='Super Admin').first()
        
        # VITAL Worklife users to create
        vital_users = [
            {'first_name': 'Dane', 'last_name': 'Jensen', 'email': 'dane.jensen@vitalworklife.com', 'is_admin': True},
            {'first_name': 'Grace', 'last_name': 'Lee', 'email': 'grace.lee@vitalworklife.com', 'is_admin': True},
            {'first_name': 'Adam', 'last_name': 'Frei', 'email': 'adam.frei@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Mitchell', 'last_name': 'Best', 'email': 'mitchell.best@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Aric', 'last_name': 'Bandy', 'email': 'aric.bandy@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Nicole', 'last_name': 'Hale', 'email': 'nicole.hale@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Lacey', 'last_name': 'Lefere', 'email': 'lacey.lefere@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Derek', 'last_name': 'Bell', 'email': 'derek.bell@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Eric', 'last_name': 'LeBow', 'email': 'eric.lebow@vitalworklife.com', 'is_admin': True},
        ]
        
        temp_password = 'VitalDemo2025!'
        created_users = []
        
        for user_data in vital_users:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email'].lower()).first()
            if existing_user:
                continue
            
            # Create user
            user = User(
                username=user_data['email'].lower(),
                email=user_data['email'].lower(),
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                password_hash=generate_password_hash(temp_password),
                organization_id=org.id,
                is_active=True,
                role='admin' if user_data['is_admin'] else 'user'
            )
            
            # Assign roles
            if user_data['is_admin'] and super_admin_role:
                user.roles.append(super_admin_role)
            elif leadership_role:
                user.roles.append(leadership_role)
            
            db.session.add(user)
            created_users.append(f"{user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
        
        db.session.commit()
        
        return jsonify({
            'message': 'VITAL Worklife setup complete',
            'organization_id': org.id,
            'organization_name': org.name,
            'users_created': created_users,
            'temporary_password': temp_password,
            'note': 'Users should change their password on first login'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': str(e),
            'message': 'Failed to set up VITAL Worklife'
        }), 500
