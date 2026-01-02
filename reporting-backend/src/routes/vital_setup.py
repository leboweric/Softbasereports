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
            
            # Assign role
            if user_data['is_admin'] and vital_admin_role:
                user.roles.append(vital_admin_role)
            elif vital_user_role:
                user.roles.append(vital_user_role)
            
            db.session.add(user)
            created_users.append(f"{user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'VITAL Worklife setup complete',
            'organization': {
                'id': org.id,
                'name': org.name,
                'created': org_created
            },
            'users_created': created_users,
            'users_updated': updated_users,
            'users_skipped': skipped_users,
            'temp_password': temp_password
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vital_setup_bp.route('/update-vital-roles', methods=['POST', 'GET'])
def update_vital_roles():
    """Update VITAL users to have VITAL Admin/User roles"""
    try:
        vital_admin_role = Role.query.filter_by(name='VITAL Admin').first()
        vital_user_role = Role.query.filter_by(name='VITAL User').first()
        
        if not vital_admin_role or not vital_user_role:
            return jsonify({'error': 'VITAL roles not found'}), 404
        
        # Get all VITAL users (organization_id = 6)
        vital_users = User.query.filter_by(organization_id=6).all()
        
        updated = []
        for user in vital_users:
            # Clear existing roles
            user.roles.clear()
            
            # Assign VITAL Admin to admins, VITAL User to others
            if user.email in ['dane.jensen@vitalworklife.com', 'grace.lee@vitalworklife.com', 'eric.lebow@vitalworklife.com']:
                user.roles.append(vital_admin_role)
                updated.append(f"{user.first_name} {user.last_name} -> VITAL Admin")
            else:
                user.roles.append(vital_user_role)
                updated.append(f"{user.first_name} {user.last_name} -> VITAL User")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_users': updated
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@vital_setup_bp.route('/update-org-logos', methods=['POST', 'GET'])
def update_org_logos():
    """
    Update organization logos with CDN URLs.
    """
    try:
        bennett_logo_url = "https://files.manuscdn.com/user_upload_by_module/session_file/112395888/fQukILbpeKwYoxYP.webp"
        vital_logo_url = "https://files.manuscdn.com/user_upload_by_module/session_file/112395888/ejZUzfwNYvRJiFhg.webp"
        
        bennett = Organization.query.filter_by(name='Bennett Material Handling').first()
        vital = Organization.query.filter_by(name='VITAL Worklife').first()
        
        updated_orgs = []
        
        if bennett:
            bennett.logo_url = bennett_logo_url
            updated_orgs.append("Bennett Material Handling")
            
        if vital:
            vital.logo_url = vital_logo_url
            updated_orgs.append("VITAL Worklife")
            
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_orgs': updated_orgs,
            'message': 'Organization logos updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@vital_setup_bp.route('/assign-roles-to-orgs', methods=['POST', 'GET'])
def assign_roles_to_orgs():
    """
    Assign organization_id to existing roles.
    Bennett roles -> org 4
    VITAL roles -> org 6
    """
    try:
        # Bennett Material Handling roles (org 4)
        bennett_role_names = [
            'Super Admin', 'Leadership', 'Accounting Manager', 'Parts Manager',
            'Service Manager', 'Rental Manager', 'Parts Staff', 'Parts User',
            'Service Tech', 'Sales Rep', 'Accounting User', 'Read Only',
            'Service User', 'Sales Manager'
        ]
        
        # VITAL Worklife roles (org 6)
        vital_role_names = ['VITAL Admin', 'VITAL User']
        
        updated_roles = []
        
        # Assign Bennett roles to org 4 (force update)
        for role_name in bennett_role_names:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                role.organization_id = 4  # Bennett Material Handling
                updated_roles.append(f"{role_name} -> Bennett (org 4)")
        
        # Assign VITAL roles to org 6 (force update)
        for role_name in vital_role_names:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                role.organization_id = 6  # VITAL Worklife
                updated_roles.append(f"{role_name} -> VITAL (org 6)")
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'updated_roles': updated_roles,
            'message': 'Roles assigned to organizations successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
