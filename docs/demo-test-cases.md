# CardVault Demo Dataset & Test Cases

## Demo Dataset

### Test Card Sets (Magic: The Gathering)

**Core Set 2021 (M21)**
```json
{
  "set_id": "m21-uuid",
  "name": "Core Set 2021",
  "code": "M21",
  "game_type": "MTG",
  "release_date": "2020-07-03",
  "total_cards": 274,
  "sample_cards": [
    {
      "id": "lightning-bolt-m21",
      "name": "Lightning Bolt",
      "card_number": "161",
      "rarity": "Common",
      "card_type": "Instant",
      "normalized_name": "lightning bolt",
      "tcgplayer_id": "497329",
      "current_price": 15.50,
      "price_history": [
        { "date": "2024-01-01", "price": 14.00 },
        { "date": "2024-01-08", "price": 14.50 },
        { "date": "2024-01-15", "price": 15.50 }
      ]
    },
    {
      "id": "counterspell-m21",
      "name": "Counterspell",
      "card_number": "48",
      "rarity": "Common",
      "card_type": "Instant",
      "normalized_name": "counterspell",
      "tcgplayer_id": "497298",
      "current_price": 10.00,
      "price_history": [
        { "date": "2024-01-01", "price": 9.50 },
        { "date": "2024-01-15", "price": 10.00 }
      ]
    },
    {
      "id": "solemn-simulacrum-m21",
      "name": "Solemn Simulacrum",
      "card_number": "239",
      "rarity": "Rare",
      "card_type": "Artifact Creature",
      "normalized_name": "solemn simulacrum",
      "tcgplayer_id": "497367",
      "current_price": 8.00
    }
  ]
}
```

**Throne of Eldraine (ELD)**
```json
{
  "set_id": "eld-uuid",
  "name": "Throne of Eldraine",
  "code": "ELD",
  "game_type": "MTG",
  "release_date": "2019-10-04",
  "total_cards": 269,
  "sample_cards": [
    {
      "id": "oko-thief-of-crowns-eld",
      "name": "Oko, Thief of Crowns",
      "card_number": "197",
      "rarity": "Mythic Rare",
      "card_type": "Planeswalker",
      "normalized_name": "oko thief of crowns",
      "tcgplayer_id": "435185",
      "current_price": 45.00
    },
    {
      "id": "emry-lurker-of-the-loch-eld",
      "name": "Emry, Lurker of the Loch",
      "card_number": "43",
      "rarity": "Rare",
      "card_type": "Legendary Creature",
      "normalized_name": "emry lurker of the loch",
      "current_price": 12.00
    }
  ]
}
```

---

## Test Users

### User 1: Collector Alice
```json
{
  "id": "alice-uuid",
  "email": "alice@example.com",
  "username": "collector_alice",
  "inventory": [
    {
      "card_id": "lightning-bolt-m21",
      "quantity": 2,
      "condition": "Near Mint",
      "purchase_price": 10.00,
      "current_value": 15.50
    },
    {
      "card_id": "counterspell-m21",
      "quantity": 1,
      "condition": "Lightly Played",
      "purchase_price": 9.00,
      "current_value": 10.00
    }
  ],
  "want_list": [
    {
      "card_id": "oko-thief-of-crowns-eld",
      "min_condition": "Near Mint",
      "max_price": 50.00
    }
  ]
}
```

### User 2: Trader Bob
```json
{
  "id": "bob-uuid",
  "email": "bob@example.com",
  "username": "trader_bob",
  "inventory": [
    {
      "card_id": "oko-thief-of-crowns-eld",
      "quantity": 1,
      "condition": "Near Mint",
      "purchase_price": 35.00,
      "current_value": 45.00
    },
    {
      "card_id": "emry-lurker-of-the-loch-eld",
      "quantity": 3,
      "condition": "Near Mint",
      "purchase_price": 8.00,
      "current_value": 12.00
    }
  ],
  "listings": [
    {
      "card_id": "oko-thief-of-crowns-eld",
      "price": 47.00,
      "condition": "Near Mint",
      "quantity": 1,
      "status": "active"
    }
  ],
  "want_list": [
    {
      "card_id": "lightning-bolt-m21",
      "min_condition": "Near Mint",
      "max_price": 18.00
    }
  ]
}
```

