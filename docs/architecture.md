# CardVault System Architecture

## High-Level Overview

CardVault is a microservices-based web application designed for collectible card inventory management, valuation, and marketplace trading. The system follows a serverless-first approach with containerized services for ML inference.

## Architecture Diagram (Textual)

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  React PWA (Mobile-First) + Tailwind CSS                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │   Scan   │ │Inventory │ │Marketplace│ │  Agent   │          │
│  │   UI     │ │   View   │ │    UI     │ │ Dashboard│          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway (API Gateway)                   │
│  Auth: JWT + OAuth2 | Rate Limiting | Request Routing           │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   Auth      │  │   Core API      │  │   ML Service    │
│  Service    │  │   (REST/GraphQL)│  │   (Container)   │
│             │  │                 │  │                 │
│ • JWT       │  │ • Inventory     │  │ • Card Detection│
│ • OAuth     │  │ • Cards         │  │ • Classification│
│ • RBAC      │  │ • Valuations    │  │ • Condition     │
│             │  │ • Listings      │  │ • OCR           │
│             │  │ • Trades        │  │                 │
└──────────────┘  └─────────────────┘  └─────────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Background Services                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │AI Agent      │  │ Price Feed   │  │ Notification │          │
│  │Engine        │  │ Service      │  │ Service      │          │
│  │              │  │              │  │              │          │
│  │• Valuation   │  │• Scrapers    │  │• Email       │          │
│  │  Analysis    │  │• API Pollers │  │• Push        │          │
│  │• Alert Rules │  │• Aggregators │  │• In-app      │          │
│  │• Suggestions │  │• FMV Calc    │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Layer                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ PostgreSQL   │  │   Redis      │  │   S3/Blob    │          │
│  │ (Primary DB) │  │ (Cache/Queue)│  │   (Images)   │          │
│  │              │  │              │  │              │          │
│  │• Encrypted   │  │• Sessions    │  │• Card Images │          │
│  │  User Data   │  │• Job Queue   │  │• Thumbnails  │          │
│  │• Inventory   │  │• Rate Limits │  │• ML Assets   │          │
│  │• Marketplace │  │              │  │              │          │
│  │• Trades      │  │              │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    External Integrations                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   Stripe     │  │   Price APIs │  │   Escrow     │          │
│  │   Payments   │  │              │  │   Services   │          │
│  │              │  │• TCGPlayer   │  │              │          │
│  │              │  │• eBay Sales  │  │              │          │
│  │              │  │• CardMarket  │  │              │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

## Component Responsibilities

### Frontend Layer
- **React PWA**: Single Page Application with service worker for offline capability
- **State Management**: Redux Toolkit or Zustand for global state
- **Routing**: React Router v6
- **UI Framework**: Tailwind CSS with shadcn/ui or Headless UI components
- **Image Upload**: React Dropzone or similar with compression
- **Real-time Updates**: WebSocket client for notifications

### API Gateway
- **Authentication**: JWT token validation, OAuth2 flows
- **Rate Limiting**: Per-user and per-IP limits
- **Request Routing**: Route to appropriate microservice
- **CORS**: Configured for PWA origins
- **SSL/TLS**: All traffic encrypted

### Core Services

#### Auth Service
- User registration/login (email, OAuth)
- JWT token generation/refresh
- Role-based access control (User, Admin, Moderator)
- Session management

#### Core API Service
- Inventory CRUD operations
- Card metadata management
- Marketplace operations (listings, searches, offers)
- Trade workflow management
- User profile & preferences

#### ML Service (Containerized)
- **Multi-card detection**: YOLOv8 or similar object detection
- **Card classification**: Fine-tuned Vision Transformer (ViT) or EfficientNet
- **Condition grading**: Regression model (1-10 scale) or classification
- **OCR**: Tesseract or cloud OCR (Google Cloud Vision)
- **Latency optimization**: Model quantization, TensorRT/ONNX Runtime

### Background Services

#### AI Agent Engine
- **Valuation Monitoring**: Poll price feeds, compare against user inventory
- **Alert Generation**: Price threshold breaches, portfolio value changes
- **Strategy Suggestions**: ML-based recommendations (hold/sell/trade)
- **Portfolio Analytics**: Performance metrics, gains/losses, diversification
- **Rules Engine**: Configurable alert rules per user

#### Price Feed Service
- **Data Ingestion**: Scheduled scrapers for TCGPlayer, eBay, CardMarket
- **API Integration**: TCGPlayer API, eBay API, etc.
- **Data Normalization**: Standardize card identifiers (set codes, names)
- **Valuation Calculation**: Fair Market Value (FMV) = weighted median of recent sales
- **Confidence Intervals**: Statistical model based on sample size and variance

