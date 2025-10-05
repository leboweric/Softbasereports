#!/usr/bin/env python3
"""
Update RBAC system with new Parts User role and permissions

This script adds the new Parts User role and specific Parts permissions
to the existing RBAC system.

Usage:
    python update_rbac_parts.py
"""

import sys
import os

# Add the parent directory to sys.path to import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.user import db
from src.models.rbac import Role, Permission
from src.main import create_app

def update_rbac():
    """Update RBAC system with new Parts User role and permissions"""
    
    app = create_app()
    
    with app.app_context():
        print("Updating RBAC system for Parts User role...")
        
        # 1. Create new specific Parts permissions
        new_permissions = [
            {
                'name': 'view_parts_work_orders',
                'resource': 'parts',
                'action': 'view_work_orders',
                'description': 'View Parts work orders report'
            },
            {
                'name': 'view_parts_inventory_location',
                'resource': 'parts',
                'action': 'view_inventory_location',
                'description': 'View Parts inventory by location report'
            },
            {
                'name': 'view_parts_stock_alerts',
                'resource': 'parts',
                'action': 'view_stock_alerts',
                'description': 'View Parts stock alerts report'
            },
            {
                'name': 'view_parts_forecast',
                'resource': 'parts',
                'action': 'view_forecast',
                'description': 'View Parts forecast report'
            }
        ]
        
        print("\n1. Creating new Parts permissions...")
        created_permissions = []
        for perm_data in new_permissions:
            perm = Permission.query.filter_by(name=perm_data['name']).first()
            if not perm:
                perm = Permission(**perm_data)
                db.session.add(perm)
                created_permissions.append(perm)
                print(f"  ✓ Created permission: {perm_data['name']}")
            else:
                created_permissions.append(perm)
                print(f"  - Permission exists: {perm_data['name']}")
        
        db.session.commit()
        
        # 2. Create Parts User role
        print("\n2. Creating Parts User role...")
        parts_user_role = Role.query.filter_by(name='Parts User').first()
        if not parts_user_role:
            parts_user_role = Role(
                name='Parts User',
                description='Restricted access to specific Parts reports and Minitrac only',
                department='Parts',
                level=2
            )
            db.session.add(parts_user_role)
            print("  ✓ Created Parts User role")
        else:
            print("  - Parts User role exists")
        
        db.session.commit()
        
        # 3. Assign permissions to Parts User role
        print("\n3. Assigning permissions to Parts User role...")
        
        # Get required permissions
        required_permission_names = [
            'view_parts_work_orders',
            'view_parts_inventory_location', 
            'view_parts_stock_alerts',
            'view_parts_forecast',
            'view_minitrac',
            'export_minitrac'
        ]
        
        for perm_name in required_permission_names:
            perm = Permission.query.filter_by(name=perm_name).first()
            if perm:
                if perm not in parts_user_role.permissions:
                    parts_user_role.permissions.append(perm)
                    print(f"  ✓ Assigned permission: {perm_name}")
                else:
                    print(f"  - Permission already assigned: {perm_name}")
            else:
                print(f"  ⚠ Permission not found: {perm_name}")
        
        db.session.commit()
        
        # 4. Update existing Parts Manager role to include new permissions
        print("\n4. Updating Parts Manager role...")
        parts_manager_role = Role.query.filter_by(name='Parts Manager').first()
        if parts_manager_role:
            for perm_name in ['view_parts_work_orders', 'view_parts_inventory_location', 
                             'view_parts_stock_alerts', 'view_parts_forecast']:
                perm = Permission.query.filter_by(name=perm_name).first()
                if perm and perm not in parts_manager_role.permissions:
                    parts_manager_role.permissions.append(perm)
                    print(f"  ✓ Added permission to Parts Manager: {perm_name}")
            
            db.session.commit()
            print("  ✓ Updated Parts Manager role")
        else:
            print("  ⚠ Parts Manager role not found")
        
        print("\n✅ RBAC update completed successfully!")
        print("\nParts User role permissions:")
        for perm in parts_user_role.permissions:
            print(f"  - {perm.name}: {perm.description}")
        
        print(f"\nTo assign users to Parts User role, use:")
        print(f"  python manage_parts_users.py --assign <username_or_email>")

if __name__ == '__main__':
    update_rbac()