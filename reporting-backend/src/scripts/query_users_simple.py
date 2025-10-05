#!/usr/bin/env python3
"""
Query users using the app's existing database setup
"""

import sys
import os

# Add the parent directory to sys.path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def query_users_with_app_context():
    """Query users using Flask app context and SQLAlchemy"""
    try:
        from src.models.user import User, db
        from src.models.rbac import Role
        from src.main import app
        
        with app.app_context():
            print("\n" + "="*80)
            print("USER AND ROLE ANALYSIS - LOCAL DATABASE")
            print("="*80)
            
            # Check what database is being used
            db_uri = app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')
            if 'postgresql' in db_uri or 'postgres' in db_uri:
                db_type = "PostgreSQL"
            elif 'sqlite' in db_uri:
                db_type = "SQLite"
            else:
                db_type = "Unknown"
            
            print(f"\n📊 DATABASE: {db_type}")
            print(f"📍 URI: {db_uri[:50]}{'...' if len(db_uri) > 50 else ''}")
            
            # Get total user count
            total_users = User.query.count()
            print(f"\n👥 TOTAL USERS: {total_users}")
            
            if total_users == 0:
                print("❌ No users found in database")
                return
            
            # Get all users
            users = User.query.all()
            
            print(f"\n📋 ALL USERS:")
            print("-" * 80)
            print(f"{'ID':<4} {'Email':<35} {'Username':<20} {'Name':<25} {'Active':<6}")
            print("-" * 80)
            
            for user in users:
                full_name = f"{user.first_name or ''} {user.last_name or ''}".strip()
                if not full_name:
                    full_name = "N/A"
                
                active_status = "Yes" if user.is_active else "No"
                print(f"{user.id:<4} {user.email:<35} {user.username:<20} {full_name:<25} {active_status:<6}")
            
            # Check if roles exist
            try:
                total_roles = Role.query.count()
                print(f"\n🔐 ROLES SYSTEM:")
                print(f"   Total roles: {total_roles}")
                
                if total_roles > 0:
                    roles = Role.query.all()
                    print(f"\n📋 AVAILABLE ROLES:")
                    for role in roles:
                        dept = role.department or 'N/A'
                        print(f"  - {role.name} ({dept}): {role.description or 'No description'}")
                    
                    # Check for Parts-related roles
                    parts_roles = Role.query.filter(
                        (Role.name.ilike('%parts%')) | 
                        (Role.department.ilike('%parts%'))
                    ).all()
                    
                    print(f"\n📦 PARTS-RELATED ROLES:")
                    if parts_roles:
                        for role in parts_roles:
                            print(f"  ✅ {role.name} (Department: {role.department or 'N/A'})")
                            
                            # Find users with this role
                            role_users = User.query.filter(User.roles.contains(role)).all()
                            if role_users:
                                print(f"     Users with this role ({len(role_users)}):")
                                for user in role_users:
                                    name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'N/A'
                                    print(f"       • {user.email} ({name})")
                            else:
                                print(f"     No users assigned to this role")
                    else:
                        print("  ❌ No Parts-related roles found")
                    
                    # Check specifically for Parts User role
                    parts_user_role = Role.query.filter_by(name='Parts User').first()
                    if parts_user_role:
                        print(f"\n✅ 'Parts User' role exists (ID: {parts_user_role.id})")
                        print(f"   Description: {parts_user_role.description}")
                        print(f"   Department: {parts_user_role.department}")
                        print(f"   Level: {parts_user_role.level}")
                        
                        # Count permissions
                        perm_count = len(parts_user_role.permissions)
                        print(f"   Permissions: {perm_count}")
                        if perm_count > 0:
                            print("   Permission list:")
                            for perm in parts_user_role.permissions:
                                print(f"     • {perm.name}: {perm.description}")
                    else:
                        print(f"\n❌ 'Parts User' role NOT FOUND")
                        print("   This role should be created by auto-initialization")
                    
                    # Show users and their roles
                    print(f"\n👥 USERS WITH ROLES:")
                    print("-" * 80)
                    
                    for user in users:
                        name = f"{user.first_name or ''} {user.last_name or ''}".strip() or 'N/A'
                        roles_list = [f"{r.name} ({r.department or 'N/A'})" for r in user.roles]
                        roles_str = ", ".join(roles_list) if roles_list else "No roles assigned"
                        
                        print(f"ID {user.id}: {user.email}")
                        print(f"  Name: {name}")
                        print(f"  Roles: {roles_str}")
                        print()
                
                else:
                    print("❌ No roles found in database")
                    print("   RBAC system may not be initialized")
                    
            except Exception as e:
                print(f"❌ Error accessing roles: {e}")
                print("   Roles table may not exist yet")
            
            print(f"\n🎯 SUMMARY:")
            print(f"   • Database type: {db_type}")
            print(f"   • Total users: {total_users}")
            try:
                role_count = Role.query.count()
                print(f"   • Total roles: {role_count}")
                
                # Count role assignments
                assignments = 0
                for user in users:
                    assignments += len(user.roles)
                print(f"   • Role assignments: {assignments}")
                
            except:
                print(f"   • Roles system: Not initialized")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Make sure you're running from the correct directory")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    query_users_with_app_context()