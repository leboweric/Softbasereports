# Softbase Reports Project Context

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

## Common Commands
- **Frontend dev**: `cd reporting-frontend && npm run dev`
- **Backend dev**: `cd reporting-backend && python -m src.run`
- **Build frontend**: `cd reporting-frontend && npm run build`
- **Deploy**: Auto-deploys on git push (Netlify for frontend, Railway for backend)

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

## CRITICAL: AR Aging Report Implementation (2025-08-04)

### AR AGING ISSUES AND CURRENT STATUS

**Current Problem**: AR aging buckets are showing incorrect values compared to source system. The calculations are complex and still being debugged.

**User's Expected Values from Direct Database Pull**:
- **Total AR**: $1,697,050.59 ✓ (matches)
- **Current**: $389,448.08
- **30-60 Days**: $312,764.25  
- **60-90 Days**: $173,548.60
- **90-120 Days**: $27,931.75
- **120+ Days**: Unknown (user provided conflicting info)
- **Over 90 Days Total**: $201,480.35 (this is 60-90 + 90-120, which seems wrong)

**What We're Currently Getting**:
- Buckets are calculating different amounts than expected
- Over 90 is showing ~$91K instead of expected $201K
- The bucket boundaries may be off

### CRITICAL DISCOVERIES:

1. **Invoice-Level Grouping Required**: 
   - Must group ARDetail by invoice first, then age the invoice balance
   - Individual ARDetail records include payments (negative amounts) that shouldn't be aged separately

2. **Over 90 Days Calculation Confusion**:
   - User says it should be $201,479 but this equals 60-90 + 90-120 buckets
   - This suggests their "over 90" might actually mean "over 60" or there's a labeling issue

3. **Customer AR Debug Findings** (Grede example):
   - Total AR: $241,297.06 ✓ (matches)
   - Our Over 90: $22,073.89 (too low)
   - Expected: $47,320.42 ($22,073.89 + $25,246.53)
   - Fixed by using >= 90 instead of > 90 in queries

4. **Bucket Structure Issues**:
   - Source system appears to have non-standard buckets
   - Current implementation uses: Current (0-29), 30-60, 60-90, 90-120, 120+
   - But the math still doesn't add up correctly

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