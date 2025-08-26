# Softbase Reports Project Context

## Sales Commission System Overhaul (2025-08-26)

### Overview
Completely redesigned the sales commission calculation system from a complex, manual process to a simplified, automated system using actual cost data from InvoiceReg table.

### Key Discoveries

#### InvoiceReg Has Cost Data!
- **Discovery**: InvoiceReg table contains actual cost columns we weren't using
- **Cost Fields Available**:
  - `EquipmentCost` - Cost of equipment sold
  - `LaborCost` - Cost of labor
  - `PartsCost` - Cost of parts
  - `MiscCost` - Cost of miscellaneous items
  - `RentalCost` - Cost of rentals
- **Impact**: Can calculate actual gross profit instead of using estimated margins

#### Previous Issues
- System was using hardcoded margin assumptions (20% for new equipment, 25% for rental sales)
- Commissions were inaccurate - based on assumed margins rather than actual profitability
- Complex rules with 20+ special cases made automation nearly impossible

### Implemented Solution: Simplified Commission Structure

#### New Commission Rules (Proposed)
1. **Equipment Sales** (All Types - New, Used, Allied):
   - 15% of actual gross profit (Revenue - Cost)
   - $75 minimum per invoice
   - No complex subcategories or special cases

2. **Rentals**:
   - 8% of rental revenue (reduced from 10%)
   - Unlimited duration (removed 12-month cap)
   - House accounts excluded via customer flag

#### Mathematical Justification for Rental Changes
- **Old System**: 10% × 12 months max = 120% of monthly rent maximum
- **New System**: 8% × unlimited months
- **Break-even**: At 15 months (120% total commission)
- **Benefits**:
  - Short rentals (<15 months): Company saves slightly
  - Long rentals (>15 months): Sales reps earn more
  - Encourages long-term customer retention
  - Eliminates complex tracking requirements

### Implementation Details

#### Backend Changes (`department_reports.py`)
1. **Updated SQL Queries** to include cost columns:
   ```sql
   -- Now fetching both revenue and cost
   SUM(CASE WHEN ir.SaleCode IN (...) 
       THEN COALESCE(ir.EquipmentTaxable, 0) + COALESCE(ir.EquipmentNonTax, 0)
   END) as NewEquipmentSales,
   SUM(CASE WHEN ir.SaleCode IN (...) 
       THEN COALESCE(ir.EquipmentCost, 0)
   END) as NewEquipmentCost
   ```

2. **Commission Calculation** using actual gross profit:
   ```python
   # OLD: Using assumed margins
   new_gp = new * 0.20  # Assumed 20% margin
   new_commission = new_gp * 0.20
   
   # NEW: Using actual cost data
   new_gp = new - new_cost  # Actual gross profit
   new_commission = new_gp * 0.15 if new_gp > 0 else 0
   ```

3. **Exclusions Added**:
   - House accounts excluded from commission calculations
   - Filter: `AND UPPER(sl.Salesman) != 'HOUSE'`

#### Frontend Updates (`SalesCommissionReport.jsx`)

1. **Commission Display Formatting**:
   - Created `formatCommission()` function for 2 decimal places ($150.70 not $151)
   - Sales amounts continue using `formatCurrency()` for whole dollars

2. **Added "Proposed Commission Structure" Card** showing:
   - Commission philosophy and benefits
   - Clear breakdown of new structure
   - Mathematical equivalence demonstration
   - Real-world rental duration examples

3. **Commission Calculation Breakdown** for each sales rep:
   - Shows actual gross profit calculations
   - Displays: Revenue - Cost = Gross Profit × 15% = Commission
   - Groups invoices by category for clarity
   - Full transparency in commission math

4. **UI Improvements**:
   - Renamed "Commission Structure" to "Current Commission Structure"
   - Added sortable columns to all invoice tables
   - Color-coded the proposed structure (green theme)
   - Added detailed calculation breakdowns under each rep's invoices

### Technical Patterns Established

#### Data Access Pattern
- Backend calculates commissions using actual cost data
- Frontend receives both revenue and cost for transparency
- Commission calculation happens in backend, display logic in frontend

#### Commission Calculation Flow
```javascript
// Frontend receives from backend:
{
  category_amount: 50000,  // Revenue
  category_cost: 40000,    // Cost (now included!)
  commission: 1500         // Pre-calculated commission
}

// Frontend can show the math:
Gross Profit = $50,000 - $40,000 = $10,000
Commission = $10,000 × 15% = $1,500
```

### Benefits Achieved

1. **Accuracy**: Commissions based on actual profitability, not estimates
2. **Simplicity**: Two rules replace 20+ complex scenarios
3. **Transparency**: Sales reps can see exact calculations
4. **Automation**: Fully automatable with no manual interventions
5. **Fairness**: Aligns company and sales rep interests

### Future Considerations

- Add `IsHouseAccount` flag to Customer table for automatic exclusions
- Consider phase-in period running old and new systems in parallel
- May need to adjust rates based on historical commission analysis
- Rental tracking table no longer needed with unlimited commission duration

## Minitrac Historical Data Integration (2025-08-22)

### Overview
Successfully implemented a complete solution to replace $600/month Minitrac subscription with self-hosted PostgreSQL storage of 28,030 equipment records from Excel export.

### Implementation Details

#### 1. Database Architecture
- **PostgreSQL Schema Created**: `minitrac_equipment` table with 120+ columns
- **Data Successfully Imported**: All 28,030 records from `MTrEquipment250226.xlsx`
- **Indexes Added**: On unit_num, serial, make, model, status, customer fields for performance
- **Full-text Search**: PostgreSQL GIN index for searching across multiple fields

#### 2. Backend API Endpoints Created
- `/api/minitrac/search` - Advanced search with filters and pagination
- `/api/minitrac/equipment/<unit_num>` - Detailed equipment information
- `/api/minitrac/filters` - Dynamic filter options for dropdowns
- `/api/minitrac/export` - CSV export functionality
- `/api/minitrac/stats` - Statistics (removed from UI but endpoint exists)

#### 3. Frontend Interface
- **Component**: `MinitracSearch.jsx` with comprehensive search UI
- **Features**: Search box, category/status/make filters, pagination, detail views
- **Export**: CSV download of search results
- **Menu Integration**: Added "Minitrac" item to navigation between Accounting and AI Query

