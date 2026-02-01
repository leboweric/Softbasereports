-- ============================================================
-- Mart CEO Metrics Table
-- Pre-aggregated metrics for fast CEO Dashboard loading
-- Refreshes every 2 hours during business hours
-- ============================================================

CREATE TABLE IF NOT EXISTS mart_ceo_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Snapshot timestamp
    snapshot_timestamp TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    snapshot_date DATE NOT NULL,
    
    -- KPI Metrics
    current_month_sales NUMERIC(18,2) DEFAULT 0,
    ytd_sales NUMERIC(18,2) DEFAULT 0,
    inventory_count INTEGER DEFAULT 0,
    active_customers INTEGER DEFAULT 0,
    active_customers_previous INTEGER DEFAULT 0,
    total_customers INTEGER DEFAULT 0,
    
    -- Work Order Metrics
    open_work_orders_count INTEGER DEFAULT 0,
    open_work_orders_value NUMERIC(18,2) DEFAULT 0,
    open_work_orders_previous_value NUMERIC(18,2) DEFAULT 0,
    uninvoiced_wo_count INTEGER DEFAULT 0,
    uninvoiced_wo_value NUMERIC(18,2) DEFAULT 0,
    awaiting_invoice_count INTEGER DEFAULT 0,
    awaiting_invoice_value NUMERIC(18,2) DEFAULT 0,
    awaiting_invoice_avg_days NUMERIC(8,2) DEFAULT 0,
    
    -- Work Order Types Breakdown (JSON)
    work_order_types JSONB DEFAULT '[]',
    
    -- Monthly Sales Data (JSON - last 13 months)
    monthly_sales JSONB DEFAULT '[]',
    monthly_sales_excluding_equipment JSONB DEFAULT '[]',
    monthly_sales_by_stream JSONB DEFAULT '[]',
    
    -- Equipment Sales (JSON)
    monthly_equipment_sales JSONB DEFAULT '[]',
    
    -- Monthly Work Orders (JSON)
    monthly_work_orders JSONB DEFAULT '[]',
    
    -- Monthly Quotes (JSON)
    monthly_quotes JSONB DEFAULT '[]',
    
    -- Department P&L (JSON)
    department_margins JSONB DEFAULT '[]',
    
    -- Top Customers (JSON)
    top_customers JSONB DEFAULT '[]',
    
    -- Invoice Delay Metrics (JSON)
    monthly_invoice_delays JSONB DEFAULT '[]',
    
    -- Parts Work Orders
    open_parts_wo_count INTEGER DEFAULT 0,
    open_parts_wo_value NUMERIC(18,2) DEFAULT 0,
    parts_awaiting_invoice_count INTEGER DEFAULT 0,
    parts_awaiting_invoice_value NUMERIC(18,2) DEFAULT 0,
    
    -- Fiscal Year Info
    fiscal_year_start DATE,
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'softbase',
    etl_duration_seconds NUMERIC(8,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, snapshot_timestamp)
);

-- Indexes for fast queries
CREATE INDEX IF NOT EXISTS idx_mart_ceo_org_date ON mart_ceo_metrics(org_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_mart_ceo_org_timestamp ON mart_ceo_metrics(org_id, snapshot_timestamp DESC);

-- View to get latest metrics for each org
CREATE OR REPLACE VIEW v_latest_ceo_metrics AS
SELECT DISTINCT ON (org_id) *
FROM mart_ceo_metrics
ORDER BY org_id, snapshot_timestamp DESC;

-- Success message
-- mart_ceo_metrics table created successfully!
