# CardVault

A comprehensive web application for managing collectible card inventory, tracking valuations, and facilitating marketplace trading with AI-powered insights.

## Project Overview

CardVault enables collectors to:
- Scan cards (single or multi-card images) using AI-powered detection and classification
- Manage inventory with automatic price tracking
- Trade cards via a marketplace with two-way matching
- Receive AI agent alerts and suggestions for portfolio optimization

## Documentation

Complete technical documentation and specifications are available in the `docs/` directory:

- **[System Architecture](./docs/architecture.md)** - High-level architecture, components, and technology stack
- **[MVP Features](./docs/mvp-features.md)** - Prioritized feature list with acceptance criteria
- **[Data Schema](./docs/data-schema.md)** - Complete database schema and relationships
- **[API Specification](./docs/api-spec.md)** - REST API endpoints with examples
- **[ML Pipeline Design](./docs/ml-pipeline.md)** - Machine learning models and pipeline
- **[Marketplace Algorithm](./docs/marketplace-algorithm.md)** - Matching and trade suggestion algorithms
- **[Notification & Agent Engine](./docs/notification-agent.md)** - Alert rules and AI agent design
- **[Security Checklist](./docs/security-checklist.md)** - Security requirements and GDPR/CCPA compliance
- **[12-Week Roadmap](./docs/roadmap.md)** - Development roadmap broken into sprints
- **[Demo Dataset & Test Cases](./docs/demo-test-cases.md)** - Test scenarios and demo data

## Quick Start (1-Day MVP)

**For the fastest setup, see [QUICK_START.md](./QUICK_START.md)**

### Prerequisites

- Docker & Docker Compose (recommended) **OR**
- Node.js 18+ + Python 3.11+ (for manual setup)

### Fast Setup (Docker - 5 minutes)

```bash
# 1. Clone and start all services
docker-compose up -d

# 2. Access the application
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### Manual Setup (Without Docker)

See [QUICK_START.md](./QUICK_START.md) for detailed instructions.

**Quick version:**
```bash
# Backend
cd backend && pip install -r requirements.txt && python main.py

# ML Service (separate terminal)
cd ml-service && pip install -r requirements.txt && python app.py

# Frontend (separate terminal)
cd frontend && npm install && npm start
```

## Technology Stack

### Frontend
- React 18+ with TypeScript
- Tailwind CSS
- React Router
- Zustand (state management)

### Backend
- Node.js (Express) or Python (FastAPI)
- PostgreSQL
- Redis (cache & queue)
- JWT authentication

### ML/AI
- PyTorch / TensorFlow
- YOLOv8 (card detection)
- EfficientNet-B3 (card classification)
- ONNX Runtime (inference optimization)

### Infrastructure
- Docker & Kubernetes
- AWS/GCP
- S3 (image storage)
- CloudFront/CDN

## Project Structure

```
cardvault/
├── docs/              # Documentation
├── frontend/          # React frontend application
├── backend/           # API server
├── ml-service/        # ML inference service
├── database/          # Database migrations and schemas
└── tests/             # Test suites
```

## Development Roadmap

See [12-Week Roadmap](./docs/roadmap.md) for detailed sprint breakdown.

**Phase 1** (Weeks 1-4): Foundation & Authentication  
**Phase 2** (Weeks 5-8): ML Pipeline & Scanning  
**Phase 3** (Weeks 9-12): Price Feed & AI Agent  
**Phase 4** (Weeks 13-16): Marketplace & Trading  
**Phase 5** (Weeks 17-20): Polish & Testing  
**Phase 6** (Weeks 21-24): Pre-Launch & Beta

## Contributing

1. Create a feature branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `npm test` or `pytest`
4. Submit a pull request

## License

Proprietary - All rights reserved

## Contact

- **Product Team**: product@cardvault.app
- **Security**: security@cardvault.app
- **Support**: support@cardvault.app
