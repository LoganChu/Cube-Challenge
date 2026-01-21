# CardVault Marketplace Matching Algorithm

## Overview

The marketplace matching algorithm facilitates two-way matching: finding cards users want (wants) that other users have (listings/haves), and suggesting value-balanced trades.

---

## Matching Types

### 1. Direct Matching (Want → Listing)

**Goal**: Match user A's want list with user B's active listings.

**Algorithm**:
```
For each want in User A's wants:
  1. Search listings for:
     - card_id match (exact)
     - set_id match (if card_id unavailable)
     - normalized_name match (fuzzy)
  2. Filter by:
     - condition >= want.min_condition
     - price <= want.max_price (if specified)
     - seller != User A
     - listing.status == 'active'
  3. Rank by:
     - Exact match (card_id) > set match > name match
     - Price proximity (if price specified)
     - Seller rating
  4. Return top 10 matches
```

**Complexity**: O(W × L) where W = wants, L = listings
**Optimization**: Use Elasticsearch or PostgreSQL GIN index for fast text matching

---

### 2. Fuzzy Matching (Similar Cards)

**Goal**: Match similar cards (same card name, different sets/printings).

**Algorithm**:
```
1. Normalize card names:
   - Lowercase
   - Remove special characters
   - Expand abbreviations ("Lightning Bolt" = "Lightning Bolt")
   - Handle variants ("Lightning Bolt" vs "Lightning Bolt (Showcase)")

2. Use Levenshtein distance or Jaccard similarity:
   - If similarity >= 0.85: consider match
   - Weight by set similarity (same set = higher score)

3. Return matches with similarity score
```

**Example**:
- Want: "Lightning Bolt" (Core Set 2021)
- Match: "Lightning Bolt" (Throne of Eldraine) → 90% similarity
- Match: "Lightning Strike" → 70% similarity (excluded)

---

### 3. Value-Balanced Trade Suggestions

**Goal**: Suggest trades where both parties benefit (balanced value).

**Algorithm**:
```
For User A (initiator):
  1. Get User A's wants (W_A)
  2. Get User A's haves (listings/inventory they're willing to trade)
  3. For each potential match User B:
      a. Get User B's wants (W_B)
      b. Get User B's haves (listings/inventory)
      c. Find intersection: W_A ∩ H_B (User A wants, User B has)
      d. Find intersection: W_B ∩ H_A (User B wants, User A has)
      e. If both intersections non-empty:
         - Calculate value of trade:
           * Value_A_gives = sum(H_A ∩ W_B)
           * Value_A_receives = sum(H_B ∩ W_A)
           * Balance = |Value_A_gives - Value_A_receives| / max(Value_A_gives, Value_A_receives)
         - If Balance <= 0.15 (within 15%): suggest trade
         - Score = (card_match_count × 2) - (balance_penalty × 100)
  4. Return top 20 matches sorted by score
```

**Example**:
- User A wants: Lightning Bolt ($15), Counterspell ($10)
- User A has: Sol Ring ($20), Demonic Tutor ($18)
- User B wants: Sol Ring ($20)
- User B has: Lightning Bolt ($15), Counterspell ($10)
- Match: User A gives Sol Ring ($20), receives Lightning Bolt + Counterspell ($25)
- Balance: |20 - 25| / 25 = 0.20 (20% imbalance) → still suggest (threshold: 15%, but close)

---

### 4. Multi-Card Trade Matching

**Goal**: Suggest trades involving multiple cards (package deals).

**Algorithm**:
```
1. Build candidate sets:
   - User A wants: [Card1, Card2, Card3]
   - User B has: [Card1, Card2, Card3, Card4]

2. Use combinatorial matching:
   - Generate all valid subsets of User B's cards that match User A's wants
   - For each subset, check if User B wants any of User A's cards
   - Calculate value balance

3. Optimize for:
   - Maximum card matches
   - Minimum value imbalance
   - Minimum number of cards (simpler trades preferred)

4. Use greedy algorithm or dynamic programming (if <10 cards)
```

**Complexity**: O(2^N) worst case (N = number of cards)
**Optimization**: Limit to top 5-10 wants/haves per user, prune early

---

## Heuristics

### Match Score Calculation

```
match_score = (
    card_match_weight × exact_card_match +
    set_match_weight × set_match +
    name_match_weight × fuzzy_name_match +
    condition_match_weight × condition_match +
    price_match_weight × price_proximity +
    seller_rating_weight × seller_rating_normalized
) / total_weights
```

