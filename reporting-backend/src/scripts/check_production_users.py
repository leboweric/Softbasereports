#!/usr/bin/env python3
"""
Check production PostgreSQL database for users and Parts User role

This script tries multiple methods to connect to the production database:
1. Environment variables
2. Railway CLI variables
3. Manual input
"""

import sys
import os
import json
import subprocess

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_database_url():
    """Get DATABASE_URL from various sources"""
    
    # Method 1: Environment variables
    env_vars = ['DATABASE_URL', 'POSTGRES_URL', 'DATABASE_PRIVATE_URL', 'POSTGRES_PRIVATE_URL']
    
    for var in env_vars:
        url = os.environ.get(var)
        if url:
            print(f"✅ Found {var} in environment")
            return url
    
    # Method 2: Try Railway CLI
    try:
        print("🔧 Attempting to get DATABASE_URL from Railway CLI...")
        result = subprocess.run(['railway', 'variables', '--json'], 
                              capture_output=True, text=True, check=True)
        variables = json.loads(result.stdout)
        
        for var in env_vars:
            if var in variables:
                print(f"✅ Found {var} from Railway CLI")
                return variables[var]
                
    except subprocess.CalledProcessError:
        print("❌ Railway CLI not authenticated or failed")
    except FileNotFoundError:
        print("❌ Railway CLI not found")
    except Exception as e:
        print(f"❌ Railway CLI error: {e}")
    
    print("❌ No DATABASE_URL found in environment or Railway CLI")
    return None

def check_production_database():
    """Check production database for users and roles"""
    
    database_url = get_database_url()
    
    if not database_url:
        print("\n💡 To check the production database:")
        print("1. Authenticate with Railway: railway login")
        print("2. Run: railway run python3 src/scripts/query_users_simple.py")
        print("3. Or set DATABASE_URL environment variable manually")
        return
    
    # Try to connect using psycopg2
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        # Handle different URL formats
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        print(f"\n🔌 Connecting to production PostgreSQL...")
        conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
        cursor = conn.cursor()
        
        print("✅ Connected to production database!")
        
        # Check users table
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        print(f"\n👥 Total users in production: {user_count}")
        
        if user_count > 0:
            # Get user list
            cursor.execute("""
                SELECT id, email, username, first_name, last_name, is_active
                FROM users 
                ORDER BY id
            """)
            users = cursor.fetchall()
            
            print(f"\n📋 PRODUCTION USERS:")
            print("-" * 80)
            print(f"{'ID':<4} {'Email':<35} {'Username':<20} {'Name':<25}")
            print("-" * 80)
            
            for user in users:
                full_name = f"{user['first_name'] or ''} {user['last_name'] or ''}".strip()
                if not full_name:
                    full_name = "N/A"
                
                print(f"{user['id']:<4} {user['email']:<35} {user['username']:<20} {full_name:<25}")
        
        # Check roles
        try:
            cursor.execute("SELECT COUNT(*) as count FROM roles")
            role_count = cursor.fetchone()['count']
            print(f"\n🔐 Total roles in production: {role_count}")
            
            # Check for Parts User role specifically
            cursor.execute("SELECT * FROM roles WHERE name = 'Parts User'")
            parts_user_role = cursor.fetchone()
            
            if parts_user_role:
                print("✅ Parts User role exists in production!")
                print(f"   ID: {parts_user_role['id']}")
                print(f"   Description: {parts_user_role['description']}")
                print(f"   Department: {parts_user_role['department']}")
                print(f"   Level: {parts_user_role['level']}")
            else:
                print("❌ Parts User role NOT found in production")
                print("   The auto-initialization may not have run yet")
            
            # Check for Parts-related roles
            cursor.execute("""
                SELECT name, description, department 
                FROM roles 
                WHERE name ILIKE '%parts%' OR department ILIKE '%parts%'
                ORDER BY name
            """)
            parts_roles = cursor.fetchall()
            
            if parts_roles:
                print(f"\n📦 Parts-related roles in production:")
                for role in parts_roles:
                    print(f"  - {role['name']} ({role['department'] or 'N/A'})")
            
            # Check role assignments
            cursor.execute("""
                SELECT u.email, u.username, r.name as role_name
                FROM users u
                JOIN user_roles ur ON u.id = ur.user_id  
                JOIN roles r ON ur.role_id = r.id
                WHERE r.name ILIKE '%parts%'
                ORDER BY u.email
            """)
            parts_assignments = cursor.fetchall()
            
            if parts_assignments:
                print(f"\n👥 Users with Parts roles:")
                for assignment in parts_assignments:
                    print(f"  - {assignment['email']} → {assignment['role_name']}")
            else:
                print(f"\n❌ No users assigned to Parts roles yet")
                
        except Exception as e:
            print(f"❌ Error checking roles: {e}")
            print("   Roles tables may not exist yet")
        
        conn.close()
        print(f"\n✅ Production database check complete")
        
    except ImportError:
        print("❌ psycopg2 not available for direct database connection")
        print("   Install with: pip install psycopg2-binary")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("   Check DATABASE_URL and network connectivity")

if __name__ == '__main__':
    print("="*80)
    print("PRODUCTION DATABASE ANALYSIS")
    print("="*80)
    
    check_production_database()