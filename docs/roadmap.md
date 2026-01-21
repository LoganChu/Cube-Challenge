# CardVault 12-Week Development Roadmap

## Overview

This roadmap outlines a 12-week sprint plan to deliver the MVP (Minimum Viable Product) for CardVault. Each sprint is 2 weeks long, focusing on specific features and milestones.

---

## Sprint 1-2: Foundation & Setup (Weeks 1-4)

### Sprint 1: Infrastructure & Authentication (Weeks 1-2)

**Goal**: Set up development environment, infrastructure, and user authentication.

**Outcomes**:
- Development environment configured (Docker, local databases)
- CI/CD pipeline setup (GitHub Actions)
- Cloud infrastructure provisioned (AWS/GCP)
- User authentication system (register, login, JWT)
- Basic API structure (Express/FastAPI)
- Frontend project initialized (React + Tailwind)

**Deliverables**:
- [ ] Docker Compose for local development
- [ ] Database schema migrations (Prisma/Alembic)
- [ ] Auth API endpoints (`/auth/register`, `/auth/login`, `/auth/refresh`)
- [ ] JWT token generation/validation middleware
- [ ] Frontend authentication pages (Login, Register)
- [ ] Basic navigation layout (React Router)
- [ ] Environment configuration (dev, staging, prod)

**Success Metrics**:
- Users can register and log in successfully
- JWT tokens validated correctly
- Authentication pages render on mobile devices
- Zero critical security vulnerabilities

**Team**: 2 backend engineers, 1 frontend engineer, 1 DevOps engineer

---

### Sprint 2: Data Models & Core API (Weeks 3-4)

**Goal**: Implement core data models and basic API endpoints.

**Outcomes**:
- All database tables created (users, cards, sets, inventory_entries)
- Core API endpoints for cards and inventory
- Basic frontend inventory page (UI only, no data)
- Price feed service skeleton (manual data import for testing)

**Deliverables**:
- [ ] Database schema complete (all tables, indexes)
- [ ] Card API endpoints (`GET /cards`, `GET /cards/:id`)
- [ ] Set API endpoints (`GET /sets`)
- [ ] Inventory API endpoints (`GET /inventory`, `POST /inventory`, `PATCH /inventory/:id`)
- [ ] Inventory page UI (React, Tailwind) - grid/list view
- [ ] Card detail page UI
- [ ] Basic price feed service (manual CSV import)

**Success Metrics**:
- All database tables created and indexed
- API endpoints return valid JSON
- Inventory page renders correctly
- API response time <200ms (p95)

**Team**: 2 backend engineers, 1 frontend engineer, 1 ML engineer (part-time)

---

## Sprint 3-4: ML Pipeline & Scanning (Weeks 5-8)

### Sprint 3: ML Models & Detection (Weeks 5-6)

**Goal**: Implement card detection and classification models.

**Outcomes**:
- Multi-card detection model deployed (YOLOv8)
- Card classification model deployed (EfficientNet-B3)
- ML inference service (Docker container)
- Basic scan API endpoints

**Deliverables**:
- [ ] YOLOv8 model fine-tuned on card dataset (or pre-trained model adapted)
- [ ] EfficientNet-B3 model fine-tuned on card dataset
- [ ] ML inference service (FastAPI/Python) with Docker
- [ ] Scan upload endpoint (`POST /scans/upload`)
- [ ] Scan status endpoint (`GET /scans/:id`)
- [ ] Scan results endpoint (detected cards, bounding boxes)
- [ ] Basic frontend scan page (upload UI only)

**Success Metrics**:
- Card detection recall ≥90% (test set)
- Card classification accuracy ≥85% (test set)
- Inference latency <500ms per image (p95, GPU)
- Scan upload works end-to-end

**Team**: 2 ML engineers, 1 backend engineer, 1 frontend engineer

**ML Training Data Requirements**:
- 10,000+ annotated card images for detection
- 50,000+ labeled card images for classification
- Use public card databases (Scryfall, Pokémon API) + manual annotation

---

### Sprint 4: Scan UI & Integration (Weeks 7-8)

**Goal**: Complete scan-to-inventory workflow.

**Outcomes**:
- Scan page fully functional (upload, processing, results)
- User can confirm/edit detected cards
- Cards saved to inventory after confirmation
- Single-card and multi-card scanning working

**Deliverables**:
- [ ] Scan page UI complete (upload, camera, progress)
- [ ] Card editor component (edit set, name, condition, quantity)
- [ ] Save to inventory flow (`POST /scans/:id/save`)
- [ ] Image cropping (display detected bounding boxes)
- [ ] Error handling and retry logic
- [ ] Mobile camera integration (PWA)

**Success Metrics**:
- Users can scan and save cards to inventory
- 90%+ of scans complete successfully
- Scan-to-inventory time <30s for 10 cards (p95)
- Mobile camera works on iOS/Android browsers

**Team**: 1 ML engineer, 1 backend engineer, 2 frontend engineers

---

## Sprint 5-6: Price Feed & Valuations (Weeks 9-12)

### Sprint 5: Price Feed & Valuation Engine (Weeks 9-10)