### Key Learnings & Fixes

#### Import Path Issues in Production
- **Problem**: Routes in production need `src.` prefix for imports
- **Wrong**: `from services.postgres_service import PostgreSQLService`
- **Correct**: `from src.services.postgres_service import PostgreSQLService`

#### Authentication Decorator
- **Problem**: Used non-existent `require_auth` decorator
- **Solution**: Use `@jwt_required()` from `flask_jwt_extended` (standard in this project)

#### Select Component Constraints
- **Problem**: Radix UI Select components cannot have empty string values
- **Solution**: Use "all" as the value and convert to empty string in handler
```javascript
// Wrong
<SelectItem value="">All Categories</SelectItem>

// Correct
<SelectItem value="all">All Categories</SelectItem>
// Then in handler: value === "all" ? "" : value
```

#### Git Large File Issues
- **Problem**: 6MB Excel file caused push failures
- **Solution**: Add `*.xlsx` to `.gitignore`, data already imported to PostgreSQL

#### PostgreSQL Connection Pattern
- **Service Pattern**: Use `PostgreSQLService()` with context manager
```python
pg_service = PostgreSQLService()
with pg_service.get_connection() as conn:
    # Use connection
```

### Cost-Benefit Analysis
- **Eliminated Cost**: $600/month = $7,200/year
- **One-time Implementation**: ~2 hours
- **Result**: Full control, better integration, no recurring fees

### Files Created/Modified
- `/reporting-backend/src/routes/minitrac.py` - API endpoints
- `/reporting-backend/src/scripts/import_minitrac_data.py` - Import script
- `/reporting-frontend/src/components/MinitracSearch.jsx` - UI component
- `/reporting-frontend/src/App.jsx` - Added route
- `/reporting-frontend/src/components/Layout.jsx` - Added menu item
- `/reporting-backend/src/main.py` - Registered blueprint

## IMPORTANT: Git Workflow & Quality Assurance
**DO NOT push changes until they have been validated to work.** For the rest of any session:
1. Write the query/code changes first
2. Show the changes planned
3. Explain what is expected to happen
4. Wait for confirmation that current state is working
5. Only push after verifying the query returns data and works as expected

**Previous Issues from Lack of Testing:**
- ORDER BY clauses that referenced columns incorrectly
- Complex WHERE conditions that returned no results
- Breaking changes from untested assumptions

**Required Before Pushing:**
- Validate SQL queries return expected data
- Check for syntax errors and logical issues
- Verify changes won't break existing functionality
- Test edge cases where applicable

## CRITICAL: JSX Syntax Rules
1. **Never use `>` character directly in JSX text content** - Always escape it as `&gt;`
   - Wrong: `<p>>3 days</p>`
   - Correct: `<p>&gt;3 days</p>`
2. **Ensure all JSX tags are properly balanced** - Match opening and closing tags exactly
3. **When copying code between components, verify the data structure matches** - API responses may have different shapes

## CRITICAL: Database Query Best Practices (2025-08-15)
1. **Avoid SELECT * in production queries** - Can fail with certain column types that don't serialize to JSON
   - Wrong: `SELECT * FROM ben002.WORental`
   - Correct: `SELECT WONo, ControlNo, RentalContractNo FROM ben002.WORental`
2. **Always wrap database queries in try-catch blocks** - Tables might not exist or queries might fail
3. **Check table existence before querying** - Some tables like WORental may not exist in all installations
4. **Return partial results on failure** - Don't let one failed query break the entire endpoint
   - Use empty arrays as fallback: `except: results['data'] = []`
5. **Complex CTEs and UNION queries can fail silently** - Break them into simpler individual queries
   - Complex trace queries with multiple CTEs may not return proper error messages
   - Start with simple COUNT queries to verify tables exist and have data
6. **Debug endpoints incrementally** - Build from simplest query to complex
   - First verify table exists with COUNT(*)
   - Then try SELECT TOP 1 with specific columns
   - Only then build complex joins

## Work Order Lookup Tool Implementation (2025-08-15)

**Important Discovery**: The Work Order Detail Lookup tool uses a specific data structure from the API endpoint `/api/reports/departments/rental/wo-detail/{woNumber}`. This endpoint works for ALL work order types (Service, Rental, Parts, etc.).

**Data Structure**:
```javascript
woDetail = {
  workOrder: {
    number: "S123456",
    billTo: "12345",
    customerName: "Customer Name",
    unitNo: "U123",
    make: "CAT",
    model: "D6",
    saleCode: "SVE"
  },
  labor: {
    details: [...],      // Array of labor line items
    quoteItems: [...],   // Array of flat rate labor from quotes
    costTotal: 1234.56,
    sellTotal: 2345.67
  },
  parts: {
    details: [...],      // Array of parts with ExtendedSell calculated
    sellTotal: 3456.78
  },
  misc: {
    details: [...],      // Array of misc charges
    costTotal: 456.78,
    sellTotal: 567.89
  },
  totals: {
    totalCost: 5678.90,
    totalSell: 6789.01
  },
  invoice: [...]         // Array of associated invoices if any
}
```

**Key Learning**: When copying working implementations between components, always verify that:
1. The data structure access patterns match (e.g., `woDetail.workOrder.number` not `woDetail.header.WONo`)
2. The same endpoint is being used
3. All required state variables are defined
4. The formatCurrency function is available

## Sales Commission Report - Unassigned Invoices (2025-08-05)

