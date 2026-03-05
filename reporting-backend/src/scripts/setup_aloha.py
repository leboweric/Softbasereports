"""
Script to set up Aloha Holdings as a new tenant in AIOP
Aloha is a Hawaii-based holding company with 3 subsidiary companies,
each running their own SAP ERP system.

Run with: python -m src.scripts.setup_aloha
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta


def setup_aloha():
    """Set up Aloha Holdings organization and initial users"""
    
    # Create minimal Flask app for database context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    from src.models.user import db, Organization, User
    from src.models.rbac import Role
    
    db.init_app(app)
    
    with app.app_context():
        # Check if Aloha Holdings already exists
        existing_org = Organization.query.filter_by(name='Aloha Holdings').first()
        if existing_org:
            print(f"Aloha Holdings organization already exists (ID: {existing_org.id})")
            org = existing_org
        else:
            # Create Aloha Holdings organization
            org = Organization(
                name='Aloha Holdings',
                platform_type='sap',  # SAP ERP multi-source
                subscription_status='active',
                fiscal_year_start_month=1,  # January fiscal year (update if different)
                is_active=True,
                settings='{"data_sources": {"sap_sandia_plastics": {"name": "Sandia Plastics", "connected": false, "system_type": "", "connection_method": "", "host": "", "port": "", "client": "", "system_number": "", "username": "", "password": ""}, "sap_kauai_exclusive": {"name": "Kauai Exclusive", "connected": false, "system_type": "", "connection_method": "", "host": "", "port": "", "client": "", "system_number": "", "username": "", "password": ""}, "sap_hawaii_care": {"name": "Hawaii Care & Cleaning", "connected": false, "system_type": "", "connection_method": "", "host": "", "port": "", "client": "", "system_number": "", "username": "", "password": ""}}}'
            )
            db.session.add(org)
            db.session.commit()
            print(f"Created Aloha Holdings organization (ID: {org.id})")
        
        # Get or create Aloha Admin role
        aloha_admin_role = Role.query.filter_by(name='Aloha Admin').first()
        if not aloha_admin_role:
            aloha_admin_role = Role(
                name='Aloha Admin',
                description='Aloha Holdings administrator with full access to all subsidiary data',
                department='Administration',
                organization_id=org.id,
                is_active=True
            )
            db.session.add(aloha_admin_role)
            db.session.commit()
            print(f"Created Aloha Admin role (ID: {aloha_admin_role.id})")
        
        # Get or create Aloha User role
        aloha_user_role = Role.query.filter_by(name='Aloha User').first()
        if not aloha_user_role:
            aloha_user_role = Role(
                name='Aloha User',
                description='Aloha Holdings standard user with view access to subsidiary data',
                department='Operations',
                organization_id=org.id,
                is_active=True
            )
            db.session.add(aloha_user_role)
            db.session.commit()
            print(f"Created Aloha User role (ID: {aloha_user_role.id})")
        
        # Aloha Holdings users to create
        # Update these with actual user details when available
        aloha_users = [
            {'first_name': 'Eric', 'last_name': 'LeBow', 'email': 'elebow@aloha.com', 'is_admin': True},
            {'first_name': 'J', 'last_name': 'Foos', 'email': 'jfoos@aloha.com', 'is_admin': True},
            {'first_name': 'C', 'last_name': 'Shannon', 'email': 'cshannon@aloha.com', 'is_admin': True},
        ]
        
        temp_password = 'abc123'
        
        for user_data in aloha_users:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email'].lower()).first()
            if existing_user:
                print(f"User {user_data['email']} already exists (ID: {existing_user.id})")
                # Update org assignment if needed
                if existing_user.organization_id != org.id:
                    print(f"  Note: User is in org {existing_user.organization_id}, not Aloha ({org.id})")
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
            if user_data['is_admin']:
                user.roles.append(aloha_admin_role)
            else:
                user.roles.append(aloha_user_role)
            
            db.session.add(user)
            print(f"Created user: {user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
        
        db.session.commit()
        print("\n=== Aloha Holdings Setup Complete ===")
        print(f"Organization ID: {org.id}")
        print(f"Temporary Password for all users: {temp_password}")
        print("Users should change their password on first login.")
        print("\nNext steps:")
        print("1. Update subsidiary names in org settings")
        print("2. Configure SAP connections for each subsidiary")
        print("3. Add actual users with their email addresses")
        print("4. Set up ETL jobs for SAP data extraction")


if __name__ == '__main__':
    setup_aloha()