**Goal**: Implement price data ingestion and valuation calculations.

**Outcomes**:
- Price feed service ingests data from external sources
- Valuation engine calculates FMV per card
- Card valuations displayed in inventory
- Portfolio valuation summary

**Deliverables**:
- [ ] Price feed service (scheduled scraper/job)
- [ ] TCGPlayer API integration (or manual CSV import)
- [ ] eBay API integration (historical sales)
- [ ] Valuation calculation engine (FMV = weighted median)
- [ ] Card valuation endpoint (`GET /cards/:id/valuation`)
- [ ] Portfolio valuation endpoint (`GET /portfolio/valuation`)
- [ ] Inventory page shows card values
- [ ] Portfolio dashboard (total value, value by set)

**Success Metrics**:
- 70%+ of scanned cards have price data
- Price accuracy within 15% of actual market (validation set)
- Price data updates daily
- Portfolio valuation loads in <2s

**Team**: 1 backend engineer, 1 data engineer, 1 frontend engineer

**External API Requirements**:
- TCGPlayer API key (free tier or paid)
- eBay API credentials (or manual scraping with consent)
- Scryfall API (free, for MTG cards)

---

### Sprint 6: AI Agent & Alerts (Weeks 11-12)

**Goal**: Implement basic AI agent alerts and notifications.

**Outcomes**:
- Alert rules engine functional
- Price alerts working
- Notifications sent via email and in-app
- Basic AI suggestions (price-based recommendations)

**Deliverables**:
- [ ] Alert rules API (`POST /agent/alert-rules`, `GET /agent/alerts`)
- [ ] Alert evaluation engine (background job)
- [ ] Notification service (email via SendGrid, in-app)
- [ ] AI agent suggestion engine (basic price-based recommendations)
- [ ] Alert dashboard UI
- [ ] Agent suggestions UI
- [ ] User notification preferences

**Success Metrics**:
- Alerts triggered correctly when price thresholds met
- 95%+ alert delivery success rate
- Notifications sent within 1 hour of price change
- User can create and manage alert rules

**Team**: 1 backend engineer, 1 frontend engineer, 1 ML engineer (part-time)

---

## Sprint 7-8: Marketplace & Trading (Weeks 13-16)

### Sprint 7: Marketplace Listings (Weeks 13-14)

**Goal**: Users can create and browse listings.

**Outcomes**:
- Users can create listings from inventory
- Marketplace browse/search page
- Listing detail pages
- Basic listing management (edit, delete)

**Deliverables**:
- [ ] Listing API endpoints (`POST /marketplace/listings`, `GET /marketplace/listings`)
- [ ] Marketplace search/filter functionality
- [ ] Listing creation page (UI)
- [ ] Listing detail page
- [ ] Listing management (edit, delete, mark as sold)
- [ ] Image upload for listings (max 5 images)

**Success Metrics**:
- Users can create listings successfully
- Marketplace search returns relevant results (<1s latency)
- Listings visible to other users (if marketplace enabled)

**Team**: 1 backend engineer, 2 frontend engineers

---

### Sprint 8: Messaging & Basic Trades (Weeks 15-16)

**Goal**: Users can message each other and initiate trades.

**Outcomes**:
- Messaging system functional
- Basic trade workflow (create, accept, reject)
- Trade history visible to both parties

**Deliverables**:
- [ ] Messaging API (`GET /messages/conversations`, `POST /messages/conversations/:id/messages`)
- [ ] Trade API (`POST /trades`, `POST /trades/:id/accept`)
- [ ] Messaging UI (conversations, messages)
- [ ] Trade creation UI
- [ ] Trade management UI (view status, accept/reject)
- [ ] WebSocket support for real-time messaging (optional, P1)

**Success Metrics**:
- Users can send/receive messages
- Messages delivered reliably (99%+ success)
- Trade workflow functional end-to-end

**Team**: 1 backend engineer, 2 frontend engineers

---

## Sprint 9-10: Polish & Testing (Weeks 17-20)

### Sprint 9: Matching Algorithm & Advanced Features (Weeks 17-18)

**Goal**: Implement marketplace matching and advanced trading features.

**Outcomes**:
- Two-way matching (wants vs haves)
- Trade suggestions based on value balance
- Want list functionality

**Deliverables**:
- [ ] Want list API (`POST /wants`, `GET /wants`)
- [ ] Matching algorithm implementation
- [ ] Trade suggestions API (`GET /agent/suggestions`)
- [ ] Want list UI
- [ ] Match notifications
- [ ] Trade suggestion UI

**Success Metrics**:
- 80%+ of matches are relevant (user feedback)
- Matching algorithm runs daily for all users
- Trade suggestions have ≥10% conversion rate

**Team**: 1 backend engineer, 1 ML engineer (part-time), 1 frontend engineer

---

### Sprint 10: Testing, Bug Fixes & Performance (Weeks 19-20)

**Goal**: Comprehensive testing, bug fixes, and performance optimization.

**Outcomes**:
- All P0 features tested and working
- Critical bugs fixed
- Performance optimized (API latency, page load times)
- Security audit completed

