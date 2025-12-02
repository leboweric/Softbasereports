# Quarterly Business Review (QBR) Feature - Technical Design Document

**Project:** Softbase Reports - QBR Dashboard & PowerPoint Export  
**Version:** 1.0  
**Date:** November 24, 2025  
**Author:** Technical Architecture Team  
**For:** Claude Code Implementation

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Technical Architecture](#technical-architecture)
3. [Database Schema](#database-schema)
4. [Backend Implementation](#backend-implementation)
5. [Frontend Implementation](#frontend-implementation)
6. [PowerPoint Generation](#powerpoint-generation)
7. [Implementation Phases](#implementation-phases)
8. [Testing & Deployment](#testing--deployment)
9. [Appendix](#appendix)

---

## 1. Project Overview

### 1.1 Feature Description

The Quarterly Business Review (QBR) feature enables users to generate comprehensive customer business reviews with a single click. The system automatically pulls data from the database, calculates key metrics, generates visualizations, and exports everything to a professionally branded PowerPoint presentation.

### 1.2 Key Objectives

- **Automate QBR creation** - Reduce manual prep time from 4 hours to 1 hour
- **Data-driven insights** - Pull 40+ metrics automatically from database
- **Professional output** - Generate branded PowerPoint presentations
- **Customer engagement** - Enable regular quarterly touchpoints
- **ROI demonstration** - Show tangible value of services

### 1.3 Success Criteria

- Users can generate a complete QBR in under 5 minutes
- 95% of data is automatically populated from database
- PowerPoint exports successfully with all charts and data
- Dashboard is responsive and performs well with large datasets
- Feature is used by 80% of account managers within 3 months

### 1.4 Technical Stack

**Backend:**
- Python 3.11
- Flask (existing framework)
- Azure SQL Server (existing database)
- python-pptx (new - for PowerPoint generation)
- matplotlib (new - for chart image generation)
- Pillow (new - for image processing)

**Frontend:**
- React 18+ (existing framework)
- Chart.js (existing - for dashboard charts)
- Axios (existing - for API calls)
- react-select (new - for customer dropdown)
- date-fns (new - for date/quarter handling)

**Infrastructure:**
- Railway (existing deployment platform)
- Azure SQL Database (existing)
- GitHub (existing version control)

---

## 2. Technical Architecture

### 2.1 System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Browser                             │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              React Frontend (QBR Dashboard)                 │ │
│  │                                                              │ │
│  │  • Customer Selector                                         │ │
│  │  • Quarter Selector                                          │ │
│  │  • Metrics Dashboard (Charts & KPIs)                         │ │
│  │  • Manual Input Forms                                        │ │
│  │  • Export to PowerPoint Button                               │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────┘
                           │ HTTPS/REST API
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Flask Backend (Railway)                       │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                    QBR API Routes                            │ │
│  │                                                              │ │
│  │  • GET /api/qbr/customers                                    │ │
│  │  • GET /api/qbr/<customer_id>/data?quarter=Q3-2025          │ │
│  │  • POST /api/qbr/<customer_id>/save                          │ │
│  │  • POST /api/qbr/<qbr_id>/export                             │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                QBR Business Logic Service                    │ │
│  │                                                              │ │
│  │  • Calculate fleet metrics                                   │ │
│  │  • Calculate service metrics                                 │
│  │  • Calculate cost metrics                                    │ │
│  │  • Calculate ROI metrics                                     │ │
│  │  • Generate recommendations                                  │ │
│  └────────────────────────────────────────────────────────────┘ │
│                           │                                      │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              PowerPoint Generation Service                   │ │
│  │                                                              │ │
│  │  • Load template PPTX                                        │ │
│  │  • Populate placeholders                                     │ │
│  │  • Generate chart images (matplotlib)                        │ │
│  │  • Insert charts into slides                                 │ │
│  │  • Save and return PPTX file                                 │ │
│  └────────────────────────────────────────────────────────────┘ │
└──────────────────────────┬───────────────────────────────────────┘
                           │ SQL Queries
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Azure SQL Database                            │
│                                                                  │
│  Existing Tables:                                                │
│  • Customers                                                     │
│  • Equipment (fleet inventory)                                   │
│  • ServiceOrders (service calls)                                 │
│  • PartsOrders (parts transactions)                              │
│  • Rentals (rental transactions)                                 │
│  • GLDetail (financial data)                                     │
│                                                                  │
│  New Tables:                                                     │
│  • QBR_Sessions                                                  │
│  • QBR_Business_Priorities                                       │
│  • QBR_Recommendations                                           │
│  • QBR_Action_Items                                              │
│  • Equipment_Condition_History                                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow

**QBR Generation Flow:**

1. User selects customer and quarter
2. Frontend calls `GET /api/qbr/<customer_id>/data?quarter=Q3-2025`
3. Backend queries database for all required metrics
4. Backend calculates derived metrics (ROI, uptime, etc.)
5. Backend returns JSON with all dashboard data
6. Frontend renders dashboard with charts and metrics
7. User fills in manual sections (priorities, recommendations, action items)
8. User clicks "Save QBR"
9. Frontend calls `POST /api/qbr/<customer_id>/save` with manual data
10. Backend saves QBR session to database
11. User clicks "Export to PowerPoint"
12. Frontend calls `POST /api/qbr/<qbr_id>/export`
13. Backend generates PowerPoint using python-pptx
14. Backend returns PPTX file for download
15. User downloads and presents to customer

### 2.3 Project Structure

```
Softbasereports/
├── reporting-backend/
│   ├── src/
│   │   ├── routes/
│   │   │   ├── qbr.py                    # NEW - Main QBR API routes
│   │   │   └── ... (existing routes)
│   │   ├── services/
│   │   │   ├── qbr_service.py            # NEW - QBR business logic
│   │   │   ├── pptx_generator.py         # NEW - PowerPoint generation
│   │   │   ├── azure_sql_service.py      # EXISTING - Database service
│   │   │   └── ... (existing services)
│   │   ├── templates/
│   │   │   └── BMH_QBR_Template.pptx     # NEW - PowerPoint template
│   │   └── main.py                       # MODIFY - Register QBR blueprint
│   ├── migrations/
│   │   └── 20251124_add_qbr_tables.sql   # NEW - Database schema
│   └── requirements.txt                  # MODIFY - Add new dependencies
└── reporting-frontend/
    └── src/
        ├── pages/
        │   ├── QBRDashboard.jsx          # NEW - Main QBR page
        │   └── ... (existing pages)
        ├── components/
        │   ├── qbr/                      # NEW FOLDER
        │   │   ├── CustomerSelector.jsx
        │   │   ├── QuarterSelector.jsx
        │   │   ├── FleetOverview.jsx
        │   │   ├── FleetHealth.jsx
        │   │   ├── ServicePerformance.jsx
        │   │   ├── ServiceCosts.jsx
        │   │   ├── PartsRentals.jsx
        │   │   ├── ValueDelivered.jsx
        │   │   ├── BusinessPrioritiesForm.jsx
        │   │   ├── RecommendationsForm.jsx
        │   │   └── ActionItemsForm.jsx
        │   └── ... (existing components)
        ├── services/
        │   ├── qbrApi.js                 # NEW - QBR API client
        │   └── ... (existing services)
        └── package.json                  # MODIFY - Add new dependencies
```

---

## 3. Database Schema

### 3.1 New Tables

#### 3.1.1 QBR_Sessions

Stores each QBR session with metadata.

```sql
CREATE TABLE ben002.QBR_Sessions (
    qbr_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    quarter VARCHAR(10) NOT NULL,
    fiscal_year INT NOT NULL,
    meeting_date DATE,
    created_date DATETIME DEFAULT GETDATE(),
    created_by VARCHAR(100),
    last_modified_date DATETIME DEFAULT GETDATE(),
    last_modified_by VARCHAR(100),
    status VARCHAR(20) DEFAULT 'draft', -- 'draft', 'finalized'
    notes TEXT,
    CONSTRAINT FK_QBR_Customer FOREIGN KEY (customer_id) REFERENCES ben002.Customers(CustomerID)
);

CREATE INDEX IDX_QBR_Customer ON ben002.QBR_Sessions(customer_id);
CREATE INDEX IDX_QBR_Quarter ON ben002.QBR_Sessions(quarter, fiscal_year);
CREATE INDEX IDX_QBR_Status ON ben002.QBR_Sessions(status);
```

**Example Data:**
```sql
INSERT INTO ben002.QBR_Sessions (qbr_id, customer_id, customer_name, quarter, fiscal_year, meeting_date, created_by, status)
VALUES ('QBR-2025-Q3-CUST001', 'CUST001', 'ABC Manufacturing', 'Q3', 2025, '2025-10-15', 'john.smith@bmhmn.com', 'draft');
```

#### 3.1.2 QBR_Business_Priorities

Stores customer business priorities for each QBR.

```sql
CREATE TABLE ben002.QBR_Business_Priorities (
    priority_id INT IDENTITY(1,1) PRIMARY KEY,
    qbr_id VARCHAR(50) NOT NULL,
    priority_number INT NOT NULL, -- 1, 2, or 3
    title VARCHAR(255) NOT NULL,
    description TEXT,
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_QBR_Priority FOREIGN KEY (qbr_id) REFERENCES ben002.QBR_Sessions(qbr_id) ON DELETE CASCADE,
    CONSTRAINT CHK_Priority_Number CHECK (priority_number BETWEEN 1 AND 3)
);

CREATE INDEX IDX_Priority_QBR ON ben002.QBR_Business_Priorities(qbr_id);
```

**Example Data:**
```sql
INSERT INTO ben002.QBR_Business_Priorities (qbr_id, priority_number, title, description)
VALUES 
('QBR-2025-Q3-CUST001', 1, 'Increase warehouse throughput', 'Need to process 20% more orders by Q4 to meet seasonal demand'),
('QBR-2025-Q3-CUST001', 2, 'Reduce equipment downtime', 'Current downtime is impacting production schedules'),
('QBR-2025-Q3-CUST001', 3, 'Improve operator safety', 'Zero accidents goal for next quarter');
```

#### 3.1.3 QBR_Recommendations

Stores recommendations (auto-generated and custom).

```sql
CREATE TABLE ben002.QBR_Recommendations (
    recommendation_id INT IDENTITY(1,1) PRIMARY KEY,
    qbr_id VARCHAR(50) NOT NULL,
    category VARCHAR(50) NOT NULL, -- 'equipment_refresh', 'safety_training', 'optimization'
    title VARCHAR(255) NOT NULL,
    description TEXT,
    estimated_impact VARCHAR(255), -- e.g., "$15,000 annual savings" or "10% efficiency gain"
    is_auto_generated BIT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'proposed', -- 'proposed', 'accepted', 'declined'
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_QBR_Recommendation FOREIGN KEY (qbr_id) REFERENCES ben002.QBR_Sessions(qbr_id) ON DELETE CASCADE
);

CREATE INDEX IDX_Recommendation_QBR ON ben002.QBR_Recommendations(qbr_id);
CREATE INDEX IDX_Recommendation_Category ON ben002.QBR_Recommendations(category);
```

**Example Data:**
```sql
INSERT INTO ben002.QBR_Recommendations (qbr_id, category, title, description, estimated_impact, is_auto_generated)
VALUES 
('QBR-2025-Q3-CUST001', 'equipment_refresh', 'Replace 3 aging reach trucks', 'Units #12, #15, #23 are 12+ years old with maintenance costs exceeding 40% of replacement value', '$15,000 annual savings', 1),
('QBR-2025-Q3-CUST001', 'safety_training', 'Implement operator certification program', 'Reduce accident rate and improve equipment handling', '25% reduction in damage incidents', 0),
('QBR-2025-Q3-CUST001', 'optimization', 'Optimize preventive maintenance schedule', 'Align PM schedule with production downtime windows', '50 hours downtime avoided annually', 1);
```

#### 3.1.4 QBR_Action_Items

Stores action items with owners and due dates.

```sql
CREATE TABLE ben002.QBR_Action_Items (
    action_id INT IDENTITY(1,1) PRIMARY KEY,
    qbr_id VARCHAR(50) NOT NULL,
    party VARCHAR(20) NOT NULL, -- 'BMH' or 'Customer'
    description VARCHAR(500) NOT NULL,
    owner_name VARCHAR(100),
    due_date DATE,
    completed BIT DEFAULT 0,
    completed_date DATE,
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT FK_QBR_Action FOREIGN KEY (qbr_id) REFERENCES ben002.QBR_Sessions(qbr_id) ON DELETE CASCADE,
    CONSTRAINT CHK_Party CHECK (party IN ('BMH', 'Customer'))
);

CREATE INDEX IDX_Action_QBR ON ben002.QBR_Action_Items(qbr_id);
CREATE INDEX IDX_Action_DueDate ON ben002.QBR_Action_Items(due_date);
```

**Example Data:**
```sql
INSERT INTO ben002.QBR_Action_Items (qbr_id, party, description, owner_name, due_date, completed)
VALUES 
('QBR-2025-Q3-CUST001', 'BMH', 'Schedule equipment assessment for units #12, #15, #23', 'John Smith', '2025-10-30', 0),
('QBR-2025-Q3-CUST001', 'Customer', 'Provide operator training schedule availability', 'Jane Doe', '2025-11-15', 0),
('QBR-2025-Q3-CUST001', 'BMH', 'Prepare equipment replacement proposal', 'John Smith', '2025-11-30', 0),
('QBR-2025-Q3-CUST001', 'Customer', 'Review and approve PM schedule changes', 'Jane Doe', '2025-12-15', 0);
```

#### 3.1.5 Equipment_Condition_History

Tracks equipment condition assessments over time.

```sql
CREATE TABLE ben002.Equipment_Condition_History (
    condition_id INT IDENTITY(1,1) PRIMARY KEY,
    equipment_id VARCHAR(50) NOT NULL,
    customer_id VARCHAR(50) NOT NULL,
    assessment_date DATE NOT NULL,
    condition_status VARCHAR(20) NOT NULL, -- 'good', 'monitor', 'replace'
    age_years DECIMAL(5,2),
    annual_maintenance_cost DECIMAL(12,2),
    notes TEXT,
    assessed_by VARCHAR(100),
    created_date DATETIME DEFAULT GETDATE(),
    CONSTRAINT CHK_Condition_Status CHECK (condition_status IN ('good', 'monitor', 'replace'))
);

CREATE INDEX IDX_Condition_Equipment ON ben002.Equipment_Condition_History(equipment_id);
CREATE INDEX IDX_Condition_Customer ON ben002.Equipment_Condition_History(customer_id);
CREATE INDEX IDX_Condition_Date ON ben002.Equipment_Condition_History(assessment_date);
CREATE INDEX IDX_Condition_Status ON ben002.Equipment_Condition_History(condition_status);
```

**Example Data:**
```sql
INSERT INTO ben002.Equipment_Condition_History (equipment_id, customer_id, assessment_date, condition_status, age_years, annual_maintenance_cost, assessed_by)
VALUES 
('EQ-001', 'CUST001', '2025-09-30', 'good', 3.5, 2500.00, 'Tech-001'),
('EQ-002', 'CUST001', '2025-09-30', 'monitor', 7.2, 5800.00, 'Tech-001'),
('EQ-003', 'CUST001', '2025-09-30', 'replace', 12.5, 12000.00, 'Tech-001');
```

### 3.2 Database Migration Script

**File:** `reporting-backend/migrations/20251124_add_qbr_tables.sql`

```sql
-- QBR Feature Database Migration
-- Date: 2025-11-24
-- Description: Creates tables for Quarterly Business Review feature

USE SoftbaseDB;
GO

-- Create QBR_Sessions table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'QBR_Sessions' AND schema_id = SCHEMA_ID('ben002'))
BEGIN
    CREATE TABLE ben002.QBR_Sessions (
        qbr_id VARCHAR(50) PRIMARY KEY,
        customer_id VARCHAR(50) NOT NULL,
        customer_name VARCHAR(255) NOT NULL,
        quarter VARCHAR(10) NOT NULL,
        fiscal_year INT NOT NULL,
        meeting_date DATE,
        created_date DATETIME DEFAULT GETDATE(),
        created_by VARCHAR(100),
        last_modified_date DATETIME DEFAULT GETDATE(),
        last_modified_by VARCHAR(100),
        status VARCHAR(20) DEFAULT 'draft',
        notes TEXT
    );
    
    CREATE INDEX IDX_QBR_Customer ON ben002.QBR_Sessions(customer_id);
    CREATE INDEX IDX_QBR_Quarter ON ben002.QBR_Sessions(quarter, fiscal_year);
    CREATE INDEX IDX_QBR_Status ON ben002.QBR_Sessions(status);
    
    PRINT 'Created table: QBR_Sessions';
END
GO

-- Create QBR_Business_Priorities table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'QBR_Business_Priorities' AND schema_id = SCHEMA_ID('ben002'))
BEGIN
    CREATE TABLE ben002.QBR_Business_Priorities (
        priority_id INT IDENTITY(1,1) PRIMARY KEY,
        qbr_id VARCHAR(50) NOT NULL,
        priority_number INT NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        created_date DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_QBR_Priority FOREIGN KEY (qbr_id) REFERENCES ben002.QBR_Sessions(qbr_id) ON DELETE CASCADE,
        CONSTRAINT CHK_Priority_Number CHECK (priority_number BETWEEN 1 AND 3)
    );
    
    CREATE INDEX IDX_Priority_QBR ON ben002.QBR_Business_Priorities(qbr_id);
    
    PRINT 'Created table: QBR_Business_Priorities';
END
GO

-- Create QBR_Recommendations table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'QBR_Recommendations' AND schema_id = SCHEMA_ID('ben002'))
BEGIN
    CREATE TABLE ben002.QBR_Recommendations (
        recommendation_id INT IDENTITY(1,1) PRIMARY KEY,
        qbr_id VARCHAR(50) NOT NULL,
        category VARCHAR(50) NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        estimated_impact VARCHAR(255),
        is_auto_generated BIT DEFAULT 0,
        status VARCHAR(20) DEFAULT 'proposed',
        created_date DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_QBR_Recommendation FOREIGN KEY (qbr_id) REFERENCES ben002.QBR_Sessions(qbr_id) ON DELETE CASCADE
    );
    
    CREATE INDEX IDX_Recommendation_QBR ON ben002.QBR_Recommendations(qbr_id);
    CREATE INDEX IDX_Recommendation_Category ON ben002.QBR_Recommendations(category);
    
    PRINT 'Created table: QBR_Recommendations';
END
GO

-- Create QBR_Action_Items table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'QBR_Action_Items' AND schema_id = SCHEMA_ID('ben002'))
BEGIN
    CREATE TABLE ben002.QBR_Action_Items (
        action_id INT IDENTITY(1,1) PRIMARY KEY,
        qbr_id VARCHAR(50) NOT NULL,
        party VARCHAR(20) NOT NULL,
        description VARCHAR(500) NOT NULL,
        owner_name VARCHAR(100),
        due_date DATE,
        completed BIT DEFAULT 0,
        completed_date DATE,
        created_date DATETIME DEFAULT GETDATE(),
        CONSTRAINT FK_QBR_Action FOREIGN KEY (qbr_id) REFERENCES ben002.QBR_Sessions(qbr_id) ON DELETE CASCADE,
        CONSTRAINT CHK_Party CHECK (party IN ('BMH', 'Customer'))
    );
    
    CREATE INDEX IDX_Action_QBR ON ben002.QBR_Action_Items(qbr_id);
    CREATE INDEX IDX_Action_DueDate ON ben002.QBR_Action_Items(due_date);
    
    PRINT 'Created table: QBR_Action_Items';
END
GO

-- Create Equipment_Condition_History table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'Equipment_Condition_History' AND schema_id = SCHEMA_ID('ben002'))
BEGIN
    CREATE TABLE ben002.Equipment_Condition_History (
        condition_id INT IDENTITY(1,1) PRIMARY KEY,
        equipment_id VARCHAR(50) NOT NULL,
        customer_id VARCHAR(50) NOT NULL,
        assessment_date DATE NOT NULL,
        condition_status VARCHAR(20) NOT NULL,
        age_years DECIMAL(5,2),
        annual_maintenance_cost DECIMAL(12,2),
        notes TEXT,
        assessed_by VARCHAR(100),
        created_date DATETIME DEFAULT GETDATE(),
        CONSTRAINT CHK_Condition_Status CHECK (condition_status IN ('good', 'monitor', 'replace'))
    );
    
    CREATE INDEX IDX_Condition_Equipment ON ben002.Equipment_Condition_History(equipment_id);
    CREATE INDEX IDX_Condition_Customer ON ben002.Equipment_Condition_History(customer_id);
    CREATE INDEX IDX_Condition_Date ON ben002.Equipment_Condition_History(assessment_date);
    CREATE INDEX IDX_Condition_Status ON ben002.Equipment_Condition_History(condition_status);
    
    PRINT 'Created table: Equipment_Condition_History';
END
GO

PRINT 'QBR database migration completed successfully!';
GO
```

---

## 4. Backend Implementation

### 4.1 Dependencies

**File:** `reporting-backend/requirements.txt`

Add these lines:

```txt
python-pptx==0.6.21
matplotlib==3.7.1
Pillow==10.0.0
```

Install with:
```bash
pip install python-pptx matplotlib Pillow
```

### 4.2 QBR Service (Business Logic)

**File:** `reporting-backend/src/services/qbr_service.py`

```python
"""
QBR Service - Business Logic for Quarterly Business Reviews
Handles metric calculations, data aggregation, and recommendation generation
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class QBRService:
    """Service class for QBR business logic"""
    
    def __init__(self, sql_service):
        self.sql_service = sql_service
    
    def get_quarter_date_range(self, quarter: str, year: int) -> tuple:
        """
        Convert quarter string to date range
        Args:
            quarter: 'Q1', 'Q2', 'Q3', or 'Q4'
            year: fiscal year
        Returns:
            (start_date, end_date) tuple
        """
        quarter_map = {
            'Q1': (1, 3),
            'Q2': (4, 6),
            'Q3': (7, 9),
            'Q4': (10, 12)
        }
        
        if quarter not in quarter_map:
            raise ValueError(f"Invalid quarter: {quarter}")
        
        start_month, end_month = quarter_map[quarter]
        start_date = datetime(year, start_month, 1)
        
        # Get last day of end month
        if end_month == 12:
            end_date = datetime(year, 12, 31)
        else:
            end_date = datetime(year, end_month + 1, 1) - timedelta(days=1)
        
        return (start_date, end_date)
    
    def get_fleet_overview(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get fleet overview metrics
        Returns total units, owned/leased/rented breakdown, and equipment mix
        """
        try:
            # Total units and ownership breakdown
            query = """
            SELECT 
                COUNT(*) as total_units,
                SUM(CASE WHEN OwnershipType = 'Owned' THEN 1 ELSE 0 END) as owned,
                SUM(CASE WHEN OwnershipType = 'Leased' THEN 1 ELSE 0 END) as leased,
                SUM(CASE WHEN OwnershipType = 'Rented' THEN 1 ELSE 0 END) as rented
            FROM ben002.Equipment
            WHERE CustomerID = ?
              AND Status = 'Active'
              AND AcquisitionDate <= ?
            """
            
            result = self.sql_service.execute_query(query, [customer_id, end_date])
            overview = result[0] if result else {
                'total_units': 0, 'owned': 0, 'leased': 0, 'rented': 0
            }
            
            # Equipment mix by type
            mix_query = """
            SELECT 
                EquipmentType,
                COUNT(*) as count
            FROM ben002.Equipment
            WHERE CustomerID = ?
              AND Status = 'Active'
              AND AcquisitionDate <= ?
            GROUP BY EquipmentType
            ORDER BY COUNT(*) DESC
            """
            
            equipment_mix = self.sql_service.execute_query(mix_query, [customer_id, end_date])
            
            return {
                'total_units': overview['total_units'] or 0,
                'owned': overview['owned'] or 0,
                'leased': overview['leased'] or 0,
                'rented': overview['rented'] or 0,
                'equipment_mix': equipment_mix or []
            }
            
        except Exception as e:
            logger.error(f"Error getting fleet overview: {str(e)}")
            return {
                'total_units': 0,
                'owned': 0,
                'leased': 0,
                'rented': 0,
                'equipment_mix': []
            }
    
    def get_fleet_health(self, customer_id: str, assessment_date: datetime) -> Dict:
        """
        Get fleet health metrics
        Returns equipment condition breakdown and average age
        """
        try:
            # Get latest condition assessment for each equipment
            query = """
            WITH LatestAssessments AS (
                SELECT 
                    equipment_id,
                    condition_status,
                    age_years,
                    ROW_NUMBER() OVER (PARTITION BY equipment_id ORDER BY assessment_date DESC) as rn
                FROM ben002.Equipment_Condition_History
                WHERE customer_id = ?
                  AND assessment_date <= ?
            )
            SELECT 
                condition_status,
                COUNT(*) as count,
                AVG(age_years) as avg_age
            FROM LatestAssessments
            WHERE rn = 1
            GROUP BY condition_status
            """
            
            conditions = self.sql_service.execute_query(query, [customer_id, assessment_date])
            
            # Parse results
            good_count = 0
            monitor_count = 0
            replace_count = 0
            total_age = 0
            total_count = 0
            
            for row in conditions:
                count = row['count']
                total_count += count
                total_age += (row['avg_age'] or 0) * count
                
                if row['condition_status'] == 'good':
                    good_count = count
                elif row['condition_status'] == 'monitor':
                    monitor_count = count
                elif row['condition_status'] == 'replace':
                    replace_count = count
            
            avg_fleet_age = round(total_age / total_count, 1) if total_count > 0 else 0
            
            # Age distribution
            age_query = """
            WITH LatestAssessments AS (
                SELECT 
                    age_years,
                    ROW_NUMBER() OVER (PARTITION BY equipment_id ORDER BY assessment_date DESC) as rn
                FROM ben002.Equipment_Condition_History
                WHERE customer_id = ?
                  AND assessment_date <= ?
            )
            SELECT 
                CASE 
                    WHEN age_years < 3 THEN '0-2 years'
                    WHEN age_years < 6 THEN '3-5 years'
                    WHEN age_years < 9 THEN '6-8 years'
                    WHEN age_years < 12 THEN '9-11 years'
                    ELSE '12+ years'
                END as age_range,
                COUNT(*) as count
            FROM LatestAssessments
            WHERE rn = 1
            GROUP BY 
                CASE 
                    WHEN age_years < 3 THEN '0-2 years'
                    WHEN age_years < 6 THEN '3-5 years'
                    WHEN age_years < 9 THEN '6-8 years'
                    WHEN age_years < 12 THEN '9-11 years'
                    ELSE '12+ years'
                END
            ORDER BY 
                CASE 
                    WHEN age_years < 3 THEN 1
                    WHEN age_years < 6 THEN 2
                    WHEN age_years < 9 THEN 3
                    WHEN age_years < 12 THEN 4
                    ELSE 5
                END
            """
            
            age_distribution = self.sql_service.execute_query(age_query, [customer_id, assessment_date])
            
            return {
                'good_condition': good_count,
                'monitor': monitor_count,
                'replace_soon': replace_count,
                'avg_fleet_age': avg_fleet_age,
                'age_distribution': age_distribution or []
            }
            
        except Exception as e:
            logger.error(f"Error getting fleet health: {str(e)}")
            return {
                'good_condition': 0,
                'monitor': 0,
                'replace_soon': 0,
                'avg_fleet_age': 0,
                'age_distribution': []
            }
    
    def get_service_performance(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get service performance metrics
        Returns service calls, PM completion, response time, first-time fix rate
        """
        try:
            # Service calls and metrics
            query = """
            SELECT 
                COUNT(*) as total_calls,
                SUM(CASE WHEN ServiceType = 'PM' THEN 1 ELSE 0 END) as pm_count,
                SUM(CASE WHEN ServiceType = 'PM' AND Status = 'Completed' THEN 1 ELSE 0 END) as pm_completed,
                AVG(DATEDIFF(HOUR, CallReceived, TechnicianArrived)) as avg_response_hours,
                SUM(CASE WHEN VisitCount = 1 AND Status = 'Completed' THEN 1 ELSE 0 END) as first_time_fixes
            FROM ben002.ServiceOrders
            WHERE CustomerID = ?
              AND ServiceDate >= ?
              AND ServiceDate <= ?
            """
            
            result = self.sql_service.execute_query(query, [customer_id, start_date, end_date])
            metrics = result[0] if result else {}
            
            total_calls = metrics.get('total_calls', 0) or 0
            pm_count = metrics.get('pm_count', 0) or 0
            pm_completed = metrics.get('pm_completed', 0) or 0
            avg_response = metrics.get('avg_response_hours', 0) or 0
            first_time_fixes = metrics.get('first_time_fixes', 0) or 0
            
            pm_completion_rate = round((pm_completed / pm_count * 100), 1) if pm_count > 0 else 0
            first_time_fix_rate = round((first_time_fixes / total_calls * 100), 1) if total_calls > 0 else 0
            
            # Service type breakdown
            breakdown_query = """
            SELECT 
                CASE 
                    WHEN ServiceType = 'PM' THEN 'Planned Maintenance'
                    WHEN ServiceType = 'Repair' THEN 'Unplanned Repairs'
                    WHEN ServiceType = 'Damage' THEN 'Damage/Accidents'
                    ELSE 'Other'
                END as service_type,
                COUNT(*) as count
            FROM ben002.ServiceOrders
            WHERE CustomerID = ?
              AND ServiceDate >= ?
              AND ServiceDate <= ?
            GROUP BY 
                CASE 
                    WHEN ServiceType = 'PM' THEN 'Planned Maintenance'
                    WHEN ServiceType = 'Repair' THEN 'Unplanned Repairs'
                    WHEN ServiceType = 'Damage' THEN 'Damage/Accidents'
                    ELSE 'Other'
                END
            """
            
            breakdown = self.sql_service.execute_query(breakdown_query, [customer_id, start_date, end_date])
            
            # Calculate percentages
            service_breakdown = {}
            for row in breakdown:
                service_type = row['service_type']
                count = row['count']
                percentage = round((count / total_calls * 100), 1) if total_calls > 0 else 0
                service_breakdown[service_type.lower().replace(' ', '_').replace('/', '_')] = percentage
            
            # Monthly trend
            trend_query = """
            SELECT 
                MONTH(ServiceDate) as month,
                COUNT(*) as calls
            FROM ben002.ServiceOrders
            WHERE CustomerID = ?
              AND ServiceDate >= ?
              AND ServiceDate <= ?
            GROUP BY MONTH(ServiceDate)
            ORDER BY MONTH(ServiceDate)
            """
            
            monthly_trend = self.sql_service.execute_query(trend_query, [customer_id, start_date, end_date])
            
            # Convert month numbers to names
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for row in monthly_trend:
                row['month_name'] = month_names[row['month'] - 1]
            
            return {
                'service_calls': total_calls,
                'pm_completion_rate': pm_completion_rate,
                'avg_response_time': round(avg_response, 1),
                'first_time_fix_rate': first_time_fix_rate,
                'service_breakdown': service_breakdown,
                'monthly_trend': monthly_trend or []
            }
            
        except Exception as e:
            logger.error(f"Error getting service performance: {str(e)}")
            return {
                'service_calls': 0,
                'pm_completion_rate': 0,
                'avg_response_time': 0,
                'first_time_fix_rate': 0,
                'service_breakdown': {},
                'monthly_trend': []
            }
    
    def get_service_costs(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get service cost analysis
        Returns total spend and breakdown by category
        """
        try:
            # Total spend and category breakdown
            query = """
            SELECT 
                SUM(TotalCost) as total_spend,
                SUM(CASE WHEN ServiceType = 'PM' THEN TotalCost ELSE 0 END) as pm_cost,
                SUM(CASE WHEN ServiceType = 'PM' THEN 1 ELSE 0 END) as pm_services,
                SUM(CASE WHEN ServiceType = 'Repair' THEN TotalCost ELSE 0 END) as repair_cost,
                SUM(CASE WHEN ServiceType = 'Repair' THEN 1 ELSE 0 END) as repair_services,
                SUM(CASE WHEN ServiceType = 'Damage' THEN TotalCost ELSE 0 END) as damage_cost,
                SUM(CASE WHEN ServiceType = 'Damage' THEN 1 ELSE 0 END) as damage_incidents
            FROM ben002.ServiceOrders
            WHERE CustomerID = ?
              AND ServiceDate >= ?
              AND ServiceDate <= ?
            """
            
            result = self.sql_service.execute_query(query, [customer_id, start_date, end_date])
            costs = result[0] if result else {}
            
            # Quarterly trend (last 4 quarters)
            # Calculate previous quarters
            year = start_date.year
            quarter_num = (start_date.month - 1) // 3 + 1
            
            quarters = []
            for i in range(3, -1, -1):  # Last 4 quarters
                q_num = quarter_num - i
                q_year = year
                if q_num <= 0:
                    q_num += 4
                    q_year -= 1
                
                q_start, q_end = self.get_quarter_date_range(f'Q{q_num}', q_year)
                
                q_query = """
                SELECT SUM(TotalCost) as cost
                FROM ben002.ServiceOrders
                WHERE CustomerID = ?
                  AND ServiceDate >= ?
                  AND ServiceDate <= ?
                """
                
                q_result = self.sql_service.execute_query(q_query, [customer_id, q_start, q_end])
                q_cost = q_result[0]['cost'] if q_result and q_result[0]['cost'] else 0
                
                quarters.append({
                    'quarter': f'Q{q_num} {q_year}',
                    'cost': float(q_cost)
                })
            
            return {
                'total_spend': float(costs.get('total_spend', 0) or 0),
                'planned_maintenance': {
                    'cost': float(costs.get('pm_cost', 0) or 0),
                    'services': int(costs.get('pm_services', 0) or 0)
                },
                'unplanned_repairs': {
                    'cost': float(costs.get('repair_cost', 0) or 0),
                    'services': int(costs.get('repair_services', 0) or 0)
                },
                'damage_accidents': {
                    'cost': float(costs.get('damage_cost', 0) or 0),
                    'incidents': int(costs.get('damage_incidents', 0) or 0)
                },
                'quarterly_trend': quarters
            }
            
        except Exception as e:
            logger.error(f"Error getting service costs: {str(e)}")
            return {
                'total_spend': 0,
                'planned_maintenance': {'cost': 0, 'services': 0},
                'unplanned_repairs': {'cost': 0, 'services': 0},
                'damage_accidents': {'cost': 0, 'incidents': 0},
                'quarterly_trend': []
            }
    
    def get_parts_rentals(self, customer_id: str, start_date: datetime, end_date: datetime) -> Dict:
        """
        Get parts and rental activity
        Returns parts orders, spend, rental usage
        """
        try:
            # Parts metrics
            parts_query = """
            SELECT 
                COUNT(*) as orders,
                SUM(TotalAmount) as total_spend
            FROM ben002.PartsOrders
            WHERE CustomerID = ?
              AND OrderDate >= ?
              AND OrderDate <= ?
            """
            
            parts_result = self.sql_service.execute_query(parts_query, [customer_id, start_date, end_date])
            parts = parts_result[0] if parts_result else {'orders': 0, 'total_spend': 0}
            
            # Top parts categories
            categories_query = """
            SELECT TOP 5
                Category,
                SUM(TotalAmount) as spend
            FROM ben002.PartsOrders
            WHERE CustomerID = ?
              AND OrderDate >= ?
              AND OrderDate <= ?
            GROUP BY Category
            ORDER BY SUM(TotalAmount) DESC
            """
            
            top_categories = self.sql_service.execute_query(categories_query, [customer_id, start_date, end_date])
            
            # Rental metrics
            rental_query = """
            SELECT 
                COUNT(DISTINCT RentalID) as active_rentals,
                SUM(DATEDIFF(DAY, StartDate, COALESCE(EndDate, GETDATE()))) as rental_days
            FROM ben002.Rentals
            WHERE CustomerID = ?
              AND StartDate <= ?
              AND (EndDate IS NULL OR EndDate >= ?)
            """
            
            rental_result = self.sql_service.execute_query(rental_query, [customer_id, end_date, start_date])
            rentals = rental_result[0] if rental_result else {'active_rentals': 0, 'rental_days': 0}
            
            # Monthly rental trend
            rental_trend_query = """
            SELECT 
                MONTH(StartDate) as month,
                SUM(DATEDIFF(DAY, StartDate, COALESCE(EndDate, ?))) as days
            FROM ben002.Rentals
            WHERE CustomerID = ?
              AND StartDate >= ?
              AND StartDate <= ?
            GROUP BY MONTH(StartDate)
            ORDER BY MONTH(StartDate)
            """
            
            rental_trend = self.sql_service.execute_query(rental_trend_query, [end_date, customer_id, start_date, end_date])
            
            month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
            for row in rental_trend:
                row['month_name'] = month_names[row['month'] - 1]
            
            return {
                'parts': {
                    'orders': int(parts['orders'] or 0),
                    'total_spend': float(parts['total_spend'] or 0),
                    'top_categories': top_categories or []
                },
                'rentals': {
                    'active_rentals': int(rentals['active_rentals'] or 0),
                    'rental_days': int(rentals['rental_days'] or 0),
                    'monthly_trend': rental_trend or []
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting parts/rentals: {str(e)}")
            return {
                'parts': {'orders': 0, 'total_spend': 0, 'top_categories': []},
                'rentals': {'active_rentals': 0, 'rental_days': 0, 'monthly_trend': []}
            }
    
    def get_value_delivered(self, customer_id: str, start_date: datetime, end_date: datetime, 
                           service_costs: Dict, parts_rentals: Dict) -> Dict:
        """
        Calculate value delivered / ROI metrics
        Returns estimated savings, uptime, downtime avoided
        """
        try:
            # Calculate estimated savings (25% savings from preventive maintenance)
            pm_cost = service_costs['planned_maintenance']['cost']
            reactive_only_cost = service_costs['total_spend'] * 1.25
            estimated_savings = reactive_only_cost - service_costs['total_spend']
            
            # Calculate uptime
            # Assume 2080 hours/year per unit, quarterly = 520 hours
            fleet_query = """
            SELECT COUNT(*) as units
            FROM ben002.Equipment
            WHERE CustomerID = ?
              AND Status = 'Active'
            """
            
            fleet_result = self.sql_service.execute_query(fleet_query, [customer_id])
            total_units = fleet_result[0]['units'] if fleet_result else 0
            
            quarterly_hours = total_units * 520  # 520 hours per quarter per unit
            
            # Get downtime hours
            downtime_query = """
            SELECT SUM(DowntimeHours) as total_downtime
            FROM ben002.ServiceOrders
            WHERE CustomerID = ?
              AND ServiceDate >= ?
              AND ServiceDate <= ?
            """
            
            downtime_result = self.sql_service.execute_query(downtime_query, [customer_id, start_date, end_date])
            downtime_hours = downtime_result[0]['total_downtime'] if downtime_result and downtime_result[0]['total_downtime'] else 0
            
            uptime_hours = quarterly_hours - downtime_hours
            uptime_percentage = round((uptime_hours / quarterly_hours * 100), 1) if quarterly_hours > 0 else 0
            
            # Spend breakdown
            service_labor = service_costs['total_spend']
            parts_spend = parts_rentals['parts']['total_spend']
            
            # Get rental spend
            rental_query = """
            SELECT SUM(TotalCost) as rental_spend
            FROM ben002.Rentals
            WHERE CustomerID = ?
              AND StartDate >= ?
              AND StartDate <= ?
            """
            
            rental_result = self.sql_service.execute_query(rental_query, [customer_id, start_date, end_date])
            rental_spend = rental_result[0]['rental_spend'] if rental_result and rental_result[0]['rental_spend'] else 0
            
            total_spend = service_labor + parts_spend + rental_spend
            
            # Rolling 4 quarters trend
            year = start_date.year
            quarter_num = (start_date.month - 1) // 3 + 1
            
            quarters = []
            for i in range(3, -1, -1):
                q_num = quarter_num - i
                q_year = year
                if q_num <= 0:
                    q_num += 4
                    q_year -= 1
                
                q_start, q_end = self.get_quarter_date_range(f'Q{q_num}', q_year)
                
                # Get service spend
                q_service = self.sql_service.execute_query("""
                    SELECT SUM(TotalCost) as cost
                    FROM ben002.ServiceOrders
                    WHERE CustomerID = ? AND ServiceDate >= ? AND ServiceDate <= ?
                """, [customer_id, q_start, q_end])
                
                # Get parts spend
                q_parts = self.sql_service.execute_query("""
                    SELECT SUM(TotalAmount) as cost
                    FROM ben002.PartsOrders
                    WHERE CustomerID = ? AND OrderDate >= ? AND OrderDate <= ?
                """, [customer_id, q_start, q_end])
                
                # Get rental spend
                q_rental = self.sql_service.execute_query("""
                    SELECT SUM(TotalCost) as cost
                    FROM ben002.Rentals
                    WHERE CustomerID = ? AND StartDate >= ? AND StartDate <= ?
                """, [customer_id, q_start, q_end])
                
                q_total = 0
                if q_service and q_service[0]['cost']:
                    q_total += float(q_service[0]['cost'])
                if q_parts and q_parts[0]['cost']:
                    q_total += float(q_parts[0]['cost'])
                if q_rental and q_rental[0]['cost']:
                    q_total += float(q_rental[0]['cost'])
                
                quarters.append({
                    'quarter': f'Q{q_num} {q_year}',
                    'spend': q_total
                })
            
            return {
                'estimated_savings': round(estimated_savings, 2),
                'uptime_achieved': uptime_percentage,
                'downtime_avoided': round(downtime_hours, 1),
                'spend_breakdown': {
                    'service_labor': round(service_labor, 2),
                    'parts': round(parts_spend, 2),
                    'rentals': round(rental_spend, 2),
                    'total': round(total_spend, 2)
                },
                'rolling_4q_trend': quarters
            }
            
        except Exception as e:
            logger.error(f"Error calculating value delivered: {str(e)}")
            return {
                'estimated_savings': 0,
                'uptime_achieved': 0,
                'downtime_avoided': 0,
                'spend_breakdown': {'service_labor': 0, 'parts': 0, 'rentals': 0, 'total': 0},
                'rolling_4q_trend': []
            }
    
    def generate_recommendations(self, customer_id: str, fleet_health: Dict, service_costs: Dict) -> List[Dict]:
        """
        Generate auto-recommendations based on data
        Returns list of recommendation objects
        """
        recommendations = []
        
        try:
            # Recommendation 1: Equipment replacement
            if fleet_health['replace_soon'] > 0:
                recommendations.append({
                    'category': 'equipment_refresh',
                    'title': f"Replace {fleet_health['replace_soon']} aging equipment units",
                    'description': f"These units are over 10 years old with maintenance costs exceeding 40% of replacement value",
                    'estimated_impact': f"${fleet_health['replace_soon'] * 5000} annual savings",
                    'is_auto_generated': True
                })
            
            # Recommendation 2: High maintenance costs
            if service_costs['unplanned_repairs']['cost'] > service_costs['planned_maintenance']['cost']:
                savings = (service_costs['unplanned_repairs']['cost'] - service_costs['planned_maintenance']['cost']) * 0.3
                recommendations.append({
                    'category': 'optimization',
                    'title': "Increase preventive maintenance frequency",
                    'description': "Unplanned repairs exceed planned maintenance costs, indicating reactive maintenance approach",
                    'estimated_impact': f"${round(savings, 0)} potential savings",
                    'is_auto_generated': True
                })
            
            # Recommendation 3: Safety concerns
            if service_costs['damage_accidents']['incidents'] > 2:
                recommendations.append({
                    'category': 'safety_training',
                    'title': "Implement operator safety training program",
                    'description': f"{service_costs['damage_accidents']['incidents']} damage incidents this quarter indicate need for operator training",
                    'estimated_impact': "50% reduction in damage incidents",
                    'is_auto_generated': True
                })
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
        
        return recommendations
```

### 4.3 QBR API Routes

**File:** `reporting-backend/src/routes/qbr.py`

```python
"""
QBR API Routes
Provides endpoints for Quarterly Business Review dashboard and PowerPoint export
"""

from flask import Blueprint, jsonify, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from src.services.azure_sql_service import AzureSQLService
from src.services.qbr_service import QBRService
import logging
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

qbr_bp = Blueprint('qbr', __name__)
sql_service = AzureSQLService()
qbr_service = QBRService(sql_service)

@qbr_bp.route('/api/qbr/customers', methods=['GET'])
@jwt_required()
def get_qbr_customers():
    """
    Get list of customers for QBR dropdown
    Returns: List of customers with ID and name
    """
    try:
        query = """
        SELECT 
            CustomerID as customer_id,
            CustomerName as customer_name,
            (SELECT COUNT(*) FROM ben002.Equipment WHERE CustomerID = c.CustomerID AND Status = 'Active') as total_units
        FROM ben002.Customers c
        WHERE Active = 1
        ORDER BY CustomerName
        """
        
        customers = sql_service.execute_query(query)
        
        return jsonify({
            'success': True,
            'customers': customers or []
        })
        
    except Exception as e:
        logger.error(f"Error getting QBR customers: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@qbr_bp.route('/api/qbr/<customer_id>/data', methods=['GET'])
@jwt_required()
def get_qbr_data(customer_id):
    """
    Get all QBR metrics for a customer and quarter
    Query params: quarter (e.g., 'Q3-2025')
    Returns: Complete QBR dashboard data
    """
    try:
        quarter_param = request.args.get('quarter', 'Q4-2025')
        
        # Parse quarter
        parts = quarter_param.split('-')
        quarter = parts[0]  # 'Q3'
        year = int(parts[1])  # 2025
        
        # Get date range
        start_date, end_date = qbr_service.get_quarter_date_range(quarter, year)
        
        # Get customer info
        customer_query = """
        SELECT CustomerID as customer_id, CustomerName as customer_name
        FROM ben002.Customers
        WHERE CustomerID = ?
        """
        customer_result = sql_service.execute_query(customer_query, [customer_id])
        customer = customer_result[0] if customer_result else None
        
        if not customer:
            return jsonify({
                'success': False,
                'error': 'Customer not found'
            }), 404
        
        # Get all metrics
        fleet_overview = qbr_service.get_fleet_overview(customer_id, start_date, end_date)
        fleet_health = qbr_service.get_fleet_health(customer_id, end_date)
        service_performance = qbr_service.get_service_performance(customer_id, start_date, end_date)
        service_costs = qbr_service.get_service_costs(customer_id, start_date, end_date)
        parts_rentals = qbr_service.get_parts_rentals(customer_id, start_date, end_date)
        value_delivered = qbr_service.get_value_delivered(customer_id, start_date, end_date, service_costs, parts_rentals)
        recommendations = qbr_service.generate_recommendations(customer_id, fleet_health, service_costs)
        
        return jsonify({
            'success': True,
            'data': {
                'customer': customer,
                'quarter': f'{quarter} {year}',
                'date_range': {
                    'start': start_date.strftime('%Y-%m-%d'),
                    'end': end_date.strftime('%Y-%m-%d')
                },
                'fleet_overview': fleet_overview,
                'fleet_health': fleet_health,
                'service_performance': service_performance,
                'service_costs': service_costs,
                'parts_rentals': parts_rentals,
                'value_delivered': value_delivered,
                'recommendations': recommendations
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting QBR data: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@qbr_bp.route('/api/qbr/<customer_id>/save', methods=['POST'])
@jwt_required()
def save_qbr(customer_id):
    """
    Save QBR session with manual inputs
    Body: {quarter, meeting_date, business_priorities, custom_recommendations, action_items, status}
    Returns: QBR ID
    """
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Generate QBR ID
        quarter = data.get('quarter', 'Q4 2025')
        qbr_id = f"QBR-{quarter.replace(' ', '-')}-{customer_id}-{uuid.uuid4().hex[:8]}"
        
        # Get customer name
        customer_query = "SELECT CustomerName FROM ben002.Customers WHERE CustomerID = ?"
        customer_result = sql_service.execute_query(customer_query, [customer_id])
        customer_name = customer_result[0]['CustomerName'] if customer_result else 'Unknown'
        
        # Parse quarter
        parts = quarter.split(' ')
        quarter_str = parts[0]  # 'Q3'
        fiscal_year = int(parts[1])  # 2025
        
        # Insert QBR session
        session_query = """
        INSERT INTO ben002.QBR_Sessions 
        (qbr_id, customer_id, customer_name, quarter, fiscal_year, meeting_date, created_by, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        sql_service.execute_query(session_query, [
            qbr_id,
            customer_id,
            customer_name,
            quarter_str,
            fiscal_year,
            data.get('meeting_date'),
            current_user,
            data.get('status', 'draft')
        ])
        
        # Insert business priorities
        if 'business_priorities' in data:
            for priority in data['business_priorities']:
                priority_query = """
                INSERT INTO ben002.QBR_Business_Priorities 
                (qbr_id, priority_number, title, description)
                VALUES (?, ?, ?, ?)
                """
                
                sql_service.execute_query(priority_query, [
                    qbr_id,
                    priority['priority_number'],
                    priority['title'],
                    priority.get('description', '')
                ])
        
        # Insert custom recommendations
        if 'custom_recommendations' in data:
            for rec in data['custom_recommendations']:
                rec_query = """
                INSERT INTO ben002.QBR_Recommendations 
                (qbr_id, category, title, description, estimated_impact, is_auto_generated)
                VALUES (?, ?, ?, ?, ?, 0)
                """
                
                sql_service.execute_query(rec_query, [
                    qbr_id,
                    rec['category'],
                    rec['title'],
                    rec.get('description', ''),
                    rec.get('estimated_impact', '')
                ])
        
        # Insert action items
        if 'action_items' in data:
            for action in data['action_items']:
                action_query = """
                INSERT INTO ben002.QBR_Action_Items 
                (qbr_id, party, description, owner_name, due_date)
                VALUES (?, ?, ?, ?, ?)
                """
                
                sql_service.execute_query(action_query, [
                    qbr_id,
                    action['party'],
                    action['description'],
                    action.get('owner_name', ''),
                    action.get('due_date')
                ])
        
        return jsonify({
            'success': True,
            'qbr_id': qbr_id,
            'message': 'QBR saved successfully'
        })
        
    except Exception as e:
        logger.error(f"Error saving QBR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@qbr_bp.route('/api/qbr/<qbr_id>/export', methods=['POST'])
@jwt_required()
def export_qbr(qbr_id):
    """
    Export QBR to PowerPoint
    Returns: PPTX file download
    """
    try:
        # Get QBR data
        qbr_query = """
        SELECT * FROM ben002.QBR_Sessions WHERE qbr_id = ?
        """
        qbr_result = sql_service.execute_query(qbr_query, [qbr_id])
        
        if not qbr_result:
            return jsonify({
                'success': False,
                'error': 'QBR not found'
            }), 404
        
        qbr_data = qbr_result[0]
        
        # Get all related data
        # (Business priorities, recommendations, action items)
        # Then generate PowerPoint using pptx_generator service
        
        # For now, return a placeholder
        return jsonify({
            'success': True,
            'message': 'PowerPoint export will be implemented in Phase 4'
        })
        
    except Exception as e:
        logger.error(f"Error exporting QBR: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### 4.4 Register Blueprint in Main App

**File:** `reporting-backend/src/main.py`

Add these lines:

```python
# Import QBR blueprint
from src.routes.qbr import qbr_bp

# Register QBR blueprint (add after other blueprints)
app.register_blueprint(qbr_bp)
```

---

## 5. Frontend Implementation

### 5.1 Dependencies

**File:** `reporting-frontend/package.json`

Add to dependencies:

```json
{
  "dependencies": {
    "react-select": "^5.7.4",
    "date-fns": "^2.30.0"
  }
}
```

Install with:
```bash
npm install react-select date-fns
```

### 5.2 QBR API Client

**File:** `reporting-frontend/src/services/qbrApi.js`

```javascript
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'https://softbasereports-production.up.railway.app';

/**
 * QBR API Client
 * Handles all API calls for Quarterly Business Review feature
 */

/**
 * Get list of customers for QBR
 */
export const getCustomers = async () => {
  const response = await axios.get(`${API_BASE_URL}/api/qbr/customers`, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

/**
 * Get QBR data for a customer and quarter
 * @param {string} customerId - Customer ID
 * @param {string} quarter - Quarter string (e.g., 'Q3-2025')
 */
export const getQBRData = async (customerId, quarter) => {
  const response = await axios.get(`${API_BASE_URL}/api/qbr/${customerId}/data`, {
    params: { quarter },
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    }
  });
  return response.data;
};

/**
 * Save QBR session
 * @param {string} customerId - Customer ID
 * @param {object} data - QBR data to save
 */
export const saveQBR = async (customerId, data) => {
  const response = await axios.post(`${API_BASE_URL}/api/qbr/${customerId}/save`, data, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`,
      'Content-Type': 'application/json'
    }
  });
  return response.data;
};

/**
 * Export QBR to PowerPoint
 * @param {string} qbrId - QBR ID
 */
export const exportQBR = async (qbrId) => {
  const response = await axios.post(`${API_BASE_URL}/api/qbr/${qbrId}/export`, {}, {
    headers: {
      'Authorization': `Bearer ${localStorage.getItem('access_token')}`
    },
    responseType: 'blob'
  });
  return response.data;
};
```

### 5.3 Main QBR Dashboard Page

**File:** `reporting-frontend/src/pages/QBRDashboard.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button, Spinner, Alert } from 'react-bootstrap';
import CustomerSelector from '../components/qbr/CustomerSelector';
import QuarterSelector from '../components/qbr/QuarterSelector';
import FleetOverview from '../components/qbr/FleetOverview';
import FleetHealth from '../components/qbr/FleetHealth';
import ServicePerformance from '../components/qbr/ServicePerformance';
import ServiceCosts from '../components/qbr/ServiceCosts';
import PartsRentals from '../components/qbr/PartsRentals';
import ValueDelivered from '../components/qbr/ValueDelivered';
import BusinessPrioritiesForm from '../components/qbr/BusinessPrioritiesForm';
import RecommendationsForm from '../components/qbr/RecommendationsForm';
import ActionItemsForm from '../components/qbr/ActionItemsForm';
import * as qbrApi from '../services/qbrApi';
import './QBRDashboard.css';

const QBRDashboard = () => {
  const [customer, setCustomer] = useState(null);
  const [quarter, setQuarter] = useState('Q4-2025');
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);
  
  // Manual input states
  const [businessPriorities, setBusinessPriorities] = useState([]);
  const [customRecommendations, setCustomRecommendations] = useState([]);
  const [actionItems, setActionItems] = useState([]);
  
  const loadQBRData = async () => {
    if (!customer) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await qbrApi.getQBRData(customer.customer_id, quarter);
      
      if (response.success) {
        setData(response.data);
      } else {
        setError(response.error || 'Failed to load QBR data');
      }
    } catch (err) {
      setError(err.message || 'An error occurred while loading QBR data');
    } finally {
      setLoading(false);
    }
  };
  
  const handleSaveQBR = async () => {
    if (!customer || !data) return;
    
    setSaving(true);
    setError(null);
    
    try {
      const saveData = {
        quarter: data.quarter,
        meeting_date: new Date().toISOString().split('T')[0],
        business_priorities: businessPriorities,
        custom_recommendations: customRecommendations,
        action_items: actionItems,
        status: 'draft'
      };
      
      const response = await qbrApi.saveQBR(customer.customer_id, saveData);
      
      if (response.success) {
        alert('QBR saved successfully!');
      } else {
        setError(response.error || 'Failed to save QBR');
      }
    } catch (err) {
      setError(err.message || 'An error occurred while saving QBR');
    } finally {
      setSaving(false);
    }
  };
  
  const handleExportPPTX = async () => {
    // Will be implemented in Phase 4
    alert('PowerPoint export will be available in Phase 4');
  };
  
  return (
    <Container fluid className="qbr-dashboard">
      <Row className="mb-4">
        <Col>
          <h1>Quarterly Business Review</h1>
          <p className="text-muted">Generate comprehensive customer business reviews</p>
        </Col>
      </Row>
      
      <Row className="mb-4">
        <Col md={6}>
          <CustomerSelector value={customer} onChange={setCustomer} />
        </Col>
        <Col md={4}>
          <QuarterSelector value={quarter} onChange={setQuarter} />
        </Col>
        <Col md={2}>
          <Button 
            variant="primary" 
            onClick={loadQBRData}
            disabled={!customer || loading}
            className="w-100"
          >
            {loading ? <Spinner animation="border" size="sm" /> : 'Load Data'}
          </Button>
        </Col>
      </Row>
      
      {error && (
        <Alert variant="danger" dismissible onClose={() => setError(null)}>
          {error}
        </Alert>
      )}
      
      {loading && (
        <div className="text-center my-5">
          <Spinner animation="border" role="status">
            <span className="visually-hidden">Loading...</span>
          </Spinner>
          <p className="mt-3">Loading QBR data...</p>
        </div>
      )}
      
      {data && !loading && (
        <>
          <Row className="mb-4">
            <Col>
              <Card>
                <Card.Body>
                  <Card.Title>
                    {data.customer.customer_name} - {data.quarter}
                  </Card.Title>
                  <Card.Text className="text-muted">
                    {data.date_range.start} to {data.date_range.end}
                  </Card.Text>
                </Card.Body>
              </Card>
            </Col>
          </Row>
          
          <FleetOverview data={data.fleet_overview} />
          <FleetHealth data={data.fleet_health} />
          <ServicePerformance data={data.service_performance} />
          <ServiceCosts data={data.service_costs} />
          <PartsRentals data={data.parts_rentals} />
          <ValueDelivered data={data.value_delivered} />
          
          <BusinessPrioritiesForm 
            priorities={businessPriorities}
            onChange={setBusinessPriorities}
          />
          
          <RecommendationsForm 
            autoRecommendations={data.recommendations}
            customRecommendations={customRecommendations}
            onChange={setCustomRecommendations}
          />
          
          <ActionItemsForm 
            actionItems={actionItems}
            onChange={setActionItems}
          />
          
          <Row className="mt-4 mb-5">
            <Col className="text-center">
              <Button 
                variant="success" 
                size="lg"
                onClick={handleSaveQBR}
                disabled={saving}
                className="me-3"
              >
                {saving ? <Spinner animation="border" size="sm" /> : 'Save QBR'}
              </Button>
              
              <Button 
                variant="primary" 
                size="lg"
                onClick={handleExportPPTX}
                disabled={exporting}
              >
                {exporting ? <Spinner animation="border" size="sm" /> : 'Export to PowerPoint'}
              </Button>
            </Col>
          </Row>
        </>
      )}
    </Container>
  );
};

export default QBRDashboard;
```

### 5.4 Customer Selector Component

**File:** `reporting-frontend/src/components/qbr/CustomerSelector.jsx`

```jsx
import React, { useState, useEffect } from 'react';
import Select from 'react-select';
import { Form } from 'react-bootstrap';
import * as qbrApi from '../../services/qbrApi';

const CustomerSelector = ({ value, onChange }) => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    loadCustomers();
  }, []);
  
  const loadCustomers = async () => {
    try {
      const response = await qbrApi.getCustomers();
      if (response.success) {
        const options = response.customers.map(c => ({
          value: c.customer_id,
          label: `${c.customer_name} (${c.total_units} units)`,
          customer_id: c.customer_id,
          customer_name: c.customer_name,
          total_units: c.total_units
        }));
        setCustomers(options);
      }
    } catch (error) {
      console.error('Error loading customers:', error);
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Form.Group>
      <Form.Label>Select Customer</Form.Label>
      <Select
        options={customers}
        value={value ? { value: value.customer_id, label: value.customer_name } : null}
        onChange={(selected) => onChange(selected)}
        isLoading={loading}
        placeholder="Select a customer..."
        isClearable
      />
    </Form.Group>
  );
};

export default CustomerSelector;
```

### 5.5 Quarter Selector Component

**File:** `reporting-frontend/src/components/qbr/QuarterSelector.jsx`

```jsx
import React from 'react';
import { Form } from 'react-bootstrap';

const QuarterSelector = ({ value, onChange }) => {
  const currentYear = new Date().getFullYear();
  const quarters = [];
  
  // Generate last 2 years of quarters
  for (let year = currentYear; year >= currentYear - 1; year--) {
    for (let q = 4; q >= 1; q--) {
      quarters.push({
        value: `Q${q}-${year}`,
        label: `Q${q} ${year}`
      });
    }
  }
  
  return (
    <Form.Group>
      <Form.Label>Select Quarter</Form.Label>
      <Form.Select 
        value={value} 
        onChange={(e) => onChange(e.target.value)}
      >
        {quarters.map(q => (
          <option key={q.value} value={q.value}>
            {q.label}
          </option>
        ))}
      </Form.Select>
    </Form.Group>
  );
};

export default QuarterSelector;
```

### 5.6 Fleet Overview Component

**File:** `reporting-frontend/src/components/qbr/FleetOverview.jsx`

```jsx
import React from 'react';
import { Row, Col, Card } from 'react-bootstrap';
import { Bar } from 'react-chartjs-2';

const FleetOverview = ({ data }) => {
  if (!data) return null;
  
  const chartData = {
    labels: data.equipment_mix.map(item => item.EquipmentType),
    datasets: [{
      label: 'Equipment Count',
      data: data.equipment_mix.map(item => item.count),
      backgroundColor: 'rgba(220, 38, 38, 0.8)',
      borderColor: 'rgba(220, 38, 38, 1)',
      borderWidth: 1
    }]
  };
  
  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Equipment Mix'
      }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          stepSize: 1
        }
      }
    }
  };
  
  return (
    <Row className="mb-4">
      <Col>
        <Card>
          <Card.Header className="bg-danger text-white">
            <h4 className="mb-0">Fleet Overview</h4>
            <small>Your equipment inventory at a glance</small>
          </Card.Header>
          <Card.Body>
            <Row className="mb-4">
              <Col md={3} className="text-center">
                <div className="metric-box">
                  <h2 className="text-danger">{data.total_units}</h2>
                  <p className="text-muted">Total Units</p>
                </div>
              </Col>
              <Col md={3} className="text-center">
                <div className="metric-box">
                  <h2>{data.owned}</h2>
                  <p className="text-muted">Owned</p>
                </div>
              </Col>
              <Col md={3} className="text-center">
                <div className="metric-box">
                  <h2>{data.leased}</h2>
                  <p className="text-muted">Leased</p>
                </div>
              </Col>
              <Col md={3} className="text-center">
                <div className="metric-box">
                  <h2>{data.rented}</h2>
                  <p className="text-muted">Rented</p>
                </div>
              </Col>
            </Row>
            
            <Row>
              <Col>
                <div style={{ height: '300px' }}>
                  <Bar data={chartData} options={chartOptions} />
                </div>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      </Col>
    </Row>
  );
};

export default FleetOverview;
```

**Note:** Due to length constraints, I'll provide the remaining components in a condensed format. The pattern is similar to FleetOverview.

### 5.7 Additional Components (Summary)

Create these files following the same pattern:

- **FleetHealth.jsx** - Shows good/monitor/replace breakdown and age chart
- **ServicePerformance.jsx** - Shows service metrics and trend chart
- **ServiceCosts.jsx** - Shows cost breakdown and quarterly trend
- **PartsRentals.jsx** - Shows parts orders and rental usage
- **ValueDelivered.jsx** - Shows ROI metrics and spend breakdown
- **BusinessPrioritiesForm.jsx** - Form for 3 business priorities
- **RecommendationsForm.jsx** - Shows auto-recommendations + custom form
- **ActionItemsForm.jsx** - Checklist for action items

---

## 6. PowerPoint Generation

### 6.1 PowerPoint Generator Service

**File:** `reporting-backend/src/services/pptx_generator.py`

```python
"""
PowerPoint Generator Service
Generates branded PowerPoint presentations from QBR data
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import io
import os
import logging

logger = logging.getLogger(__name__)

class PPTXGenerator:
    """Service class for generating PowerPoint presentations"""
    
    def __init__(self, template_path):
        self.template_path = template_path
    
    def generate_qbr_presentation(self, qbr_data, output_path):
        """
        Generate complete QBR PowerPoint presentation
        Args:
            qbr_data: Dictionary with all QBR data
            output_path: Path to save generated PPTX
        Returns:
            Path to generated file
        """
        try:
            # Load template
            prs = Presentation(self.template_path)
            
            # Populate slides
            self._populate_cover_slide(prs.slides[0], qbr_data)
            self._populate_fleet_overview(prs.slides[3], qbr_data)
            self._populate_fleet_health(prs.slides[4], qbr_data)
            self._populate_service_performance(prs.slides[5], qbr_data)
            self._populate_service_costs(prs.slides[6], qbr_data)
            self._populate_parts_rentals(prs.slides[7], qbr_data)
            self._populate_value_delivered(prs.slides[8], qbr_data)
            
            # Save presentation
            prs.save(output_path)
            
            logger.info(f"Generated QBR presentation: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generating PPTX: {str(e)}")
            raise
    
    def _populate_cover_slide(self, slide, data):
        """Populate cover slide with customer name and quarter"""
        for shape in slide.shapes:
            if shape.has_text_frame:
                text = shape.text
                if '[Customer Name]' in text:
                    shape.text = text.replace('[Customer Name]', data['customer']['customer_name'])
                if 'Q[X]' in text:
                    shape.text = text.replace('Q[X]', data['quarter'])
                if '[Meeting Date]' in text:
                    shape.text = text.replace('[Meeting Date]', data.get('meeting_date', 'TBD'))
    
    def _populate_fleet_overview(self, slide, data):
        """Populate fleet overview slide"""
        fleet = data['fleet_overview']
        
        # Replace placeholders
        for shape in slide.shapes:
            if shape.has_text_frame:
                text = shape.text
                if '[##]' in text:
                    # Determine which metric based on position or context
                    # This is simplified - actual implementation would be more sophisticated
                    pass
        
        # Generate equipment mix chart
        chart_image = self._generate_equipment_mix_chart(fleet['equipment_mix'])
        
        # Add chart to slide (position would be determined from template)
        # slide.shapes.add_picture(chart_image, left, top, width, height)
    
    def _generate_equipment_mix_chart(self, equipment_mix):
        """Generate equipment mix bar chart as image"""
        fig, ax = plt.subplots(figsize=(8, 5))
        
        types = [item['EquipmentType'] for item in equipment_mix]
        counts = [item['count'] for item in equipment_mix]
        
        ax.barh(types, counts, color='#DC2626')
        ax.set_xlabel('Count')
        ax.set_title('Equipment Mix')
        ax.grid(axis='x', alpha=0.3)
        
        # Save to bytes
        img_bytes = io.BytesIO()
        plt.savefig(img_bytes, format='png', bbox_inches='tight', dpi=150)
        img_bytes.seek(0)
        plt.close()
        
        return img_bytes
    
    # Additional methods for other slides...
    # _populate_fleet_health, _populate_service_performance, etc.
```

---

## 7. Implementation Phases

### Phase 1: Database & Backend API (Week 1-2)

**Tasks:**
1. Run database migration to create 5 new tables
2. Create `qbr_service.py` with all business logic
3. Create `qbr.py` API routes
4. Register blueprint in `main.py`
5. Test API endpoints with Postman/curl

**Deliverables:**
- ✅ Database tables created
- ✅ API endpoints functional
- ✅ Metrics calculating correctly

**Testing:**
```bash
# Test customers endpoint
curl -H "Authorization: Bearer <token>" \
  "https://softbasereports-production.up.railway.app/api/qbr/customers"

# Test data endpoint
curl -H "Authorization: Bearer <token>" \
  "https://softbasereports-production.up.railway.app/api/qbr/CUST001/data?quarter=Q3-2025"
```

### Phase 2: Frontend Dashboard (Week 3-4)

**Tasks:**
1. Create QBR page and all components
2. Implement customer/quarter selectors
3. Build metric display components
4. Integrate Chart.js visualizations
5. Connect to backend API
6. Add loading states and error handling

**Deliverables:**
- ✅ QBR page accessible from menu
- ✅ Dashboard displays all metrics
- ✅ Charts render correctly
- ✅ Responsive design

### Phase 3: Manual Input Forms (Week 5)

**Tasks:**
1. Create business priorities form
2. Create recommendations form
3. Create action items form
4. Implement save functionality
5. Add form validation

**Deliverables:**
- ✅ Forms accept user input
- ✅ Data saves to database
- ✅ Validation works

### Phase 4: PowerPoint Export (Week 6-7)

**Tasks:**
1. Set up python-pptx library
2. Create PPTX generator service
3. Implement template population
4. Generate chart images
5. Add download functionality

**Deliverables:**
- ✅ Export button generates PPTX
- ✅ File downloads successfully
- ✅ All data populated correctly

---

## 8. Testing & Deployment

### 8.1 Testing Checklist

**Backend:**
- [ ] Database tables created successfully
- [ ] All API endpoints return 200 status
- [ ] Metrics calculate correctly
- [ ] Error handling works
- [ ] Authentication required

**Frontend:**
- [ ] Page loads without errors
- [ ] Customer selector populates
- [ ] Quarter selector works
- [ ] All metrics display
- [ ] Charts render
- [ ] Forms save data
- [ ] Export button works

**Integration:**
- [ ] Frontend connects to backend
- [ ] Data flows correctly
- [ ] PowerPoint generates
- [ ] File downloads

### 8.2 Deployment Steps

1. **Backend:**
   - Commit code to GitHub
   - Railway auto-deploys
   - Run database migration
   - Verify endpoints

2. **Frontend:**
   - Build production bundle
   - Deploy to hosting
   - Test in production

---

## 9. Appendix

### 9.1 Sample API Responses

**GET /api/qbr/customers:**
```json
{
  "success": true,
  "customers": [
    {
      "customer_id": "CUST001",
      "customer_name": "ABC Manufacturing",
      "total_units": 45
    }
  ]
}
```

**GET /api/qbr/CUST001/data?quarter=Q3-2025:**
```json
{
  "success": true,
  "data": {
    "customer": {
      "customer_id": "CUST001",
      "customer_name": "ABC Manufacturing"
    },
    "quarter": "Q3 2025",
    "fleet_overview": {
      "total_units": 45,
      "owned": 30,
      "leased": 10,
      "rented": 5,
      "equipment_mix": [...]
    },
    "fleet_health": {...},
    "service_performance": {...},
    "service_costs": {...},
    "parts_rentals": {...},
    "value_delivered": {...},
    "recommendations": [...]
  }
}
```

### 9.2 Environment Variables

```bash
# Backend (.env)
DATABASE_URL=<Azure SQL connection string>
JWT_SECRET_KEY=<your secret key>
```

### 9.3 File Locations Summary

**Backend Files to Create:**
- `src/services/qbr_service.py`
- `src/services/pptx_generator.py`
- `src/routes/qbr.py`
- `migrations/20251124_add_qbr_tables.sql`

**Backend Files to Modify:**
- `src/main.py` (register blueprint)
- `requirements.txt` (add dependencies)

**Frontend Files to Create:**
- `src/pages/QBRDashboard.jsx`
- `src/services/qbrApi.js`
- `src/components/qbr/*.jsx` (11 components)

**Frontend Files to Modify:**
- `package.json` (add dependencies)
- App routing (add QBR route)

---

## END OF DOCUMENT

**Total Pages:** 80+  
**Version:** 1.0  
**Date:** November 24, 2025  
**Ready for:** Claude Code Implementation

---

**Next Steps:**
1. Share this document with Claude Code
2. Start with Phase 1 (Database & Backend)
3. Test each phase before moving to next
4. Deploy incrementally

**Questions?** Refer to the QBR Feature Analysis document for additional context.
