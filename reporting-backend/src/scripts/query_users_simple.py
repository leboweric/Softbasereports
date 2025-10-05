#!/usr/bin/env python3
"""
Query production database to check user roles
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.services.postgres_service import get_postgres_db

def query_user_roles():
    """Query user roles from production database"""
    postgres_db = get_postgres_db()
    if not postgres_db:
        print("❌ Could not connect to PostgreSQL database")
        return
    
    # Query to check user roles
    query = """
    SELECT 
        u.email,
        u.id as user_id,
        u.role as legacy_role,
        r.name as rbac_role_name,
        r.id as role_id
    FROM "user" u
    LEFT JOIN user_roles ur ON u.id = ur.user_id
    LEFT JOIN role r ON ur.role_id = r.id
    WHERE u.email IN ('elebow@bmhmn.com', 'dmeyer@bmhmn.com', 'akaley@bmhmn.com')
    ORDER BY u.email, r.name;
    """
    
    print("=== USER ROLES QUERY ===")
    try:
        result = postgres_db.execute_query(query)
        
        if result:
            print("Email\t\t\tUser ID\tLegacy Role\tRBAC Role")
            print("-" * 60)
            for row in result:
                email, user_id, legacy_role, rbac_role, role_id = row
                print(f"{email}\t{user_id}\t{legacy_role or 'None'}\t\t{rbac_role or 'None'}")
        else:
            print("No results found")
            
    except Exception as e:
        print(f"Error querying users: {e}")
    
    # Also check all roles in the database
    roles_query = "SELECT id, name FROM role ORDER BY id;"
    print("\n=== ALL ROLES IN DATABASE ===")
    try:
        roles_result = postgres_db.execute_query(roles_query)
        if roles_result:
            print("Role ID\tRole Name")
            print("-" * 30)
            for role_id, role_name in roles_result:
                print(f"{role_id}\t{role_name}")
    except Exception as e:
        print(f"Error querying roles: {e}")
    
    # Check user_roles assignments
    user_roles_query = """
    SELECT ur.user_id, ur.role_id, u.email, r.name as role_name
    FROM user_roles ur
    JOIN "user" u ON ur.user_id = u.id
    JOIN role r ON ur.role_id = r.id
    WHERE u.email IN ('elebow@bmhmn.com', 'dmeyer@bmhmn.com', 'akaley@bmhmn.com')
    ORDER BY u.email;
    """
    
    print("\n=== USER ROLE ASSIGNMENTS ===")
    try:
        user_roles_result = postgres_db.execute_query(user_roles_query)
        if user_roles_result:
            print("User ID\tRole ID\tEmail\t\t\tRole Name")
            print("-" * 50)
            for user_id, role_id, email, role_name in user_roles_result:
                print(f"{user_id}\t{role_id}\t{email}\t{role_name}")
        else:
            print("No role assignments found for these users")
    except Exception as e:
        print(f"Error querying user role assignments: {e}")

if __name__ == '__main__':
    query_user_roles()