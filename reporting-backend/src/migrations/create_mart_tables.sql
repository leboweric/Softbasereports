-- AIOP Data Mart Layer Migration
-- Version: 1.0
-- Date: January 20, 2026
-- Description: Creates all Mart tables for multi-tenant data warehouse

-- ============================================================
-- 3.1 Financial Metrics (QuickBooks)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_financial_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    
    -- Income Statement
    total_revenue NUMERIC(18,2) DEFAULT 0,
    total_expenses NUMERIC(18,2) DEFAULT 0,
    net_income NUMERIC(18,2) DEFAULT 0,
    gross_profit NUMERIC(18,2) DEFAULT 0,
    gross_margin_pct NUMERIC(5,2) DEFAULT 0,
    
    -- Balance Sheet Highlights
    total_assets NUMERIC(18,2) DEFAULT 0,
    total_liabilities NUMERIC(18,2) DEFAULT 0,
    total_equity NUMERIC(18,2) DEFAULT 0,
    cash_balance NUMERIC(18,2) DEFAULT 0,
    accounts_receivable NUMERIC(18,2) DEFAULT 0,
    accounts_payable NUMERIC(18,2) DEFAULT 0,
    
    -- Cash Flow
    operating_cash_flow NUMERIC(18,2) DEFAULT 0,
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'quickbooks',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, year, month)
);

CREATE INDEX IF NOT EXISTS idx_mart_financial_org_period ON mart_financial_metrics(org_id, year, month);

-- ============================================================
-- 3.2 CRM Contacts (HubSpot)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_crm_contacts (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    snapshot_date DATE NOT NULL,
    
    -- Contact Counts
    total_contacts INTEGER DEFAULT 0,
    new_contacts_30d INTEGER DEFAULT 0,
    new_contacts_7d INTEGER DEFAULT 0,
    
    -- Lifecycle Stage Breakdown
    subscribers INTEGER DEFAULT 0,
    leads INTEGER DEFAULT 0,
    marketing_qualified INTEGER DEFAULT 0,
    sales_qualified INTEGER DEFAULT 0,
    opportunities INTEGER DEFAULT 0,
    customers INTEGER DEFAULT 0,
    evangelists INTEGER DEFAULT 0,
    other_lifecycle INTEGER DEFAULT 0,
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'hubspot',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_mart_crm_contacts_org_date ON mart_crm_contacts(org_id, snapshot_date);

-- ============================================================
-- 3.2 CRM Deals (HubSpot)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_crm_deals (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    snapshot_date DATE NOT NULL,
    
    -- Deal Counts
    total_deals INTEGER DEFAULT 0,
    open_deals INTEGER DEFAULT 0,
    won_deals INTEGER DEFAULT 0,
    lost_deals INTEGER DEFAULT 0,
    
    -- Deal Values
    total_pipeline_value NUMERIC(18,2) DEFAULT 0,
    won_value NUMERIC(18,2) DEFAULT 0,
    lost_value NUMERIC(18,2) DEFAULT 0,
    average_deal_size NUMERIC(18,2) DEFAULT 0,
    
    -- Pipeline Stage Breakdown (JSON for flexibility)
    deals_by_stage JSONB DEFAULT '{}',
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'hubspot',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_mart_crm_deals_org_date ON mart_crm_deals(org_id, snapshot_date);

-- ============================================================
-- 3.3 Communication Metrics (Zoom)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_zoom_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    metric_date DATE NOT NULL,
    
    -- User Counts
    total_users INTEGER DEFAULT 0,
    phone_users INTEGER DEFAULT 0,
    
    -- Meeting Metrics
    total_meetings INTEGER DEFAULT 0,
    total_meeting_minutes INTEGER DEFAULT 0,
    total_participants INTEGER DEFAULT 0,
    avg_meeting_duration_mins NUMERIC(8,2) DEFAULT 0,
    
    -- Call Center Metrics (Zoom Phone)
    total_calls INTEGER DEFAULT 0,
    inbound_calls INTEGER DEFAULT 0,
    outbound_calls INTEGER DEFAULT 0,
    missed_calls INTEGER DEFAULT 0,
    total_call_minutes INTEGER DEFAULT 0,
    avg_call_duration_mins NUMERIC(8,2) DEFAULT 0,
    
    -- Queue Metrics
    queue_count INTEGER DEFAULT 0,
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'zoom',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, metric_date)
);

CREATE INDEX IF NOT EXISTS idx_mart_zoom_org_date ON mart_zoom_metrics(org_id, metric_date);

-- ============================================================
-- 3.4 Case Management Metrics (VITAL Azure SQL)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_case_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    snapshot_date DATE NOT NULL,
    
    -- Case Counts
    total_cases INTEGER DEFAULT 0,
    new_cases_30d INTEGER DEFAULT 0,
    closed_cases_30d INTEGER DEFAULT 0,
    
    -- Case Breakdown (flexible JSON for various groupings)
    cases_by_type JSONB DEFAULT '{}',
    cases_by_status JSONB DEFAULT '{}',
    cases_by_category JSONB DEFAULT '{}',
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'azure_sql',
    source_table VARCHAR(100) DEFAULT 'Case_Data_Summary_NOPHI',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_mart_case_org_date ON mart_case_metrics(org_id, snapshot_date);

