# Reporting System Architecture

## Overview
A multi-tenant reporting system to replace a $700/month reporting package for forklift dealerships using Softbase Evolution DMS.

## Technology Stack

### Frontend
- **Framework**: Next.js 14 with App Router
- **Styling**: Tailwind CSS
- **UI Components**: Shadcn/ui
- **Charts**: Recharts
- **Icons**: Lucide React
- **Deployment**: Netlify

### Backend
- **Framework**: Flask (Python)
- **Database**: PostgreSQL (for user management only)
- **Authentication**: JWT tokens
- **API Integration**: Direct calls to Softbase Evolution API
- **Deployment**: Railway

### Data Flow
1. User authenticates via frontend
2. Frontend sends requests to Flask backend
3. Backend validates JWT and organization access
4. Backend calls Softbase Evolution API with organization context
5. Backend processes and returns data to frontend
6. Frontend displays data in tables/charts

## Multi-Tenancy Strategy
- Each user belongs to an organization (organization_id)
- All API calls include organization context
- Data isolation enforced at API level
- Single URL for all customers with organization-based routing

## Key Features
- Real-time data from Softbase Evolution
- Interactive dashboards with filtering
- Export to PDF, CSV, Excel
- Responsive design
- Role-based access control
- Report customization and scheduling

## Security Considerations
- JWT-based authentication
- Organization-level data isolation
- Input validation and sanitization
- HTTPS enforcement
- Rate limiting on API endpoints

