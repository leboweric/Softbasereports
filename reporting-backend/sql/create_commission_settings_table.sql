-- Table to store whether specific invoice lines are commissionable
-- This allows users to manually control which invoices generate commissions
CREATE TABLE IF NOT EXISTS commission_settings (
    id SERIAL PRIMARY KEY,
    invoice_no INTEGER NOT NULL,
    sale_code VARCHAR(50),
    category VARCHAR(100),
    -- Unique identifier for the invoice line (combination of invoice + sale_code + category)
    is_commissionable BOOLEAN DEFAULT TRUE,
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by VARCHAR(100),
    -- Create a unique constraint to prevent duplicate entries
    CONSTRAINT unique_invoice_line UNIQUE (invoice_no, sale_code, category)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_commission_invoice_no ON commission_settings(invoice_no);
CREATE INDEX IF NOT EXISTS idx_commission_is_commissionable ON commission_settings(is_commissionable);

-- Add a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_commission_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_commission_settings_timestamp ON commission_settings;
CREATE TRIGGER update_commission_settings_timestamp
BEFORE UPDATE ON commission_settings
FOR EACH ROW
EXECUTE FUNCTION update_commission_settings_timestamp();