-- ============================================================
-- 3.5 Mobile App Analytics (BigQuery/GA4)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_app_analytics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    metric_date DATE NOT NULL,
    
    -- User Metrics
    daily_active_users INTEGER DEFAULT 0,
    weekly_active_users INTEGER DEFAULT 0,
    monthly_active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    returning_users INTEGER DEFAULT 0,
    
    -- Engagement Metrics
    total_sessions INTEGER DEFAULT 0,
    avg_session_duration_secs NUMERIC(10,2) DEFAULT 0,
    screens_per_session NUMERIC(8,2) DEFAULT 0,
    
    -- App Downloads (if available)
    ios_downloads INTEGER DEFAULT 0,
    android_downloads INTEGER DEFAULT 0,
    
    -- Top Screens (JSON for flexibility)
    top_screens JSONB DEFAULT '[]',
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'bigquery_ga4',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, metric_date)
);

CREATE INDEX IF NOT EXISTS idx_mart_app_org_date ON mart_app_analytics(org_id, metric_date);

-- ============================================================
-- 3.6 Sales & Revenue Metrics (Bennett - Softbase)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_sales_daily (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    sales_date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    day_of_week INTEGER,  -- 0=Sunday, 6=Saturday
    
    -- Revenue by Department
    service_revenue NUMERIC(18,2) DEFAULT 0,
    parts_revenue NUMERIC(18,2) DEFAULT 0,
    rental_revenue NUMERIC(18,2) DEFAULT 0,
    sales_revenue NUMERIC(18,2) DEFAULT 0,
    total_revenue NUMERIC(18,2) DEFAULT 0,
    
    -- Invoice Counts
    service_invoices INTEGER DEFAULT 0,
    parts_invoices INTEGER DEFAULT 0,
    rental_invoices INTEGER DEFAULT 0,
    sales_invoices INTEGER DEFAULT 0,
    total_invoices INTEGER DEFAULT 0,
    
    -- Work Order Metrics
    open_work_orders INTEGER DEFAULT 0,
    closed_work_orders INTEGER DEFAULT 0,
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'softbase',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, sales_date)
);

CREATE INDEX IF NOT EXISTS idx_mart_sales_org_date ON mart_sales_daily(org_id, sales_date);
CREATE INDEX IF NOT EXISTS idx_mart_sales_org_year_month ON mart_sales_daily(org_id, year, month);

-- ============================================================
-- 3.7 Rental Fleet Metrics (Bennett - Softbase)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_rental_fleet (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    snapshot_date DATE NOT NULL,
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    
    -- Fleet Counts
    total_units INTEGER DEFAULT 0,
    available_units INTEGER DEFAULT 0,
    rented_units INTEGER DEFAULT 0,
    maintenance_units INTEGER DEFAULT 0,
    
    -- Utilization
    utilization_rate NUMERIC(5,2) DEFAULT 0,  -- Percentage
    
    -- Revenue
    rental_revenue_mtd NUMERIC(18,2) DEFAULT 0,
    rental_revenue_ytd NUMERIC(18,2) DEFAULT 0,
    
    -- By Equipment Type (JSON for flexibility)
    units_by_type JSONB DEFAULT '{}',
    revenue_by_type JSONB DEFAULT '{}',
    
    -- Customer Breakdown
    active_rental_customers INTEGER DEFAULT 0,
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'softbase',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, snapshot_date)
);

CREATE INDEX IF NOT EXISTS idx_mart_rental_org_date ON mart_rental_fleet(org_id, snapshot_date);

-- ============================================================
-- 3.8 Cash Flow Metrics (Bennett - Softbase GL)
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_cash_flow (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL,
    
    -- Time dimensions
    year INTEGER NOT NULL,
    month INTEGER NOT NULL,
    period_end DATE NOT NULL,
    
    -- Cash Position
    cash_balance NUMERIC(18,2) DEFAULT 0,
    cash_change_mtd NUMERIC(18,2) DEFAULT 0,
    
    -- Operating Cash Flow
    operating_cash_flow NUMERIC(18,2) DEFAULT 0,
    
    -- Working Capital Changes
    ar_change NUMERIC(18,2) DEFAULT 0,
    inventory_change NUMERIC(18,2) DEFAULT 0,
    ap_change NUMERIC(18,2) DEFAULT 0,
    
    -- Non-Operating
    investing_cash_flow NUMERIC(18,2) DEFAULT 0,
    financing_cash_flow NUMERIC(18,2) DEFAULT 0,
    
    -- Health Indicator
    health_status VARCHAR(20) DEFAULT 'unknown',  -- healthy, warning, critical
    
    -- Breakdown (JSON for detailed analysis)
    non_operating_breakdown JSONB DEFAULT '{}',
    
    -- Metadata
    source_system VARCHAR(50) DEFAULT 'softbase_gl',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, year, month)
);

CREATE INDEX IF NOT EXISTS idx_mart_cash_org_period ON mart_cash_flow(org_id, year, month);

-- ============================================================
-- ETL Job Tracking Table
-- ============================================================
CREATE TABLE IF NOT EXISTS mart_etl_log (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(100) NOT NULL,
    org_id INTEGER,
    
    -- Execution details
    started_at TIMESTAMP NOT NULL,
    completed_at TIMESTAMP,
    status VARCHAR(20) NOT NULL,  -- running, success, failed
    
    -- Results
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Metadata
    source_system VARCHAR(50),
    target_table VARCHAR(100)
);

CREATE INDEX IF NOT EXISTS idx_mart_etl_job ON mart_etl_log(job_name, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_mart_etl_status ON mart_etl_log(status, started_at DESC);

-- ============================================================
-- Success message
-- ============================================================
-- All Mart tables created successfully!
