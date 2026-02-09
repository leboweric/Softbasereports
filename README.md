# AI First Operations (AIOP)

A modern, multi-tenant dealership analytics platform at [aiop.one](https://aiop.one). Provides AI-powered business intelligence, financial reporting, P&L analysis, customer churn tracking, and data mart/ETL infrastructure for ERP tenants.

## Architecture

```
Frontend (React + Vite)          Backend (Flask)                  Data Layer
├── Authentication               ├── JWT Authentication           ├── PostgreSQL (Railway)
├── CEO Dashboard                ├── Multi-tenant RBAC            ├── Azure SQL (Tenant ERPs)
├── Department Reports           ├── ETL Pipeline                 ├── Data Marts
├── P&L / Financial              ├── GL Account Mapping           └── Scheduled Jobs
├── Customer Churn               ├── Report Generation
├── GL Account Mapping           ├── Billing (Stripe)
└── User/Tenant Management       └── Organization Management
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React, Vite, TailwindCSS, Shadcn/UI |
| Backend | Python Flask, SQLAlchemy, Flask-JWT |
| Database | PostgreSQL (app data), Azure SQL (tenant ERP) |
| Hosting | Netlify (frontend), Railway (backend) |
| Domain | aiop.one |
| ETL | Custom Python jobs, scheduled via APScheduler |

## Key Features

- **Multi-Tenant Architecture**: Automatic tenant discovery from ERP Organization table with data isolation
- **Dynamic P&L**: Revenue (4xxx), COGS (5xxx), Expenses (6xxx) using LIKE queries across all tenants
- **GL Account Mapping**: Auto-discovery of chart of accounts with admin UI for categorization
- **Customer Churn Analysis**: AI-powered insights on customer activity and risk assessment
- **CEO Dashboard**: Pre-aggregated metrics with ETL pipeline for fast loading
- **Department Reports**: Parts, Service, Rental, Accounting with employee performance
- **RBAC**: Dual-layer role-based access control (config + database)
- **Billing**: Stripe integration for SaaS subscriptions

## Current Tenants

| Tenant | Org ID | Schema | GL Format |
|--------|--------|--------|-----------|
| Bennett Material Handling | 4 | ben002 | 6-digit (4xxxxx) |
| Industrial Parts & Service | 7 | ind004 | 7-digit (4xxxxxx) |
| VITAL Worklife | 6 | N/A | Non-ERP tenant |

## ETL Schedule

- **Daily 2 AM CST**: Full ETL for all tenants (Sales, Cash Flow, Customer Activity, CEO Dashboard, Department Metrics)
- **Every 2 hours (6AM-8PM)**: Dashboard refresh for all tenants

## Quick Start

### Backend
```bash
cd reporting-backend
pip install -r requirements.txt
python src/main.py
```

### Frontend
```bash
cd reporting-frontend
npm install
npm run dev
```

## License

Proprietary software developed by AI First Operations.
