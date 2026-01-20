# AIOP Data Mart Layer Schema Design

**Version:** 1.0
**Date:** January 20, 2026
**Status:** Design Phase

---

## 1. Overview

This document defines the schema for the AIOP Data Mart layer, which will store pre-aggregated data from all source systems for both Bennett and VITAL WorkLife organizations. All tables use a multi-tenant design with `org_id` for data isolation.

---

## 2. Multi-Tenancy Design

All Mart tables include:
- `org_id` (INTEGER, NOT NULL) - Foreign key to organizations table
- `created_at` (TIMESTAMP) - When the record was created
- `updated_at` (TIMESTAMP) - When the record was last updated by ETL

This allows:
- Single query across all orgs (for admin dashboards)
- Filtered queries per org (for tenant dashboards)
- Efficient indexing on org_id + date columns

---

## 3. Mart Table Schemas

### 3.1 Financial Metrics (QuickBooks)

**Table: `mart_financial_metrics`**

Stores monthly financial summaries from QuickBooks for both organizations.

```sql
CREATE TABLE IF NOT EXISTS mart_financial_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_financial_org_period ON mart_financial_metrics(org_id, year, month);
```

---

### 3.2 CRM Metrics (HubSpot)

**Table: `mart_crm_contacts`**

Stores contact and lead metrics from HubSpot.

```sql
CREATE TABLE IF NOT EXISTS mart_crm_contacts (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_crm_contacts_org_date ON mart_crm_contacts(org_id, snapshot_date);
```

**Table: `mart_crm_deals`**

Stores deal/pipeline metrics from HubSpot.

```sql
CREATE TABLE IF NOT EXISTS mart_crm_deals (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_crm_deals_org_date ON mart_crm_deals(org_id, snapshot_date);
```

---

### 3.3 Communication Metrics (Zoom)

**Table: `mart_zoom_metrics`**

Stores Zoom meeting and call center metrics.

```sql
CREATE TABLE IF NOT EXISTS mart_zoom_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_zoom_org_date ON mart_zoom_metrics(org_id, metric_date);
```

---

### 3.4 Case Management Metrics (VITAL Azure SQL)

**Table: `mart_case_metrics`**

Stores aggregated case data from VITAL's Case_Data_Summary_NOPHI table.

```sql
CREATE TABLE IF NOT EXISTS mart_case_metrics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_case_org_date ON mart_case_metrics(org_id, snapshot_date);
```

---

### 3.5 Mobile App Analytics (BigQuery/GA4)

**Table: `mart_app_analytics`**

Stores mobile app analytics from BigQuery/GA4.

```sql
CREATE TABLE IF NOT EXISTS mart_app_analytics (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_app_org_date ON mart_app_analytics(org_id, metric_date);
```

---

### 3.6 Sales & Revenue Metrics (Bennett - Softbase)

**Table: `mart_sales_daily`**

Stores daily sales summaries from Softbase for Bennett.

```sql
CREATE TABLE IF NOT EXISTS mart_sales_daily (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_sales_org_date ON mart_sales_daily(org_id, sales_date);
CREATE INDEX idx_mart_sales_org_year_month ON mart_sales_daily(org_id, year, month);
```

---

### 3.7 Rental Fleet Metrics (Bennett - Softbase)

**Table: `mart_rental_fleet`**

Stores rental fleet utilization metrics to replace the slow Rental Service Report.

```sql
CREATE TABLE IF NOT EXISTS mart_rental_fleet (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_rental_org_date ON mart_rental_fleet(org_id, snapshot_date);
```

---

### 3.8 Cash Flow Metrics (Bennett - Softbase GL)

**Table: `mart_cash_flow`**

Stores pre-computed cash flow metrics to replace the slow Cash Burn report.

```sql
CREATE TABLE IF NOT EXISTS mart_cash_flow (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organizations(id),
    
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

CREATE INDEX idx_mart_cash_org_period ON mart_cash_flow(org_id, year, month);
```

---

## 4. ETL Job Schedule

| Job Name | Source | Target Table | Frequency | Org |
|----------|--------|--------------|-----------|-----|
| `etl_quickbooks_financial` | QuickBooks API | mart_financial_metrics | Daily 2 AM | Both |
| `etl_hubspot_contacts` | HubSpot API | mart_crm_contacts | Daily 3 AM | VITAL |
| `etl_hubspot_deals` | HubSpot API | mart_crm_deals | Daily 3 AM | VITAL |
| `etl_zoom_metrics` | Zoom API | mart_zoom_metrics | Daily 4 AM | VITAL |
| `etl_case_metrics` | Azure SQL | mart_case_metrics | Daily 5 AM | VITAL |
| `etl_app_analytics` | BigQuery | mart_app_analytics | Daily 6 AM | VITAL |
| `etl_sales_daily` | Azure SQL (Softbase) | mart_sales_daily | Daily 1 AM | Bennett |
| `etl_rental_fleet` | Azure SQL (Softbase) | mart_rental_fleet | Daily 1:30 AM | Bennett |
| `etl_cash_flow` | Azure SQL (Softbase GL) | mart_cash_flow | Daily 2 AM | Bennett |

---

## 5. Migration Strategy

### Phase 1: Create Tables (Day 1)
- Run CREATE TABLE statements in Railway PostgreSQL
- Verify indexes are created

### Phase 2: Build ETL Jobs (Days 2-7)
- Create Python ETL scripts for each source
- Test with manual runs
- Verify data accuracy against live queries

### Phase 3: Schedule Jobs (Day 8)
- Configure Railway cron or Python scheduler
- Set up error alerting

### Phase 4: Update Dashboards (Days 9-14)
- Point dashboards at Mart tables
- Keep live queries as fallback
- Monitor performance

### Phase 5: Decommission Live Queries (Day 15+)
- Remove live query endpoints
- Document new architecture

---

## 6. Benefits

| Metric | Before (Live Queries) | After (Mart Layer) |
|--------|----------------------|-------------------|
| Dashboard Load Time | 5-30 seconds | < 1 second |
| API Rate Limit Risk | High | None |
| Data Consistency | Variable | Consistent snapshot |
| Query Complexity | High (in route files) | Low (simple SELECTs) |
| Debugging | Difficult | Easy (check Mart tables) |

---

## 7. Next Steps

1. **Approve schema design** - Review tables and confirm structure
2. **Create migration script** - SQL file to create all tables
3. **Build first ETL job** - Start with most critical data source
4. **Test and iterate** - Verify data accuracy before switching dashboards