---

## Integration Test Cases

### Test Case 1: Single Card Scan Flow

**Scenario**: User scans a single card and adds it to inventory.

**Steps**:
1. User logs in as Alice
2. Navigate to Scan page
3. Select "Single Card" scan type
4. Upload image of Lightning Bolt (M21)
5. Wait for scan to complete (<5s)
6. Verify detected card:
   - Set: "Core Set 2021" (M21)
   - Name: "Lightning Bolt"
   - Confidence: ≥85%
7. Set condition: "Near Mint"
8. Set quantity: 1
9. Click "Save to Inventory"
10. Verify card appears in inventory

**Expected Results**:
- Scan completes in <5s
- Card correctly identified (set + name)
- Card saved to inventory
- Inventory entry shows correct metadata

**Test Data**:
- Image: `test-data/cards/lightning-bolt-m21.jpg`
- Expected set: M21
- Expected name: "Lightning Bolt"

---

### Test Case 2: Multi-Card Scan Flow

**Scenario**: User scans image with multiple cards.

**Steps**:
1. User logs in as Alice
2. Navigate to Scan page
3. Select "Multiple Cards" scan type
4. Upload image containing 3 cards:
   - Lightning Bolt (M21)
   - Counterspell (M21)
   - Solemn Simulacrum (M21)
5. Wait for scan to complete (<30s)
6. Verify all 3 cards detected:
   - All bounding boxes shown
   - All cards correctly identified
7. Edit each card (condition, quantity)
8. Click "Save to Inventory"
9. Verify all 3 cards in inventory

**Expected Results**:
- All 3 cards detected (recall ≥90%)
- All cards correctly identified (accuracy ≥85%)
- All cards saved to inventory
- Processing completes in <30s

**Test Data**:
- Image: `test-data/multi-card/3-cards-m21.jpg`
- Expected cards: Lightning Bolt, Counterspell, Solemn Simulacrum

---

### Test Case 3: Price Alert Trigger

**Scenario**: Card price increases, alert is triggered.

**Steps**:
1. User logs in as Alice
2. Navigate to AI Agent page
3. Create alert rule:
   - Card: Lightning Bolt (M21)
   - Rule type: "Price Above"
   - Threshold: $16.00
4. Admin updates price feed:
   - Lightning Bolt price changes from $15.50 to $18.00
5. Background job evaluates alerts (runs hourly)
6. Alert generated and sent
7. User checks alerts page
8. Verify alert appears with correct information

**Expected Results**:
- Alert rule created successfully
- Alert triggered when price exceeds threshold
- Alert appears in user's alert list
- Alert shows correct old/new price

**Test Data**:
- Card: Lightning Bolt (M21)
- Initial price: $15.50
- Updated price: $18.00
- Threshold: $16.00

---

### Test Case 4: Marketplace Matching

**Scenario**: User's want list matches another user's listing.

**Steps**:
1. User logs in as Alice
   - Alice has Lightning Bolt in want list (max $18.00)
2. User logs in as Bob
   - Bob has Lightning Bolt listing ($17.00)
3. Background matching job runs (daily)
4. Match created: Alice's want → Bob's listing
5. Alice checks matches page
6. Verify match appears with Bob's listing
7. Alice clicks "Contact Seller"
8. Verify messaging interface opens

**Expected Results**:
- Match found between Alice's want and Bob's listing
- Match appears in Alice's matches
- Alice can contact Bob via messaging

**Test Data**:
- Alice wants: Lightning Bolt, max $18.00
- Bob has: Lightning Bolt listing, $17.00

---

