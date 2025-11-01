"""
Run the migration script to update organization with multi-tenant fields
"""

from src.models.user import Organization, db
from src.main import app

with app.app_context():
    # Get the organization
    org = Organization.query.filter_by(id=1).first()
    
    if not org:
        print("ERROR: Organization with ID 1 not found")
        exit(1)
    
    print(f"Before migration - Organization: {org.name}")
    print(f"  Platform Type: {org.platform_type}")
    print(f"  DB Server: {org.db_server}")
    
    # Update the organization with multi-tenant configuration
    org.platform_type = 'evolution'
    org.db_server = 'evo1-sql-replica.database.windows.net'
    org.db_name = 'evo'
    org.db_username = 'ben002user'
    org.db_password_encrypted = 'gAAAAABpBkzh22K1A1_QVFuArNXgew0RJYMrML52iM_L3ZJSLIN89bUXu_IS7ROmKeq86e5Lvr-iFPM94gl0Fq-U1sPDDwZ5OAFbz_s_jtjPHc9oNs9qF5g='
    org.subscription_tier = 'enterprise'
    org.max_users = 50
    
    # Commit the changes
    db.session.commit()
    
    print("\n✅ Migration completed successfully!")
    print(f"\nAfter migration - Organization: {org.name}")
    print(f"  Platform Type: {org.platform_type}")
    print(f"  DB Server: {org.db_server}")
    print(f"  DB Name: {org.db_name}")
    print(f"  DB Username: {org.db_username}")
    print(f"  Subscription Tier: {org.subscription_tier}")
    print(f"  Max Users: {org.max_users}")
    print(f"  Encrypted Password: {org.db_password_encrypted[:50]}...") # Show first 50 chars