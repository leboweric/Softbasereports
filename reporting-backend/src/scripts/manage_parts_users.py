#!/usr/bin/env python3
"""
Script to manage Parts User role assignments

This script allows administrators to:
1. List all users and their current roles
2. Assign Parts User role to specific users
3. Remove Parts User role from users
4. List users with Parts User role

Usage:
    python manage_parts_users.py --help
"""

import sys
import os
import argparse

# Add the parent directory to sys.path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.user import User, db
from src.models.rbac import Role
from src.main import create_app

def list_users():
    """List all users and their current roles"""
    users = User.query.all()
    print("\n=== ALL USERS ===")
    print(f"{'ID':<4} {'Username':<20} {'Email':<30} {'Roles':<50}")
    print("-" * 104)
    
    for user in users:
        role_names = [role.name for role in user.roles]
        roles_str = ", ".join(role_names) if role_names else "No roles"
        print(f"{user.id:<4} {user.username:<20} {user.email:<30} {roles_str:<50}")
    
    print(f"\nTotal users: {len(users)}")

def list_parts_users():
    """List users with Parts User role"""
    parts_role = Role.query.filter_by(name='Parts User').first()
    if not parts_role:
        print("Parts User role not found. Run init_rbac.py first.")
        return
    
    parts_users = User.query.filter(User.roles.contains(parts_role)).all()
    print("\n=== PARTS USERS ===")
    print(f"{'ID':<4} {'Username':<20} {'Email':<30} {'Department':<15}")
    print("-" * 69)
    
    for user in parts_users:
        print(f"{user.id:<4} {user.username:<20} {user.email:<30} Parts")
    
    print(f"\nTotal Parts Users: {len(parts_users)}")

def assign_parts_user_role(username_or_email):
    """Assign Parts User role to a user"""
    # Find user
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if not user:
        print(f"User not found: {username_or_email}")
        return False
    
    # Find Parts User role
    parts_role = Role.query.filter_by(name='Parts User').first()
    if not parts_role:
        print("Parts User role not found. Run init_rbac.py first.")
        return False
    
    # Check if user already has the role
    if parts_role in user.roles:
        print(f"User {user.username} already has Parts User role")
        return True
    
    # Assign role
    user.roles.append(parts_role)
    db.session.commit()
    
    print(f"✓ Assigned Parts User role to {user.username} ({user.email})")
    return True

def remove_parts_user_role(username_or_email):
    """Remove Parts User role from a user"""
    # Find user
    user = User.query.filter(
        (User.username == username_or_email) | (User.email == username_or_email)
    ).first()
    
    if not user:
        print(f"User not found: {username_or_email}")
        return False
    
    # Find Parts User role
    parts_role = Role.query.filter_by(name='Parts User').first()
    if not parts_role:
        print("Parts User role not found.")
        return False
    
    # Check if user has the role
    if parts_role not in user.roles:
        print(f"User {user.username} does not have Parts User role")
        return True
    
    # Remove role
    user.roles.remove(parts_role)
    db.session.commit()
    
    print(f"✓ Removed Parts User role from {user.username} ({user.email})")
    return True

def main():
    parser = argparse.ArgumentParser(description='Manage Parts User role assignments')
    parser.add_argument('--list-all', action='store_true', help='List all users and their roles')
    parser.add_argument('--list-parts', action='store_true', help='List users with Parts User role')
    parser.add_argument('--assign', type=str, help='Assign Parts User role to user (username or email)')
    parser.add_argument('--remove', type=str, help='Remove Parts User role from user (username or email)')
    
    args = parser.parse_args()
    
    # Create app context
    app = create_app()
    
    with app.app_context():
        if args.list_all:
            list_users()
        elif args.list_parts:
            list_parts_users()
        elif args.assign:
            assign_parts_user_role(args.assign)
        elif args.remove:
            remove_parts_user_role(args.remove)
        else:
            parser.print_help()
            print("\nExamples:")
            print("  python manage_parts_users.py --list-all")
            print("  python manage_parts_users.py --list-parts")
            print("  python manage_parts_users.py --assign john.doe@company.com")
            print("  python manage_parts_users.py --remove john.doe")

if __name__ == '__main__':
    main()