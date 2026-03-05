"""
Script to set up Aloha Holdings as a new tenant in AIOP
Aloha is a Hawaii-based holding company with 8 subsidiary companies:
  SAP: Sandia, Mercury, Ultimate Solutions, Avalon, Orbot
  NetSuite: Hawaii Care and Cleaning, Kauai Exclusive, Heavenly Vacations

Run with: python -m src.scripts.setup_aloha
"""
import os
import sys
import json

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
            # Data source templates
            sap_template = {
                'connected': False,
                'erp_type': 'sap',
                'system_type': '',
                'connection_method': '',
                'host': '',
                'port': '',
                'client': '',
                'system_number': '',
                'username': '',
                'password': '',
                'company_db': '',
            }
            
            netsuite_template = {
                'connected': False,
                'erp_type': 'netsuite',
                'account_id': '',
                'consumer_key': '',
                'consumer_secret': '',
                'token_id': '',
                'token_secret': '',
                'realm': '',
            }
            
            default_settings = {
                'data_sources': {
                    'sap_sandia': {'name': 'Sandia', **sap_template},
                    'sap_mercury': {'name': 'Mercury', **sap_template},
                    'sap_ultimate_solutions': {'name': 'Ultimate Solutions', **sap_template},
                    'sap_avalon': {'name': 'Avalon', **sap_template},
                    'sap_orbot': {'name': 'Orbot', **sap_template},
                    'ns_hawaii_care': {'name': 'Hawaii Care and Cleaning', **netsuite_template},
                    'ns_kauai_exclusive': {'name': 'Kauai Exclusive', **netsuite_template},
                    'ns_heavenly_vacations': {'name': 'Heavenly Vacations', **netsuite_template},
                }
            }
            
            org = Organization(
                name='Aloha Holdings',
                platform_type='multi_erp',
                subscription_status='active',
                fiscal_year_start_month=1,
                is_active=True,
                settings=json.dumps(default_settings)
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
        
        # Aloha Holdings users
        aloha_users = [
            {'first_name': 'Eric', 'last_name': 'LeBow', 'email': 'elebow@aloha.com', 'is_admin': True},
            {'first_name': 'J', 'last_name': 'Foos', 'email': 'jfoos@aloha.com', 'is_admin': True},
            {'first_name': 'C', 'last_name': 'Shannon', 'email': 'cshannon@aloha.com', 'is_admin': True},
        ]
        
        temp_password = 'abc123'
        
        for user_data in aloha_users:
            existing_user = User.query.filter_by(email=user_data['email'].lower()).first()
            if existing_user:
                print(f"User {user_data['email']} already exists (ID: {existing_user.id})")
                if existing_user.organization_id != org.id:
                    print(f"  Note: User is in org {existing_user.organization_id}, not Aloha ({org.id})")
                continue
            
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
        print("\nSubsidiaries (SAP):")
        print("  - Sandia")
        print("  - Mercury")
        print("  - Ultimate Solutions")
        print("  - Avalon")
        print("  - Orbot")
        print("\nSubsidiaries (NetSuite):")
        print("  - Hawaii Care and Cleaning")
        print("  - Kauai Exclusive")
        print("  - Heavenly Vacations")
        print("\nNext steps:")
        print("1. Configure SAP connections for each SAP subsidiary")
        print("2. Configure NetSuite connections for each NetSuite subsidiary")
        print("3. Set up ETL jobs for data extraction")


if __name__ == '__main__':
    setup_aloha()
