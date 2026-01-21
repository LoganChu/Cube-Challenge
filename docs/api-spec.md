# CardVault API Specification

## Base URL
```
Production: https://api.cardvault.app/v1
Staging: https://api-staging.cardvault.app/v1
```

## Authentication
All endpoints (except auth) require JWT Bearer token:
```
Authorization: Bearer <access_token>
```

## Response Format
Standard JSON responses:
```json
{
  "success": true,
  "data": { ... },
  "error": null,
  "meta": {
    "request_id": "uuid",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

Error responses:
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": { "field": "email", "issue": "Invalid format" }
  },
  "meta": { ... }
}
```

---

## Authentication Endpoints

### POST /auth/register
Register new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "username": "collector123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "username": "collector123",
      "email_verified": false
    },
    "message": "Verification email sent"
  }
}
```

**Status Codes:** 201 Created, 400 Bad Request, 409 Conflict

---

### POST /auth/login
Authenticate user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_in": 900,
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "username": "collector123"
    }
  }
}
```

**Status Codes:** 200 OK, 401 Unauthorized

---

### POST /auth/refresh
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** Same as `/auth/login`

---

### POST /auth/logout
Invalidate refresh token.

**Request:** (none)

**Response:**
```json
{
  "success": true,
  "data": { "message": "Logged out successfully" }
}
```

---

## Scan Endpoints

### POST /scans/upload
Upload image for scanning (single or multi-card).

**Request:** Multipart form-data
```
image: <file> (required, max 10MB, JPG/PNG/HEIC)
scan_type: "single" | "multi" (required)
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_id": "uuid",
    "status": "pending",
    "image_url": "https://s3.../upload.jpg",
    "estimated_processing_time_seconds": 5
  }
}
```

**Status Codes:** 202 Accepted, 400 Bad Request

---

### GET /scans/{scan_id}
Get scan status and results.

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_id": "uuid",
    "status": "completed",
    "scan_type": "multi",
    "image_url": "https://s3.../upload.jpg",
    "detected_cards": [
      {
        "id": "uuid",
        "bounding_box": { "x": 0.1, "y": 0.2, "width": 0.3, "height": 0.4 },
        "crop_image_url": "https://s3.../crop1.jpg",
        "predicted_set": { "id": "uuid", "name": "Core Set 2021", "code": "M21" },
        "predicted_name": "Lightning Bolt",
        "predicted_confidence": 92.5,
        "confirmed": false,
        "condition": null,
        "quantity": null
      }
    ],
    "processed_at": "2024-01-15T10:35:00Z"
  }
}
```

**Status Codes:** 200 OK, 404 Not Found

---

### PATCH /scans/{scan_id}/cards/{card_id}
Confirm/edit detected card before saving.

**Request:**
```json
{
  "confirmed_set_id": "uuid",
  "confirmed_name": "Lightning Bolt",
  "condition": "Near Mint",
  "quantity": 2
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "scan_card_id": "uuid",
    "confirmed": true,
    "card": {
      "id": "uuid",
      "name": "Lightning Bolt",
      "set": { "id": "uuid", "name": "Core Set 2021", "code": "M21" }
    }
  }
}
```

---

### POST /scans/{scan_id}/save
Save confirmed cards to inventory.

**Request:**
```json
{
  "card_ids": ["uuid1", "uuid2"] // Optional: only save specific cards
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "saved_count": 2,
    "inventory_entries": [
      {
        "id": "uuid",
        "card": { "id": "uuid", "name": "Lightning Bolt" },
        "quantity": 2,
        "condition": "Near Mint"
      }
    ]
  }
}
```

---

## Inventory Endpoints

### GET /inventory
Get user's inventory with filters.

**Query Parameters:**
- `page`: integer (default: 1)
- `limit`: integer (default: 50, max: 100)
- `search`: string (card name, set name)
- `set_id`: uuid
- `condition`: string
- `sort_by`: "name" | "date_added" | "value" | "condition" (default: "date_added")
- `sort_order`: "asc" | "desc" (default: "desc")

**Response:**
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "uuid",
        "card": {
          "id": "uuid",
          "name": "Lightning Bolt",
          "set": { "id": "uuid", "name": "Core Set 2021", "code": "M21" },
          "image_url": "https://s3.../card.jpg"
        },
        "quantity": 2,
        "condition": "Near Mint",
        "condition_grade": 9.5,
        "current_value": { "amount": 15.50, "currency": "USD", "confidence": "high" },
        "scanned_at": "2024-01-15T10:30:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total": 150,
      "total_pages": 3
    }
  }
}
```

---

