# Softbase Reports - System Architecture

## Project Overview

Softbase Reports is a comprehensive business intelligence and reporting system that connects to Softbase Evolution ERP data. The application provides real-time reporting, data analytics, and automated dashboard capabilities for equipment rental, service, parts, and accounting departments.

**Core Functionality:**
- Department-specific reporting (Service, Rental, Parts, Accounting)
- Real-time dashboards with sales metrics and KPIs
- Customer activity tracking and work order management
- AI-powered query generation and data analysis
- Commission tracking and sales forecasting
- Equipment rental availability and utilization reporting

**Tech Stack Summary:**
- **Frontend**: React 19 + Vite + Tailwind CSS + Radix UI
- **Backend**: Flask + PyMSSQL + Flask-JWT-Extended
- **Primary Database**: Azure SQL Server (Softbase Evolution data)
- **Secondary Database**: PostgreSQL (custom data, work order notes, Minitrac)
- **Deployment**: Netlify (frontend) + Railway (backend + PostgreSQL)

---

## Frontend Architecture (Netlify)

### Framework & Build System
- **React 19.1.0** with modern hooks and concurrent features
- **Vite 6.3.5** for fast development and optimized builds
- **TypeScript/JavaScript** mixed codebase (.jsx/.tsx files)

### UI Framework & Styling
- **Tailwind CSS 4.1.7** for utility-first styling
- **Radix UI** comprehensive component library (40+ components)
- **Lucide React** for consistent iconography
- **Recharts** for data visualization and charts
- **Framer Motion** for animations and transitions

### Project Structure
```
reporting-frontend/src/
├── components/
│   ├── ui/                     # Reusable UI components (Radix-based)
│   ├── departments/            # Department-specific reports
│   │   ├── ServiceReport.jsx
│   │   ├── RentalReport.jsx
│   │   ├── PartsReport.jsx
│   │   └── AccountingReport.jsx
│   ├── diagnostics/            # Debug and diagnostic tools
│   ├── Layout.jsx              # Main app layout with navigation
│   ├── Dashboard.jsx           # Executive dashboard
│   ├── Login.jsx               # Authentication component
│   └── Reports.jsx             # Report listing and management
├── lib/
│   ├── api.js                  # API utilities and URL management
│   ├── utils.js                # Shared utility functions
│   └── employeeMapping.js      # Employee data mappings
├── hooks/
│   └── use-mobile.js           # Mobile detection hook
└── pages/                      # Route-based page components
```

### Key Dependencies
- **React Router DOM 7.6.1** - Client-side routing
- **React Hook Form 7.56.3** - Form management and validation
- **Zod 3.24.4** - Schema validation
- **ExcelJS + File-saver** - Excel export functionality
- **Date-fns** - Date manipulation and formatting
- **Next-themes** - Dark/light mode theming

### Build Process
- **Development**: `npm run dev` → Vite dev server with HMR
- **Production**: `npm run build` → Optimized static assets
- **Proxy Configuration**: `/api` routes proxied to `localhost:5001` in development

### Environment Variables
```
VITE_API_URL=https://softbasereports-production.up.railway.app
```

---

## Backend Architecture (Railway)

### Framework & Core Technologies
- **Flask 3.1.1** - Lightweight WSGI web framework
- **Flask-CORS 6.0.0** - Cross-origin resource sharing
- **Flask-JWT-Extended 4.7.1** - JWT-based authentication
- **Flask-SQLAlchemy 3.1.1** - ORM for PostgreSQL operations
- **PyMSSQL 2.3.6** - Azure SQL Server connectivity

