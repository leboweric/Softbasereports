"""
Check current organization record before migration
"""

from src.models.user import Organization
from src.main import app

with app.app_context():
    orgs = Organization.query.all()
    
    print("=" * 80)
    print("CURRENT ORGANIZATION RECORDS")
    print("=" * 80)
    
    for org in orgs:
        print(f"ID: {org.id}")
        print(f"Name: {org.name}")
        print(f"Platform Type: {org.platform_type}")
        print(f"DB Server: {org.db_server}")
        print(f"DB Name: {org.db_name}")
        print(f"DB Username: {org.db_username}")
        print(f"Encrypted Password: {org.db_password_encrypted}")
        print(f"Subscription Tier: {org.subscription_tier}")
        print(f"Max Users: {org.max_users}")
        print(f"Is Active: {org.is_active}")
        print("-" * 40)
    
    print("=" * 80)