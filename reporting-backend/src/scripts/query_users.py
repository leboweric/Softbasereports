#!/usr/bin/env python3
"""
Query the PostgreSQL database to show user information and roles

This script connects to the production PostgreSQL database and shows:
1. All existing users (email, name, current roles)
2. Total count of users  
3. Users with Parts-related roles
"""

import sys
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Add the parent directory to sys.path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_database_url():
    """Get database URL from environment or Railway"""
    # Try environment variable first
    database_url = os.environ.get('DATABASE_URL')
    if database_url:
        return database_url
    
    # Try to get from Railway if available
    try:
        import subprocess
        result = subprocess.run(['railway', 'variables', '--json'], 
                              capture_output=True, text=True, check=True)
        import json
        variables = json.loads(result.stdout)
        return variables.get('DATABASE_URL')
    except:
        pass
    
    return None

def connect_to_database():
    """Connect to PostgreSQL database"""
    database_url = get_database_url()
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Set DATABASE_URL environment variable or authenticate with Railway CLI")
        return None
    
    # Handle Railway PostgreSQL URL format
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        print(f"✅ Connected to PostgreSQL database")
        return conn
    except Exception as e:
        print(f"❌ Failed to connect to database: {e}")
        return None

def query_users_and_roles():
    """Query users table and their roles"""
    conn = connect_to_database()
    if not conn:
        return
    
    try:
        cursor = conn.cursor()
        
        print("\n" + "="*80)
        print("POSTGRESQL DATABASE USER AND ROLE ANALYSIS")
        print("="*80)
        
        # 1. Get total user count
        cursor.execute("SELECT COUNT(*) as total_users FROM users")
        result = cursor.fetchone()
        total_users = result['total_users'] if result else 0
        print(f"\n📊 TOTAL USERS: {total_users}")
        
        # 2. Check if tables exist
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('users', 'roles', 'user_roles')
            ORDER BY table_name
        """)
        tables = [row['table_name'] for row in cursor.fetchall()]
        print(f"\n📋 EXISTING TABLES: {', '.join(tables)}")
        
        if 'users' not in tables:
            print("❌ Users table not found")
            return
        
        # 3. Get all users with basic info
        print(f"\n👥 ALL USERS:")
        print("-" * 80)
        print(f"{'ID':<4} {'Email':<35} {'Username':<20} {'Name':<25} {'Active':<6}")
        print("-" * 80)
        
        cursor.execute("""
            SELECT id, email, username, first_name, last_name, is_active, created_at
            FROM users 
            ORDER BY id
        """)
        users = cursor.fetchall()
        
        for user in users:
            full_name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip()
            if not full_name:
                full_name = "N/A"
            
            active_status = "Yes" if user['is_active'] else "No"
            print(f"{user['id']:<4} {user['email']:<35} {user['username']:<20} {full_name:<25} {active_status:<6}")
        
        # 4. Check if roles and user_roles tables exist for role analysis
        if 'roles' in tables and 'user_roles' in tables:
            print(f"\n🔐 USER ROLES:")
            print("-" * 80)
            
            # Get all roles
            cursor.execute("SELECT id, name, description, department FROM roles ORDER BY name")
            all_roles = cursor.fetchall()
            
            print(f"\n📋 AVAILABLE ROLES ({len(all_roles)}):")
            for role in all_roles:
                dept = role['department'] or 'N/A'
                print(f"  - {role['name']} ({dept}): {role['description'] or 'No description'}")
            
            # Get users with roles
            cursor.execute("""
                SELECT 
                    u.id, u.email, u.username, u.first_name, u.last_name,
                    r.name as role_name, r.department
                FROM users u
                LEFT JOIN user_roles ur ON u.id = ur.user_id
                LEFT JOIN roles r ON ur.role_id = r.id
                ORDER BY u.id, r.name
            """)
            user_roles = cursor.fetchall()
            
            # Group by user
            users_with_roles = {}
            for row in user_roles:
                user_id = row['id']
                if user_id not in users_with_roles:
                    users_with_roles[user_id] = {
                        'email': row['email'],
                        'username': row['username'],
                        'name': f"{row['first_name'] or ''} {row['last_name'] or ''}".strip() or 'N/A',
                        'roles': []
                    }
                
                if row['role_name']:
                    users_with_roles[user_id]['roles'].append({
                        'name': row['role_name'],
                        'department': row['department']
                    })
            
            print(f"\n👥 USERS WITH ROLES:")
            print("-" * 80)
            
            for user_id, user_info in users_with_roles.items():
                roles_str = ", ".join([f"{r['name']} ({r['department'] or 'N/A'})" for r in user_info['roles']])
                if not roles_str:
                    roles_str = "No roles assigned"
                
                print(f"ID {user_id}: {user_info['email']}")
                print(f"  Name: {user_info['name']}")
                print(f"  Roles: {roles_str}")
                print()
            
            # 5. Find Parts-related roles and users
            print(f"\n📦 PARTS-RELATED ROLES AND USERS:")
            print("-" * 80)
            
            # Find Parts roles
            cursor.execute("""
                SELECT id, name, description, department 
                FROM roles 
                WHERE name ILIKE '%parts%' OR department ILIKE '%parts%'
                ORDER BY name
            """)
            parts_roles = cursor.fetchall()
            
            if parts_roles:
                print("Parts-related roles found:")
                for role in parts_roles:
                    print(f"  - {role['name']} (ID: {role['id']})")
                    print(f"    Department: {role['department'] or 'N/A'}")
                    print(f"    Description: {role['description'] or 'No description'}")
                    
                    # Find users with this role
                    cursor.execute("""
                        SELECT u.id, u.email, u.username, u.first_name, u.last_name
                        FROM users u
                        JOIN user_roles ur ON u.id = ur.user_id
                        WHERE ur.role_id = %s
                        ORDER BY u.email
                    """, (role['id'],))
                    role_users = cursor.fetchall()
                    
                    if role_users:
                        print(f"    Users with this role ({len(role_users)}):")
                        for user in role_users:
                            name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip() or 'N/A'
                            print(f"      • {user['email']} ({name})")
                    else:
                        print(f"    Users with this role: None")
                    print()
            else:
                print("❌ No Parts-related roles found")
                
            # Check specifically for Parts User role
            cursor.execute("SELECT id FROM roles WHERE name = 'Parts User'")
            parts_user_role = cursor.fetchone()
            
            if parts_user_role:
                print("✅ 'Parts User' role exists")
            else:
                print("❌ 'Parts User' role NOT FOUND")
                print("   Run the auto-initialization or update script to create it")
        
        else:
            print(f"\n⚠️  RBAC tables not found. Available tables: {', '.join(tables)}")
            print("   The roles system may not be initialized yet.")
        
        print(f"\n🎯 SUMMARY:")
        print(f"   • Total users: {total_users}")
        print(f"   • Tables found: {len(tables)}")
        if 'roles' in tables:
            cursor.execute("SELECT COUNT(*) as count FROM roles")
            role_count = cursor.fetchone()['count']
            print(f"   • Total roles: {role_count}")
            
            cursor.execute("SELECT COUNT(*) as count FROM user_roles")
            assignment_count = cursor.fetchone()['count']
            print(f"   • Role assignments: {assignment_count}")
        
    except Exception as e:
        print(f"❌ Error querying database: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        conn.close()
        print(f"\n✅ Database connection closed")

if __name__ == '__main__':
    query_users_and_roles()