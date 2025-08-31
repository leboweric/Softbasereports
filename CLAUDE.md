# Softbase Reports Project Context

## CRITICAL: Azure SQL Database Access
**⚠️ IMPORTANT: Azure SQL Database has IP firewall restrictions!**
- **You CANNOT connect to Azure SQL directly from local development**
- **The database ONLY accepts connections from Railway's IP addresses**
- **All database queries MUST go through the deployed Railway backend**
- **Use the web interface or deployed API endpoints to access data**
- **Never waste time trying to connect directly with pymssql/pyodbc locally**

## Overview
Comprehensive reporting system for Softbase Evolution connecting React frontend to Azure SQL Server via Flask backend.

## Tech Stack
- **Frontend**: React, Vite, Tailwind CSS, Recharts
- **Backend**: Flask, PyMSSQL, JWT auth
- **Database**: Azure SQL Server (schema: ben002) + PostgreSQL for custom data
- **Deployment**: Netlify (frontend), Railway (backend)

## Critical Development Rules

### API URL Usage
**NEVER hardcode URLs!** Always use:
```javascript
import { apiUrl } from '@/lib/api';
const response = await fetch(apiUrl('/api/endpoint'));
```

### JSX Syntax
- Escape `>` as `&gt;` in text content
- Verify data structures when copying between components

### Database Queries
- Avoid `SELECT *` - specify columns explicitly
- Wrap queries in try-catch blocks
- Use `SUM(Sell * Qty)` not `SUM(Sell)` for parts calculations
- Keep CTEs simple, do complex joins in final SELECT

### Git Workflow
1. Write and test changes locally
2. Verify queries return expected data
3. Test edge cases
4. Only push after validation

## Key Database Tables

### Core Tables
- **InvoiceReg**: Invoice records with revenue/cost data
- **WO**: Work orders (Type: S=Service, R=Rental, P=Parts)
- **Customer**: Customer info (join on Number field, not Id)
- **Equipment**: Equipment inventory
- **Parts**: Parts inventory (NOT NationalParts!)
- **WOParts**: Parts used on work orders
- **WOLabor/WOMisc**: Labor and misc charges

### Important Fields
- **SaleCode**: Department identifier (SVE=Service, PRT=Parts)
- **BillTo**: Customer number on invoices/work orders
- **CompletedDate/ClosedDate**: WO lifecycle tracking

## User Management & RBAC

### Permission System
- Super Admin: Full access
- Leadership: View all departments
- Department Managers: Full department access
- Department Staff: Limited department access
- Read Only: Dashboard only

### Key Files
- `backend/src/models/rbac.py` - RBAC models
- `backend/src/utils/auth_decorators.py` - Permission decorators
- `frontend/src/components/Layout.jsx` - Menu filtering

## PostgreSQL Integration
Used for custom data not in Softbase:
- Work order notes
- Minitrac equipment data (28K records)
- Connection: Railway PostgreSQL instance

## Recent Major Features

### Sales Commission System
- Uses actual cost data from InvoiceReg
- Equipment: 15% of gross profit
- Rentals: 8% of revenue (unlimited duration)

### AR Aging Report
- Group by `CustomerNo, InvoiceNo` only (not Due date!)
- Invoice-level aging required
- Debug endpoints available

### Work Order Notes
- PostgreSQL table for custom notes
- Auto-save with 1-second debounce
- Included in CSV exports

### Minitrac Integration
- Replaced $600/month subscription
- Self-hosted in PostgreSQL
- Full search and export capabilities

### Rental Availability Report
**Key Learning: Never assume data values - always verify actual database content**

#### Solution Summary
The report determines rental status by checking for OPEN rental work orders in Softbase, matching the "WIP > Open Rental Orders" section in the Equipment Setup screen.

#### Technical Details
- **Primary Filter**: `e.InventoryDept = 60` - Units owned by Rental Department
- **Customer Owned Filter**: `AND (e.Customer = 0 OR e.Customer IS NULL)` - Excludes customer-owned equipment
- **On Rent Detection**: Check for open rental work orders:
  - Join with `WORental` and `WO` tables
  - `WHERE wo.Type = 'R' AND wo.ClosedDate IS NULL`
  - **CRITICAL**: Exclude quotes with `AND wo.WONo NOT LIKE '9%'`
- **Available Status**: Units with no open rental work orders (excluding quotes)

#### Quotes vs Work Orders
**IMPORTANT: Quotes are NOT rental orders!**
- **Quotes**: WO numbers starting with '9' (e.g., 91600003)
- **Work Orders**: WO numbers starting with '13' or other numbers (e.g., 130000713, 16001378)
- **Why this matters**: Quotes can appear in WORental table with Type='R' but are NOT actual rentals
- **Softbase Logic**: "Open Rental Orders" section only shows actual work orders, not quotes

#### Column Explorer Tool
Added to Table Discovery to analyze actual database values:
- **Endpoint**: `/api/database/column-values` in `table_discovery.py`
- **UI**: Column Explorer tab in TableDiscovery.jsx
- **Purpose**: Explore distinct values and distributions without assumptions
- **Key Insight**: Helped discover Department 60's clean data state

#### Common Pitfalls Avoided
1. Don't filter by assumed RentalStatus values ('Sold', 'Disposed', etc.) that don't exist
2. Don't use IsDeleted field - not relevant for Department 60
3. Don't build complex exclusion lists - department ownership is the key filter
4. Always verify actual data values before creating filters

## Common Issues & Solutions

### Import Paths
- Production needs `src.` prefix: `from src.services.module`

### Authentication
- Use `@jwt_required()` from flask_jwt_extended

### Performance
- Dashboard uses parallel queries
- CTEs for aggregation, joins in final SELECT
- Indexes on commonly queried columns

## Deployment
- **Frontend**: https://softbasereports.netlify.app
- **Backend**: https://softbasereports-production.up.railway.app
- Auto-deploys on git push

## File Structure
```
/reporting-frontend
  /src/components
    /departments (department reports)
    /ui (reusable components)
  /src/lib (API utilities)

/reporting-backend
  /src/routes (API endpoints)
  /src/services (database services)
  /src/models (data models)
```

## Quick Reference

### Work Order Types
- S = Service
- R = Rental  
- P = Parts
- I = Internal

### Commission Structure
- New Equipment: 15% of gross profit ($75 min)
- Rentals: 8% of revenue (no duration cap)

### Rental Customer Lookup
```
Equipment → WORental → WO (Type='R') → Customer
```

### Environment Variables
Backend requires:
- DATABASE_URL
- JWT_SECRET_KEY
- FLASK_ENV
- PORT

## Database Schema
**📚 COMPLETE SCHEMA DOCUMENTATION: See [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)**
- Detailed table structures, column types, and relationships
- Common join patterns and gotchas
- Data quality issues and workarounds
- For live exploration: Use Database Explorer in app menu