# CardVault Data Schema

## Database: PostgreSQL

All timestamps use UTC. Soft deletes use `deleted_at` (nullable timestamp).

---

## Core Tables

### `users`
Primary user accounts.

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    email_verified_at TIMESTAMP,
    password_hash VARCHAR(255) NOT NULL, -- bcrypt
    username VARCHAR(50) UNIQUE NOT NULL,
    avatar_url VARCHAR(512),
    phone VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    -- Privacy settings
    inventory_public BOOLEAN DEFAULT FALSE,
    marketplace_enabled BOOLEAN DEFAULT FALSE,
    share_analytics BOOLEAN DEFAULT FALSE,
    
    -- Preferences
    currency VARCHAR(3) DEFAULT 'USD',
    timezone VARCHAR(50) DEFAULT 'UTC',
    notification_email BOOLEAN DEFAULT TRUE,
    notification_push BOOLEAN DEFAULT TRUE,
    
    INDEX idx_users_email (email),
    INDEX idx_users_username (username)
);
```

### `user_sessions`
JWT refresh tokens and session management.

```sql
CREATE TABLE user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    refresh_token_hash VARCHAR(255) NOT NULL, -- hashed JWT
    ip_address VARCHAR(45),
    user_agent TEXT,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_sessions_user_id (user_id),
    INDEX idx_sessions_expires_at (expires_at)
);
```

---

## Inventory & Cards

### `sets`
Card set metadata (Magic: The Gathering sets, Pokémon sets, etc.).

```sql
CREATE TABLE sets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL, -- e.g., "M21", "XY"
    game_type VARCHAR(50) NOT NULL, -- "MTG", "Pokemon", "YuGiOh", etc.
    release_date DATE,
    total_cards INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_sets_code (code),
    INDEX idx_sets_game_type (game_type)
);
```

### `cards`
Master card catalog (normalized, shared across users).

```sql
CREATE TABLE cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    set_id UUID NOT NULL REFERENCES sets(id),
    name VARCHAR(255) NOT NULL,
    card_number VARCHAR(20), -- e.g., "001/150"
    rarity VARCHAR(50), -- "Common", "Rare", "Mythic", etc.
    card_type VARCHAR(100), -- "Creature", "Instant", "Trainer", etc.
    image_url VARCHAR(512),
    thumbnail_url VARCHAR(512),
    
    -- Normalized identifiers for matching
    normalized_name VARCHAR(255) NOT NULL, -- lowercase, stripped
    tcgplayer_id VARCHAR(50),
    scryfall_id VARCHAR(50),
    
    metadata JSONB, -- flexible fields (mana cost, attack, etc.)
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(set_id, normalized_name, card_number),
    INDEX idx_cards_set_id (set_id),
    INDEX idx_cards_normalized_name (normalized_name),
    INDEX idx_cards_tcgplayer_id (tcgplayer_id),
    INDEX idx_cards_metadata_gin (metadata) -- GIN index for JSONB
);
```

### `inventory_entries`
User's card collection (references cards).

```sql
CREATE TABLE inventory_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id UUID NOT NULL REFERENCES cards(id),
    
    quantity INTEGER NOT NULL DEFAULT 1,
    condition VARCHAR(50) NOT NULL, -- "Near Mint", "Lightly Played", etc.
    condition_grade DECIMAL(3,1), -- 1.0-10.0 (optional, from ML)
    notes TEXT,
    
    -- Purchase/source info
    purchase_price DECIMAL(10,2),
    purchase_date DATE,
    purchase_source VARCHAR(255),
    
    -- Scan metadata
    scanned_at TIMESTAMP DEFAULT NOW(),
    scan_image_url VARCHAR(512), -- S3 URL of scanned image
    scan_confidence DECIMAL(5,2), -- 0-100, ML classification confidence
    
    -- Value tracking (denormalized for performance)
    last_valuated_at TIMESTAMP,
    last_valuated_price DECIMAL(10,2),
    last_valuated_currency VARCHAR(3) DEFAULT 'USD',
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    INDEX idx_inventory_user_id (user_id),
    INDEX idx_inventory_card_id (card_id),
    INDEX idx_inventory_user_card (user_id, card_id),
    INDEX idx_inventory_scanned_at (scanned_at)
) PARTITION BY HASH (user_id); -- Partitioning for scale
```

---

## Scanning & ML

### `scans`
Scan job tracking.

```sql
CREATE TABLE scans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    image_url VARCHAR(512) NOT NULL, -- S3 URL
    scan_type VARCHAR(20) NOT NULL, -- "single", "multi"
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- "pending", "processing", "completed", "failed"
    error_message TEXT,
    
    -- ML results (raw JSON)
    detection_results JSONB, -- bounding boxes, confidence scores
    classification_results JSONB, -- set, name, confidence
    
    processed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_scans_user_id (user_id),
    INDEX idx_scans_status (status),
    INDEX idx_scans_created_at (created_at)
);
```

### `scan_cards`
Individual cards detected in a scan (before user confirmation).

```sql
CREATE TABLE scan_cards (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scan_id UUID NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    card_id UUID REFERENCES cards(id), -- NULL if not matched yet
    
    -- Detection data
    bounding_box JSONB NOT NULL, -- {"x", "y", "width", "height"} (normalized 0-1)
    crop_image_url VARCHAR(512), -- S3 URL of cropped card
    
    -- Classification (before user confirmation)
    predicted_set_id UUID REFERENCES sets(id),
    predicted_name VARCHAR(255),
    predicted_confidence DECIMAL(5,2),
    
    -- User confirmed data
    confirmed_set_id UUID REFERENCES sets(id),
    confirmed_name VARCHAR(255),
    confirmed_condition VARCHAR(50),
    confirmed_quantity INTEGER DEFAULT 1,
    
    saved_to_inventory BOOLEAN DEFAULT FALSE,
    inventory_entry_id UUID REFERENCES inventory_entries(id),
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_scan_cards_scan_id (scan_id),
    INDEX idx_scan_cards_card_id (card_id)
);
```

---

## Pricing & Valuations

### `price_sources`
External price data sources.

```sql
CREATE TABLE price_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL, -- "TCGPlayer", "eBay", etc.
    source_type VARCHAR(50) NOT NULL, -- "api", "scraper"
    api_endpoint VARCHAR(512),
    last_sync_at TIMESTAMP,
    sync_frequency_minutes INTEGER DEFAULT 1440, -- daily
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);
```

### `card_prices`
Historical price data per card (from external sources).

```sql
CREATE TABLE card_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    price_source_id UUID NOT NULL REFERENCES price_sources(id),
    
    price DECIMAL(10,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    condition VARCHAR(50), -- if condition-specific pricing
    listing_type VARCHAR(50), -- "market", "low", "mid", "high", "sale"
    
    observed_at TIMESTAMP NOT NULL, -- when price was observed
    sale_date DATE, -- if historical sale
    
    metadata JSONB, -- source-specific data (listing ID, seller, etc.)
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_prices_card_id (card_id),
    INDEX idx_prices_source_id (price_source_id),
    INDEX idx_prices_observed_at (observed_at),
    INDEX idx_prices_card_observed (card_id, observed_at DESC)
);
```

### `card_valuations`
Computed fair market value (FMV) per card.

```sql
CREATE TABLE card_valuations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    card_id UUID NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    condition VARCHAR(50), -- if condition-specific
    
    fmv DECIMAL(10,2) NOT NULL, -- fair market value (median)
    confidence_interval_lower DECIMAL(10,2),
    confidence_interval_upper DECIMAL(10,2),
    sample_size INTEGER NOT NULL, -- number of price points used
    currency VARCHAR(3) DEFAULT 'USD',
    
    -- Price statistics
    min_price DECIMAL(10,2),
    max_price DECIMAL(10,2),
    median_price DECIMAL(10,2),
    
    computed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    valid_until TIMESTAMP, -- TTL for cache
    
    INDEX idx_valuations_card_id (card_id),
    INDEX idx_valuations_computed_at (computed_at),
    UNIQUE(card_id, condition, computed_at)
);
```

---

## Marketplace

### `listings`
User listings for sale/trade.

```sql
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id UUID NOT NULL REFERENCES cards(id),
    inventory_entry_id UUID REFERENCES inventory_entries(id), -- if from inventory
    
    title VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10,2), -- NULL if trade-only
    currency VARCHAR(3) DEFAULT 'USD',
    condition VARCHAR(50) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    
    -- Listing status
    status VARCHAR(20) NOT NULL DEFAULT 'active', -- "active", "pending", "sold", "expired", "cancelled"
    listing_type VARCHAR(20) NOT NULL, -- "sale", "trade", "both"
    
    -- Images (JSON array of S3 URLs)
    image_urls JSONB NOT NULL, -- ["url1", "url2", ...]
    
    expires_at TIMESTAMP,
    sold_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_listings_user_id (user_id),
    INDEX idx_listings_card_id (card_id),
    INDEX idx_listings_status (status),
    INDEX idx_listings_created_at (created_at DESC)
);
```

### `wants`
User want lists (cards they want to acquire).

```sql
CREATE TABLE wants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id UUID NOT NULL REFERENCES cards(id),
    
    min_condition VARCHAR(50),
    max_price DECIMAL(10,2),
    priority INTEGER DEFAULT 0, -- 0-10
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP,
    
    UNIQUE(user_id, card_id),
    INDEX idx_wants_user_id (user_id),
    INDEX idx_wants_card_id (card_id)
);
```

### `trade_matches`
System-generated trade suggestions (wants vs haves).

```sql
CREATE TABLE trade_matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_a_id UUID NOT NULL REFERENCES users(id),
    user_b_id UUID NOT NULL REFERENCES users(id),
    card_a_id UUID NOT NULL REFERENCES cards(id), -- user A wants this
    card_b_id UUID NOT NULL REFERENCES cards(id), -- user B has this
    
    match_score DECIMAL(5,2), -- 0-100, how good the match is
    match_type VARCHAR(50), -- "direct", "fuzzy", "value_balanced"
    
    notified_at TIMESTAMP, -- when users were notified
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_matches_user_a (user_a_id),
    INDEX idx_matches_user_b (user_b_id),
    INDEX idx_matches_notified (notified_at)
);
```

---

## Trades & Offers

### `trades`
Trade transactions.

```sql
CREATE TABLE trades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    initiator_user_id UUID NOT NULL REFERENCES users(id),
    recipient_user_id UUID NOT NULL REFERENCES users(id),
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- "pending", "countered", "accepted", "shipped", "completed", "cancelled"
    
    -- Trade items (JSONB array)
    initiator_items JSONB NOT NULL, -- [{"inventory_entry_id", "card_id", "quantity"}]
    recipient_items JSONB NOT NULL,
    
    -- Value estimates
    initiator_total_value DECIMAL(10,2),
    recipient_total_value DECIMAL(10,2),
    
    -- Escrow (optional)
    escrow_enabled BOOLEAN DEFAULT FALSE,
    escrow_provider VARCHAR(50), -- "stripe", "manual", etc.
    escrow_id VARCHAR(255),
    
    expires_at TIMESTAMP,
    accepted_at TIMESTAMP,
    shipped_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_trades_initiator (initiator_user_id),
    INDEX idx_trades_recipient (recipient_user_id),
    INDEX idx_trades_status (status)
);
```

### `trade_offers`
Individual offers within a trade negotiation.

```sql
CREATE TABLE trade_offers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    trade_id UUID NOT NULL REFERENCES trades(id) ON DELETE CASCADE,
    offered_by_user_id UUID NOT NULL REFERENCES users(id),
    
    items JSONB NOT NULL, -- same structure as trades.initiator_items
    message TEXT,
    
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- "pending", "accepted", "rejected", "countered"
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_offers_trade_id (trade_id),
    INDEX idx_offers_offered_by (offered_by_user_id)
);
```

---

## Messaging

### `conversations`
Message threads between users.

```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_a_id UUID NOT NULL REFERENCES users(id),
    user_b_id UUID NOT NULL REFERENCES users(id),
    
    last_message_at TIMESTAMP,
    last_read_by_a TIMESTAMP,
    last_read_by_b TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_a_id, user_b_id),
    INDEX idx_conv_user_a (user_a_id),
    INDEX idx_conv_user_b (user_b_id),
    INDEX idx_conv_last_message (last_message_at DESC)
);
```

### `messages`
Individual messages.

```sql
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    sender_id UUID NOT NULL REFERENCES users(id),
    
    content TEXT NOT NULL,
    message_type VARCHAR(20) DEFAULT 'text', -- "text", "offer", "system"
    
    -- Optional references
    listing_id UUID REFERENCES listings(id),
    trade_id UUID REFERENCES trades(id),
    
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_messages_conversation (conversation_id),
    INDEX idx_messages_sender (sender_id),
    INDEX idx_messages_created (created_at DESC)
);
```

---

## AI Agent & Alerts

### `alert_rules`
User-defined alert rules.

```sql
CREATE TABLE alert_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    rule_type VARCHAR(50) NOT NULL, -- "price_above", "price_below", "price_change_pct", "portfolio_value_change"
    target_type VARCHAR(50) NOT NULL, -- "card", "set", "portfolio"
    target_id UUID, -- card_id, set_id, or NULL for portfolio
    
    threshold_value DECIMAL(10,2),
    threshold_percentage DECIMAL(5,2),
    
    is_active BOOLEAN DEFAULT TRUE,
    last_triggered_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_alert_rules_user_id (user_id),
    INDEX idx_alert_rules_active (is_active)
);
```

### `alerts`
Generated alert instances.

```sql
CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    alert_rule_id UUID REFERENCES alert_rules(id),
    
    alert_type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    severity VARCHAR(20) DEFAULT 'info', -- "info", "warning", "urgent"
    
    -- Context data
    card_id UUID REFERENCES cards(id),
    old_value DECIMAL(10,2),
    new_value DECIMAL(10,2),
    
    read_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_alerts_user_id (user_id),
    INDEX idx_alerts_read (read_at),
    INDEX idx_alerts_created (created_at DESC)
);
```

### `agent_suggestions`
AI-generated suggestions (hold/sell/trade).

```sql
CREATE TABLE agent_suggestions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    suggestion_type VARCHAR(50) NOT NULL, -- "sell", "hold", "trade", "buy"
    card_id UUID REFERENCES cards(id),
    inventory_entry_id UUID REFERENCES inventory_entries(id),
    
    title VARCHAR(255) NOT NULL,
    reasoning TEXT NOT NULL,
    confidence_score DECIMAL(5,2), -- 0-100
    
    -- Value projections
    current_value DECIMAL(10,2),
    projected_value DECIMAL(10,2),
    time_horizon_days INTEGER,
    
    viewed_at TIMESTAMP,
    dismissed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_suggestions_user_id (user_id),
    INDEX idx_suggestions_created (created_at DESC)
);
```

---

## Analytics & Reporting

### `portfolio_snapshots`
Daily snapshots of user portfolio value.

```sql
CREATE TABLE portfolio_snapshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    snapshot_date DATE NOT NULL,
    total_value DECIMAL(12,2) NOT NULL,
    total_cards INTEGER NOT NULL,
    unique_cards INTEGER NOT NULL,
    
    -- Breakdown by set (JSONB)
    value_by_set JSONB,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, snapshot_date),
    INDEX idx_snapshots_user_date (user_id, snapshot_date DESC)
);
```

---

## Admin & Moderation

### `admin_users`
Admin/moderator accounts (separate from regular users for RBAC).

```sql
CREATE TABLE admin_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(50) NOT NULL, -- "admin", "moderator", "support"
    permissions JSONB, -- granular permissions
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    UNIQUE(user_id, role)
);
```

### `reports`
User reports (spam, scams, etc.).

```sql
CREATE TABLE reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reporter_user_id UUID NOT NULL REFERENCES users(id),
    reported_user_id UUID REFERENCES users(id),
    reported_listing_id UUID REFERENCES listings(id),
    reported_trade_id UUID REFERENCES trades(id),
    
    report_type VARCHAR(50) NOT NULL, -- "spam", "scam", "inappropriate", "fraud"
    description TEXT,
    
    status VARCHAR(20) DEFAULT 'pending', -- "pending", "reviewed", "resolved", "dismissed"
    admin_notes TEXT,
    resolved_by_admin_id UUID REFERENCES admin_users(id),
    resolved_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_reports_status (status),
    INDEX idx_reports_created (created_at DESC)
);
```

---

## Indexes & Performance

Additional indexes for common query patterns:

```sql
-- Full-text search on card names
CREATE INDEX idx_cards_name_trgm ON cards USING gin (name gin_trgm_ops);

-- Partial indexes for active listings
CREATE INDEX idx_listings_active ON listings (card_id, created_at DESC) WHERE status = 'active';

-- Composite index for inventory queries
CREATE INDEX idx_inventory_user_condition ON inventory_entries (user_id, condition) WHERE deleted_at IS NULL;
```

---

## Encryption Notes

Sensitive fields encrypted at rest using application-level encryption (AES-256-GCM):
- `users.password_hash` (already hashed, but additional encryption layer)
- `inventory_entries.purchase_price`, `purchase_source` (if sensitive)
- `trades.*` (if required by compliance)

Encryption keys managed via AWS KMS or similar.

---

## Data Retention & Deletion

- **Soft Deletes**: `deleted_at` timestamps for user-requested deletions
- **GDPR Compliance**: Hard delete after 30-day grace period
- **Audit Trail**: All deletions logged in audit table (not shown here)

---

## Migration Strategy

Use a migration tool (Prisma Migrate, Alembic, Flyway):
1. Create tables in dependency order
2. Add indexes after bulk data loads
3. Partition `inventory_entries` after initial data population
4. Add GIN indexes for JSONB after data exists
