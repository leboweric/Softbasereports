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
- **NationalParts**: Parts inventory
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