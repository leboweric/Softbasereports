#!/usr/bin/env python3
"""
Create Parts team user accounts and assign to Parts User role
"""

import sys
import os

# Add the parent directory to sys.path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.user import User, db
from src.models.rbac import Role
from src.main import create_app
from werkzeug.security import generate_password_hash

def create_parts_users():
    """Create Parts team user accounts"""
    
    # Users to create
    users_data = [
        {
            'email': 'dmeyer@bmhmn.com',
            'username': 'dmeyer@bmhmn.com',
            'first_name': 'Dan',
            'last_name': 'Meyer',
            'password': 'abc123'
        },
        {
            'email': 'mmikota@bmhmn.com',
            'username': 'mmikota@bmhmn.com',
            'first_name': 'Molly',
            'last_name': 'Mikota',
            'password': 'abc123'
        },
        {
            'email': 'dgritti@bmhmn.com',
            'username': 'dgritti@bmhmn.com',
            'first_name': 'Derek',
            'last_name': 'Gritti',
            'password': 'abc123'
        }
    ]
    
    # Create app context
    app = create_app()
    
    try:
        with app.app_context():
            print("="*80)
            print("CREATING PARTS TEAM USER ACCOUNTS")
            print("="*80)
            
            # Get Parts User role
            parts_user_role = Role.query.filter_by(name='Parts User').first()
            
            if not parts_user_role:
                print("❌ Parts User role not found!")
                print("   Run auto-initialization first: railway run python3 src/scripts/update_rbac_parts.py")
                return
            
            print(f"✅ Found Parts User role (ID: {parts_user_role.id})")
            print(f"   Description: {parts_user_role.description}")
            print(f"   Permissions: {len(parts_user_role.permissions)}")
            
            created_count = 0
            updated_count = 0
            
            for user_data in users_data:
                print(f"\n👤 Processing user: {user_data['email']}")
                
                # Check if user already exists
                existing_user = User.query.filter_by(email=user_data['email']).first()
                
                if existing_user:
                    print(f"⚠️  User {user_data['email']} already exists")
                    
                    # Check if already has Parts User role
                    if parts_user_role in existing_user.roles:
                        print(f"   Already has Parts User role - no changes needed")
                    else:
                        # Assign Parts User role
                        existing_user.roles.append(parts_user_role)
                        db.session.commit()
                        print(f"✅ Assigned Parts User role to existing user")
                        updated_count += 1
                    continue
                
                # Create new user
                print(f"   Creating new user: {user_data['first_name']} {user_data['last_name']}")
                
                new_user = User(
                    email=user_data['email'],
                    username=user_data['username'],
                    first_name=user_data['first_name'],
                    last_name=user_data['last_name'],
                    password_hash=generate_password_hash(user_data['password']),
                    is_active=True,
                    role='user'  # Legacy role field
                )
                
                # Assign Parts User role
                new_user.roles.append(parts_user_role)
                
                db.session.add(new_user)
                db.session.commit()
                
                print(f"✅ Created user: {user_data['email']}")
                print(f"   Name: {user_data['first_name']} {user_data['last_name']}")
                print(f"   Assigned to Parts User role")
                created_count += 1
            
            print("\n" + "="*80)
            print("PARTS TEAM USER CREATION COMPLETE!")
            print("="*80)
            print(f"📊 SUMMARY:")
            print(f"   • New users created: {created_count}")
            print(f"   • Existing users updated: {updated_count}")
            print(f"   • Total Parts team members: {created_count + updated_count}")
            
            # Verify all assignments
            print(f"\n👥 CURRENT PARTS USER ROLE ASSIGNMENTS:")
            parts_users = User.query.filter(User.roles.contains(parts_user_role)).all()
            for user in parts_users:
                name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'N/A'
                print(f"   • {user.email} ({name})")
            
            print(f"\n⚠️  SECURITY WARNING:")
            print(f"   Initial password is 'abc123' - users MUST change on first login!")
            print(f"   Consider implementing forced password change on first login.")
            
    except Exception as e:
        print(f"❌ Error creating Parts team users: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    create_parts_users()