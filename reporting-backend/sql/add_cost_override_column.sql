-- Add cost_override column to store user-adjusted costs for New/Allied equipment
-- This allows users to override the cost from the database for commission calculations

ALTER TABLE commission_settings 
ADD COLUMN cost_override DECIMAL(12,2);

-- The cost_override will be NULL by default, meaning use the original cost from InvoiceReg
-- When set, it will override the cost for profit and commission calculations