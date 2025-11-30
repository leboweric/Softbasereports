# Currie Cloud Platform

B2B SaaS platform for aggregating financial data from material handling dealerships.

## Overview

Currie Cloud connects to multiple ERP/DMS systems used by material handling dealers:
- **Softbase Evolution** (implemented)
- DIS/Cai (planned)
- e-Emphasys (planned)
- And more...

The platform provides:
- **For Dealers**: Access to financial reports and industry benchmarking
- **For Currie**: Aggregate analytics across all participating dealers
- **For ERP Vendors**: Standardized integration point

## Tech Stack

### Backend
- Python/Flask
- PostgreSQL (Railway)
- SQLAlchemy ORM
- Flask-JWT-Extended for authentication

### Frontend
- React 18
- Vite
- Tailwind CSS
- React Query

### Infrastructure
- Backend: Railway
- Frontend: Netlify
- Database: Railway PostgreSQL

## Project Structure

```
currie-cloud/
├── backend/
│   ├── src/
│   │   ├── adapters/      # ERP system adapters
│   │   ├── config/        # Configuration
│   │   ├── middleware/    # Request middleware
│   │   ├── models/        # Database models
│   │   ├── routes/        # API endpoints
│   │   ├── services/      # Business logic
│   │   └── utils/         # Utilities
│   ├── app.py             # Flask application
│   ├── requirements.txt   # Python dependencies
│   └── Procfile          # Railway deployment
│
└── frontend/
    ├── src/
    │   ├── components/    # React components
    │   ├── hooks/         # Custom hooks
    │   ├── lib/           # API utilities
    │   └── pages/         # Page components
    ├── package.json       # NPM dependencies
    └── vite.config.js     # Vite configuration
```

## Getting Started

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your values

# Run development server
python app.py
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

## Environment Variables

See `backend/.env.example` for required environment variables.

## API Documentation

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `GET /api/auth/me` - Get current user

### Dealers
- `GET /api/dealers` - List dealers
- `POST /api/dealers` - Create dealer (admin)
- `GET /api/dealers/:id` - Get dealer details
- `PUT /api/dealers/:id` - Update dealer

### Reports
- `GET /api/reports/periods` - List reporting periods
- `GET /api/reports/currie-model` - Generate Currie Financial Model
- `POST /api/reports/live-pull` - Pull fresh data from ERP

### Data Sync
- `GET /api/sync/jobs` - List sync jobs
- `POST /api/sync/trigger` - Trigger manual sync

## License

Proprietary - Currie Management Consultants
