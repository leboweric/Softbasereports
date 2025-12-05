-- Table to store manual commission entries
-- This allows users to add commission entries for specific sales reps
-- when invoices are assigned to the wrong rep or need manual adjustments
CREATE TABLE IF NOT EXISTS manual_commissions (
    id SERIAL PRIMARY KEY,
    salesman_name VARCHAR(100) NOT NULL,
    month VARCHAR(7) NOT NULL,  -- Format: YYYY-MM
    -- Invoice-like fields (to match the detail breakdown display)
    invoice_no VARCHAR(50),  -- Can be manual/reference number
    invoice_date DATE,
    bill_to VARCHAR(100),
    customer_name VARCHAR(200),
    sale_code VARCHAR(50),
    category VARCHAR(100),
    amount DECIMAL(12, 2) DEFAULT 0,
    cost DECIMAL(12, 2),  -- Optional cost for profit calculation
    commission_amount DECIMAL(12, 2) DEFAULT 0,
    description TEXT,  -- Optional note explaining why this was added
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    updated_by VARCHAR(100)
);

-- Indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_manual_commissions_salesman ON manual_commissions(salesman_name);
CREATE INDEX IF NOT EXISTS idx_manual_commissions_month ON manual_commissions(month);
CREATE INDEX IF NOT EXISTS idx_manual_commissions_salesman_month ON manual_commissions(salesman_name, month);

-- Add a trigger to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_manual_commissions_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_manual_commissions_timestamp ON manual_commissions;
CREATE TRIGGER update_manual_commissions_timestamp
BEFORE UPDATE ON manual_commissions
FOR EACH ROW
EXECUTE FUNCTION update_manual_commissions_timestamp();