### Project Structure
```
reporting-backend/src/
├── routes/                     # API endpoints organized by feature
│   ├── auth.py                 # Authentication endpoints
│   ├── user.py                 # User management
│   ├── softbase_reports.py     # Core business reports
│   ├── dashboard_optimized.py  # Dashboard data endpoints
│   ├── accounting_diagnostics.py
│   ├── database_explorer.py    # Schema exploration tools
│   ├── ai_query.py            # AI-powered query generation
│   ├── minitrac.py            # Minitrac equipment integration
│   ├── work_order_notes.py    # PostgreSQL work order notes
│   └── diagnostics/           # Debug and diagnostic endpoints
├── services/                   # Business logic layer
│   ├── azure_sql_service.py    # Azure SQL connection service
│   ├── softbase_service.py     # Softbase data access layer
│   ├── openai_service.py       # AI integration service
│   ├── cache_service.py        # Redis caching service
│   └── sql_generator.py        # Dynamic SQL generation
├── models/                     # Data models and schemas
│   ├── user.py                 # User and RBAC models
│   └── rbac.py                 # Role-based access control
├── config/                     # Configuration modules
│   ├── database_config.py      # Database connection configs
│   └── openai_config.py        # AI service configuration
├── middleware/                 # Request/response middleware
│   └── tenant_middleware.py    # Multi-tenant support
└── main.py                     # Application entry point
```

### Major API Route Groups

#### Core Business Reports (`/api/reports/`)
- Customer activity and work order reports
- Equipment rental and service tracking
- Parts inventory and sales analysis
- Commission calculations and forecasting

#### Dashboard APIs (`/api/dashboard/`)
- Real-time KPI metrics
- Sales pace tracking and projections
- Department performance summaries
- Executive summary data

#### Database Operations (`/api/database/`)
- Schema exploration and table discovery
- Custom SQL query execution
- Data export and CSV generation
- Column-level data analysis

#### AI & Analytics (`/api/ai/`)
- Natural language to SQL conversion
- Predictive analytics and forecasting
- Query optimization suggestions
- Automated report generation

#### User Management (`/api/auth/`, `/api/users/`)
- JWT-based authentication
- Role-based access control (RBAC)
- User profile management
- Permission-based feature access

### Key Dependencies
- **Pandas 2.3.0** - Data manipulation and analysis
- **OpenAI 1.59.8** - AI-powered features
- **Requests 2.32.3** - HTTP client for external APIs
- **BCrypt 4.2.1** - Password hashing
- **Gunicorn 23.0.0** - WSGI HTTP server
- **Redis 5.0.1** - Caching and session storage
- **ReportLab + FPDF2** - PDF generation
- **Matplotlib + Seaborn** - Advanced data visualization

### Environment Variables
```
# Database Connections
AZURE_SQL_SERVER=evo1-sql-replica.database.windows.net
AZURE_SQL_DATABASE=evo
AZURE_SQL_USERNAME=ben002user
AZURE_SQL_PASSWORD=[encrypted]
DATABASE_URL=[PostgreSQL connection string]

# Application Security
JWT_SECRET_KEY=[random secret]
FLASK_ENV=production

# External Services
OPENAI_API_KEY=[encrypted]
REDIS_URL=[Redis connection string]

# Server Configuration
PORT=5001
```

---

## Database Architecture

### Primary Database: Azure SQL Server
**Connection**: `evo1-sql-replica.database.windows.net`
**Schema**: `ben002`
**Purpose**: Softbase Evolution ERP data (read-only)

#### Critical Access Constraints
- **IP Firewall Restrictions**: Database only accepts connections from Railway's IP addresses
- **No Local Development Access**: All database queries must go through deployed Railway backend
- **Schema Access**: Read-only access to Softbase Evolution production data

#### Key Tables & Relationships
```
Customer (2,227 rows)
├── InvoiceReg (5,148 rows) → BillTo = Customer.Number
├── WO (Work Orders) → Customer = Customer.Number
└── Equipment → CustomerNo = Customer.Number

Equipment (21,291 rows)
├── WORental → Equipment = Equipment.SerialNo
├── Parts → Equipment relationships
└── Service history tracking

InvoiceReg (Invoice Headers)
├── InvoiceDetail (Line items)
├── ARDetail (Accounts receivable)
└── GLDetail (General ledger postings)

Work Orders (WO)
├── WOParts (Parts used)
├── WOLabor (Labor charges)
├── WOMisc (Miscellaneous charges)
└── WORental (Rental work orders)
```

#### Data Quality & Gotchas
- Customer joins use `Number` field, not `Id` 
- Equipment `Customer` field is boolean, `CustomerNo` is the actual reference
- Work order quotes have `WONo` starting with '9' (filter out for actual rentals)
- No direct revenue calculations - must aggregate from detail tables