### Test Case 5: Trade Workflow

**Scenario**: Users create and complete a trade.

**Steps**:
1. User logs in as Alice
   - Alice has: Counterspell (M21), wants: Oko
2. User logs in as Bob
   - Bob has: Oko (ELD), wants: Lightning Bolt or Counterspell
3. Alice creates trade offer:
   - Gives: Counterspell (M21)
   - Receives: Oko (ELD) from Bob
4. Bob receives notification
5. Bob views trade offer
6. Bob accepts trade
7. Trade status changes to "Accepted"
8. Both users see trade in history

**Expected Results**:
- Trade created successfully
- Bob receives notification
- Bob can view and accept trade
- Trade status updates correctly
- Trade visible in both users' histories

**Test Data**:
- Alice gives: Counterspell (M21) ≈ $10.00
- Bob gives: Oko (ELD) ≈ $45.00
- Note: Value imbalance acceptable for testing

---

## ML Model Test Cases

### Test Case 6: Card Detection Accuracy

**Test Data**: 100 test images (various card arrangements)
- 50 single-card images
- 50 multi-card images (2-10 cards per image)

**Expected Results**:
- Detection recall ≥90% (≥90 of 100 cards detected)
- False positive rate <10% (≤10 false detections per 100 images)
- Bounding box IoU ≥0.7 (accurate localization)

**Evaluation Metrics**:
- mAP@0.5 ≥0.90
- Recall ≥0.90
- Precision ≥0.85

---

### Test Case 7: Card Classification Accuracy

**Test Data**: 500 test images (100 cards × 5 images each)
- Cards from 10 different sets
- Various conditions (NM, LP, MP)
- Various lighting conditions

**Expected Results**:
- Top-1 accuracy ≥85% (≥425 of 500 correctly classified)
- Top-3 accuracy ≥95% (≥475 of 500 in top 3)
- Per-set accuracy ≥80% (each set ≥80% accurate)

**Evaluation Metrics**:
- Overall accuracy: ≥85%
- Per-set accuracy: ≥80%
- Per-condition accuracy: ≥75%

---

### Test Case 8: Condition Grading Accuracy

**Test Data**: 200 test images with expert-labeled conditions
- 40 Near Mint (9.0-10.0)
- 40 Lightly Played (7.0-8.9)
- 40 Moderately Played (5.0-6.9)
- 40 Heavily Played (3.0-4.9)
- 40 Damaged (1.0-2.9)

**Expected Results**:
- MAE <1.0 grade (within 1 grade of expert)
- Within 1 grade accuracy ≥75% (≥150 of 200)
- Per-condition accuracy ≥70%

**Evaluation Metrics**:
- MAE: <1.0
- Within 1 grade: ≥75%
- Exact match: ≥60%

---

## API Test Cases

### Test Case 9: Authentication Flow

**Request**: `POST /auth/register`
```json
{
  "email": "test@example.com",
  "password": "SecurePass123!",
  "username": "testuser"
}
```

**Expected Response**: 201 Created
```json
{
  "success": true,
  "data": {
    "user": { "id": "uuid", "email": "test@example.com", "username": "testuser" },
    "message": "Verification email sent"
  }
}
```

---

### Test Case 10: Scan Upload

**Request**: `POST /scans/upload` (multipart form-data)
- `image`: test image file
- `scan_type`: "single"

**Expected Response**: 202 Accepted
```json
{
  "success": true,
  "data": {
    "scan_id": "uuid",
    "status": "pending",
    "estimated_processing_time_seconds": 5
  }
}
```

---

### Test Case 11: Inventory Retrieval

**Request**: `GET /inventory?page=1&limit=50`

**Expected Response**: 200 OK
```json
{
  "success": true,
  "data": {
    "items": [ ... ],
    "pagination": { "page": 1, "limit": 50, "total": 10, "total_pages": 1 }
  }
}
```

---

## Load Test Cases

