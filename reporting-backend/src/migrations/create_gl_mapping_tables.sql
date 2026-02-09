-- GL Account Mapping Tables Migration
-- Stores auto-discovered and user-edited GL account mappings per tenant

-- Main table: stores each GL account with its classification
CREATE TABLE IF NOT EXISTS tenant_gl_accounts (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    account_no VARCHAR(20) NOT NULL,
    account_type VARCHAR(20) NOT NULL CHECK (account_type IN ('revenue', 'cogs', 'expense', 'other_income', 'other')),
    department_code VARCHAR(10),
    department_name VARCHAR(100),
    expense_category VARCHAR(50),
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_auto_discovered BOOLEAN DEFAULT TRUE,
    last_seen_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, account_no)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_gl_accounts_org_type ON tenant_gl_accounts(organization_id, account_type);
CREATE INDEX IF NOT EXISTS idx_gl_accounts_org_dept ON tenant_gl_accounts(organization_id, department_code);
CREATE INDEX IF NOT EXISTS idx_gl_accounts_org_active ON tenant_gl_accounts(organization_id, is_active);

-- Department configuration table: stores the department definitions per tenant
CREATE TABLE IF NOT EXISTS tenant_departments (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    dept_code VARCHAR(10) NOT NULL,
    dept_name VARCHAR(100) NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, dept_code)
);

-- Expense category configuration: stores the expense category definitions per tenant
CREATE TABLE IF NOT EXISTS tenant_expense_categories (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    category_key VARCHAR(50) NOT NULL,
    category_name VARCHAR(100) NOT NULL,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(organization_id, category_key)
);

-- Discovery log: tracks when auto-discovery was last run
CREATE TABLE IF NOT EXISTS gl_discovery_log (
    id SERIAL PRIMARY KEY,
    organization_id INTEGER NOT NULL,
    discovery_type VARCHAR(50) NOT NULL,
    accounts_found INTEGER DEFAULT 0,
    accounts_new INTEGER DEFAULT 0,
    accounts_updated INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_gl_discovery_org ON gl_discovery_log(organization_id);
