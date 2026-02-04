# CardVault

A comprehensive web application for managing collectible card inventory, tracking valuations, and facilitating marketplace trading with AI-powered insights.

## Overview

CardVault is a modern, full-stack application built for collectors and trading enthusiasts. It enables users to scan, catalog, value, and trade collectible cards using cutting-edge AI technology. The platform leverages machine learning for card detection and classification while providing a marketplace for connecting buyers and sellers.

### Key Features
- **AI-Powered Card Scanning**: Automatically detect and classify cards from single or multi-card images
- **Inventory Management**: Track your card collection with condition ratings and valuations
- **Smart Marketplace**: Find and trade cards with two-way matching algorithms
- **Price Tracking**: Automatic price updates from market data
- **AI Agent Insights**: Get AI-powered suggestions for portfolio optimization
- **Notifications**: Stay updated with real-time alerts on market opportunities

## Architecture

CardVault follows a **microservices architecture** with three main components:

```
┌─────────────────────────────────────────┐
│         Frontend (React + TypeScript)   │
│    - Scan, Inventory, Marketplace       │
│    - Mobile-first PWA with Tailwind     │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│     Backend (FastAPI + SQLAlchemy)      │
│    - Authentication & User Management   │
│    - Inventory & Card Management        │
│    - Marketplace & Trading Logic        │
│    - Price & Valuation Tracking         │
└────────────────┬────────────────────────┘
                 │
     ┌───────────┴───────────┐
     │                       │
┌────▼──────────┐  ┌────────▼────────┐
│  ML Service   │  │  Database       │
│  - Detection  │  │  - Cards        │
│  - Classify   │  │  - Users        │
│  - OCR        │  │  - Listings     │
└───────────────┘  │  - Trades       │
                   └─────────────────┘
```

### Tech Stack

**Frontend:**
- React 18 with TypeScript
- React Router for navigation
- Tailwind CSS for styling
- Lucide React for icons
- PWA-ready for mobile support

**Backend:**
- FastAPI (modern, fast Python web framework)
- SQLAlchemy ORM
- Pydantic for data validation
- JWT authentication with OAuth2
- bcrypt for password hashing

**ML Service:**
- Python-based service
- Google Cloud Vision API for card detection
- Gemini AI for card classification
- Image processing with Pillow

**Deployment:**
- Docker & Docker Compose for containerization
- SQLite for MVP (easily upgradeable to PostgreSQL)

## Project Structure

```
├── backend/                 # FastAPI backend service
│   ├── main.py             # Application entry point
│   ├── requirements.txt     # Python dependencies
│   ├── Dockerfile          # Container configuration
│   └── uploads/            # User-uploaded images
│
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── pages/         # Page components (Login, Scan, Inventory, etc.)
│   │   ├── components/    # Reusable React components
│   │   └── index.tsx      # App entry point
│   ├── package.json       # Node dependencies
│   ├── tailwind.config.js # Tailwind CSS configuration
│   └── Dockerfile         # Container configuration
│
├── ml-service/            # Python ML inference service
│   ├── app.py            # ML service entry point
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile        # Container configuration
│
├── docs/                  # Project documentation
│   ├── api-spec.md           # API endpoint specifications
│   ├── architecture.md        # Detailed architecture docs
│   ├── data-schema.md         # Database schema
│   ├── mvp-features.md        # Feature requirements
│   ├── ml-pipeline.md         # ML pipeline details
│   ├── marketplace-algorithm.md # Trading algorithm docs
│   └── security-checklist.md  # Security considerations
│
├── docker-compose.yml     # Multi-container orchestration
├── QUICK_START.md        # Quick setup guide
└── README.md             # This file
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (optional, for local frontend development)
- Python 3.11+ (optional, for local backend development)

### Fastest Setup (Docker - Recommended)

1. **Clone the repository and start services:**
```bash
docker-compose up -d
```

2. **Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- ML Service: http://localhost:8001

3. **Test the API:**
```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!","username":"testuser"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test123!"}'
```

### Manual Setup (Local Development)

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend will be available at: http://localhost:8000

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

Frontend will be available at: http://localhost:3000

#### ML Service Setup
```bash
cd ml-service
pip install -r requirements.txt
python app.py
```

ML Service will be available at: http://localhost:8001

### Environment Variables

Create a `.env` file in the project root for environment-specific settings:

```
# Database
DATABASE_URL=sqlite:///./cardvault.db

