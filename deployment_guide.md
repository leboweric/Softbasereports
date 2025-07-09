# Forklift Reporting System - Deployment Guide

## Overview
This guide will help you deploy your custom reporting system to replace the $700/month reporting package. The system includes OpenAI integration for natural language queries and multi-tenant architecture.

## System Architecture
- **Frontend**: React with Next.js, Tailwind CSS, Shadcn UI components
- **Backend**: Flask with SQLAlchemy, JWT authentication, CORS enabled
- **Database**: SQLite (easily upgradeable to PostgreSQL)
- **AI Integration**: OpenAI API for natural language queries
- **Multi-tenancy**: Organization-based data isolation

## Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- OpenAI API key (for natural language queries)
- Softbase Evolution API credentials (when available)

## Local Development Setup

### Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd reporting-backend
   ```

2. Create and activate virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set environment variables:
   ```bash
   export OPENAI_API_KEY="your-openai-api-key"
   export FLASK_ENV="development"
   ```

5. Initialize database:
   ```bash
   python -c "from src.main import app; from src.models.user import db; app.app_context().push(); db.create_all()"
   ```

6. Start the backend server:
   ```bash
   python src/main.py
   ```
   Backend will run on http://localhost:5000

### Frontend Setup
1. Navigate to the frontend directory:
   ```bash
   cd reporting-frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```
   Frontend will run on http://localhost:5175

## Production Deployment

### Backend Deployment (Railway)
1. Create a new Railway project
2. Connect your GitHub repository
3. Set environment variables in Railway dashboard:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `FLASK_ENV`: production
   - `DATABASE_URL`: PostgreSQL connection string (Railway provides this)

4. Update database configuration for PostgreSQL:
   ```python
   # In src/main.py, replace SQLite with PostgreSQL
   app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
   ```

5. Deploy using Railway CLI or GitHub integration

### Frontend Deployment (Netlify)
1. Build the frontend:
   ```bash
   cd reporting-frontend
   npm run build
   ```

2. Deploy to Netlify:
   - Connect your GitHub repository to Netlify
   - Set build command: `npm run build`
   - Set publish directory: `dist`
   - Add environment variable: `VITE_API_URL` pointing to your Railway backend URL

## Configuration

### Softbase Evolution API Integration
When you receive the Softbase Evolution API details, update the following files:

1. **Backend Configuration** (`src/services/softbase_service.py`):
   ```python
   def __init__(self, organization):
       self.organization = organization
       self.api_key = organization.softbase_api_key
       self.endpoint = organization.softbase_endpoint or "YOUR_SOFTBASE_API_URL"
   ```

2. **Environment Variables**:
   ```bash
   export SOFTBASE_API_URL="your-softbase-api-url"
   export SOFTBASE_API_KEY="your-softbase-api-key"
   ```

### OpenAI Configuration
1. Get your OpenAI API key from https://platform.openai.com/
2. Set the environment variable:
   ```bash
   export OPENAI_API_KEY="sk-your-openai-api-key"
   ```

## Features Overview

### 1. User Authentication
- Multi-tenant user registration and login
- JWT-based authentication
- Organization-based data isolation

### 2. Dashboard
- Key business metrics (Sales, Inventory, Customers, Growth)
- Interactive charts and visualizations
- Real-time data updates

### 3. AI Query Assistant
- Natural language query processing
- Questions like: "which Linde Parts were we not able to fill last week?"
- Smart query suggestions organized by category
- Query history and validation

### 4. Reports
- Traditional report generation
- Multiple export formats (CSV, Excel, PDF)
- Customizable filters and parameters
- Scheduled report generation

### 5. Multi-Tenancy
- Organization-based data separation
- User management per organization
- Configurable API settings per organization

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user info

### Reports
- `GET /api/reports/list` - Get available reports
- `POST /api/reports/generate` - Generate report with parameters
- `GET /api/reports/export/{format}` - Export report in specified format

### AI Queries
- `POST /api/ai/query` - Process natural language query
- `GET /api/ai/suggestions` - Get query suggestions
- `GET /api/ai/history` - Get query history

### Organization Management
- `GET /api/organization/settings` - Get organization settings
- `PUT /api/organization/settings` - Update organization settings
- `GET /api/organization/users` - Get organization users

## Database Schema

### Users Table
- id, username, email, password_hash
- first_name, last_name, organization_id
- created_at, updated_at, is_active

### Organizations Table
- id, name, created_at, updated_at
- softbase_api_key, softbase_endpoint
- settings (JSON field for custom configurations)

### Report Templates Table
- id, name, description, organization_id
- query_template, parameters, created_at

## Security Considerations
- JWT tokens for authentication
- Password hashing with bcrypt
- CORS configuration for cross-origin requests
- Input validation and sanitization
- Organization-based data isolation

## Monitoring and Maintenance
- Log all API requests and errors
- Monitor database performance
- Regular backups of user data and configurations
- Update dependencies regularly for security patches

## Support and Troubleshooting

### Common Issues
1. **Database Connection Errors**: Check DATABASE_URL environment variable
2. **CORS Issues**: Ensure backend CORS is configured for frontend domain
3. **API Key Errors**: Verify OpenAI and Softbase API keys are set correctly
4. **Build Failures**: Check Node.js and Python versions match requirements

### Logs Location
- Backend logs: Check Railway deployment logs
- Frontend logs: Check Netlify deployment logs
- Application logs: Available in browser developer tools

## Cost Savings
- **Current Cost**: $700/month for reporting package
- **New System Cost**: 
  - Netlify: Free tier (or $19/month for pro features)
  - Railway: $5-20/month depending on usage
  - OpenAI API: Pay-per-use (estimated $10-50/month)
  - **Total**: ~$15-90/month vs $700/month
  - **Annual Savings**: $7,320 - $8,220

## Next Steps
1. Get Softbase Evolution API credentials and integrate
2. Add your OpenAI API key for natural language queries
3. Deploy to production environments
4. Train users on the new system
5. Monitor usage and optimize performance
6. Plan for additional features and customers

This system is designed to scale and can easily support multiple customers with the multi-tenant architecture already in place.