#### Notification Service
- **Multi-channel**: Email (SendGrid/Resend), Push (Firebase Cloud Messaging), In-app
- **Queue Processing**: Redis/Bull for reliable delivery
- **User Preferences**: Opt-in/opt-out per channel and notification type
- **Templates**: Jinja2 or similar for email templates

### Data Layer

#### PostgreSQL (Primary Database)
- **Encryption at Rest**: AWS KMS or similar for sensitive fields
- **Indexing**: Optimized for marketplace searches, user queries
- **Partitioning**: By user_id for inventory tables (scale)
- **Backups**: Daily automated backups, point-in-time recovery

#### Redis (Cache & Queue)
- **Session Storage**: JWT refresh tokens, active sessions
- **Caching**: Frequently accessed card metadata, price data (TTL: 5-15 min)
- **Job Queue**: Bull or similar for async tasks (image processing, notifications)
- **Rate Limiting**: Token bucket algorithm

#### Object Storage (S3/Blob)
- **Card Images**: Original uploads, processed crops
- **Thumbnails**: Multiple sizes (128px, 256px, 512px)
- **ML Model Artifacts**: Trained models, weights
- **CDN Integration**: CloudFront or Cloudflare for fast delivery

## Data Flow Examples

### Multi-Card Scan Flow
1. User uploads image via Frontend
2. Frontend compresses image, uploads to S3 (signed URL)
3. API Gateway routes to Core API
4. Core API creates scan job, enqueues to ML Service queue
5. ML Service:
   - Detects card bounding boxes (YOLOv8)
   - Crops each card
   - Classifies each (set + name)
   - Optionally runs condition grader
   - Returns results to Core API
6. Core API stores card metadata, creates inventory entries
7. Frontend polls for completion or receives WebSocket update

### Price Alert Flow
1. Price Feed Service updates card valuations (hourly/daily)
2. AI Agent Engine compares new prices to user inventory
3. If threshold breached (user configurable):
   - AI Agent Engine creates alert
   - Enqueues notification job
4. Notification Service sends email/push/in-app notification
5. User views alert in dashboard

## Technology Stack Recommendations

### Frontend
- **Framework**: React 18+ with TypeScript
- **Styling**: Tailwind CSS 3+
- **State**: Zustand or Redux Toolkit
- **Forms**: React Hook Form + Zod validation
- **HTTP Client**: Axios or fetch with interceptors
- **PWA**: Workbox for service worker

### Backend
- **API Framework**: Node.js (Express/Fastify) or Python (FastAPI)
- **GraphQL**: Apollo Server (optional, if GraphQL chosen)
- **ORM**: Prisma (Node.js) or SQLAlchemy (Python)
- **Queue**: Bull (Node.js) or Celery (Python)

### ML/Data
- **Framework**: PyTorch or TensorFlow
- **Inference**: ONNX Runtime or TensorRT (production optimization)
- **Vision**: YOLOv8 (detection), ViT-B/16 (classification)
- **OCR**: Tesseract (local) or Google Cloud Vision (cloud)

### Infrastructure
- **Hosting**: AWS, GCP, or Azure
- **Containers**: Docker + Kubernetes (EKS/GKE) or AWS ECS/Fargate
- **Serverless**: AWS Lambda (background jobs) or Cloud Functions
- **CDN**: CloudFront, Cloudflare
- **Monitoring**: Datadog, New Relic, or Prometheus + Grafana
- **Logging**: ELK Stack or CloudWatch

## Scalability Considerations

- **Horizontal Scaling**: Stateless API services, auto-scaling containers
- **Database Sharding**: Partition by user_id (eventual consistency acceptable)
- **Caching Strategy**: Multi-layer (Redis → DB) for hot data
- **Image Processing**: Async queue prevents blocking user requests
- **ML Inference**: GPU-enabled containers for low latency, batch processing for cost efficiency

## Tradeoffs

| Decision | Pros | Cons |
|----------|------|------|
| Microservices | Independent scaling, tech diversity | Network latency, deployment complexity |
| Serverless Functions | Cost-effective for sporadic workloads | Cold starts (unacceptable for ML) |
| Containerized ML | Low latency, predictable performance | Higher infrastructure cost |
| PostgreSQL | ACID guarantees, mature ecosystem | Requires sharding at large scale |
| Redis Cache | Fast reads, reduces DB load | Additional infrastructure, cache invalidation complexity |