# JWT & Security
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# ML Service
GEMINI_API_KEY=your-gemini-api-key
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Service URLs
ML_SERVICE_URL=http://localhost:8001
```

## API Documentation

The backend provides interactive API documentation at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main API Endpoints

**Authentication:**
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Refresh JWT token

**Cards & Inventory:**
- `GET /api/v1/inventory` - Get user's inventory
- `POST /api/v1/cards/scan` - Scan and upload cards
- `GET /api/v1/cards/{id}` - Get card details
- `PUT /api/v1/cards/{id}` - Update card information
- `DELETE /api/v1/cards/{id}` - Remove card from inventory

**Marketplace:**
- `GET /api/v1/marketplace` - Browse available listings
- `POST /api/v1/listings` - Create a listing
- `GET /api/v1/listings/{id}` - Get listing details
- `POST /api/v1/trades` - Initiate a trade

**Valuations & Price:**
- `GET /api/v1/valuations` - Get portfolio valuation
- `GET /api/v1/prices/{card_id}` - Get current card price

For detailed API specifications, see [docs/api-spec.md](docs/api-spec.md)

## Features

### Must-Have (MVP)
- ✅ User authentication with JWT
- ✅ Single-card image scanning and classification
- ✅ Multi-card batch scanning
- ✅ Card inventory management
- ✅ Marketplace listing and trading
- ✅ Price tracking and valuations
- ✅ User notifications

### Should-Have (Near-term)
- Analytics dashboard
- Advanced search and filtering
- Watchlist functionality
- Trade history
- Portfolio performance metrics
- Integration with grading services

### Nice-to-Have (Future)
- Mobile native apps
- Social features (teams, clubs)
- Advanced ML (condition detection)
- Real-time price alerts
- Integration with card pricing APIs

See [docs/mvp-features.md](docs/mvp-features.md) for complete feature specifications.

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test
```

### Building for Production

```bash
# Build Docker images
docker-compose build

# Run production containers
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### Code Structure

**Backend:**
- `routers/` - API endpoint handlers
- `models/` - SQLAlchemy database models
- `schemas/` - Pydantic validation schemas
- `services/` - Business logic
- `utils/` - Helper functions

**Frontend:**
- `pages/` - Full-page components
- `components/` - Reusable UI components
- `hooks/` - Custom React hooks
- `services/` - API client functions

## Security

- All user passwords are hashed with bcrypt
- JWT tokens for stateless authentication
- HTTPS-ready (configure in production)
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy ORM
- CORS configured for frontend domain

See [docs/security-checklist.md](docs/security-checklist.md) for comprehensive security guidelines.

## Performance

- Single card scan latency: <5 seconds
- API response time: <500ms (p95)
- Classification accuracy: ≥85%
- Supports concurrent users via async FastAPI

## Documentation

Comprehensive documentation is available in the `docs/` folder:

- [API Specification](docs/api-spec.md) - Complete API reference
- [Architecture](docs/architecture.md) - System design details
- [Data Schema](docs/data-schema.md) - Database structure
- [ML Pipeline](docs/ml-pipeline.md) - Card detection & classification process
- [Marketplace Algorithm](docs/marketplace-algorithm.md) - Trading logic
- [Features](docs/mvp-features.md) - Feature requirements & acceptance criteria
- [Notifications](docs/notification-agent.md) - Alert system design
- [Security](docs/security-checklist.md) - Security best practices
- [Roadmap](docs/roadmap.md) - Future development plans

## Troubleshooting

### Docker issues
```bash
# View logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs ml-service

# Restart services
docker-compose restart

# Full reset
docker-compose down -v
docker-compose up -d
```

### Port conflicts
If ports 3000, 8000, or 8001 are in use, modify `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # Change 3000 to your preferred port
```

### ML Service errors
Ensure Google Cloud credentials are properly configured:
```bash
export GEMINI_API_KEY=your-key
export GOOGLE_CLOUD_PROJECT=your-project
docker-compose up -d ml-service
```

