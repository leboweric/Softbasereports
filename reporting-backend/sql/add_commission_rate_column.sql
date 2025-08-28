-- Add commission_rate column to store the selected commission rate for rental invoices
-- This allows users to choose between 10% and 5% for rental commissions

ALTER TABLE commission_settings 
ADD COLUMN commission_rate DECIMAL(5,2);

-- Set default rate for rentals to 10% (0.10)
UPDATE commission_settings 
SET commission_rate = 0.10 
WHERE category = 'Rental' AND commission_rate IS NULL;