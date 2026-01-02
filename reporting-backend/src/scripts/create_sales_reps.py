"""
Script to create sales rep user accounts with proper RBAC.
Run this after deploying the salesman_name column migration.

Sales Reps:
- Kevin Buckman (KBuckman@bmhmn.com) -> "Kevin Buckman"
- Todd Auge (TAuge@bmhmn.com) -> "Todd Auge"  
- Rod Hauer (RHauer@bmhmn.com) -> "Rod Hauer"
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from flask import Flask
from src.models.user import db, User, Organization
from src.models.rbac import Role
from werkzeug.security import generate_password_hash

# Sales rep data
SALES_REPS = [
    {
        'email': 'KBuckman@bmhmn.com',
        'username': 'kbuckman',
        'first_name': 'Kevin',
        'last_name': 'Buckman',
        'salesman_name': 'Kevin Buckman',
        'password': 'TempPass123!'  # They should change this on first login
    },
    {
        'email': 'TAuge@bmhmn.com',
        'username': 'tauge',
        'first_name': 'Todd',
        'last_name': 'Auge',
        'salesman_name': 'Todd Auge',
        'password': 'TempPass123!'
    },
    {
        'email': 'RHauer@bmhmn.com',
        'username': 'rhauer',
        'first_name': 'Rod',
        'last_name': 'Hauer',
        'salesman_name': 'Rod Hauer',
        'password': 'TempPass123!'
    }
]

def create_sales_reps():
    """Create sales rep user accounts"""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///app.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        # Get the organization (assuming single tenant for now - BMH)
        org = Organization.query.first()
        if not org:
            print("ERROR: No organization found. Please create an organization first.")
            return
        
        print(f"Using organization: {org.name} (ID: {org.id})")
        
        # Get the Sales Rep role
        sales_rep_role = Role.query.filter_by(name='Sales Rep').first()
        if not sales_rep_role:
            print("ERROR: Sales Rep role not found. Please run RBAC initialization first.")
            return
        
        print(f"Found Sales Rep role (ID: {sales_rep_role.id})")
        
        for rep_data in SALES_REPS:
            # Check if user already exists
            existing = User.query.filter(
                (User.email == rep_data['email']) | (User.username == rep_data['username'])
            ).first()
            
            if existing:
                print(f"User {rep_data['email']} already exists (ID: {existing.id})")
                # Update salesman_name if not set
                if not existing.salesman_name:
                    existing.salesman_name = rep_data['salesman_name']
                    db.session.commit()
                    print(f"  -> Updated salesman_name to '{rep_data['salesman_name']}'")
                # Ensure they have Sales Rep role
                if sales_rep_role not in existing.roles:
                    existing.roles.append(sales_rep_role)
                    db.session.commit()
                    print(f"  -> Added Sales Rep role")
                continue
            
            # Create new user
            new_user = User(
                email=rep_data['email'],
                username=rep_data['username'],
                first_name=rep_data['first_name'],
                last_name=rep_data['last_name'],
                salesman_name=rep_data['salesman_name'],
                organization_id=org.id,
                is_active=True
            )
            new_user.set_password(rep_data['password'])
            
            db.session.add(new_user)
            db.session.commit()
            
            # Assign Sales Rep role
            new_user.roles.append(sales_rep_role)
            db.session.commit()
            
            print(f"Created user: {rep_data['email']}")
            print(f"  -> Username: {rep_data['username']}")
            print(f"  -> Salesman Name: {rep_data['salesman_name']}")
            print(f"  -> Role: Sales Rep")
            print(f"  -> Temp Password: {rep_data['password']}")
        
        print("\nDone! Sales reps can now log in and view their commissions.")
        print("IMPORTANT: Have them change their passwords on first login!")

if __name__ == '__main__':
    create_sales_reps()
