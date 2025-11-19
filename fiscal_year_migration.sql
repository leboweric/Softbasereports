-- Migration: Add fiscal_year_start_month to Organization table
-- Purpose: Allow per-organization fiscal year configuration
-- Date: 2025-11-19

-- Add the fiscal_year_start_month column with default value of 11 (November)
ALTER TABLE organization 
ADD COLUMN fiscal_year_start_month INTEGER DEFAULT 11;

-- Add a comment to document the column
COMMENT ON COLUMN organization.fiscal_year_start_month IS 'Fiscal year start month (1-12, where 1=January, 11=November). Defaults to 11 for November fiscal year start.';

-- Add a check constraint to ensure valid month values (1-12)
ALTER TABLE organization 
ADD CONSTRAINT check_fiscal_year_start_month 
CHECK (fiscal_year_start_month >= 1 AND fiscal_year_start_month <= 12);

-- Update existing organizations to use November (11) as default if NULL
UPDATE organization 
SET fiscal_year_start_month = 11 
WHERE fiscal_year_start_month IS NULL;

-- Verify the migration
SELECT id, name, fiscal_year_start_month 
FROM organization 
ORDER BY id;
