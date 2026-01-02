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
        org = Organization.query.filter_by(name='VITAL Worklife').first()
        org_created = False
        
        if not org:
            # Create VITAL Worklife organization
            org = Organization(
                name='VITAL Worklife',
                platform_type='demo',  # Demo mode - no external DB connection needed
                subscription_status='active',  # No trial - full access
                fiscal_year_start_month=1,  # January fiscal year
                is_active=True
            )
            db.session.add(org)
            db.session.flush()  # Get the org ID
            org_created = True
        
        # Get or create VITAL Admin role
        vital_admin_role = Role.query.filter_by(name='VITAL Admin').first()
        vital_user_role = Role.query.filter_by(name='VITAL User').first()
        
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
        updated_users = []
        skipped_users = []
        
        for user_data in vital_users:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email'].lower()).first()
            if existing_user:
                # Update existing user's roles to VITAL roles
                existing_user.roles.clear()
                if user_data['is_admin'] and vital_admin_role:
                    existing_user.roles.append(vital_admin_role)
                elif vital_user_role:
                    existing_user.roles.append(vital_user_role)
                updated_users.append(f"{user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
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
            
            # Assign VITAL roles
            if user_data['is_admin'] and vital_admin_role:
                user.roles.append(vital_admin_role)
            elif vital_user_role:
                user.roles.append(vital_user_role)
            
            db.session.add(user)
            created_users.append(f"{user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
        
        db.session.commit()
        
        return jsonify({
            'message': 'VITAL Worklife setup complete',
            'organization_id': org.id,
            'organization_name': org.name,
            'organization_created': org_created,
            'users_created': created_users,
            'users_updated': updated_users,
            'users_skipped': skipped_users,
            'temporary_password': temp_password if created_users else None,
            'note': 'Users should change their password on first login' if created_users else 'Existing users updated with VITAL roles'
        }), 201 if created_users or org_created else 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc(),
            'message': 'Failed to set up VITAL Worklife'
        }), 500


@vital_setup_bp.route('/update-vital-roles', methods=['GET', 'POST'])
def update_vital_roles():
    """
    Update existing VITAL users to use VITAL Admin/User roles instead of generic roles.
    """
    try:
        # Get VITAL roles
        vital_admin_role = Role.query.filter_by(name='VITAL Admin').first()
        vital_user_role = Role.query.filter_by(name='VITAL User').first()
        
        if not vital_admin_role or not vital_user_role:
            return jsonify({
                'error': 'VITAL roles not found. Please ensure RBAC is initialized.',
                'vital_admin_exists': vital_admin_role is not None,
                'vital_user_exists': vital_user_role is not None
            }), 400
        
        # Get VITAL Worklife organization
        org = Organization.query.filter_by(name='VITAL Worklife').first()
        if not org:
            return jsonify({'error': 'VITAL Worklife organization not found'}), 404
        
        # Admin emails
        admin_emails = [
            'dane.jensen@vitalworklife.com',
            'grace.lee@vitalworklife.com',
            'eric.lebow@vitalworklife.com'
        ]
        
        updated_users = []
        
        # Update all users in VITAL organization
        users = User.query.filter_by(organization_id=org.id).all()
        for user in users:
            user.roles.clear()
            if user.email.lower() in admin_emails:
                user.roles.append(vital_admin_role)
                updated_users.append(f"{user.first_name} {user.last_name} -> VITAL Admin")
            else:
                user.roles.append(vital_user_role)
                updated_users.append(f"{user.first_name} {user.last_name} -> VITAL User")
        
        db.session.commit()
        
        return jsonify({
            'message': 'VITAL user roles updated',
            'updated_users': updated_users
        }), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500
