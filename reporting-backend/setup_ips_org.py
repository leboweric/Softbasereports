#!/usr/bin/env python3
"""
Setup Industrial Parts and Service organization with correct database credentials
"""
import os
import psycopg2
from cryptography.fernet import Fernet

# Set the encryption key (same as used in production)
ENCRYPTION_KEY = 'iuvsi7GwSgz0j0pG1rJO69YK3Y1Aj1RRuNPajbti3bE='

# Industrial Parts and Service credentials from Softbase
IPS_CONFIG = {
    'org_id': 7,
    'name': 'Industrial Parts and Service',
    'platform_type': 'evolution',
    'database_schema': 'ind004',
    'db_server': 'evo1-sql-replica.database.windows.net',
    'db_name': 'evo',
    'db_username': 'ind004user',
    'db_password': 'a20135Jb06Red5Jn',
    'subscription_tier': 'enterprise',
    'is_active': True
}

# PostgreSQL connection
POSTGRES_URL = 'postgresql://postgres:ZINQrdsRJEQeYMsLEPazJJbyztwWSMiY@nozomi.proxy.rlwy.net:45435/railway'

def encrypt_password(password: str) -> str:
    """Encrypt password using Fernet"""
    cipher = Fernet(ENCRYPTION_KEY.encode())
    encrypted = cipher.encrypt(password.encode())
    return encrypted.decode()

def main():
    print("=" * 80)
    print("Setting up Industrial Parts and Service Organization")
    print("=" * 80)
    
    # Encrypt the password
    encrypted_password = encrypt_password(IPS_CONFIG['db_password'])
    print(f"\n✅ Password encrypted successfully")
    
    # Connect to PostgreSQL
    conn = psycopg2.connect(POSTGRES_URL)
    cursor = conn.cursor()
    
    # Update the organization
    update_query = """
        UPDATE organization 
        SET 
            platform_type = %s,
            database_schema = %s,
            db_server = %s,
            db_name = %s,
            db_username = %s,
            db_password_encrypted = %s,
            subscription_tier = %s,
            is_active = %s
        WHERE id = %s
    """
    
    cursor.execute(update_query, (
        IPS_CONFIG['platform_type'],
        IPS_CONFIG['database_schema'],
        IPS_CONFIG['db_server'],
        IPS_CONFIG['db_name'],
        IPS_CONFIG['db_username'],
        encrypted_password,
        IPS_CONFIG['subscription_tier'],
        IPS_CONFIG['is_active'],
        IPS_CONFIG['org_id']
    ))
    
    conn.commit()
    print(f"✅ Organization ID {IPS_CONFIG['org_id']} updated successfully")
    
    # Verify the update
    cursor.execute("""
        SELECT id, name, platform_type, database_schema, db_server, db_name, db_username,
               CASE WHEN db_password_encrypted IS NOT NULL THEN 'YES' ELSE 'NO' END as has_password,
               subscription_tier, is_active
        FROM organization
        WHERE id = %s
    """, (IPS_CONFIG['org_id'],))
    
    org = cursor.fetchone()
    print(f"\n📋 Updated Organization Details:")
    print(f"   ID: {org[0]}")
    print(f"   Name: {org[1]}")
    print(f"   Platform Type: {org[2]}")
    print(f"   Database Schema: {org[3]}")
    print(f"   DB Server: {org[4]}")
    print(f"   DB Name: {org[5]}")
    print(f"   DB Username: {org[6]}")
    print(f"   Has Password: {org[7]}")
    print(f"   Subscription Tier: {org[8]}")
    print(f"   Is Active: {org[9]}")
    
    conn.close()
    print("\n" + "=" * 80)
    print("✅ Industrial Parts and Service setup complete!")
    print("=" * 80)

if __name__ == '__main__':
    main()
