-- ============================================================================
-- Migrate Existing Customer to Multi-Tenant Architecture
-- ============================================================================

-- This script updates the existing organization with multi-tenant configuration
-- Encrypted password generated from encrypt_existing_password.py

BEGIN;

-- Update the organization record
-- Assuming the existing organization has id=1 (adjust if different)
UPDATE organization
SET 
    platform_type = 'evolution',
    db_server = 'evo1-sql-replica.database.windows.net',
    db_name = 'evo',
    db_username = 'ben002user',
    db_password_encrypted = 'gAAAAABpBkzh22K1A1_QVFuArNXgew0RJYMrML52iM_L3ZJSLIN89bUXu_IS7ROmKeq86e5Lvr-iFPM94gl0Fq-U1sPDDwZ5OAFbz_s_jtjPHc9oNs9qF5g=',
    subscription_tier = 'enterprise',  -- Set appropriate tier
    max_users = 50  -- Set appropriate limit
WHERE id = 1;  -- Adjust ID if needed

COMMIT;

-- Verify the update
SELECT 
    id,
    name,
    platform_type,
    db_server,
    db_name,
    db_username,
    subscription_tier,
    max_users,
    is_active
FROM organization
WHERE id = 1;

-- ============================================================================
-- Expected Output:
-- You should see the organization record with all the new fields populated
-- The db_password_encrypted field should contain the encrypted password
-- ============================================================================