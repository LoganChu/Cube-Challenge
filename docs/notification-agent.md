# CardVault Notification & AI Agent Rule Engine

## Overview

The notification and agent system monitors user portfolios, price changes, and marketplace activity, generating alerts and AI-driven suggestions based on configurable rules.

---

## Notification Types

### 1. Price Alerts
- **Price Above Threshold**: Card value exceeds user-defined threshold
- **Price Below Threshold**: Card value drops below threshold
- **Price Change**: Percentage change (e.g., +20% or -15%)

### 2. Portfolio Alerts
- **Portfolio Value Change**: Total portfolio value changes significantly
- **New High**: Portfolio reaches new all-time high
- **New Low**: Portfolio drops below recent low

### 3. Marketplace Alerts
- **Want List Match**: Card on want list is available
- **Trade Suggestion**: New trade opportunity found
- **Listing Update**: User's listing receives offer or message

### 4. AI Agent Suggestions
- **Sell Recommendation**: Price spike detected, suggest selling
- **Buy Recommendation**: Price dip detected, suggest buying
- **Hold Recommendation**: Price stable, suggest holding
- **Trade Recommendation**: Value-balanced trade opportunity

---

## Rule Engine Design

### Rule Structure

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "rule_type": "price_above",
  "target_type": "card", // "card", "set", "portfolio"
  "target_id": "uuid", // card_id, set_id, or null for portfolio
  "condition": {
    "threshold_value": 20.00,
    "threshold_percentage": null,
    "time_window_days": 7
  },
  "action": {
    "notification_channels": ["email", "push", "in_app"],
    "severity": "info", // "info", "warning", "urgent"
    "message_template": "Your {card_name} is now worth ${price} (was ${old_price})"
  },
  "is_active": true,
  "created_at": "2024-01-15T10:00:00Z",
  "last_triggered_at": "2024-01-15T11:00:00Z"
}
```

### Rule Types

#### 1. Price Above Threshold
```
IF card.current_value > rule.threshold_value
   AND card.current_value > card.last_valuated_price (prevents duplicates)
THEN trigger alert
```

#### 2. Price Below Threshold
```
IF card.current_value < rule.threshold_value
   AND card.current_value < card.last_valuated_price
THEN trigger alert
```

#### 3. Price Change Percentage
```
IF |(card.current_value - card.last_valuated_price) / card.last_valuated_price| >= rule.threshold_percentage
THEN trigger alert
```

#### 4. Portfolio Value Change
```
IF |portfolio.current_value - portfolio.previous_value| / portfolio.previous_value >= rule.threshold_percentage
THEN trigger alert
```

---

## Evaluation Engine

### Execution Flow

```
1. Price Feed Service updates card valuations (hourly/daily)
   ↓
2. Trigger evaluation job for all active alert rules
   ↓
3. For each rule:
   a. Load rule configuration
   b. Fetch target data (card, set, portfolio)
   c. Evaluate rule condition
   d. If condition met:
      - Create alert record
      - Enqueue notification job
   ↓
4. Notification Service processes jobs:
   a. Render message template
   b. Send via configured channels (email, push, in_app)
   c. Mark alert as sent
```

### Rule Evaluation Algorithm

```python
def evaluate_rule(rule: AlertRule, context: Dict) -> bool:
    """Evaluate if rule condition is met."""
    
    if rule.rule_type == "price_above":
        current_value = get_card_value(rule.target_id)
        return current_value > rule.threshold_value
    
    elif rule.rule_type == "price_below":
        current_value = get_card_value(rule.target_id)
        return current_value < rule.threshold_value
    
    elif rule.rule_type == "price_change_pct":
        current_value = get_card_value(rule.target_id)
        previous_value = get_previous_value(rule.target_id, days=rule.time_window_days)
        if previous_value is None:
            return False
        change_pct = abs((current_value - previous_value) / previous_value) * 100
        return change_pct >= rule.threshold_percentage
    
    elif rule.rule_type == "portfolio_value_change":
        current_value = get_portfolio_value(rule.user_id)
        previous_value = get_previous_portfolio_value(rule.user_id, days=1)
        if previous_value is None:
            return False
        change_pct = abs((current_value - previous_value) / previous_value) * 100
        return change_pct >= rule.threshold_percentage
    
    return False
```

---

## AI Agent Suggestions

### Suggestion Types

#### 1. Sell Recommendation
**Trigger**: Price spike detected (e.g., +25% in 7 days)

**Algorithm**:
```
1. Get card's price history (last 90 days)
2. Calculate trend (linear regression slope)
3. If trend > 0 AND recent_change > 25%:
   - Calculate momentum: (current_price - price_30d_ago) / price_30d_ago
   - If momentum > 0.3: suggest sell (high confidence)
   - If momentum 0.15-0.3: suggest sell (medium confidence)
4. Generate reasoning: "Price increased 30% in 7 days. Historical data suggests potential dip."
5. Project future value (30-day forecast)
```

**Reasoning Template**:
```
"Your {card_name} has increased {change_pct}% in the last {days} days, 
from ${old_price} to ${new_price}. Historical data suggests this card 
may dip in the next 30 days (projected: ${projected_price}). 
Consider selling to lock in gains."
```

#### 2. Buy Recommendation
**Trigger**: Price dip detected (e.g., -20% in 7 days) AND card on want list

**Algorithm**:
```
1. Check if card is on user's want list
2. If price dropped >20% in 7 days:
   - Check if price near recent low (bottom 25th percentile)
   - If yes: suggest buy
