-- Migration: Add database_schema column for multi-tenant data isolation
-- Run this BEFORE deploying the multi-tenancy code changes
-- Date: 2026-01-02

-- Step 1: Add the database_schema column to organization table
ALTER TABLE organization 
ADD COLUMN IF NOT EXISTS database_schema VARCHAR(50);

-- Step 2: Set Bennett Material Handling's schema (organization_id = 1)
-- This is the existing production tenant using the ben002 schema
UPDATE organization 
SET database_schema = 'ben002' 
WHERE id = 1;

-- Step 3: Verify the update
SELECT id, name, database_schema 
FROM organization 
WHERE id = 1;

-- Note: For new tenants, you must set database_schema when creating the organization
-- Example for VITAL Worklife (if organization already exists):
-- UPDATE organization SET database_schema = 'vital001' WHERE name = 'VITAL Worklife';
