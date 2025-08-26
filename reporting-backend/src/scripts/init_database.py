#!/usr/bin/env python3
"""
Initialize the database with RBAC tables and default data
Run this script after deploying to set up the role-based access control system
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.main import app
from src.models.user import db
from src.utils.init_rbac import init_rbac, migrate_existing_users

def main():
    """Initialize the database with RBAC data"""
    with app.app_context():
        print("Creating database tables...")
        db.create_all()
        
        print("\nInitializing RBAC system...")
        init_rbac(app)
        
        print("\nMigrating existing users to RBAC...")
        migrate_existing_users()
        
        print("\n✅ Database initialization complete!")
        print("The RBAC system has been set up with default roles and permissions.")
        print("Existing users have been migrated to the new permission system.")

if __name__ == '__main__':
    main()