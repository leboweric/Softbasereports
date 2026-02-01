-- mart_department_metrics: Pre-aggregated department dashboard data
-- Refreshed bi-hourly during business hours for instant page loads

CREATE TABLE IF NOT EXISTS mart_department_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    department VARCHAR(50) NOT NULL,  -- 'service', 'parts', 'rental', 'accounting', 'financial'
    snapshot_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    
    -- Monthly revenue data (JSON array of {year, month, amount, margin, prior_year_amount})
    monthly_revenue JSONB,
    
    -- Sub-category revenue (JSON array - varies by department)
    -- Service: field_revenue, shop_revenue
    -- Parts: counter_revenue, repair_order_revenue
    -- Rental: monthly_trend
    sub_category_1 JSONB,
    sub_category_2 JSONB,
    
    -- Summary metrics (varies by department)
    metric_1 DECIMAL(15,2),  -- Service: current month labor | Parts: current month parts | Rental: total fleet | Accounting: total expenses | Financial: total AR
    metric_2 DECIMAL(15,2),  -- Service: YTD labor | Parts: YTD parts | Rental: units on rent | Accounting: avg monthly | Financial: past due
    metric_3 DECIMAL(15,2),  -- Service: avg margin | Parts: avg margin | Rental: utilization rate | Accounting: N/A | Financial: over 90 days
    metric_4 DECIMAL(15,2),  -- Additional metric as needed
    
    -- Counts
    count_1 INTEGER,  -- Rental: fleet size | Financial: customers with balance
    count_2 INTEGER,  -- Rental: units on rent
    
    -- Additional JSON data
    additional_data JSONB,  -- For department-specific data (top customers, expense categories, etc.)
    
    -- ETL metadata
    etl_duration_seconds DECIMAL(10,2),
    
    -- Constraints
    UNIQUE(org_id, department, snapshot_timestamp)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_mart_department_metrics_lookup 
ON mart_department_metrics(org_id, department, snapshot_timestamp DESC);

-- Comment
COMMENT ON TABLE mart_department_metrics IS 'Pre-aggregated department dashboard metrics for instant page loads. Refreshed bi-hourly.';
