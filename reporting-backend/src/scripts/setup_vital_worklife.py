"""
Script to set up VITAL Worklife as a new tenant in IOP
Run with: python -m src.scripts.setup_vital_worklife
"""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

def setup_vital_worklife():
    """Set up VITAL Worklife organization and users"""
    
    # Create minimal Flask app for database context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    from src.models.user import db, Organization, User
    from src.models.rbac import Role
    
    db.init_app(app)
    
    with app.app_context():
        # Check if VITAL Worklife already exists
        existing_org = Organization.query.filter_by(name='VITAL Worklife').first()
        if existing_org:
            print(f"VITAL Worklife organization already exists (ID: {existing_org.id})")
            org = existing_org
        else:
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
            db.session.commit()
            print(f"Created VITAL Worklife organization (ID: {org.id})")
        
        # Get or create VITAL Admin role
        vital_admin_role = Role.query.filter_by(name='VITAL Admin').first()
        if not vital_admin_role:
            vital_admin_role = Role(
                name='VITAL Admin',
                description='VITAL Worklife administrator with full access',
                department='Administration',
                is_active=True
            )
            db.session.add(vital_admin_role)
            db.session.commit()
            print(f"Created VITAL Admin role (ID: {vital_admin_role.id})")
        
        # Get Leadership role for regular users
        leadership_role = Role.query.filter_by(name='Leadership').first()
        
        # VITAL Worklife users to create
        vital_users = [
            {'first_name': 'Dane', 'last_name': 'Jensen', 'email': 'Dane.Jensen@VITALWorkLife.com', 'is_admin': True},
            {'first_name': 'Grace', 'last_name': 'Lee', 'email': 'grace.lee@VITALWorkLife.com', 'is_admin': True},
            {'first_name': 'Adam', 'last_name': 'Frei', 'email': 'Adam.Frei@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Mitchell', 'last_name': 'Best', 'email': 'Mitchell.Best@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Aric', 'last_name': 'Bandy', 'email': 'Aric.Bandy@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Nicole', 'last_name': 'Hale', 'email': 'Nicole.Hale@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Lacey', 'last_name': 'Lefere', 'email': 'lacey.lefere@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Derek', 'last_name': 'Bell', 'email': 'derek.bell@vitalworklife.com', 'is_admin': False},
            {'first_name': 'Eric', 'last_name': 'LeBow', 'email': 'eric.lebow@vitalworklife.com', 'is_admin': True},
        ]
        
        temp_password = 'VitalDemo2025!'
        
        for user_data in vital_users:
            # Check if user already exists
            existing_user = User.query.filter_by(email=user_data['email'].lower()).first()
            if existing_user:
                print(f"User {user_data['email']} already exists (ID: {existing_user.id})")
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
                user.roles.append(vital_admin_role)
            if leadership_role:
                user.roles.append(leadership_role)
            
            db.session.add(user)
            print(f"Created user: {user_data['first_name']} {user_data['last_name']} ({user_data['email']})")
        
        db.session.commit()
        print("\n=== VITAL Worklife Setup Complete ===")
        print(f"Organization ID: {org.id}")
        print(f"Temporary Password for all users: {temp_password}")
        print("Users should change their password on first login.")

if __name__ == '__main__':
    setup_vital_worklife()
