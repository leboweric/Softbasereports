#!/usr/bin/env python3
"""
Check all organizations in the database
"""
import os
import sys

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.user import Organization, User, db

with app.app_context():
    print("=" * 80)
    print("EXISTING ORGANIZATIONS IN DATABASE")
    print("=" * 80)
    
    orgs = Organization.query.all()
    
    if not orgs:
        print("No organizations found!")
    else:
        for org in orgs:
            user_count = User.query.filter_by(organization_id=org.id).count()
            print(f"\nOrganization ID: {org.id}")
            print(f"  Name: {org.name}")
            print(f"  Platform Type: {org.platform_type}")
            print(f"  Database Schema: {org.database_schema}")
            print(f"  DB Server: {org.db_server}")
            print(f"  DB Name: {org.db_name}")
            print(f"  DB Username: {org.db_username}")
            print(f"  Has Password: {bool(org.db_password_encrypted)}")
            print(f"  Subscription Tier: {org.subscription_tier}")
            print(f"  Is Active: {org.is_active}")
            print(f"  User Count: {user_count}")
            print(f"  Created At: {org.created_at}")
    
    print("\n" + "=" * 80)
    print(f"Total Organizations: {len(orgs)}")
    print("=" * 80)
