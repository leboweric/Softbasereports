"""
Script to encrypt the existing customer's database password
"""

import os
from src.services.credential_manager import get_credential_manager

# Make sure CREDENTIAL_ENCRYPTION_KEY is set
if not os.getenv('CREDENTIAL_ENCRYPTION_KEY'):
    print("ERROR: CREDENTIAL_ENCRYPTION_KEY not set in environment")
    exit(1)

# Get the current Azure SQL password from environment
current_password = os.getenv('AZURE_SQL_PASSWORD')

if not current_password:
    print("ERROR: AZURE_SQL_PASSWORD not set in environment")
    exit(1)

# Encrypt it
cm = get_credential_manager()
encrypted_password = cm.encrypt_password(current_password)

print("=" * 80)
print("ENCRYPTED PASSWORD FOR MIGRATION")
print("=" * 80)
print(f"\nEncrypted password:\n{encrypted_password}\n")
print("=" * 80)
print("\nCopy this value and use it in the migration SQL script.")
print("=" * 80)