**Deliverables**:
- [ ] End-to-end tests (Cypress, Playwright)
- [ ] Integration tests (API endpoints)
- [ ] Unit tests (critical functions, 80%+ coverage)
- [ ] Load testing (1000 concurrent users)
- [ ] Security audit (automated + manual review)
- [ ] Performance optimization (DB queries, caching, CDN)
- [ ] Bug fixes (all P0 bugs resolved)

**Success Metrics**:
- 95%+ test coverage (critical paths)
- API latency <200ms (p95)
- Page load time <2s (p95)
- Zero critical security vulnerabilities
- 99.5% uptime (staging environment)

**Team**: Full team (all engineers, QA engineer)

---

## Sprint 11-12: Pre-Launch & Launch (Weeks 21-24)

### Sprint 11: Documentation & Admin Tools (Weeks 21-22)

**Goal**: Complete documentation, admin tools, and launch preparation.

**Outcomes**:
- User documentation complete
- Admin moderation tools functional
- Privacy policy and terms of service
- GDPR compliance verified

**Deliverables**:
- [ ] User guide / help documentation
- [ ] Admin moderation dashboard (reports, user management)
- [ ] Privacy policy page
- [ ] Terms of service page
- [ ] GDPR compliance checklist verified
- [ ] Data export functionality (user data export)
- [ ] Account deletion functionality

**Success Metrics**:
- Documentation complete and reviewed
- Admin tools functional
- Legal pages approved by legal team
- GDPR compliance verified

**Team**: 1 backend engineer, 1 frontend engineer, 1 technical writer, legal review

---

### Sprint 12: Launch Preparation & Beta Launch (Weeks 23-24)

**Goal**: Beta launch with select users, gather feedback, fix critical issues.

**Outcomes**:
- Beta launch with 100-500 users
- Monitoring and alerting in place
- User feedback collected
- Critical issues resolved

**Deliverables**:
- [ ] Production environment fully configured
- [ ] Monitoring dashboard (Datadog, CloudWatch)
- [ ] Alerting setup (PagerDuty, Slack)
- [ ] Beta user onboarding (invite-only)
- [ ] Feedback collection mechanism
- [ ] Bug tracking and prioritization
- [ ] Production bug fixes

**Success Metrics**:
- Beta launch successful (100-500 users)
- 99.5% uptime (production)
- Zero critical bugs (P0)
- User satisfaction ≥4/5 stars (first 100 users)
- 80%+ user retention (week 1)

**Team**: Full team (all engineers, PM, QA, support)

---

## Post-Launch (Weeks 25+)

### Month 7-8: MVP Launch & Iteration

**Goals**:
- Public MVP launch
- User acquisition (marketing)
- Iterate based on feedback
- P1 features (condition grader, OCR)

**Features**:
- Condition grader (automated ML-based grading)
- OCR for card identifiers
- Enhanced AI suggestions (ML-based forecasting)
- Payment integration (Stripe)

---

## Success Metrics Summary

### MVP Launch Criteria

**Technical**:
- All P0 features complete and tested
- 99.5% uptime (production)
- API latency <200ms (p95)
- Zero critical security vulnerabilities
- 95%+ test coverage (critical paths)

**Product**:
- User satisfaction ≥4/5 stars (first 100 users)
- 80%+ user retention (week 1)
- 85%+ card classification accuracy
- 90%+ scan success rate
- 70%+ of cards have price data

**Business**:
- 100-500 beta users
- 1000+ cards scanned by users
- 50+ listings created
- 10+ trades completed

---

## Risk Mitigation

### High-Risk Items

1. **ML Model Accuracy**: Mitigation - Start with pre-trained models, iterate with user feedback
2. **Price Data Availability**: Mitigation - Manual data import as fallback, expand sources gradually
3. **Scalability Issues**: Mitigation - Load testing, horizontal scaling, caching strategy
4. **Security Vulnerabilities**: Mitigation - Security audit, penetration testing, code reviews

### Contingency Plans

- **Sprint Delays**: Buffer time in Sprint 11-12 for catch-up
- **Model Accuracy Issues**: Fall back to manual classification, improve models post-launch
- **External API Failures**: Cache data, use backup sources, graceful degradation

---

## Team Composition

**Recommended Team Size**: 6-8 engineers

- **Backend Engineers**: 2-3
- **Frontend Engineers**: 2
- **ML Engineers**: 1-2
- **DevOps Engineer**: 1 (part-time)
- **QA Engineer**: 1 (part-time, Sprint 10+)
- **Product Manager**: 1
- **Technical Writer**: 1 (Sprint 11)

---

## Technology Stack Summary

- **Frontend**: React 18+, TypeScript, Tailwind CSS
- **Backend**: Node.js (Express) or Python (FastAPI)
- **Database**: PostgreSQL
- **Cache/Queue**: Redis
- **Storage**: AWS S3 / GCP Cloud Storage
- **ML**: PyTorch/TensorFlow, ONNX Runtime
- **Infrastructure**: Docker, Kubernetes (EKS/GKE) or AWS ECS
- **CI/CD**: GitHub Actions
- **Monitoring**: Datadog or CloudWatch
- **Email**: SendGrid or Resend
