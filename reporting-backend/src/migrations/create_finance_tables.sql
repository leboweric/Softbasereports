-- VITAL WorkLife Finance Module Database Schema
-- Creates tables for billing management, contracts, and revenue tracking

-- =============================================================================
-- CLIENTS TABLE
-- Master table for all billing clients (may differ from HubSpot company names)
-- =============================================================================
CREATE TABLE IF NOT EXISTS finance_clients (
    id SERIAL PRIMARY KEY,
    org_id INTEGER NOT NULL REFERENCES organization(id),
    
    -- Client identification
    billing_name VARCHAR(255) NOT NULL,           -- Name as it appears on invoices
    hubspot_company_id VARCHAR(100),              -- Link to HubSpot company (if mapped)
    hubspot_company_name VARCHAR(255),            -- HubSpot company name for reference
    
    -- Client details
    industry VARCHAR(100),                        -- Healthcare, Manufacturing, etc.
    tier VARCHAR(50),                             -- Tier 1, Tier 2, etc.
    solution_type VARCHAR(100),                   -- EAP, Wellness, etc.
    
    -- Contract metadata
    applicable_law_state VARCHAR(50),             -- State governing the contract
    nexus_state VARCHAR(50),                      -- Tax nexus state
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',          -- active, at_risk, termed
    at_risk_reason TEXT,                          -- Why client is at risk
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(org_id, billing_name)
);

-- =============================================================================
-- CONTRACTS TABLE
-- Tracks contract terms and renewal dates
-- =============================================================================
CREATE TABLE IF NOT EXISTS finance_contracts (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES finance_clients(id) ON DELETE CASCADE,
    
    -- Contract dates
    start_date DATE NOT NULL,
    end_date DATE,                                -- NULL if evergreen
    renewal_date DATE NOT NULL,                   -- Annual renewal date
    
    -- Contract terms
    billing_frequency VARCHAR(50) DEFAULT 'monthly',  -- monthly, quarterly, annual
    payment_terms INTEGER DEFAULT 30,             -- Net 30, Net 60, etc.
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',          -- active, pending_renewal, termed
    renewal_status VARCHAR(50),                   -- pending, confirmed, at_risk
    
    -- Notes
    contract_notes TEXT,                          -- Special terms, nuances
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- RATE SCHEDULES TABLE
-- Tracks PEPM rates with effective dates (handles mid-year rate changes)
-- =============================================================================
CREATE TABLE IF NOT EXISTS finance_rate_schedules (
    id SERIAL PRIMARY KEY,
    contract_id INTEGER NOT NULL REFERENCES finance_contracts(id) ON DELETE CASCADE,
    
    -- Rate details
    effective_date DATE NOT NULL,                 -- When this rate takes effect
    end_date DATE,                                -- When this rate ends (NULL if current)
    pepm_rate DECIMAL(10,2) NOT NULL,             -- Per Employee Per Month rate
    
    -- Rate type
    rate_type VARCHAR(50) DEFAULT 'confirmed',    -- confirmed, projected, pending
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(contract_id, effective_date)
);

-- =============================================================================
-- POPULATION HISTORY TABLE
-- Tracks population changes over time (from HubSpot or manual entry)
-- =============================================================================
CREATE TABLE IF NOT EXISTS finance_population_history (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES finance_clients(id) ON DELETE CASCADE,
    
    -- Population data
    effective_date DATE NOT NULL,                 -- When this population count took effect
    population_count INTEGER NOT NULL,            -- Number of employees
    
    -- Source tracking
    source VARCHAR(50) DEFAULT 'manual',          -- manual, hubspot, import
    hubspot_update_id VARCHAR(100),               -- HubSpot activity ID if from HubSpot
    
    -- Notes
    notes TEXT,                                   -- Reason for change
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(client_id, effective_date)
);

-- =============================================================================
-- MONTHLY BILLING TABLE
-- Pre-calculated monthly billing amounts (the "billing sheet" data)
-- =============================================================================
CREATE TABLE IF NOT EXISTS finance_monthly_billing (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES finance_clients(id) ON DELETE CASCADE,
    
    -- Period
    billing_year INTEGER NOT NULL,
    billing_month INTEGER NOT NULL,               -- 1-12
    
    -- Billing calculation
    population_count INTEGER NOT NULL,            -- Population for this month
    pepm_rate DECIMAL(10,2) NOT NULL,             -- Rate applied
    
    -- Revenue types
    revenue_revrec DECIMAL(12,2),                 -- Revenue recognition amount
    revenue_cash DECIMAL(12,2),                   -- Cash basis amount
    
    -- Status
    status VARCHAR(50) DEFAULT 'projected',       -- projected, actual, closed
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(client_id, billing_year, billing_month)
);

-- =============================================================================
-- AT RISK TRACKING TABLE
-- Tracks clients at risk of termination
-- =============================================================================
CREATE TABLE IF NOT EXISTS finance_at_risk (
    id SERIAL PRIMARY KEY,
    client_id INTEGER NOT NULL REFERENCES finance_clients(id) ON DELETE CASCADE,
    
    -- Risk details
    identified_date DATE NOT NULL,
    expected_term_date DATE,                      -- When they're expected to leave
    risk_reason TEXT,                             -- Why they're at risk
    
    -- Financial impact
    monthly_revenue_at_risk DECIMAL(12,2),        -- Monthly revenue we'd lose
    annual_revenue_at_risk DECIMAL(12,2),         -- Annual revenue we'd lose
    
    -- Status
    status VARCHAR(50) DEFAULT 'active',          -- active, resolved, termed
    resolution_notes TEXT,                        -- How it was resolved
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- AUDIT LOG TABLE
-- Tracks all changes to billing data
-- =============================================================================
CREATE TABLE IF NOT EXISTS finance_audit_log (
    id SERIAL PRIMARY KEY,
    
    -- What changed
    table_name VARCHAR(100) NOT NULL,
    record_id INTEGER NOT NULL,
    action VARCHAR(50) NOT NULL,                  -- INSERT, UPDATE, DELETE
    
    -- Change details
    old_values JSONB,
    new_values JSONB,
    
    -- Who made the change
    user_id INTEGER,
    user_email VARCHAR(255),
    
    -- When
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- INDEXES
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_finance_clients_org ON finance_clients(org_id);
CREATE INDEX IF NOT EXISTS idx_finance_clients_status ON finance_clients(status);
CREATE INDEX IF NOT EXISTS idx_finance_contracts_client ON finance_contracts(client_id);
CREATE INDEX IF NOT EXISTS idx_finance_contracts_renewal ON finance_contracts(renewal_date);
CREATE INDEX IF NOT EXISTS idx_finance_rates_contract ON finance_rate_schedules(contract_id);
CREATE INDEX IF NOT EXISTS idx_finance_rates_effective ON finance_rate_schedules(effective_date);
CREATE INDEX IF NOT EXISTS idx_finance_population_client ON finance_population_history(client_id);
CREATE INDEX IF NOT EXISTS idx_finance_billing_client ON finance_monthly_billing(client_id);
CREATE INDEX IF NOT EXISTS idx_finance_billing_period ON finance_monthly_billing(billing_year, billing_month);
CREATE INDEX IF NOT EXISTS idx_finance_at_risk_client ON finance_at_risk(client_id);
CREATE INDEX IF NOT EXISTS idx_finance_audit_table ON finance_audit_log(table_name, record_id);
