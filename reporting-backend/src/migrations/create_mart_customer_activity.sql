-- ============================================================
-- Mart Customer Activity Table
-- Tracks customer activity for churn analysis
-- ============================================================

CREATE TABLE IF NOT EXISTS mart_customer_activity (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Customer Identification
    customer_name VARCHAR(255) NOT NULL,
    bill_to VARCHAR(100),
    
    -- Activity Metrics (Last 90 days - "Recent Period")
    recent_invoice_count INTEGER DEFAULT 0,
    recent_revenue NUMERIC(18,2) DEFAULT 0,
    recent_service_revenue NUMERIC(18,2) DEFAULT 0,
    recent_parts_revenue NUMERIC(18,2) DEFAULT 0,
    recent_rental_revenue NUMERIC(18,2) DEFAULT 0,
    recent_first_invoice DATE,
    recent_last_invoice DATE,
    
    -- Activity Metrics (Previous 90 days - "Previous Period")
    previous_invoice_count INTEGER DEFAULT 0,
    previous_revenue NUMERIC(18,2) DEFAULT 0,
    previous_service_revenue NUMERIC(18,2) DEFAULT 0,
    previous_parts_revenue NUMERIC(18,2) DEFAULT 0,
    previous_rental_revenue NUMERIC(18,2) DEFAULT 0,
    
    -- Lifetime Metrics
    lifetime_invoice_count INTEGER DEFAULT 0,
    lifetime_revenue NUMERIC(18,2) DEFAULT 0,
    first_invoice_date DATE,
    last_invoice_date DATE,
    days_since_last_invoice INTEGER DEFAULT 0,
    
    -- Churn Status
    activity_status VARCHAR(20) DEFAULT 'active',  -- active, at_risk, churned, new
    revenue_change_percent NUMERIC(8,2) DEFAULT 0,
    
    -- Work Order Breakdown (JSON for flexibility)
    work_order_breakdown JSONB DEFAULT '{}',
    
    -- Monthly Revenue Trend (last 12 months)
    monthly_revenue_trend JSONB DEFAULT '[]',
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'softbase',
    snapshot_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, customer_name, snapshot_date)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_mart_customer_org_status ON mart_customer_activity(org_id, activity_status);
CREATE INDEX IF NOT EXISTS idx_mart_customer_org_date ON mart_customer_activity(org_id, snapshot_date);
CREATE INDEX IF NOT EXISTS idx_mart_customer_name ON mart_customer_activity(org_id, customer_name);
CREATE INDEX IF NOT EXISTS idx_mart_customer_last_invoice ON mart_customer_activity(org_id, last_invoice_date);

-- Success message
-- mart_customer_activity table created successfully!