### Secondary Database: PostgreSQL on Railway
**Purpose**: Custom application data and extended functionality

#### Tables
```
users                    # User accounts and authentication
user_roles              # Role-based access control
work_order_notes        # Custom notes for work orders
minitrac_equipment      # 28K Minitrac equipment records
organizations           # Multi-tenant organization data
```

#### Connection Management
- **Primary**: SQLAlchemy ORM for user management and application data
- **Custom Data**: Direct PostgreSQL queries for Minitrac and notes
- **Session Management**: Flask-SQLAlchemy with connection pooling

---

## Deployment Architecture

### Frontend Deployment (Netlify)
**URL**: https://softbasereports.netlify.app

#### Build Process
1. **Source**: GitHub repository auto-deploy
2. **Build Command**: `npm run build`
3. **Publish Directory**: `dist/`
4. **Environment Variables**: `VITE_API_URL` set to Railway backend URL

#### Optimization Features
- **Static Asset CDN**: Global content delivery
- **Build Caching**: Incremental builds for faster deployments
- **Preview Deployments**: Branch-based preview environments
- **Form Handling**: Contact forms and feedback collection

### Backend Deployment (Railway)
**URL**: https://softbasereports-production.up.railway.app

#### Deployment Configuration
```json
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "gunicorn -w 4 -b 0.0.0.0:$PORT src.main:app",
    "healthcheckPath": "/health"
  }
}
```

#### Infrastructure Features
- **Auto-scaling**: Horizontal scaling based on load
- **Health Monitoring**: Application health checks and restart policies
- **Environment Management**: Secure environment variable storage
- **Database Integration**: Built-in PostgreSQL database included
- **Logging**: Centralized application and access logs

### CI/CD Pipeline
- **Trigger**: Git push to main branch
- **Frontend**: Netlify auto-build and deploy
- **Backend**: Railway auto-build and deploy
- **Database Migrations**: Automatic SQLAlchemy migrations on deploy
- **Rollback**: One-click rollback to previous deployments

---

## Integrations & External Services

### Softbase Evolution ERP
**Type**: Primary data source
**Access**: Read-only via Azure SQL Server
**Data Scope**: Complete business operation data including customers, equipment, work orders, invoicing, and financial records

### OpenAI Integration
**Service**: GPT-4 for natural language processing
**Features**:
- Natural language to SQL query conversion
- Automated report generation and insights
- Data analysis and trend identification
- Query optimization recommendations

### Minitrac Equipment Database
**Type**: Self-hosted replacement for $600/month SaaS
**Implementation**: 28,000+ equipment records in PostgreSQL
**Features**:
- Equipment search and filtering
- Rental availability tracking
- Equipment specification lookup
- Custom data fields and notes

### Authentication & Security
**JWT Implementation**: Flask-JWT-Extended
**Session Management**: Redis-backed sessions
**Role-Based Access Control**: Custom RBAC system with department-level permissions
**Password Security**: BCrypt hashing with salt rounds

---

## Recent Major Developments

### Accounting Inventory Report Implementation (December 2024)

A comprehensive year-end inventory report was implemented for the Accounting department, providing GL account-based financial reporting with equipment categorization. This implementation revealed several critical technical insights and architectural lessons.

#### Technical Implementation
**Backend**: `accounting_inventory.py` - GL account balance integration with equipment categorization
**Frontend**: `InventoryReport.jsx` - Responsive equipment display with financial summaries
**Integration**: Added to AccountingReport.jsx as dedicated inventory tab

#### Core Features Implemented
- **GL Account Integration**: Direct GLDetail queries for accurate financial reporting
- **Equipment Categorization**: Business logic-based categorization (Rental, New, Used, Batteries/Chargers, Allied)
- **Financial Accuracy**: GL account balances as source of truth, not equipment book values
- **YTD Depreciation**: Fiscal year (Nov 2024 - Oct 2025) depreciation expense tracking
- **Responsive UI**: Category cards, detailed equipment lists, status badges

#### Critical Technical Lessons Learned