3. Calculate value: current_price vs historical_average
4. Generate reasoning: "Price dipped below average. Good buying opportunity."
```

#### 3. Hold Recommendation
**Trigger**: Price stable, long-term value potential

**Algorithm**:
```
1. If price change <5% in 30 days:
   - Check long-term trend (90+ days)
   - If trend positive: suggest hold
   - Reasoning: "Price stable, long-term upward trend. Hold for future gains."
```

#### 4. Trade Recommendation
**Trigger**: Value-balanced trade match found

**Algorithm**:
```
1. Use marketplace matching algorithm
2. If match found with value balance <= 15%:
   - Generate suggestion
   - Reasoning: "Trade opportunity: {your_cards} for {their_cards}. Value balanced."
```

---

## Suggestion Generation Pipeline

### ML-Based Suggestions (Post-MVP)

**Model**: Time series forecasting (LSTM or Transformer)

**Inputs**:
- Card price history (180 days)
- Card features (set, rarity, popularity, condition)
- Market trends (overall card market index)
- User portfolio composition

**Outputs**:
- Price forecast (30/60/90 days)
- Confidence interval
- Recommendation (sell/hold/buy)
- Confidence score (0-100)

**Training Data**:
- Historical price data (5+ years)
- Labeled decisions (if available): "Did price go up/down after recommendation?"

**Evaluation**:
- **Direction Accuracy**: % of correct up/down predictions (target: ≥60%)
- **MAE**: Mean absolute error (target: <15% of actual price)

---

## Notification Channels

### Email
- **Provider**: SendGrid, Resend, or AWS SES
- **Template Engine**: Jinja2 or Handlebars
- **Frequency**: Daily digest (batch all alerts) or immediate (urgent only)

**Email Template Example**:
```html
<h2>Price Alert: {{ card_name }}</h2>
<p>Your {{ card_name }} ({{ set_name }}) is now worth <strong>${{ current_price }}</strong> 
   (was ${{ old_price }}, {{ change_pct }}% change).</p>
<p><a href="{{ card_url }}">View Card</a></p>
```

### Push Notifications
- **Provider**: Firebase Cloud Messaging (FCM) or OneSignal
- **Frequency**: Immediate (all alerts)
- **Opt-in**: User must enable push notifications

**Push Payload**:
```json
{
  "title": "Price Alert: Lightning Bolt",
  "body": "Your Lightning Bolt is now worth $18.00 (+16%)",
  "data": {
    "type": "price_alert",
    "card_id": "uuid",
    "alert_id": "uuid"
  }
}
```

### In-App Notifications
- **Storage**: Database table `alerts`
- **Delivery**: WebSocket or polling (every 30s)
- **UI**: Notification bell icon with badge count

---

## Cadence & Scheduling

### Evaluation Frequency

- **Price Alerts**: Evaluate after each price feed update (hourly/daily)
- **Portfolio Alerts**: Evaluate daily (after price feed)
- **Marketplace Alerts**: Evaluate in real-time (when listing created)
- **AI Suggestions**: Generate daily (batch job)

### Notification Frequency Limits

**Per-User Limits**:
- **Email**: Max 1 digest per day (batch all alerts)
- **Push**: Max 10 per day (urgent only after limit)
- **In-App**: Unlimited (user controls visibility)

**Deduplication**:
- **Cooldown**: Same alert type for same card: 24 hours
- **Throttling**: Max 1 alert per card per day (except urgent)

---

## User Controls

### Notification Preferences

Users can configure:
- **Enable/Disable**: Per alert type (price, portfolio, marketplace, AI)
- **Channels**: Email, push, in-app (per alert type)
- **Frequency**: Immediate, daily digest, weekly digest
- **Thresholds**: Minimum price change to trigger (e.g., only if >10%)

### Alert Management

- **View All Alerts**: Dashboard shows all alerts (read/unread)
- **Dismiss Alerts**: Mark as read or dismiss permanently
- **Snooze**: Temporarily disable specific alert rules
- **Delete Rules**: Remove alert rules

---

## Performance Optimization

### Batch Processing

- **Evaluation**: Process all rules in batches (1000 rules per batch)
- **Notifications**: Batch email sends (daily digest)
- **Caching**: Cache card values (Redis, TTL: 5 minutes)

### Database Optimization

- **Indexes**: `alert_rules.user_id`, `alert_rules.is_active`, `alerts.user_id`, `alerts.read_at`
- **Partitioning**: `alerts` table partitioned by `created_at` (monthly)
- **Cleanup**: Archive old alerts (>90 days) to cold storage

---

## Monitoring & Metrics

### Key Metrics

- **Alert Generation Rate**: Alerts generated per day
- **Notification Delivery Rate**: % successfully delivered
- **User Engagement**: % of users who view/dismiss alerts
- **False Positive Rate**: % of alerts user dismisses immediately

### A/B Testing

- Test different alert thresholds (10% vs 15% price change)
- Test notification cadence (immediate vs daily digest)
- Test AI suggestion confidence thresholds

---

## Example Rules

### Example 1: Price Above $20
```json
{
  "rule_type": "price_above",
  "target_type": "card",
  "target_id": "lightning-bolt-uuid",
  "threshold_value": 20.00,
  "notification_channels": ["email", "push"],
  "severity": "info"
}
```

### Example 2: 20% Price Increase
```json
{
  "rule_type": "price_change_pct",
  "target_type": "card",
  "target_id": "lightning-bolt-uuid",
  "threshold_percentage": 20.0,
  "time_window_days": 7,
  "notification_channels": ["email", "push", "in_app"],
  "severity": "warning"
}
```

### Example 3: Portfolio Drops 10%
```json
{
  "rule_type": "portfolio_value_change",
  "target_type": "portfolio",
  "threshold_percentage": 10.0,
  "notification_channels": ["email"],
  "severity": "warning"
}
```