### Current Status:
The following invoices remain unassigned because the customer records exist but have no salesman assigned:
- Invoice 110000007: B.D. SCHIFFLER INC /TANI (Customer #78700) - No salesman in Customer table
- Invoice 110000009: CKC GOOD FOOD (Customer #90960, #90961) - No salesman in Customer table

### Solution:
These need to be fixed in the source data by assigning salesmen to these customer records. The matching logic is working correctly - it's finding the customer records, but they don't have salesmen assigned.

### Commission Report Improvements Made:
1. Added ROW_NUMBER() to prevent duplicate invoices
2. Enhanced matching with three levels:
   - Direct BillTo number match
   - Exact name match
   - First word match (e.g., SIMONSON matches SIMONSON LUMBER)
3. Fixed NaN values in totals
4. Improved error handling
5. **Added BillTo column** (2025-08-22) - Now displays customer number between Date and Customer in Detailed Invoice Breakdown

### Detailed Commission Structure (Updated 2025-08-22)
Complete commission structure documentation added to Commission Structure card:
- **New Equipment**: 20% of profit with various minimums ($100 standard, $50 pallet trucks)
- **Used Equipment**: 5% of selling price or variable rates based on profit levels
- **Rental Equipment**: 10% standard, 5% for discounted rentals, with specific exclusions
- **Rental Equipment Sales**: Separate from rentals with own commission structure
- **RPO (Rental Purchase Option)**: Different handling for inadvertent vs signed quotes
- **Allied Products**: 20% of profit

## Dashboard Improvements (2025-08-22)

### Monthly Sales (No Equipment) Tooltip Enhancements
1. **Added department-specific gross margin tracking**
   - Shows margin percentage and month-to-month changes for Parts, Labor, Misc
   - Format: "GM: 42.5% +2.1pts" showing both current margin and point change
   - Rental shows "(No cost data)" as placeholder since true costs aren't available
2. **Fixed alignment issues** - All revenue items now align properly using consistent spacing

### Equipment Sales Tracking
1. **Discovery**: EquipmentHistory table's WONo column doesn't exist despite documentation
   - Initial attempt to track individual units via EquipmentHistory failed
   - Reverted to using InvoiceReg with invoice counts as proxy for units
2. **Filtered to New Equipment only**
   - Changed from showing ALL equipment to just NEW equipment sales
   - Added filtering: `SaleCode IN ('NEWEQ', 'LINDE', 'LINDEN', 'KOM', 'NEW')` or `SaleDept = 80`
   - Title changed from "Equipment Sales (All)" to "New Equipment Sales"
   - Should now match competing report's unit counts more closely
3. **Added unit tracking display**
   - Shows "Units Sold" in tooltip with month-over-month changes
   - Displays average units in card header
   - Note: These are invoice counts, not actual serial-tracked units

### Known Limitations
- **Equipment unit tracking**: Without proper table relationships to individual equipment records (SerialNo, UnitNo, Make, Model), we can't match competing report's exact unit-level detail
- **Rental margins**: No true cost data available for rental revenue calculations

## Overview
This is a comprehensive reporting system for Softbase Evolution, a heavy equipment management system. The project consists of a React frontend and Flask backend that connects to an Azure SQL Server database.

## Key Technologies
- **Frontend**: React, Vite, Tailwind CSS, Recharts
- **Backend**: Flask, PyMSSQL, JWT authentication
- **Database**: Azure SQL Server (schema: ben002)
- **Deployment**: Netlify (frontend), Railway (backend)

## Database Schema Information
To get the complete database schema:
1. Navigate to Database Explorer in the web app
2. Click "Export JSON" button to download complete schema
3. The JSON file contains all tables, columns, relationships, and sample data

### Key Tables:
- **InvoiceReg**: Invoice records with revenue data
- **WO**: Work orders (Type: S=Service, R=Rental, etc.)
- **Customer**: Customer information and balances
- **Equipment**: Equipment inventory and rental status
- **Parts**: Main parts inventory table (NOT NationalParts - see Important Discovery below)
- **WOParts**: Parts used on work orders (includes BOQty for backorders)
- **InvoiceArchive**: Archived invoice data
- **InvoiceSales**: Sales line items

### Important Fields:
- **SaleCode**: Department identifier (e.g., 'SVE' for Service, 'PRT' for Parts)
- **Department**: Direct department field on invoices
- **PartsTaxable/PartsNonTax**: Revenue fields for parts
- **LaborTaxable/LaborNonTax**: Revenue fields for labor

## IMPORTANT: Development vs Production

### LOCAL DEVELOPMENT (on your machine for testing):
- **Frontend dev**: `cd reporting-frontend && npm run dev` (runs on localhost:5173 or similar)
- **Backend dev**: `cd reporting-backend && python -m src.run` (runs on localhost:5000 or 5001)
- **Purpose**: Test changes locally before pushing to git
- **Note**: Vite proxy forwards /api calls from frontend to local backend

### PRODUCTION DEPLOYMENT (automatic):
- **Deploy**: Auto-deploys on git push (Netlify for frontend, Railway for backend)
- **Frontend**: Automatically deployed to Netlify when you push to git
- **Backend**: Automatically deployed to Railway when you push to git
- **No manual deployment needed**: Just `git push` and both services auto-deploy

### Build Commands:
- **Build frontend locally** (for testing): `cd reporting-frontend && npm run build`
- **You don't need to build manually for deployment** - Netlify builds automatically

## Performance Optimizations
1. Dashboard uses parallel query execution
2. Optimized endpoints at `/api/dashboard-optimized`
3. Redis caching ready but not currently implemented
4. Database indexes recommended for commonly queried columns

## Authentication
- JWT-based authentication
- Token stored in localStorage
- All API endpoints require authentication except /auth/login

## Recent Issues Fixed
1. Tooltip import conflict in ServiceReport (renamed to RechartsTooltip)
2. Technician Performance showing 0 data (changed to last 30 days)
3. Department Gross Margins calculation (fixed to use invoice-level fields)
4. Accounting Financial Performance showing mock data (fixed endpoint conflict)
5. Monthly Quotes handling duplicates (now uses latest quote per work order per month)
6. Top 10 Customers now shows percentage of total fiscal YTD sales
7. Parts reports: Added fill rate, reorder alerts, velocity analysis, demand forecasting
8. Filtered consumables (oil, grease, coolant, anti-freeze) from Top 10 Parts
9. Fixed decimal displays to show whole numbers for stock quantities

## Known Issues to Fix

### Parts Quantity Calculation in Work Order Queries
**Issue**: Some queries are using `SUM(Sell)` instead of `SUM(Sell * Qty)` for parts calculations
**Impact**: Parts totals may be understated when quantity > 1
**Files to Check**:
- `/api/reports/dashboard/summary-optimized` endpoint
- Any work order cost calculation queries
**Correct Pattern**:
```sql
SELECT WONo, SUM(Sell * Qty) as parts_sell 
FROM ben002.WOParts 
GROUP BY WONo
```

## CRITICAL: AR Aging Report Implementation (2025-08-04)

### AR AGING ISSUES AND CURRENT STATUS

**Current Problem**: AR aging buckets are showing incorrect values compared to source system. The calculations are complex and still being debugged.

**User's Expected Values from Direct Database Pull**:
- **Total AR**: $1,697,050.59 ✓ (matches)
- **Current**: $389,448.08
- **30-60 Days**: $312,764.25  
- **60-90 Days**: $173,548.60
- **90-120 Days**: $27,931.75
- **120+ Days**: Unknown
- **Over 90 Days Total**: $55,718 (confirmed correct value)

**What We're Currently Getting**:
- Buckets are calculating different amounts than expected
- Over 90 is showing ~$91K instead of expected $55,718 (we're $35K too high)
- The bucket boundaries may be off

### CRITICAL DISCOVERIES:

1. **Invoice-Level Grouping Required**: 
   - Must group ARDetail by invoice first, then age the invoice balance
   - Individual ARDetail records include payments (negative amounts) that shouldn't be aged separately
   - **CRITICAL**: When grouping, use `GROUP BY ar.CustomerNo, ar.InvoiceNo` ONLY
   - Do NOT include `ar.Due` in the GROUP BY - this creates duplicates!

2. **The Due Date Grouping Bug** (SOLVED):
   - **Problem**: Grouping by `CustomerNo, InvoiceNo, Due` was creating duplicate invoice entries
   - **Why**: ARDetail can have multiple due dates per invoice (from payment applications, adjustments, etc.)
   - **Solution**: Group by `CustomerNo, InvoiceNo` only and use `MIN(ar.Due)` to get single due date
   - **Impact**: This was causing 2x inflation in customer balances (e.g., Grede showing $99K instead of $47K)

3. **Customer AR Debug Validation** (CONFIRMED WORKING):
   - Grede: Expected $47,320.42 ✓ (now matches exactly)
   - Polaris: Numbers now match exactly ✓
   - Owens: Numbers now match exactly ✓
   - Fixed by removing Due from GROUP BY clause

4. **Over 90 Days Total Issues**:
   - **Current Status**: Showing $91K but should be $55,718
   - User initially said $201,479 but that included 60-90 bucket
   - Actual over 90 is much lower than originally stated
   - Still investigating why we're ~$35K too high

### CURRENT IMPLEMENTATION:

```sql
-- Invoice grouping CTE
WITH InvoiceBalances AS (
    SELECT 
        ar.InvoiceNo,
        ar.CustomerNo,
        MIN(ar.Due) as Due,
        SUM(ar.Amount) as NetBalance
    FROM ben002.ARDetail ar
    WHERE (ar.HistoryFlag IS NULL OR ar.HistoryFlag = 0)
        AND ar.DeletionTime IS NULL
        AND ar.InvoiceNo IS NOT NULL
    GROUP BY ar.InvoiceNo, ar.CustomerNo
    HAVING SUM(ar.Amount) > 0.01
)
-- Then age by Due date
```

### DEBUG TOOLS CREATED:

1. **ARAgingDebug Component** (`/components/ARAgingDebug.jsx`):
   - Shows calculated vs expected values
   - Displays all buckets with counts
   - Added to AccountingReport page

2. **CustomerARDebug Component** (`/components/CustomerARDebug.jsx`):
   - Shows specific customer balances for Polaris, Grede, Owens
   - Lists individual invoices over 90 days
   - Helps verify customer-level calculations

3. **Debug Endpoints**:
   - `/api/reports/departments/accounting/ar-aging-debug`
   - `/api/reports/departments/accounting/customer-ar-debug`

### IMPORTANT NOTES:

- **NEVER access endpoints directly** - always use UI components due to firewall
- User is very frustrated with repeated mistakes and crashes
- Document EVERYTHING in CLAUDE.md immediately
- The bucket labels and boundaries are still unclear
- Need to determine if "over 90" includes the 60-90 bucket in their system

## Deployment URLs
- **Frontend**: https://softbasereports.netlify.app
- **Backend**: https://softbasereports-production.up.railway.app

## CRITICAL: API URL Usage
**NEVER hardcode backend URLs in frontend code!** Always use the `apiUrl` helper function from `@/lib/api`:

```javascript
import { apiUrl } from '@/lib/api';

// CORRECT:
const response = await fetch(apiUrl('/api/some-endpoint'));

// WRONG - NEVER DO THIS:
const response = await fetch('https://some-url.herokuapp.com/api/some-endpoint');
```

The `apiUrl` function handles:
- Local development (uses proxy)
- Production deployment (uses Netlify redirects to Railway)
- Environment-specific configuration

## Environment Variables
Backend requires:
- DATABASE_URL or individual DB connection params
- JWT_SECRET_KEY
- FLASK_ENV
- PORT (for Railway)

## File Structure
```
/reporting-frontend
  /src
    /components
      /departments (department-specific reports)
      /ui (reusable UI components)
    /contexts (AuthContext)
    /lib (API utilities)

/reporting-backend
  /src
    /routes (API endpoints)
    /services (database, cache services)
    /utils (auth, decorators)
```

## Key Features
1. Interactive Dashboard with multiple metrics
2. Department-specific reports (Service, Parts, Rental, Accounting)
3. Invoice Explorer for detailed invoice analysis
4. Database Explorer for schema browsing
5. AI Query tool for natural language queries
6. Report Creator for custom reports

## Recent Features Added

### Work Orders Awaiting Invoice Tracking (2025-08-05)

Created comprehensive invoice delay tracking system across all departments to identify work orders completed but not yet invoiced.

**Key Discoveries:**
1. **Work Order Types**:
   - S = Service
   - SH = Shop (part of Service department)
   - PM = Preventive Maintenance (part of Service department)
   - P = Parts
   - R = Rental
   - E = Equipment
   - I = Internal

2. **Invoice Delay Analysis**:
   - Added awaiting invoice tracking to Dashboard > Work Orders for ALL departments
   - Service department has worst delays: 19.4 days average (vs 16 overall)
   - Only 19.5% of Service work orders meet 3-day invoicing target
   - Over $142K in Service work orders awaiting invoice

**Implementation Details:**
1. **Backend Changes**:
   - Updated `/api/reports/dashboard/summary-optimized` to include awaiting invoice metrics
   - Created `/api/reports/departments/service/awaiting-invoice-details` endpoint
   - Created `/api/reports/departments/parts/awaiting-invoice-details` endpoint
   - Fixed SQL error: Removed non-existent CancelledDate column check
   - **IMPORTANT**: Parts queries must use `SUM(Sell * Qty)` not just `SUM(Sell)`

2. **Frontend Changes**:
   - Added comprehensive invoice delay breakdown report to Dashboard > Work Orders
   - Moved Service awaiting invoice card to Service department page
   - Created tabbed interface on Service page (Overview and Work Orders tabs)
   - Added Parts awaiting invoice card to Parts department page
   - Removed redundant cards from Dashboard (Open WOs, Uninvoiced WOs, Average Days chart)

3. **UI/UX Improvements**:
   - Work orders sorted by oldest first (ASC) to prioritize longest delays
   - Color coding: Orange for >3 days, Red for >7 days
   - Export to CSV functionality for all awaiting invoice reports
   - Avoided modal width issues by displaying reports directly on page

**Technical Notes:**
- Work order lifecycle: Open → Completed (CompletedDate set) → Closed/Invoiced (ClosedDate set)
- Awaiting Invoice = CompletedDate IS NOT NULL AND ClosedDate IS NULL
- Labor costs include both WOLabor entries AND WOQuote entries where Type='L'

### Rental Service Report (2025-07-30)
Created a comprehensive Service Report for the Rental Department showing service work orders billed to rental.

**Requirements:**
- Show total number of Service Work Orders associated with Rental Trucks
- Display list with real-time cost breakdown (Labor, Parts, Misc)
- Include sum totals at the bottom
- Service Work Orders where Rental Department is the Bill To

**Implementation Details:**
1. **Backend Endpoint**: `/api/reports/departments/rental/service-report` in `department_reports.py`
2. **Frontend Component**: `RentalServiceReport.jsx` 
3. **Access**: Available under "Service Report" tab on the Rental page

**Key Database Insights:**
- Rental service work orders are identified by SaleCode:
  - `RENTR` = Rental Repairs (SaleDept 40)
  - `RENTRS` = Rental Repairs - Shop (SaleDept 45)
- WO table uses `BillTo` field (not Customer)
- Equipment is stored in `UnitNo` field
- WOParts table doesn't have a Quantity column (use Cost directly)

**Performance Optimizations:**
- Original implementation made 100+ queries (one per work order)
- Optimized to single CTE-based query joining all cost tables
- Added optimized monthly trend query with costs/revenue
- Reduced load time from several seconds to milliseconds

**Query Structure:**
```sql
WITH RentalWOs AS (
    -- Get rental service work orders
),
LaborCosts AS (
    -- Aggregate labor costs
),
PartsCosts AS (
    -- Aggregate parts costs  
),
MiscCosts AS (
    -- Aggregate misc costs
)
-- Join everything together
```

**Diagnostic Tools Created:**
- `/api/reports/departments/rental/wo-schema` - Explores WO table structure
- `/api/reports/departments/rental/sale-codes` - Lists all sale codes
- `RentalDiagnostic.jsx` - Frontend diagnostic component (can be removed)

### Parts Inventory Table Discovery (2025-08-02)

**IMPORTANT DISCOVERY: The actual parts inventory is in the `Parts` table, NOT `NationalParts`!**

During implementation of the Parts Fill Rate report, we discovered:

1. **NationalParts table is empty** (0 rows) - This was causing all inventory queries to fail
2. **Parts table contains the actual inventory data** (11,413 rows)
3. **Parts table has the `OnHand` column** we need for inventory tracking

**Parts Table Structure:**
- `PartNo`: Part number
- `Description`: Part description  
- `OnHand`: Current inventory on hand (the key field for fill rate calculations)
- `Cost`: Part cost
- `List`: List price
- Other standard inventory fields

**WOParts Table Structure (for tracking parts orders):**
- `WONo`: Work order number
- `PartNo`: Part number ordered
- `Description`: Part description
- `Qty`: Quantity ordered
- `BOQty`: Backorder quantity (important for tracking stockouts)
- `Sell`: Selling price
- `Cost`: Cost

**Parts Fill Rate Implementation:**
The fill rate report now correctly:
1. Joins WOParts with Parts table on PartNo
2. Uses Parts.OnHand to check stock availability
3. Uses WOParts.BOQty to identify backordered items
4. Filters for Linde parts: `(PartNo LIKE 'L%' OR Description LIKE '%LINDE%')`
5. Calculates fill rate as: (Orders with stock available / Total orders) × 100

**Key Learning:**
Always verify table contents before assuming based on table names. What seems like the obvious table (NationalParts for parts inventory) may not be the correct one. The Database Explorer's export functionality is invaluable for discovering the actual data structure.

### Monthly Quotes (2025-08-02)

**WOQuote Table Structure Discovery:**
The WOQuote table contains individual quote line items, not complete quotes. Key findings:
- Each row is a line item (QuoteLine field) 
- Multiple line items per work order (WONo)
- Type field indicates line type: L=Labor, P=Parts, etc.
- No Customer field - quotes are linked via work order number
- Amount field contains the dollar value for each line item

**Current Implementation:** 
Uses only the latest quote per work order per month:
```sql
WITH LatestQuotes AS (
    -- Get the latest quote date for each WO per month
    SELECT 
        YEAR(CreationTime) as year,
        MONTH(CreationTime) as month,
        WONo,
        MAX(CAST(CreationTime AS DATE)) as latest_quote_date
    FROM ben002.WOQuote
    WHERE CreationTime >= '2025-03-01'
    AND Amount > 0
    GROUP BY YEAR(CreationTime), MONTH(CreationTime), WONo
),
QuoteTotals AS (
    -- Sum all line items for each WO on its latest quote date
    SELECT 
        lq.year,
        lq.month,
        lq.WONo,
        SUM(wq.Amount) as wo_total
    FROM LatestQuotes lq
    INNER JOIN ben002.WOQuote wq
        ON lq.WONo = wq.WONo
        AND lq.year = YEAR(wq.CreationTime)
        AND lq.month = MONTH(wq.CreationTime)
        AND CAST(wq.CreationTime AS DATE) = lq.latest_quote_date
    WHERE wq.Amount > 0
    GROUP BY lq.year, lq.month, lq.WONo
)
SELECT year, month, SUM(wo_total) as amount
FROM QuoteTotals
GROUP BY year, month
```

**Benefits of this approach:**
- Each work order uses only its most recent quote within each month
- Multiple quote revisions are handled properly (only latest counts)
- Reflects the actual quote values customers are seeing
- More accurate representation of expected revenue

### Parts Management Reports (2025-08-02)

Created comprehensive parts inventory management system with multiple reports.

**Reports Implemented:**
1. **Parts Fill Rate**: Shows which Linde parts were not on hand when ordered
2. **Parts Reorder Alerts**: Identifies parts needing reorder based on usage patterns
3. **Parts Velocity Analysis**: Categorizes inventory by movement speed
4. **Parts Demand Forecast**: Predicts future demand based on historical trends
5. **Top 10 Parts by Quantity**: Shows most frequently sold parts

**Key Features:**
- Tab-based organization (Overview, Stock Alerts, Velocity, Forecast)
- Excel download functionality for all reports
- Clickable cards showing details in modal dialogs
- Hover tooltips explaining calculations
- Filtered out consumables (oil, grease, coolant, anti-freeze) from analysis

**Technical Details:**
- Fill rate calculation: (Orders with stock / Total orders) × 100
- Reorder point: (Lead time + Safety stock) × Average daily usage
- Velocity categories: Very Fast (>12x/year), Fast (6-12x), Medium (2-6x), Slow (0.5-2x), Very Slow (<0.5x)
- Forecast uses 12-month history with trend adjustment factors

**UI Improvements:**
- Fixed decimal displays (was showing "34.0000", now shows "34")
- Removed low-value Monthly Demand Trend card
- Default "Include Current Month" unchecked on Dashboard
- Added percentage of total sales to Top 10 Customers

## Rental Availability - Ship To Customer Issue (SOLVED 2025-08-15)

**CRITICAL LEARNING: Always trust that competing products work - the data IS there!**
- The competing product showed correct customers, proving the data existed
- We initially blamed "missing data" but the real issue was not finding the right table/join
- Lesson: If another product can do it, we can too - keep searching!

**SOLUTION FOUND: WORental + WO Tables Have the Customer Data!**

The rental customer information is stored in:
1. **WORental table** - Contains SerialNo, UnitNo, and WONo for rental equipment
2. **WO table** - Work orders with Type='R' (Rental) that have:
   - RentalContractNo populated (for rental work orders)
   - BillTo field with the actual customer number
   - These WOs link to Customer table for customer names

**The Working Query Path**:
```
Equipment → WORental (via SerialNo/UnitNo) → WO (via WONo) → Customer (via BillTo)
```

**Key Discovery Process**:
1. Initially thought RentalContract → WO → Customer would work
2. Found RentalContract has no CustomerNo field
3. Found WO.RentalContractNo exists but wasn't always populated
4. Diagnostic revealed WORental records DO link to WOs with RentalContractNo
5. These Type='R' work orders have the actual customer in BillTo field

**Actual Customer Examples Found**:
- Unit 12330 → BETHANY PRESS (not RENTAL FLEET)
- Unit 12446C → ALEXANDRIA PRECISION MACHINING
- Unit 13136C → TRADEMARK TRANSPORTATION
- Unit 13400C2R → WINNESOTA
- Unit 14909 → TWIN CITY DIE

**Implementation**:
- Query the most recent rental WO for each equipment from WORental
- Join to WO table to get BillTo (customer number)
- Join to Customer table to get customer name
- Falls back to Equipment.CustomerNo if no rental WO found

**Lessons Learned**:
1. Don't assume data is missing - it's likely in an unexpected place

## CRITICAL: Query Optimization for CTEs with Complex Joins (2025-08-15)

**PROBLEM**: Service Report was timing out when trying to use the same customer lookup as Availability Report

**ROOT CAUSE**: Placement of joins matters significantly with CTEs!
- **WRONG**: Putting complex joins INSIDE the CTE (causes joins to execute for every row during CTE processing)
- **RIGHT**: Putting complex joins OUTSIDE the CTE in the final SELECT (joins only the final result set)

**The Failed Approach** (causes timeout):
```sql
WITH RentalWOs AS (
    SELECT w.*, rental_cust.Name  -- ❌ Joins inside CTE
    FROM WO w
    LEFT JOIN (complex subquery) ON ...
    LEFT JOIN Customer ON ...
),
LaborCosts AS (...),
PartsCosts AS (...)
SELECT * FROM RentalWOs ...
```

**The Working Approach** (same as Availability Report):
```sql
WITH RentalWOs AS (
    SELECT w.*  -- ✅ Simple select, no joins
    FROM WO w
),
LaborCosts AS (...),
PartsCosts AS (...)
SELECT 
    r.*,
    rental_cust.Name  -- ✅ Joins in final SELECT
FROM RentalWOs r
LEFT JOIN (complex subquery) ON ...  -- Joins happen AFTER CTEs complete
LEFT JOIN Customer ON ...
```

**Key Learning**: When using CTEs for aggregation (like summing costs), keep the CTEs simple and do complex lookups in the final SELECT. This dramatically improves performance because:
1. CTEs process their data first without complex joins
2. Complex joins only happen on the final, smaller result set
3. The database optimizer can better handle the query

**Pattern to Follow**:
- Use CTEs for filtering and aggregation
- Keep CTEs simple - avoid complex joins inside them
- Do customer lookups and complex joins in the final SELECT statement
- This is exactly how the Availability Report works successfully
2. WORental table is crucial for rental customer linkage
3. Type='R' work orders are specifically for rentals
4. The competing product's success proves the data exists - keep searching!

## Control Number Field Discovery (2025-08-15)

**Discovered**: Equipment.ControlNo field (nvarchar, 50 chars) is the internal accounting control number.

**Purpose**: Internal equipment tracking/reference number for accounting, separate from serial numbers.

**Usage Found In**:
- Equipment, WO, InvoiceReg tables (linking equipment to transactions)
- GLDetail table (for general ledger entries)
- EQControlNoChange table (audit trail for control number changes)
- Company.NextControlNo (auto-increment sequence)

**Report Created**: Control Number to Serial Number mapping report for accounting team in Accounting > Control Numbers tab.

## Feature Requests

### Work Order Notes Feature (2025-08-15) - IN PROGRESS

**Request**: Service manager requested ability to add editable notes column to the work orders report on the Service department page.

**Challenge**: The Azure SQL database (schema: ben002) is **read-only** - we cannot modify the Softbase database tables.

**Solution Implemented: PostgreSQL on Railway**

**CURRENT STATUS**: ✅ Notes feature fully working! Successfully saves and persists work order notes.

**User has PostgreSQL already deployed on Railway**:
- Connection strings provided by user:
  - Internal: `postgresql://postgres:ZINQrdsRJEQeYMsLEPazJJbyztwWSMiY@postgres.railway.internal:5432/railway`
  - External: `postgresql://postgres:ZINQrdsRJEQeYMsLEPazJJbyztwWSMiY@nozomi.proxy.rlwy.net:45435/railway`

**Implementation Completed**:

1. **Database Schema Created**:
   ```sql
   CREATE TABLE work_order_notes (
       id SERIAL PRIMARY KEY,
       wo_number VARCHAR(50) NOT NULL,
       note TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       created_by VARCHAR(100),
       updated_by VARCHAR(100)
   );
   CREATE INDEX idx_wo_number ON work_order_notes(wo_number);
   ```

2. **Backend Files Created**:
   - `reporting-backend/src/services/postgres_service.py` - PostgreSQL connection pool service
   - `reporting-backend/src/routes/work_order_notes.py` - CRUD endpoints for notes
   - `reporting-backend/src/routes/postgres_diagnostic.py` - Diagnostic endpoints for testing connection
   - Endpoints: 
     - `GET/POST /api/work-orders/notes`
     - `GET /api/work-orders/notes/<wo_number>`
     - `PUT /api/work-orders/notes/<int:note_id>`
     - `DELETE /api/work-orders/notes/<int:note_id>`
     - `POST /api/work-orders/notes/batch`
     - `GET /api/postgres/diagnostic` - Test connection
     - `POST /api/postgres/force-create-tables` - Force create tables

3. **Frontend Implementation**:
   - Modified `reporting-frontend/src/components/departments/ServiceReport.jsx`
   - Added Notes column to Work Orders table (far right)
   - Auto-save with 1-second debounce after typing stops
   - Notes included in CSV export
   - Removed Type and Technician columns for better UX
   - Added `PostgresTest` component with Test Connection button for debugging

4. **Known Issues FIXED**:
   - ✅ **Port Issue**: Vite proxy was pointing to port 5000, backend runs on 5001
   - ✅ **Production Crash**: Missing postgres_diagnostic import caused crash
   - ✅ **Type Mismatch Error**: wo_number is VARCHAR in PostgreSQL but we were sending integers
     - Error: "operator does not exist: character varying = integer"
     - Solution: Convert work order numbers to strings before sending: `String(woNumber)`

5. **Debugging Steps Taken**:
   - Created PostgresTest component with "Test Connection" button
   - Added diagnostic endpoints to verify PostgreSQL connection
   - Fixed Vite proxy configuration (port 5000 → 5001)
   - Restored diagnostic endpoints after accidentally removing them

**Files Modified**:
- `reporting-backend/src/main.py` - Added blueprint registrations
- `reporting-backend/src/services/postgres_service.py` - PostgreSQL connection service
- `reporting-backend/src/routes/work_order_notes.py` - Notes CRUD endpoints
- `reporting-backend/src/routes/postgres_diagnostic.py` - Diagnostic endpoints
- `reporting-frontend/src/components/departments/ServiceReport.jsx` - Added notes column
- `reporting-frontend/src/components/PostgresTest.jsx` - Test connection component
- `reporting-frontend/vite.config.js` - Fixed proxy port (5000 → 5001)

**Feature Complete**: Notes are working perfectly. Users can:
- Add/edit notes for any work order
- Notes auto-save 1 second after typing stops  
- Notes persist across sessions
- Notes are included in CSV export
- PostgresTest diagnostic component removed after successful implementation

## Complete Database Schema Documentation

Generated on: 2025-08-03 - Schema: `ben002`

### Base Tables (25 documented)

#### APDetail
Rows: 3,331
- Accounts payable detail transactions
- Key fields: AccountNo, Amount, APInvoiceNo, VendorNo, DueDate, CheckNo
- Links to vendors and payment processing

#### ARDetail  
Rows: 8,413
- Accounts receivable detail transactions
- Key fields: CustomerNo (nvarchar), Amount (decimal), InvoiceNo (int), CheckNo, Due (datetime)
- Other fields: EntryType, EntryDate, EffectiveDate, ApplyToInvoiceNo, AccountNo
- NO Balance column - use Amount field for outstanding amounts
- Join with Customer using CustomerNo = Customer.Number

#### ChartOfAccounts
Rows: 309
- Complete chart of accounts structure
- Key fields: AccountNo, Description, Type, Department, Section
- Defines GL account hierarchy and categories

#### Customer
Rows: 2,227  
- Master customer table
- Key fields: Id (bigint PK), Number (nvarchar), Name, Address, City, State, ZipCode
- Other fields: Terms, CreditHoldFlag, Taxable, TaxCode, Salesman1-6
- NO Balance or YTD columns - use ARDetail for outstanding balances
- Join with other tables using Number field, not Id

#### Equipment
Rows: 21,291
- Equipment inventory master
- Key fields: UnitNo (nvarchar), SerialNo (nvarchar), Make, Model, ModelYear, RentalStatus
- Financial: Cost (decimal), Sell (decimal), Retail (decimal)
- Customer: Customer (bit), CustomerNo (nvarchar) - Customer is boolean flag, CustomerNo is the actual customer number
- Rental: RentalStatus, DayRent, WeekRent, MonthRent, Location
- NO Description field! NO StockNo field!
- Join with Customer using CustomerNo = Customer.Number

#### EquipmentHistory
Rows: 15,369
- Equipment transaction history
- Key fields: SerialNo, Date, EntryType, Cost, Sell, WONo
- Records all equipment movements and transactions

#### GLDetail
Rows: 64,180
- General ledger detail transactions
- Key fields: AccountNo, Amount, EffectiveDate, Journal, Source, CustomerNo, VendorNo
- Complete GL transaction history

#### InvoiceReg
Rows: 5,148
- Invoice register/header
- Key fields: InvoiceNo (int PK), InvoiceDate (datetime), GrandTotal (decimal)
- Customer info: Customer (bit NOT NULL), BillTo (nvarchar), BillToName (nvarchar)
- Department: SaleCode (nvarchar), SaleBranch (smallint), SaleDept (smallint)
- Revenue fields: LaborTaxable, LaborNonTax, PartsTaxable, PartsNonTax, MiscTaxable, MiscNonTax
- Equipment/Rental: EquipmentTaxable, EquipmentNonTax, RentalTaxable, RentalNonTax
- Tax fields: TotalTax, StateTax, CityTax, CountyTax, LocalTax
- NO Department field! Use SaleCode/SaleDept instead
- Customer field is a boolean flag - actual customer info is in separate table

#### PM (Preventive Maintenance)
Rows: 2,792
- PM schedules and history
- Key fields: SerialNo, BillTo, Frequency, NextPMDate, Status, WONo
- Tracks equipment maintenance schedules

#### Parts
Rows: 11,413  
- Parts inventory master (NOT NationalParts!)
- Key fields: Id (bigint PK), PartNo (nvarchar), Warehouse (nvarchar), Description (nvarchar)
- Inventory: OnHand (decimal), Allocated, OnOrder, BackOrder
- Pricing: Cost (decimal), List (decimal), Discount, Internal, Warranty, Wholesale
- Stock levels: MinStock (decimal), MaxStock (decimal), AbsoluteMin
- Location: Bin, Bin1, Bin2, Bin3, Bin4
- NO Supplier field! NO QtyOnHand field - use OnHand!
- NO Price field - use List for list price!

#### PartsCost
Rows: 1,945
- Parts cost layers
- Key fields: PartNo, Warehouse, Cost, Qty, EntryDate
- Tracks parts cost history by receipt

#### PartsDemand
Rows: 11,413
- Parts demand history by month
- Key fields: PartNo, Warehouse, Demand1-12 (current year), DemandLast1-12 (prior year)
- Used for forecasting and velocity analysis

#### PartsSales  
Rows: 11,413
- Parts sales history by month
- Key fields: PartNo, Warehouse, Sales1-12 (current year), SalesLast1-12 (prior year)
- Revenue tracking for parts analytics

#### RentalContract
Rows: 318
- Rental agreement headers
- Key fields: RentalContractNo, StartDate, EndDate, DeliveryCharge, PickupCharge
- Manages rental agreements

#### RentalHistory
Rows: 11,568
- Monthly rental revenue by equipment
- Key fields: Id (bigint PK), SerialNo (nvarchar), Year (smallint), Month (smallint), DaysRented (int), RentAmount (decimal)
- Tracks actual rental activity by month for each piece of equipment
- Use this table to find active rentals: Equipment with records in recent months
- Join with Equipment table on SerialNo to get equipment details
- Join with Equipment.CustomerNo to get customer information
- Audit fields: CreationTime, CreatorUserId, LastModificationTime, LastModifierUserId

#### SaleCodes
Rows: 79
- Department/sale code definitions
- Key fields: Branch, Dept, Code, GL accounts for each revenue type
- Maps departments to GL accounts

#### Sales
Rows: 2,227
- Customer sales summary view
- Key fields: CustomerNo, YTD, LastYTD, ITD, by category (Parts, Labor, Rental, Equipment)
- Pre-aggregated customer sales data
- This is a VIEW that contains YTD sales data (Customer table itself has no YTD column)

#### ServiceClaim
Rows: 0 (empty table)
- Warranty/service claims
- Key fields: DealerInvoiceNo, CustomerNo, SerialNo, RepairDate, DealerTotal
- Tracks warranty claims processing

#### TransDetail
Rows: 0 (empty table)
- Transportation/transfer details
- Key fields: SerialNo, UnitNo, CustomerNo, ScheduledPickup, ScheduledDelivery
- Equipment movement tracking

#### WIPView
Rows: 666
- Work in progress summary view
- Key fields: WONo, Name, OpenDate, Labor, Parts, Misc totals
- Real-time WIP reporting

#### WO (Work Orders)
Rows: 6,879
- Work order headers
- Key fields: WONo (PK), Type (S/R/I), BillTo, UnitNo, OpenDate, ClosedDate, Technician
- Note: Use ClosedDate IS NULL for open work orders

#### WOLabor  
Rows: 6,401
- Work order labor details
- Key fields: WONo, MechanicName, Hours, Cost, Sell, DateOfLabor
- Labor charges by work order

#### WOMisc
Rows: 7,832
- Work order miscellaneous charges
- Key fields: WONo, Description, Cost, Sell, Taxable
- Misc charges like freight, shop supplies

#### WOParts
Rows: 10,381
- Work order parts details  
- Key fields: WONo, PartNo, Qty, BOQty (backorder), Cost, Sell
- Parts used on work orders

#### WOQuote
Rows: 1,481
- Work order quotes
- Key fields: WONo, QuoteLine, Type (L/P/M), Amount, CreationTime
- Quote line items (not complete quotes)

## Key Database Views

The database contains 271 views in addition to base tables. Here are the most important views for reporting and analytics:

### Financial/Accounting Views
- **GLDetail** (31 columns) - General ledger transaction details
- **ARDetail** (38 columns) - Accounts receivable details  
- **APDetail** (40 columns) - Accounts payable details
- **TransDetail** (40 columns) - Transaction details
- **ChartOfAccounts** (58 columns) - Account structure and hierarchy

### Sales/Customer Views
- **Sales** (57 columns) - Core sales data aggregations
- **SalesCodes** (99 columns) - Department/sales categorization details

### Work Order Views  
- **WIPView** (20 columns) - Work in progress summary view

### Equipment/Rental Views
- **EquipmentHistory** (26 columns) - Equipment usage and maintenance history
- **RentalContract** (25 columns) - Rental agreement details
- **RentalHistory** (12 columns) - Rental transaction history

### Parts/Inventory Views
- **PartsSales** (34 columns) - Parts sales analytics  
- **PartsDemand** (34 columns) - Parts demand forecasting data
- **PartsCost** (20 columns) - Parts costing and pricing data

### Service Views
- **PM** (54 columns) - Preventive maintenance schedules and history

These views contain pre-aggregated or denormalized data optimized for reporting, making them more efficient than joining multiple base tables. They are particularly useful for:
- Dashboard metrics and KPIs
- Historical trend analysis  
- Forecasting and predictive analytics
- Cross-departmental reporting