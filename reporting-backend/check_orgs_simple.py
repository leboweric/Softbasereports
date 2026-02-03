#!/usr/bin/env python3
"""
Simple script to check organizations in the SQLite database directly
"""
import sqlite3
import os

# Find the database file
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src', 'database', 'app.db')

if not os.path.exists(db_path):
    print(f"Database not found at: {db_path}")
    # Try alternative paths
    alt_paths = [
        '/home/ubuntu/SoftbaseCode/reporting-backend/app.db',
        '/home/ubuntu/SoftbaseCode/reporting-backend/instance/app.db',
        './app.db',
        './instance/app.db'
    ]
    for alt in alt_paths:
        if os.path.exists(alt):
            db_path = alt
            print(f"Found database at: {db_path}")
            break
    else:
        print("Could not find database file!")
        exit(1)

print(f"Using database: {db_path}")
print("=" * 80)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get all organizations
cursor.execute("SELECT * FROM organization")
orgs = cursor.fetchall()

print(f"\nFound {len(orgs)} organizations:\n")

for org in orgs:
    print(f"Organization ID: {org['id']}")
    print(f"  Name: {org['name']}")
    print(f"  Platform Type: {org['platform_type']}")
    print(f"  Database Schema: {org['database_schema']}")
    print(f"  DB Server: {org['db_server']}")
    print(f"  DB Name: {org['db_name']}")
    print(f"  DB Username: {org['db_username']}")
    print(f"  Has Password: {bool(org['db_password_encrypted'])}")
    print(f"  Subscription Tier: {org['subscription_tier']}")
    print(f"  Is Active: {org['is_active']}")
    
    # Count users for this org
    cursor.execute("SELECT COUNT(*) as count FROM user WHERE organization_id = ?", (org['id'],))
    user_count = cursor.fetchone()['count']
    print(f"  User Count: {user_count}")
    print()

conn.close()
print("=" * 80)
