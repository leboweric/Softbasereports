#!/usr/bin/env python3
"""
PRODUCTION USER CHECK - Run with Railway CLI

Usage:
    railway run python3 production_user_check.py

This script checks the actual production PostgreSQL database for:
1. All existing users (email, name, current roles)  
2. Total count of users
3. Users with Parts-related roles
4. Parts User role status
"""

import sys
import os

# Add the backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'reporting-backend'))

def check_production_users():
    """Check production users and roles"""
    try:
        from src.models.user import User, db
        from src.models.rbac import Role
        from src.main import app
        
        with app.app_context():
            print("="*80)
            print("🚀 PRODUCTION POSTGRESQL DATABASE ANALYSIS")
            print("="*80)
            
            # Verify we're using PostgreSQL
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', '')
            if 'postgresql' in db_uri or 'postgres' in db_uri:
                print("✅ Connected to PostgreSQL database")
                print(f"📍 Database: {db_uri.split('@')[-1] if '@' in db_uri else 'Railway PostgreSQL'}")
            else:
                print("⚠️  Warning: Not using PostgreSQL")
                print(f"📍 Database: {db_uri[:50]}...")
            
            # 1. Get all users
            users = User.query.all()
            total_users = len(users)
            
            print(f"\n👥 TOTAL USERS: {total_users}")
            
            if total_users == 0:
                print("❌ No users found in production database")
                return
            
            print(f"\n📋 ALL PRODUCTION USERS:")
            print("-" * 100)
            print(f"{'ID':<4} {'Email':<35} {'Username':<20} {'Name':<25} {'Active':<8} {'Roles'}")
            print("-" * 100)
            
            for user in users:
                # Get full name
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                if not full_name:
                    full_name = "N/A"
                
                # Get roles
                role_names = [r.name for r in user.roles] if user.roles else []
                roles_str = ", ".join(role_names) if role_names else "None"
                
                # Active status
                active_status = "Yes" if user.is_active else "No"
                
                print(f"{user.id:<4} {user.email:<35} {user.username:<20} {full_name:<25} {active_status:<8} {roles_str}")
            
            # 2. Check RBAC system
            print(f"\n🔐 RBAC SYSTEM STATUS:")
            try:
                roles = Role.query.all()
                total_roles = len(roles)
                print(f"   Total roles: {total_roles}")
                
                if total_roles > 0:
                    print(f"\n📋 ALL ROLES:")
                    for role in roles:
                        dept = role.department or 'N/A'
                        user_count = len(role.users) if role.users else 0
                        print(f"   • {role.name} ({dept}) - {user_count} users")
                        print(f"     └─ {role.description or 'No description'}")
                
                # 3. Check Parts User role specifically
                parts_user_role = Role.query.filter_by(name='Parts User').first()
                
                print(f"\n📦 PARTS USER ROLE STATUS:")
                if parts_user_role:
                    print("✅ Parts User role EXISTS in production!")
                    print(f"   ID: {parts_user_role.id}")
                    print(f"   Description: {parts_user_role.description}")
                    print(f"   Department: {parts_user_role.department}")
                    print(f"   Level: {parts_user_role.level}")
                    
                    # Check permissions
                    permissions = parts_user_role.permissions if hasattr(parts_user_role, 'permissions') else []
                    print(f"   Permissions: {len(permissions)}")
                    for perm in permissions:
                        print(f"     • {perm.name}")
                    
                    # Check assigned users
                    assigned_users = User.query.filter(User.roles.contains(parts_user_role)).all()
                    print(f"   Assigned users: {len(assigned_users)}")
                    if assigned_users:
                        for user in assigned_users:
                            name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'N/A'
                            print(f"     → {user.email} ({name})")
                    else:
                        print("     (No users assigned yet)")
                        
                else:
                    print("❌ Parts User role NOT FOUND in production")
                    print("   Auto-initialization may have failed or not run yet")
                
                # 4. Check for any Parts-related roles
                parts_roles = Role.query.filter(
                    (Role.name.ilike('%parts%')) | 
                    (Role.department.ilike('%parts%'))
                ).all()
                
                print(f"\n📦 ALL PARTS-RELATED ROLES:")
                if parts_roles:
                    for role in parts_roles:
                        user_count = len(role.users) if role.users else 0
                        print(f"   ✅ {role.name} - {user_count} users")
                        if role.users:
                            for user in role.users:
                                name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'N/A'
                                print(f"      → {user.email} ({name})")
                else:
                    print("   ❌ No Parts-related roles found")
                
            except Exception as e:
                print(f"❌ Error checking roles: {e}")
                print("   RBAC tables may not exist in production yet")
            
            # 5. Summary
            print(f"\n🎯 PRODUCTION SUMMARY:")
            print(f"   • Total users: {total_users}")
            print(f"   • Database type: PostgreSQL (Production)")
            try:
                role_count = Role.query.count()
                print(f"   • Total roles: {role_count}")
                
                # Count total role assignments
                total_assignments = 0
                for user in users:
                    total_assignments += len(user.roles)
                print(f"   • Role assignments: {total_assignments}")
                
                # Parts User role status
                parts_user_exists = Role.query.filter_by(name='Parts User').first() is not None
                print(f"   • Parts User role: {'✅ Ready' if parts_user_exists else '❌ Missing'}")
                
            except:
                print(f"   • RBAC system: ❌ Not initialized")
            
            print(f"\n🔧 NEXT STEPS:")
            if not Role.query.filter_by(name='Parts User').first():
                print("   1. Parts User role missing - check auto-initialization")
                print("   2. Run: railway run python3 src/scripts/update_rbac_parts.py")
            else:
                print("   1. ✅ Parts User role is ready")
                print("   2. Assign users: railway run python3 src/scripts/manage_parts_users.py --assign <email>")
                print("   3. Test access control with assigned users")
                
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the project root directory")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_production_users()