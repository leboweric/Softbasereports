-- Add extra_commission column to store user-defined additional commission amounts
-- This allows users to add bonuses or adjustments to the calculated commission

ALTER TABLE commission_settings 
ADD COLUMN extra_commission DECIMAL(12,2) DEFAULT 0;

-- The extra_commission will be added to the calculated commission
-- Can be positive (bonus) or negative (reduction)