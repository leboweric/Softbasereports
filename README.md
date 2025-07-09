# Forklift Reporting System

A modern, multi-tenant reporting system designed to replace expensive reporting packages with OpenAI-powered natural language queries and comprehensive business intelligence features.

## 🚀 Features

### Core Functionality
- **Multi-Tenant Architecture**: Support multiple organizations with data isolation
- **User Authentication**: Secure JWT-based authentication system
- **Professional Dashboard**: Real-time business metrics and visualizations
- **🆕 Natural Language Report Creation**: Create custom reports using plain English descriptions
- **Advanced Reporting**: Generate reports with multiple export formats (CSV, Excel, PDF)
- **AI-Powered Queries**: Ask questions in natural language like "which Linde Parts were we not able to fill last week?"

### Technical Highlights
- **Modern Tech Stack**: React + Flask + SQLAlchemy
- **Responsive Design**: Works perfectly on desktop and mobile
- **API Integration Ready**: Built for Softbase Evolution API integration
- **Scalable Architecture**: Designed to support multiple customers
- **Professional UI**: Clean, modern interface with Tailwind CSS and Shadcn components

## 🏗️ Architecture

```
Frontend (React/Next.js)     Backend (Flask)           External APIs
├── Authentication          ├── JWT Authentication    ├── Softbase Evolution API
├── Dashboard               ├── Multi-tenant Models   ├── OpenAI API
├── AI Query Interface      ├── Report Generation     └── Database (SQLite/PostgreSQL)
├── Reports Management      ├── Export Services
└── User Management         └── Organization Management
```

## 📁 Project Structure

```
reporting-system/
├── reporting-frontend/          # React frontend application
│   ├── src/
│   │   ├── components/         # Reusable UI components
│   │   │   ├── Layout.jsx      # Main layout with navigation
│   │   │   ├── Login.jsx       # Authentication component
│   │   │   ├── Dashboard.jsx   # Business metrics dashboard
│   │   │   ├── AIQuery.jsx     # Natural language query interface
│   │   │   └── Reports.jsx     # Report generation and management
│   │   ├── App.jsx            # Main application component
│   │   └── main.jsx           # Application entry point
│   ├── package.json
│   └── vite.config.js         # Vite configuration with API proxy
│
├── reporting-backend/           # Flask backend application
│   ├── src/
│   │   ├── models/            # Database models
│   │   │   └── user.py        # User, Organization, ReportTemplate models
│   │   ├── routes/            # API endpoints
│   │   │   ├── auth.py        # Authentication routes
│   │   │   ├── reports.py     # Report generation routes
│   │   │   ├── ai_query.py    # AI query processing routes
│   │   │   └── organization.py # Organization management routes
│   │   ├── services/          # Business logic services
│   │   │   ├── softbase_service.py    # Softbase API integration
│   │   │   ├── openai_service.py      # OpenAI integration
│   │   │   └── report_generator.py    # Report generation logic
│   │   ├── middleware/        # Custom middleware
│   │   │   └── tenant_middleware.py   # Multi-tenant data isolation
│   │   └── main.py           # Flask application entry point
│   ├── requirements.txt
│   └── venv/                 # Python virtual environment
│
├── deployment_guide.md        # Comprehensive deployment instructions
└── README.md                 # This file
```

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm
- Python 3.11+
- OpenAI API key (optional, for AI queries)

### 1. Backend Setup
```bash
cd reporting-backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Initialize database
python -c "from src.main import app; from src.models.user import db; app.app_context().push(); db.create_all()"

# Start backend server
python src/main.py
```
Backend runs on http://localhost:5000

### 2. Frontend Setup
```bash
cd reporting-frontend
npm install
npm run dev
```
Frontend runs on http://localhost:5175

### 3. Access the Application
1. Open http://localhost:5175 in your browser
2. Click "Register" to create a new account
3. Fill in your organization details
4. Start exploring the dashboard and features!

## 🔧 Configuration