##### 1. Database Schema Assumptions Are Dangerous
**Issue**: Initially assumed GLDetail table had `Year` and `Month` columns
**Reality**: GLDetail uses `EffectiveDate` column for temporal filtering
**Lesson**: Always verify actual table schemas before writing queries
**Fix**: Use `EffectiveDate >= '2024-12-01' AND EffectiveDate <= '2024-12-31'` instead of `Year = 2024 AND Month = 12`

##### 2. JSON Serialization Complexity with Financial Data
**Issue**: Decimal objects and None values caused JSON serialization failures
**Error**: `'<' not supported between instances of 'int' and 'NoneType'`
**Solution**: Implemented recursive `make_json_safe()` function to handle:
- Decimal → float conversion
- None → 0 for numeric contexts
- datetime → isoformat() strings
- Nested dictionaries and lists

##### 3. GL Account Balance Query Strategy
**Challenge**: Getting accurate GL balances for specific time periods
**Initial Approach**: Complex CTE queries with latest period detection
**Final Approach**: Direct GLDetail sum queries with explicit date ranges
**Key Insight**: GLDetail provides transaction-level accuracy vs GL table snapshots

##### 4. Frontend Debug Category Filtering
**Issue**: Backend debug sections (`debug_info`, `gl_analysis`) appeared as empty equipment categories
**Root Cause**: Frontend filtered `totals` and `notes` but not debug sections
**Solution**: 
- Backend: Remove debug sections before JSON response
- Frontend: Filter debug keys in equipment category loops

##### 5. Equipment Categorization Business Logic
**Requirement**: Categorize 21K+ equipment records by business rules
**Logic Implemented**:
```javascript
// Priority order: Keywords override departments
if (make.includes('allied')) return 'allied'
if (model.includes('battery')) return 'batteries_chargers'
if (inventoryDept === 60) return 'rental'
if (inventoryDept === 10) return 'new'
if (inventoryDept === 20) return 'used'
if (inventoryDept === 30) return 'allied'
```

