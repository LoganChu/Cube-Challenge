# CardVault MVP Feature List & Acceptance Criteria

## Priority Definitions
- **Must-Have (P0)**: Core functionality required for MVP launch
- **Should-Have (P1)**: Important for competitive product, can launch without
- **Nice-to-Have (P2)**: Enhances UX, post-MVP

---

## Must-Have Features (P0)

### F1: User Authentication & Profiles
**Priority**: P0  
**Description**: Secure user registration, login, and profile management.

**Acceptance Criteria**:
- [ ] Users can register with email/password (minimum 8 chars, alphanumeric + special)
- [ ] Email verification required before account activation
- [ ] Users can log in and receive JWT tokens (15min access, 7-day refresh)
- [ ] Password reset via email link
- [ ] Users can update profile (username, email, preferences)
- [ ] Profile page displays basic stats (total cards, portfolio value)
- [ ] All sensitive data encrypted at rest (AES-256)

**Success Metrics**: 95% successful registration completion rate, <2s login latency

---

### F2: Single-Card Scan & Add
**Priority**: P0  
**Description**: Upload a single card image, detect/classify card, add to inventory.

**Acceptance Criteria**:
- [ ] User can upload image via file picker or camera (mobile PWA)
- [ ] Image validation: max 10MB, formats: JPG/PNG/HEIC
- [ ] System detects card in image (bounding box or accepts single-card assumption)
- [ ] System classifies card: set name + card name (accuracy ≥85% on test set)
- [ ] User can manually correct set/name if misclassified
- [ ] User can set condition (Near Mint, Lightly Played, Moderately Played, Heavily Played, Damaged)
- [ ] User can set quantity
- [ ] Card is saved to user's inventory with timestamp
- [ ] Scan-to-save latency <5s for single card (excluding initial model load)

**Success Metrics**: 85%+ classification accuracy, <5s scan latency (p95), 80%+ user satisfaction (post-MVP survey)

---

### F3: Multi-Card Image Scan
**Priority**: P0  
**Description**: Upload image with multiple cards, detect all cards, batch process.

**Acceptance Criteria**:
- [ ] User can upload image containing multiple cards (arranged or scattered)
- [ ] System detects all card bounding boxes (recall ≥90% on test images with 2-20 cards)
- [ ] System crops each detected card automatically
- [ ] System classifies each card (same accuracy target as F2)
- [ ] User sees grid of detected cards with set/name pre-filled
- [ ] User can edit/delete individual cards before saving
- [ ] User can set condition/quantity per card
- [ ] Batch save creates multiple inventory entries
- [ ] Processing happens async; user sees progress indicator
- [ ] Complete batch processing <30s for 10 cards (p95)

**Success Metrics**: 90%+ detection recall, 85%+ classification accuracy per card, <30s batch processing time

---

### F4: Inventory Management
**Priority**: P0  
**Description**: View, search, filter, and edit user's card collection.

**Acceptance Criteria**:
- [ ] User can view inventory as list or grid view
- [ ] User can search by card name, set name
- [ ] User can filter by set, condition, date added
- [ ] User can sort by name, date added, value (ascending/descending)
- [ ] User can edit card metadata (set, name, condition, quantity)
- [ ] User can delete cards from inventory
- [ ] Inventory displays current estimated value per card (if available)
- [ ] Pagination or infinite scroll (50 items per page)
- [ ] Inventory load time <2s (p95) for 1000 cards

**Success Metrics**: <2s page load time, 95%+ search accuracy, user can find any card in <10s

---

### F5: Price/Valuation Feed (Basic)
**Priority**: P0  
**Description**: Display estimated card values from aggregated price sources.

**Acceptance Criteria**:
- [ ] System ingests price data from at least 2 sources (e.g., TCGPlayer API, eBay sales)
- [ ] Prices update at least daily
- [ ] Card detail page shows: current FMV, price history (last 30 days), confidence interval
- [ ] FMV calculation: median of recent sales (last 90 days) weighted by recency
- [ ] Missing prices show "Price unavailable" gracefully
- [ ] Price data normalized to standard card identifiers (set code + name)
- [ ] Users see portfolio total value on dashboard

**Success Metrics**: 70%+ of scanned cards have price data, price accuracy within 15% of actual market (validation set)

---

### F6: AI Agent - Basic Alerts
**Priority**: P0  
**Description**: Monitor card prices, send alerts when thresholds breached.

**Acceptance Criteria**:
- [ ] User can set price alert thresholds (absolute or percentage change)
- [ ] System checks prices daily and evaluates alert rules
- [ ] User receives in-app notification when alert triggered
- [ ] User can view all active alerts in dashboard
- [ ] User can dismiss alerts
- [ ] Alert accuracy: no false positives due to data errors (manual verification)

**Success Metrics**: 95%+ alert delivery success, <24h delay from price change to alert

---

### F7: Marketplace - List Cards
**Priority**: P0  
**Description**: Users can create listings to sell/trade cards.

**Acceptance Criteria**:
- [ ] User can select card from inventory to list
- [ ] User sets price (or "Trade Only")
- [ ] User sets listing title, description, photos (max 5)
- [ ] User sets condition, quantity available
- [ ] Listing is publicly visible (or set to private/expires)
- [ ] User can edit/delete their listings
- [ ] Listings appear in marketplace browse/search