### Test Case 12: Concurrent Scan Uploads

**Scenario**: 100 concurrent users upload scans simultaneously.

**Expected Results**:
- All uploads accepted (202 Accepted)
- Processing completes within 5 minutes
- No crashes or errors
- API latency <500ms (p95) for upload endpoint

---

### Test Case 13: Database Query Performance

**Scenario**: 1000 inventory entries, query with filters.

**Request**: `GET /inventory?search=lightning&condition=Near+Mint&sort_by=value`

**Expected Results**:
- Query completes in <200ms (p95)
- Results are correct
- Database CPU <80%

---

## Security Test Cases

### Test Case 14: Authentication Bypass

**Scenario**: Attempt to access protected endpoint without token.

**Request**: `GET /inventory` (no Authorization header)

**Expected Response**: 401 Unauthorized
```json
{
  "success": false,
  "error": { "code": "UNAUTHORIZED", "message": "Missing or invalid token" }
}
```

---

### Test Case 15: SQL Injection

**Scenario**: Attempt SQL injection in search parameter.

**Request**: `GET /inventory?search='; DROP TABLE users; --`

**Expected Results**:
- Request rejected (400 Bad Request)
- No database changes
- Error logged

---

### Test Case 16: XSS Prevention

**Scenario**: Attempt XSS in user input.

**Request**: `POST /marketplace/listings`
```json
{
  "title": "<script>alert('XSS')</script>",
  "description": "Test"
}
```

**Expected Results**:
- HTML tags sanitized
- No script execution
- Safe content saved to database

---

## Demo Script

### 5-Minute Demo Flow

1. **Login/Register** (30s)
   - Register new user or login
   - Show dashboard

2. **Scan Single Card** (1 min)
   - Upload Lightning Bolt image
   - Show detection → classification → confirmation
   - Save to inventory

3. **View Inventory** (30s)
   - Show inventory page
   - Display card with value
   - Filter by set/condition

4. **Create Listing** (30s)
   - Create listing from inventory
   - Set price, condition
   - Show in marketplace

5. **Marketplace Search** (30s)
   - Search for cards
   - View listings
   - Show matching

6. **AI Agent Alerts** (30s)
   - Show alert dashboard
   - Demonstrate price alert
   - Show suggestions

7. **Trade Flow** (2 min)
   - Create trade offer
   - Accept trade
   - Show trade history

---

## Test Data Files

### Image Files

- `test-data/cards/single/lightning-bolt-m21.jpg` - Single Lightning Bolt
- `test-data/cards/single/counterspell-m21.jpg` - Single Counterspell
- `test-data/cards/multi/3-cards-m21.jpg` - 3 cards (arranged)
- `test-data/cards/multi/scattered-5-cards.jpg` - 5 cards (scattered)

### JSON Files

- `test-data/sets/m21.json` - Core Set 2021 metadata
- `test-data/users/alice.json` - Test user Alice
- `test-data/users/bob.json` - Test user Bob

---

## Performance Benchmarks

### Target Metrics

| Metric | Target | Test Result |
|--------|--------|-------------|
| Scan upload latency | <1s | [TBD] |
| Scan processing (single) | <5s | [TBD] |
| Scan processing (multi, 10 cards) | <30s | [TBD] |
| API response time (p95) | <200ms | [TBD] |
| Page load time (p95) | <2s | [TBD] |
| Database query time | <100ms | [TBD] |
| ML inference latency | <500ms | [TBD] |
| Card detection recall | ≥90% | [TBD] |
| Card classification accuracy | ≥85% | [TBD] |

---

## Acceptance Criteria Checklist

- [ ] All P0 features tested and working
- [ ] All integration tests pass
- [ ] All security tests pass
- [ ] Performance benchmarks met
- [ ] ML model accuracy targets met
- [ ] Demo script works end-to-end
- [ ] User documentation reviewed
- [ ] Security audit completed
- [ ] Load testing completed (1000 concurrent users)