#### Financial Accuracy Requirements
**Expected Amounts** (per Marissa's specifications):
- Allied Equipment: $17,250.98 (GL Account 131300)
- New Equipment: $776,157.98 (GL Account 131000)
- Used Equipment: $155,100.30 (portion of GL Account 131200)
- Batteries: $52,116.39 (portion of GL Account 131200)
- Rental Net Book Value: GL 183000 - GL 193000

#### Performance Optimizations
- **Equipment Query**: Single query with rental status LEFT JOIN
- **GL Queries**: Separate targeted queries vs complex CTEs
- **JSON Safety**: Pre-processing vs runtime conversion
- **Frontend Filtering**: Client-side category filtering for responsive UI

#### Data Quality Insights
**Equipment Table Realities**:
- `CustomerNo` field references Customer.Number (not boolean Customer field)
- `InventoryDept` is primary categorization driver (60=Rental, 10=New, 20=Used, 30=Allied)
- Rental status determined by open work orders in WORental/WO tables
- Quote work orders (WONo starting with '9') must be excluded from rental calculations

**GLDetail Table Structure**:
- `EffectiveDate` is the temporal dimension (no Year/Month columns)
- `Posted = 1` filter required for accurate financial data
- `Amount` field can be positive or negative (requires CASE logic for depreciation)
- Account 193000 depreciation requires ABS() of negative amounts

### Key Architectural Improvements from Inventory Work

#### 1. Enhanced Error Handling
```python
def make_json_safe(obj):
    """Recursively convert ALL problematic types to JSON-safe values"""
    if obj is None: return None
    if isinstance(obj, Decimal): return float(obj)
    if isinstance(obj, (datetime, date)): return obj.isoformat()
    if isinstance(obj, dict): return {str(k): make_json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)): return [make_json_safe(item) for item in obj]
    return obj
```

#### 2. Financial Data Query Patterns
```sql
-- Accurate GL balance extraction
SELECT COALESCE(SUM(Amount), 0) as Balance
FROM [ben002].GLDetail  
WHERE AccountNo = '131300'
  AND Posted = 1
  AND EffectiveDate >= '2024-12-01'
  AND EffectiveDate <= '2024-12-31'

-- Fiscal year depreciation
WHERE AccountNo = '193000' AND Posted = 1
AND ((EffectiveDate >= '2024-11-01' AND EffectiveDate <= '2024-12-31')
     OR (EffectiveDate >= '2025-01-01' AND EffectiveDate <= '2025-10-31'))
```

#### 3. Frontend Category Management
```javascript
// Exclude debug and system sections from UI display
{Object.entries(inventoryData).filter(([key]) => 
  key !== 'totals' && 
  key !== 'notes' && 
  key !== 'debug_info' && 
  key !== 'gl_analysis'
).map(([category, data]) => (
  // Component rendering
))}
```

### Sales Commission System Enhancements (2024)

#### Implementation Details
**Files**: `SalesCommissionReport.jsx`, commission calculation endpoints
**Features**: Equipment commission (15% gross profit), Rental commission (8% revenue)
**Data Source**: InvoiceReg table with actual cost data integration

#### Key Technical Insights
- **Cost Data Reality**: Equipment cost data available in InvoiceReg, not Equipment table
- **Gross Profit Calculations**: `Revenue - Cost` from invoice-level data
- **Commission Logic**: Different rates for equipment vs rental revenue streams
- **Date Range Handling**: Flexible period selection with fiscal year support

### AR Aging Report Critical Fixes (2024)

#### Technical Challenge Solved
**Issue**: AR aging required invoice-level grouping, not customer-level
**Solution**: `GROUP BY CustomerNo, InvoiceNo` instead of just `CustomerNo`
**Impact**: Accurate aging buckets (0-30, 31-60, 61-90, 90+ days)

#### Debug Methodology Established
- **Step 1**: Verify raw data with debug endpoints
- **Step 2**: Test grouping logic in isolation
- **Step 3**: Validate aging bucket calculations
- **Step 4**: Compare results with accounting expectations

### Rental Availability Reporting Breakthrough (2024)

#### Core Discovery: Quote vs Work Order Distinction
**Critical Learning**: Quotes are NOT rental orders
- **Quotes**: WO numbers starting with '9' (e.g., 91600003)
- **Work Orders**: Actual rental work orders (e.g., 130000713)
- **Filter Logic**: `AND wo.WONo NOT LIKE '9%'` to exclude quotes

#### Equipment Status Determination
```sql
-- On Rental Status Logic
SELECT e.SerialNo,
  CASE 
    WHEN rental_check.is_on_rental = 1 THEN 'On Rental'
    ELSE 'Available'
  END as current_status
FROM Equipment e
LEFT JOIN (
  SELECT DISTINCT wr.SerialNo, 1 as is_on_rental
  FROM WORental wr
  INNER JOIN WO wo ON wr.WONo = wo.WONo
  WHERE wo.Type = 'R' 
  AND wo.ClosedDate IS NULL
  AND wo.WONo NOT LIKE '9%'  -- CRITICAL: Exclude quotes
) rental_check ON e.SerialNo = rental_check.SerialNo
```

#### Department-Based Equipment Filtering
**Primary Filter**: `e.InventoryDept = 60` (Rental Department ownership)
**Customer Filter**: `e.Customer = 0 OR e.Customer IS NULL` (Company-owned equipment)
**Result**: Clean dataset matching Softbase's "Open Rental Orders" logic

### Work Order Notes System (PostgreSQL Integration)

#### Technical Implementation
**Database**: PostgreSQL table for custom work order notes
**Features**: Auto-save with 1-second debounce, full-text search, CSV export integration
**Architecture**: Hybrid approach using both Azure SQL (Softbase data) and PostgreSQL (custom data)

#### Performance Optimizations
- **Debounced Auto-save**: Prevents excessive API calls during typing
- **Indexed Search**: Full-text search on note content
- **Batch Loading**: Efficient loading of notes for work order lists

### Minitrac Equipment Database Migration (2024)

#### Business Impact
**Cost Savings**: Replaced $600/month SaaS subscription
**Data Volume**: 28,000+ equipment records migrated to PostgreSQL
**Features**: Equipment search, specifications, availability tracking

#### Technical Architecture
- **Data Migration**: Bulk import from Minitrac export files
- **Search Optimization**: Indexed search on make, model, specifications
- **Integration**: Seamless integration with existing equipment workflows

---

## Current Issues & Limitations

### Database Access Constraints
- **Azure SQL Firewall**: No local development database access
- **Production Dependency**: All development requires deployed backend
- **Query Performance**: Large table scans can be slow without proper indexing

### Technical Debt
- **Mixed TypeScript/JavaScript**: Inconsistent typing across components
- **Schema Assumptions**: Need database schema validation before query development
- **Error Handling Patterns**: Inconsistent JSON serialization safety across endpoints
- **Test Coverage**: Minimal automated testing infrastructure
- **Debug Logging**: Railway logging visibility issues during development

### Data Quality & Schema Challenges
- **Schema Documentation**: Incomplete understanding of GLDetail vs GL table differences
- **Date Column Variations**: Different date column names across tables (EffectiveDate, TranDate, Date)
- **Join Key Inconsistencies**: Customer.Number vs Customer.Id usage patterns
- **Null Value Handling**: Inconsistent NULL vs 0 handling in financial calculations

### Performance Bottlenecks
- **Dashboard Loading**: Multiple sequential API calls for dashboard data
- **Large Dataset Exports**: Memory constraints on large CSV/Excel exports
- **GL Query Performance**: GLDetail table scans can be slow without proper date indexing
- **Equipment Categorization**: 21K+ record categorization done in Python vs SQL

### Development Process Issues
- **Production-Only Database Access**: All testing requires Railway deployment
- **Logging Visibility**: Limited visibility into Railway application logs during development
- **Query Debugging**: Difficult to debug SQL queries without local database access
- **Schema Discovery**: Manual trial-and-error for understanding table structures

### Financial Data Accuracy Challenges
- **GL vs Equipment Book Values**: Equipment.Cost != actual GL account balances
- **Depreciation Calculations**: Complex fiscal year filtering across multiple date ranges
- **Invoice-Level Aggregations**: Need for invoice-level vs customer-level grouping patterns
- **Quote vs Work Order Logic**: Business logic complexities in rental status determination

---

## Recommended Improvements

### Critical Near-term (Next 30 days)
1. **Database Schema Documentation**: Complete mapping of all table schemas, column names, and relationships
2. **Financial Query Standardization**: Establish standard patterns for GL account balance queries
3. **JSON Serialization Safety**: Apply `make_json_safe()` pattern to all financial endpoints
4. **Schema Validation Middleware**: Validate table structures before executing dynamic queries
5. **Enhanced Logging Infrastructure**: Improve Railway logging visibility for development debugging

### Development Process Improvements (1-3 months)
1. **Local Development Database**: Set up development replica or test database with same schema
2. **Query Testing Framework**: Automated testing for SQL queries against known data sets
3. **Schema Discovery Tools**: API endpoints for exploring table structures and column types
4. **Financial Data Validation**: Automated validation of financial calculations against expected results
5. **Comprehensive TypeScript Migration**: Convert all financial calculation components to TypeScript

### Data Architecture Enhancements (3-6 months)
1. **Optimized Equipment Categorization**: Move categorization logic to SQL for better performance
2. **Financial Reporting Cache Layer**: Cache GL account balances and depreciation calculations
3. **Date Column Standardization**: Wrapper functions to handle different date column patterns
4. **Business Logic Documentation**: Document all quote vs work order, rental status, and categorization rules
5. **Data Quality Monitoring**: Automated alerts for financial data discrepancies

### Long-term Strategic Improvements (6+ months)
1. **Financial Data Warehouse**: Separate analytical database for historical financial reporting
2. **Advanced Equipment Tracking**: Real-time equipment status updates with WebSocket integration
3. **Audit Trail System**: Complete audit logging for all financial calculations and data changes
4. **API Documentation & Versioning**: Comprehensive API documentation with versioning strategy
5. **Mobile Field Service App**: Mobile application for real-time equipment and work order management

### Lessons-Learned Implementation Priorities
1. **Always Verify Schema First**: No assumptions about table structures or column names
2. **Financial Accuracy Over Performance**: GL account accuracy is more important than query speed
3. **Comprehensive Error Handling**: Every financial endpoint needs JSON serialization safety
4. **Business Logic Documentation**: Document all equipment categorization and status determination rules
5. **Test-Driven Financial Development**: All financial calculations must have automated validation tests