### Environment Variables
```bash
# Backend (.env or environment)
OPENAI_API_KEY=your-openai-api-key
FLASK_ENV=development
DATABASE_URL=sqlite:///app.db  # or PostgreSQL URL for production

# Frontend (.env)
VITE_API_URL=http://localhost:5000  # Backend URL
```

### Softbase Evolution API Integration
When you receive your Softbase Evolution API credentials:

1. Update `src/services/softbase_service.py` with your API endpoint
2. Add API credentials to your organization settings
3. The system will automatically use real data instead of mock data

## 🤖 AI Query Examples

The system supports natural language queries like:
- "Which Linde parts were we not able to fill last week?"
- "Give me the serial numbers of all forklifts that Polaris rents from us"
- "Show me sales performance for this month"
- "What's our inventory status for Toyota equipment?"
- "Which customers haven't ordered in the last 30 days?"

## 📊 Dashboard Metrics

The dashboard displays key business metrics:
- **Total Sales**: Revenue with month-over-month comparison
- **Inventory**: Available units and stock levels
- **Active Customers**: Customer count with new acquisitions
- **Growth Rate**: Year-over-year business growth
- **Monthly Sales Chart**: 12-month performance visualization

## 🔐 Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: Bcrypt encryption for user passwords
- **Multi-Tenant Isolation**: Organization-based data separation
- **CORS Protection**: Configured for secure cross-origin requests
- **Input Validation**: Comprehensive data validation and sanitization

## 🚀 Deployment

### Production Deployment Options

#### Option 1: Netlify + Railway (Recommended)
- **Frontend**: Deploy to Netlify (free tier available)
- **Backend**: Deploy to Railway ($5-20/month)
- **Database**: PostgreSQL on Railway
- **Total Cost**: ~$5-20/month vs $700/month current cost

#### Option 2: Vercel + Railway
- **Frontend**: Deploy to Vercel
- **Backend**: Deploy to Railway
- **Database**: PostgreSQL on Railway

#### Option 3: Self-Hosted
- Deploy both frontend and backend to your own servers
- Use PostgreSQL or MySQL for production database

See `deployment_guide.md` for detailed deployment instructions.

## 💰 Cost Savings

| Component | Current System | New System | Savings |
|-----------|---------------|------------|---------|
| Reporting Package | $700/month | $0 | $700/month |
| Hosting (Netlify + Railway) | $0 | $5-20/month | -$5-20/month |
| OpenAI API | $0 | $10-50/month | -$10-50/month |
| **Total Monthly** | **$700** | **$15-70** | **$630-685** |
| **Annual Savings** | | | **$7,560-$8,220** |

## 🔄 Multi-Customer Ready

The system is designed to support multiple customers:
- **Multi-tenant architecture** with organization-based data isolation
- **Configurable API settings** per organization
- **Scalable infrastructure** ready for growth
- **White-label potential** for reselling to other dealerships

## 🛠️ Development

### Adding New Features
1. **Backend**: Add new routes in `src/routes/`
2. **Frontend**: Add new components in `src/components/`
3. **Database**: Update models in `src/models/user.py`
4. **Services**: Add business logic in `src/services/`

### Testing
- Backend: Use Flask's built-in testing framework
- Frontend: Use Vitest for component testing
- Integration: Test API endpoints with Postman or curl

## 📞 Support

For questions or issues:
1. Check the `deployment_guide.md` for detailed setup instructions
2. Review the troubleshooting section in the deployment guide
3. Check browser developer tools for frontend issues
4. Review backend logs for API issues

## 🎯 Next Steps

1. **Integrate Softbase Evolution API** when credentials are available
2. **Add OpenAI API key** for natural language queries
3. **Deploy to production** using Netlify + Railway
4. **Train users** on the new system
5. **Monitor performance** and optimize as needed
6. **Plan additional features** based on user feedback

## 📄 License

This project is proprietary software developed for forklift dealership reporting needs.

---

**Built with ❤️ to save $700/month and provide better reporting capabilities!**