**Success Metrics**: 90%+ successful listing creation, listings load in <2s

---

### F8: Marketplace - Search & Browse
**Priority**: P0  
**Description**: Users can search for cards in marketplace.

**Acceptance Criteria**:
- [ ] Users can search by card name, set name, seller username
- [ ] Users can filter by price range, condition, location (optional)
- [ ] Search results show card image, seller, price, condition
- [ ] Clicking listing shows full details (description, photos, seller profile)
- [ ] Search results paginated (20 per page)
- [ ] Search latency <1s (p95)

**Success Metrics**: <1s search latency, 95%+ relevant results (top 10 results)

---

### F9: Basic Messaging
**Priority**: P0  
**Description**: Users can send messages to other users (for trades/offers).

**Acceptance Criteria**:
- [ ] User can send message to another user from their profile or listing
- [ ] Messages are threaded by conversation
- [ ] User can view all conversations in inbox
- [ ] Real-time or near-real-time message delivery (WebSocket or polling)
- [ ] User receives notification when new message arrives
- [ ] Messages are persisted and searchable
- [ ] User can block other users

**Success Metrics**: Message delivery <5s latency, 99%+ message delivery reliability

---

### F10: Privacy & Security Baseline
**Priority**: P0  
**Description**: Secure user data, encrypted storage, GDPR/CCPA compliance basics.

**Acceptance Criteria**:
- [ ] All user passwords hashed with bcrypt (minimum 10 rounds)
- [ ] Sensitive inventory data encrypted at rest (field-level encryption for cards)
- [ ] HTTPS only (TLS 1.2+)
- [ ] User can export their data (JSON format)
- [ ] User can delete account and all associated data (GDPR right to erasure)
- [ ] Privacy policy and terms of service pages
- [ ] User consent checkboxes for data sharing (marketplace opt-in)
- [ ] Default privacy: inventory private unless user opts in to marketplace sharing
- [ ] API rate limiting: 100 requests/min per user, 1000/min per IP

**Success Metrics**: Zero data breaches, 100% encrypted sensitive data, GDPR audit pass

---

## Should-Have Features (P1)

### F11: Condition Grader (Automated)
**Priority**: P1  
**Description**: ML model estimates card condition from image.

**Acceptance Criteria**:
- [ ] Model analyzes card image for wear, edges, corners, surface
- [ ] Outputs condition estimate (1-10 scale or categorical)
- [ ] User can override estimate
- [ ] Model accuracy: within 1 grade of human expert 75%+ of the time

---

### F12: Two-Way Marketplace Matching
**Priority**: P1  
**Description**: Match user wants with others' haves, suggest trades.

**Acceptance Criteria**:
- [ ] User can create "Want List" (cards they want to acquire)
- [ ] System matches: User A's wants vs User B's haves
- [ ] System suggests potential trades (value-balanced or user-defined)
- [ ] Matching algorithm accounts for set, condition, edition
- [ ] Users receive notifications for matches

---

### F13: Trade Workflow (Escrow Optional)
**Priority**: P1  
**Description**: Formalized trade process with tracking.

**Acceptance Criteria**:
- [ ] Users can create trade offer (propose cards to exchange)
- [ ] Other user can accept/reject/counter-offer
- [ ] Trade status tracked (pending, accepted, shipped, completed, cancelled)
- [ ] Optional escrow integration (manual or Stripe Connect)
- [ ] Trade history visible to both parties

---

### F14: Analytics Dashboard
**Priority**: P1  
**Description**: Portfolio value charts, gains/losses, breakdowns.

**Acceptance Criteria**:
- [ ] Portfolio value over time (line chart)
- [ ] Value by set (pie chart)
- [ ] Gains/losses summary (total, % change)
- [ ] Top valued cards
- [ ] Export analytics data (CSV)

---

### F15: OCR for Card Identifiers
**Priority**: P1  
**Description**: Extract set numbers, card numbers, serial numbers from images.

**Acceptance Criteria**:
- [ ] OCR extracts card number (e.g., "001/150")
- [ ] OCR extracts serial numbers for rare cards
- [ ] OCR accuracy: 90%+ for clear images
- [ ] Data used to improve classification accuracy

---

## Nice-to-Have Features (P2)

### F16: Social Features (follow, share)
### F17: Collection wishlists
### F18: Automated condition grader feedback loop
### F19: Bulk import (CSV/Excel)
### F20: Advanced search (filters, saved searches)
### F21: Admin moderation tools
### F22: Dispute resolution workflow
### F23: Mobile native apps (React Native)
### F24: Payment integration (Stripe, PayPal)
### F25: Recommendation engine (ML-based suggestions)

---

## MVP Scope Summary

**Launch Requirements**: All P0 features (F1-F10) must be complete and tested.

**Launch Timeline**: 12 weeks (see roadmap)

**Success Criteria for MVP Launch**:
- All P0 acceptance criteria met
- System handles 1000 concurrent users
- 99.5% uptime
- Zero critical security vulnerabilities
- User feedback: 4/5 stars or better (first 100 users)