**Weights** (configurable):
- `card_match_weight`: 100 (exact card match)
- `set_match_weight`: 50 (same set, different card)
- `name_match_weight`: 30 (fuzzy name match)
- `condition_match_weight`: 20 (condition match bonus)
- `price_match_weight`: 10 (price within 10% bonus)
- `seller_rating_weight`: 10 (high-rated seller bonus)

### Normalized Name Matching

**Steps**:
1. Lowercase
2. Remove punctuation (hyphens, apostrophes)
3. Remove stop words ("the", "a", "of")
4. Expand abbreviations:
   - "Lt. Bolt" → "Lightning Bolt"
   - "Counterspell" → "Counterspell"
5. Handle variants:
   - "Lightning Bolt (Showcase)" → "Lightning Bolt"
   - "Lightning Bolt [Foil]" → "Lightning Bolt"

**Similarity Metrics**:
- **Levenshtein Distance**: Character-level edits
- **Jaccard Similarity**: Set-based (words)
- **TF-IDF Cosine Similarity**: Term frequency-inverse document frequency

**Recommendation**: Use **Jaccard Similarity** (simple, fast, good for card names).

---

## Search Implementation

### Database Query (PostgreSQL)

```sql
-- Direct matching (exact card_id)
SELECT l.*, w.id as want_id
FROM listings l
JOIN wants w ON l.card_id = w.card_id
WHERE w.user_id = $1
  AND l.status = 'active'
  AND l.user_id != $1
  AND (w.min_condition IS NULL OR l.condition >= w.min_condition)
  AND (w.max_price IS NULL OR l.price <= w.max_price);

-- Fuzzy matching (normalized name)
SELECT l.*, w.id as want_id,
       similarity(l.card_name_normalized, w.card_name_normalized) as match_score
FROM listings l
JOIN wants w ON similarity(l.card_name_normalized, w.card_name_normalized) > 0.85
WHERE w.user_id = $1
  AND l.status = 'active'
ORDER BY match_score DESC;
```

### Full-Text Search (Elasticsearch - Optional)

```json
{
  "query": {
    "bool": {
      "must": [
        { "match": { "card_name": "Lightning Bolt" } }
      ],
      "filter": [
        { "term": { "status": "active" } },
        { "range": { "price": { "lte": 20 } } }
      ]
    }
  },
  "sort": [
    { "_score": "desc" },
    { "seller_rating": "desc" }
  ]
}
```

---

## Matching Service Architecture

### Components

1. **Match Engine**: Core matching logic (described above)
2. **Notification Service**: Send notifications when matches found
3. **Match Cache**: Cache recent matches (TTL: 1 hour)
4. **Background Job**: Run matching daily for all users

### Workflow

```
1. User creates/updates want list
   ↓
2. Trigger immediate matching job (async)
   ↓
3. Match Engine runs matching algorithms
   ↓
4. Store matches in trade_matches table
   ↓
5. Notification Service sends alerts
   ↓
6. User views matches in dashboard
```

### Performance Optimization

- **Batch Processing**: Match all users overnight (low-priority job)
- **Incremental Updates**: When new listing created, match against all want lists
- **Caching**: Cache match results (Redis) for 1 hour
- **Indexing**: Ensure proper database indexes on card_id, normalized_name, set_id

---

## Match Quality Metrics

### Evaluation

- **Precision**: % of suggested matches that user finds relevant (target: ≥80%)
- **Recall**: % of actual matches found (target: ≥90%)
- **Match Conversion**: % of matches that lead to trades (target: ≥10%)

### A/B Testing

- Test different similarity thresholds (0.80 vs 0.85)
- Test different value balance thresholds (10% vs 15%)
- Test ranking algorithms (card match priority vs price priority)

---

## User Controls

Users can customize matching preferences:
- **Fuzzy Match Tolerance**: Enable/disable fuzzy matching
- **Value Balance Threshold**: Max acceptable imbalance (default: 15%)
- **Minimum Match Score**: Only show matches above threshold
- **Preferred Sellers**: Prioritize matches from specific sellers
- **Exclude Sellers**: Ignore matches from specific sellers

---

## Trade Suggestion Ranking

Final ranking formula:
```
final_score = (
    match_score × 0.4 +
    value_balance_score × 0.3 +
    seller_rating_score × 0.2 +
    trade_complexity_penalty × 0.1
)
```

- **match_score**: How well cards match (0-100)
- **value_balance_score**: How balanced the trade is (0-100, higher = more balanced)
- **seller_rating_score**: Seller reputation (0-100)
- **trade_complexity_penalty**: Penalty for multi-card trades (0-100, lower = simpler)

Return top 20 suggestions sorted by final_score.