### GET /inventory/{entry_id}
Get single inventory entry details.

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "card": { ... },
    "quantity": 2,
    "condition": "Near Mint",
    "condition_grade": 9.5,
    "notes": "Personal collection",
    "purchase_price": 10.00,
    "purchase_date": "2023-06-01",
    "current_value": {
      "amount": 15.50,
      "currency": "USD",
      "confidence": "high",
      "last_updated": "2024-01-15T08:00:00Z"
    },
    "value_history": [
      { "date": "2024-01-01", "value": 14.00 },
      { "date": "2024-01-15", "value": 15.50 }
    ],
    "scanned_at": "2024-01-15T10:30:00Z",
    "scan_image_url": "https://s3.../scan.jpg"
  }
}
```

---

### PATCH /inventory/{entry_id}
Update inventory entry.

**Request:**
```json
{
  "quantity": 3,
  "condition": "Lightly Played",
  "notes": "Updated notes"
}
```

**Response:** Updated inventory entry object

---

### DELETE /inventory/{entry_id}
Delete inventory entry (soft delete).

**Response:**
```json
{
  "success": true,
  "data": { "message": "Inventory entry deleted" }
}
```

---

## Valuation Endpoints

### GET /cards/{card_id}/valuation
Get current valuation for a card.

**Query Parameters:**
- `condition`: string (optional, for condition-specific pricing)

**Response:**
```json
{
  "success": true,
  "data": {
    "card_id": "uuid",
    "condition": "Near Mint",
    "fmv": 15.50,
    "currency": "USD",
    "confidence_interval": {
      "lower": 12.00,
      "upper": 19.00
    },
    "sample_size": 45,
    "price_statistics": {
      "min": 10.00,
      "max": 22.00,
      "median": 15.50
    },
    "price_history": [
      { "date": "2024-01-01", "fmv": 14.00 },
      { "date": "2024-01-08", "fmv": 14.50 },
      { "date": "2024-01-15", "fmv": 15.50 }
    ],
    "computed_at": "2024-01-15T08:00:00Z",
    "sources": ["TCGPlayer", "eBay"]
  }
}
```

---

### GET /portfolio/valuation
Get user's portfolio valuation summary.

**Response:**
```json
{
  "success": true,
  "data": {
    "total_value": 1250.75,
    "currency": "USD",
    "total_cards": 150,
    "unique_cards": 120,
    "value_by_set": [
      { "set_id": "uuid", "set_name": "Core Set 2021", "value": 450.00, "card_count": 50 },
      { "set_id": "uuid", "set_name": "Throne of Eldraine", "value": 800.75, "card_count": 100 }
    ],
    "value_by_condition": {
      "Near Mint": 800.00,
      "Lightly Played": 350.00,
      "Moderately Played": 100.75
    },
    "last_updated": "2024-01-15T08:00:00Z"
  }
}
```

---

## Marketplace Endpoints

### GET /marketplace/listings
Search/browse marketplace listings.

**Query Parameters:**
- `search`: string (card name, set name)
- `set_id`: uuid
- `condition`: string
- `min_price`: decimal
- `max_price`: decimal
- `listing_type`: "sale" | "trade" | "both"
- `seller_id`: uuid
- `page`: integer
- `limit`: integer
- `sort_by`: "price" | "date" | "relevance" (default: "date")

**Response:**
```json
{
  "success": true,
  "data": {
    "listings": [
      {
        "id": "uuid",
        "card": { "id": "uuid", "name": "Lightning Bolt", "set": { ... } },
        "seller": { "id": "uuid", "username": "trader123", "rating": 4.8 },
        "title": "Lightning Bolt - Near Mint",
        "description": "Perfect condition",
        "price": 16.00,
        "currency": "USD",
        "condition": "Near Mint",
        "quantity": 1,
        "listing_type": "sale",
        "image_urls": ["https://s3.../img1.jpg"],
        "created_at": "2024-01-14T15:00:00Z"
      }
    ],
    "pagination": { ... }
  }
}
```

---

### POST /marketplace/listings
Create a new listing.

**Request:**
```json
{
  "card_id": "uuid",
  "inventory_entry_id": "uuid", // Optional: link to inventory
  "title": "Lightning Bolt - Near Mint",
  "description": "Perfect condition, from personal collection",
  "price": 16.00,
  "condition": "Near Mint",
  "quantity": 1,
  "listing_type": "sale",
  "image_urls": ["https://s3.../img1.jpg", "https://s3.../img2.jpg"],
  "expires_at": "2024-02-15T00:00:00Z" // Optional
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "listing_id": "uuid",
    "status": "active",
    "created_at": "2024-01-15T10:40:00Z"
  }
}
```

---

### GET /marketplace/listings/{listing_id}
Get listing details.

**Response:** Full listing object with seller info, card details, images

---

### DELETE /marketplace/listings/{listing_id}
Cancel/delete listing.

---

## Trade Endpoints

### POST /trades
Create a trade offer.

**Request:**
```json
{
  "recipient_user_id": "uuid",
  "initiator_items": [
    { "inventory_entry_id": "uuid1", "quantity": 1 },
    { "inventory_entry_id": "uuid2", "quantity": 2 }
  ],
  "recipient_items": [
    { "listing_id": "uuid3" },
    { "card_id": "uuid4", "quantity": 1 } // if not from listing
  ],
  "message": "Interested in trading?"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "trade_id": "uuid",
    "status": "pending",
    "created_at": "2024-01-15T10:45:00Z"
  }
}
```

---

### GET /trades
Get user's trades (initiated or received).

**Query Parameters:**
- `status`: string (pending, accepted, completed, etc.)
- `direction`: "sent" | "received" | "both" (default: "both")

**Response:** Array of trade objects

---

### POST /trades/{trade_id}/accept
Accept a trade.

**Response:** Updated trade object

---

### POST /trades/{trade_id}/counter
Counter-offer.

**Request:**
```json
{
  "items": [ ... ], // Modified items
  "message": "How about this instead?"
}
```

---

## AI Agent Endpoints

### GET /agent/alerts
Get user's active alerts.

**Response:**
```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "uuid",
        "type": "price_above",
        "title": "Lightning Bolt price increased",
        "message": "Your Lightning Bolt (Near Mint) is now worth $18.00 (was $15.50)",
        "severity": "info",
        "card": { "id": "uuid", "name": "Lightning Bolt" },
        "old_value": 15.50,
        "new_value": 18.00,
        "created_at": "2024-01-15T08:30:00Z"
      }
    ]
  }
}
```

---

### POST /agent/alert-rules
Create alert rule.

**Request:**
```json
{
  "rule_type": "price_above",
  "target_type": "card",
  "target_id": "uuid",
  "threshold_value": 20.00
}
```

---

### GET /agent/suggestions
Get AI agent suggestions.

**Response:**
```json
{
  "success": true,
  "data": {
    "suggestions": [
      {
        "id": "uuid",
        "type": "sell",
        "title": "Consider selling Lightning Bolt",
        "reasoning": "Price has increased 20% in the last week. Historical data suggests it may dip soon.",
        "confidence_score": 75.0,
        "card": { "id": "uuid", "name": "Lightning Bolt" },
        "current_value": 18.00,
        "projected_value": 15.00,
        "time_horizon_days": 30
      }
    ]
  }
}
```

---

## Messaging Endpoints

### GET /messages/conversations
Get user's conversations.

**Response:**
```json
{
  "success": true,
  "data": {
    "conversations": [
      {
        "id": "uuid",
        "other_user": { "id": "uuid", "username": "trader123", "avatar_url": "..." },
        "last_message": {
          "content": "I'm interested in your Lightning Bolt",
          "sender_id": "uuid",
          "created_at": "2024-01-15T10:50:00Z"
        },
        "unread_count": 2,
        "last_message_at": "2024-01-15T10:50:00Z"
      }
    ]
  }
}
```

---

### GET /messages/conversations/{conversation_id}
Get conversation messages.

**Query Parameters:**
- `page`: integer
- `limit`: integer

**Response:** Array of messages

---

### POST /messages/conversations/{conversation_id}/messages
Send a message.

**Request:**
```json
{
  "content": "Hi, I'm interested in trading!",
  "listing_id": "uuid" // Optional: reference a listing
}
```

---

## Analytics Endpoints

### GET /analytics/portfolio/history
Get portfolio value history.

**Query Parameters:**
- `start_date`: date (ISO 8601)
- `end_date`: date
- `granularity`: "day" | "week" | "month" (default: "day")

**Response:**
```json
{
  "success": true,
  "data": {
    "snapshots": [
      { "date": "2024-01-01", "value": 1200.00, "card_count": 150 },
      { "date": "2024-01-08", "value": 1225.00, "card_count": 150 },
      { "date": "2024-01-15", "value": 1250.75, "card_count": 150 }
    ],
    "total_gain": 50.75,
    "total_gain_percentage": 4.23
  }
}
```
---

## Rate Limits

- **Authentication**: 5 requests/minute per IP
- **Scan Upload**: 10 requests/minute per user
- **General API**: 100 requests/minute per user
- **Search/Browse**: 1000 requests/minute per IP

Headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1642248000
```

---

## WebSocket Events

Connect: `wss://api.cardvault.app/v1/ws?token=<access_token>`

**Events:**
- `scan:status` - Scan processing updates
- `message:new` - New message received
- `alert:new` - New alert generated
- `trade:update` - Trade status changes

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 400 | Invalid input |
| `UNAUTHORIZED` | 401 | Missing/invalid token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `CONFLICT` | 409 | Resource conflict (e.g., duplicate) |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |
