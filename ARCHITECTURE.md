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

## Current Issues & Limitations

### Database Access Constraints
- **Azure SQL Firewall**: No local development database access
- **Production Dependency**: All development requires deployed backend
- **Query Performance**: Large table scans can be slow without proper indexing

### Technical Debt
- **Mixed TypeScript/JavaScript**: Inconsistent typing across components
- **API Error Handling**: Inconsistent error response formats
- **Cache Strategy**: Limited caching implementation for expensive queries
- **Test Coverage**: Minimal automated testing infrastructure

### Performance Bottlenecks
- **Dashboard Loading**: Multiple sequential API calls for dashboard data
- **Large Dataset Exports**: Memory constraints on large CSV/Excel exports
- **Real-time Updates**: No WebSocket implementation for live data updates

### Security Considerations
- **Database Credentials**: Some credentials in configuration files (should be environment-only)
- **API Rate Limiting**: No rate limiting on expensive endpoints
- **Audit Logging**: Limited user activity auditing

### Scalability Limitations
- **Single Backend Instance**: No horizontal scaling architecture
- **Database Connection Pool**: Limited connection pooling for high concurrency
- **File Storage**: No cloud file storage for report exports and attachments

---

## Recommended Improvements

### Near-term (Next 3 months)
1. **Implement comprehensive TypeScript** across all frontend components
2. **Add API rate limiting** and request throttling
3. **Implement Redis caching** for expensive database queries
4. **Add automated testing** with Jest and Cypress
5. **Improve error handling** with consistent error response formats

### Medium-term (3-6 months)
1. **WebSocket integration** for real-time dashboard updates
2. **Horizontal scaling** architecture with load balancing
3. **Cloud file storage** integration (AWS S3 or similar)
4. **Advanced audit logging** and user activity tracking
5. **Performance monitoring** with APM tools

### Long-term (6+ months)
1. **Microservices architecture** for better scalability
2. **Data warehouse implementation** for historical analytics
3. **Advanced AI features** with custom model training
4. **Mobile application** for field service and rental management
5. **API versioning** and public API development