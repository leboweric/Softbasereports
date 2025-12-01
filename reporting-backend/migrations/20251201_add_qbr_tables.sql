-- QBR Feature Database Migration (PostgreSQL)
-- Date: 2025-12-01
-- Description: Creates tables for Quarterly Business Review feature

-- Create QBR_Sessions table
CREATE TABLE IF NOT EXISTS qbr_sessions (
    qbr_id VARCHAR(50) PRIMARY KEY,
    customer_number VARCHAR(50) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    quarter VARCHAR(10) NOT NULL,  -- 'Q1', 'Q2', 'Q3', 'Q4'
    fiscal_year INT NOT NULL,
    meeting_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),
    last_modified_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified_by VARCHAR(100),
    status VARCHAR(20) DEFAULT 'draft',  -- 'draft', 'finalized'
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_qbr_customer ON qbr_sessions(customer_number);
CREATE INDEX IF NOT EXISTS idx_qbr_quarter ON qbr_sessions(quarter, fiscal_year);
CREATE INDEX IF NOT EXISTS idx_qbr_status ON qbr_sessions(status);

-- Create QBR_Business_Priorities table
CREATE TABLE IF NOT EXISTS qbr_business_priorities (
    priority_id SERIAL PRIMARY KEY,
    qbr_id VARCHAR(50) NOT NULL REFERENCES qbr_sessions(qbr_id) ON DELETE CASCADE,
    priority_number INT NOT NULL CHECK (priority_number BETWEEN 1 AND 3),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_priority_qbr ON qbr_business_priorities(qbr_id);

-- Create QBR_Recommendations table
CREATE TABLE IF NOT EXISTS qbr_recommendations (
    recommendation_id SERIAL PRIMARY KEY,
    qbr_id VARCHAR(50) NOT NULL REFERENCES qbr_sessions(qbr_id) ON DELETE CASCADE,
    category VARCHAR(50) NOT NULL,  -- 'equipment_refresh', 'safety_training', 'optimization'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    estimated_impact VARCHAR(255),  -- e.g., "$15,000 annual savings"
    is_auto_generated BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT 'proposed',  -- 'proposed', 'accepted', 'declined'
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_recommendation_qbr ON qbr_recommendations(qbr_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_category ON qbr_recommendations(category);

-- Create QBR_Action_Items table
CREATE TABLE IF NOT EXISTS qbr_action_items (
    action_id SERIAL PRIMARY KEY,
    qbr_id VARCHAR(50) NOT NULL REFERENCES qbr_sessions(qbr_id) ON DELETE CASCADE,
    party VARCHAR(20) NOT NULL CHECK (party IN ('BMH', 'Customer')),
    description VARCHAR(500) NOT NULL,
    owner_name VARCHAR(100),
    due_date DATE,
    completed BOOLEAN DEFAULT FALSE,
    completed_date DATE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_action_qbr ON qbr_action_items(qbr_id);
CREATE INDEX IF NOT EXISTS idx_action_duedate ON qbr_action_items(due_date);

-- Create Equipment_Condition_History table
-- This tracks condition assessments over time for fleet health metrics
CREATE TABLE IF NOT EXISTS equipment_condition_history (
    condition_id SERIAL PRIMARY KEY,
    unit_no VARCHAR(50) NOT NULL,
    customer_number VARCHAR(50) NOT NULL,
    assessment_date DATE NOT NULL,
    condition_status VARCHAR(20) NOT NULL CHECK (condition_status IN ('good', 'monitor', 'replace')),
    age_years DECIMAL(5,2),
    annual_maintenance_cost DECIMAL(12,2),
    notes TEXT,
    assessed_by VARCHAR(100),
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_condition_unitno ON equipment_condition_history(unit_no);
CREATE INDEX IF NOT EXISTS idx_condition_customer ON equipment_condition_history(customer_number);
CREATE INDEX IF NOT EXISTS idx_condition_date ON equipment_condition_history(assessment_date);
CREATE INDEX IF NOT EXISTS idx_condition_status ON equipment_condition_history(condition_status);
