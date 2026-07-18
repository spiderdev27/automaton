# GemTrade Google Cloud Architecture

## Overview

GemTrade leverages Google Cloud services to build a cost-effective, intelligent trading system. This document outlines the architecture and how to maximize your Google Cloud credits.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GemTrade Intelligence Layer                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│  │   News Scanner   │     │ Sentiment Analyzer│     │  Deep Reasoner   │    │
│  │                  │     │                  │     │                  │    │
│  │  - RSS Feeds     │     │  - Social Media  │     │  - Multi-hop     │    │
│  │  - Web Search    │     │  - Reddit/X      │     │  - Contrarian    │    │
│  │  - Econ Calendar │     │  - FinBERT       │     │  - Indirect      │    │
│  └────────┬─────────┘     └────────┬─────────┘     └────────┬─────────┘    │
│           │                        │                        │               │
│           └────────────────────────┼────────────────────────┘               │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Gemini API with Web Search Grounding              │   │
│  │                                                                      │   │
│  │   • Real-time news via Google Search                                │   │
│  │   • Function calling for trading operations                          │   │
│  │   • Structured JSON output for signal parsing                        │   │
│  │   • Cost optimization via 5-minute response caching                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
└────────────────────────────────────┼────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           GemTrade Trading Core                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐     ┌──────────────────┐     ┌──────────────────┐    │
│  │   Constitution   │     │  Survival Mgr    │     │ Adaptive Risk    │    │
│  │                  │     │                  │     │                  │    │
│  │  - Immutable     │     │  - Tier System   │     │  - Signal Score  │    │
│  │  - Risk Limits   │     │  - Auto-adjust   │     │  - Mid-trade Adj │    │
│  │  - Circuit Break │     │  - Recovery      │     │  - News Trading  │    │
│  └──────────────────┘     └──────────────────┘     └──────────────────┘    │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                         Exchange Connectors                          │  │
│  │     Delta Exchange  │  MT5  │  Paper Trading  │  OANDA              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Google Cloud Storage Layer                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                          BigQuery (Free Tier)                        │  │
│  │                                                                      │  │
│  │   Tables:                          │   Analytics:                    │  │
│  │   • trades (trade records)         │   • Performance metrics         │  │
│  │   • signals (intelligence)         │   • Signal accuracy             │  │
│  │   • patterns (learned)             │   • Pattern discovery           │  │
│  │                                    │   • Equity curves               │  │
│  │                                                                      │  │
│  │   Free: 1 TB queries/month + 10 GB storage                          │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Google Cloud Services Used

### 1. Gemini API with Web Search Grounding

**Purpose**: Real-time market intelligence with verifiable sources

**Features**:
- **Web Search Grounding**: Gemini can search Google and cite sources
- **Function Calling**: Structured output for reliable signal parsing
- **Multi-model Support**: Flash for speed, Pro for deep reasoning

**Cost Optimization**:
```python
# Free tier limits (per day)
GEMINI_FREE_TIER = {
    "gemini-3-flash": {"rpm": 10, "rpd": 1500, "tpm": 250000},
    "gemini-2.5-flash": {"rpm": 15, "rpd": 1500, "tpm": 1000000},
    "gemini-2.5-flash-lite": {"rpm": 30, "rpd": 1500, "tpm": 1000000},
}

# Our usage pattern
GEMTRADE_DAILY_USAGE = {
    "news_scans": 48,        # Every 30 min = 48/day
    "sentiment_checks": 24,   # Every hour = 24/day
    "deep_research": 4,       # 4 deep dives/day
    "contrarian_analysis": 6, # 6 contrarian checks/day
    # Total: ~82 requests/day (well within 1500/day limit)
}
```

**Implementation**:
```python
from gemtrade.cloud import GeminiIntelligence, IntelligenceQuery

# Initialize (uses GOOGLE_API_KEY env var)
intelligence = GeminiIntelligence()

# Get market intelligence
query = IntelligenceQuery(
    symbols=["XAUUSD"],
    timeframe="last 6 hours",
    include_indirect=True,
    include_contrarian=True,
)

result = await intelligence.gather_intelligence(query)

# Access signals
for symbol, direction in result.signals.items():
    confidence = result.confidence_scores[symbol]
    print(f"{symbol}: {direction.value} ({confidence:.0%})")
```

### 2. BigQuery

**Purpose**: Trade data warehouse and analytics

**Free Tier**:
- 1 TB of queries per month
- 10 GB of storage per month
- US regions only for free tier

**Tables**:
```sql
-- trades table
CREATE TABLE gemtrade.trades (
    trade_id STRING,
    symbol STRING,
    side STRING,  -- "long" or "short"
    entry_time TIMESTAMP,
    entry_price FLOAT64,
    exit_time TIMESTAMP,
    exit_price FLOAT64,
    pnl_paise INT64,
    strategy STRING,
    -- ... more fields
);

-- signals table  
CREATE TABLE gemtrade.signals (
    signal_id STRING,
    symbol STRING,
    signal_type STRING,
    direction STRING,
    confidence FLOAT64,
    outcome_correct BOOL,
    -- ... more fields
);
```

**Usage**:
```python
from gemtrade.cloud import BigQueryStore, TradeRecord

store = BigQueryStore(project_id="your-project")

# Log a trade
trade = TradeRecord(
    trade_id="trade_001",
    symbol="XAUUSD",
    side="long",
    entry_time=datetime.utcnow(),
    entry_price=2450.50,
    entry_reason="Strong bullish sentiment + Fed dovish",
)
store.insert_trade(trade)

# Get performance metrics
metrics = store.get_performance_metrics(
    start_date=datetime(2026, 1, 1),
    end_date=datetime.utcnow(),
)
print(f"Win rate: {metrics.win_rate:.1%}")
print(f"Profit factor: {metrics.profit_factor:.2f}")

# Find best patterns
patterns = store.get_best_performing_patterns(
    min_occurrences=5,
    min_win_rate=0.6,
)
```

### 3. Cloud Run (Optional)

**Purpose**: Serverless container hosting for the trading agent

**Free Tier**:
- 2 million requests/month
- 360,000 GB-seconds of memory
- 180,000 vCPU-seconds

**Use Case**: Deploy GemTrade as a serverless service

```yaml
# cloud-run-config.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: gemtrade
spec:
  template:
    spec:
      containers:
        - image: gcr.io/your-project/gemtrade
          resources:
            limits:
              memory: 1Gi
              cpu: "1"
          env:
            - name: GOOGLE_API_KEY
              valueFrom:
                secretKeyRef:
                  name: gemtrade-secrets
                  key: gemini-api-key
```

### 4. Cloud Functions (Optional)

**Purpose**: Event-driven triggers and scheduled tasks

**Free Tier**:
- 2 million invocations/month
- 400,000 GB-seconds compute time

**Use Cases**:
- Scheduled intelligence gathering
- Webhook handlers for exchange events
- Alert notifications

```python
# cloud_function.py
import functions_framework
from gemtrade.cloud import GeminiIntelligence

@functions_framework.cloud_event
async def gather_intelligence(cloud_event):
    """Scheduled function to gather market intelligence."""
    intelligence = GeminiIntelligence()
    
    result = await intelligence.gather_intelligence(
        IntelligenceQuery(symbols=["XAUUSD"], timeframe="last 30 minutes")
    )
    
    # Store results, trigger alerts if needed
    for insight in result.get_actionable_insights(min_confidence=0.7):
        if insight.direction in [SignalDirection.STRONG_BUY, SignalDirection.STRONG_SELL]:
            # Trigger alert or trade
            pass
```

## Cost Estimation

### Scenario: Active Trading (INR 5,000 capital)

| Service | Usage | Free Tier | Est. Monthly Cost |
|---------|-------|-----------|-------------------|
| Gemini API (Flash) | ~2,500 requests | 45,000/month | ₹0 |
| BigQuery Queries | ~10 GB | 1,000 GB | ₹0 |
| BigQuery Storage | ~1 GB | 10 GB | ₹0 |
| Cloud Run | ~500K requests | 2M | ₹0 |
| **Total** | | | **₹0** |

### Beyond Free Tier (if needed)

| Service | Price | Notes |
|---------|-------|-------|
| Gemini 2.5 Flash | $0.15/1M input tokens | Very cheap |
| Gemini 2.5 Pro | $1.25/1M input tokens | Use sparingly |
| BigQuery | $5/TB queried | Optimize queries |
| Cloud Run | $0.00002/request | After free tier |

## Implementation Guide

### Step 1: Set Up Google Cloud Project

```bash
# Install gcloud CLI
curl https://sdk.cloud.google.com | bash

# Authenticate
gcloud auth login
gcloud auth application-default login

# Create project
gcloud projects create gemtrade-prod
gcloud config set project gemtrade-prod

# Enable APIs
gcloud services enable \
    aiplatform.googleapis.com \
    bigquery.googleapis.com \
    cloudfunctions.googleapis.com \
    run.googleapis.com
```

### Step 2: Get Gemini API Key

```bash
# Option A: Google AI Studio (simpler, free tier)
# Go to: https://aistudio.google.com/apikey

# Option B: Vertex AI (enterprise, uses credits)
# API key is tied to your GCP project
```

### Step 3: Configure GemTrade

```python
# config.py
import os

# Gemini
os.environ["GOOGLE_API_KEY"] = "your-api-key"

# BigQuery
os.environ["GOOGLE_CLOUD_PROJECT"] = "gemtrade-prod"

# GemTrade settings
from gemtrade.cloud import GeminiConfig

config = GeminiConfig(
    default_model=GeminiModel.FLASH,      # Fast and cheap
    reasoning_model=GeminiModel.PRO,       # For deep analysis
    enable_grounding=True,                 # Web search
    cache_ttl_seconds=300,                 # 5 min cache
    rate_limit_rpm=10,                     # Free tier limit
)
```

### Step 4: Run Intelligence Gathering

```python
import asyncio
from gemtrade.cloud import GeminiIntelligence, IntelligenceQuery

async def main():
    intel = GeminiIntelligence()
    
    # Gather intelligence
    result = await intel.gather_intelligence(
        IntelligenceQuery(
            symbols=["XAUUSD"],
            timeframe="last 4 hours",
            include_indirect=True,
            include_contrarian=True,
        )
    )
    
    print(result.market_summary)
    
    # Check signals
    for insight in result.get_actionable_insights():
        print(f"[{insight.confidence:.0%}] {insight.headline}")
        print(f"  Direction: {insight.direction.value}")
        print(f"  Reasoning: {insight.reasoning}")

asyncio.run(main())
```

## Advanced Features

### 1. Hybrid Local + Cloud Architecture

For maximum efficiency, combine:
- **Local**: FinBERT for fast sentiment screening
- **Cloud**: Gemini for complex analysis and web search

```python
class HybridIntelligence:
    """Combine local ML with Gemini for cost efficiency."""
    
    def __init__(self):
        self.local_sentiment = FinBERTAnalyzer()  # Local
        self.gemini = GeminiIntelligence()         # Cloud
    
    async def analyze(self, news_items: List[str]) -> List[MarketInsight]:
        insights = []
        
        # First pass: local FinBERT (free, fast)
        for item in news_items:
            local_sentiment = self.local_sentiment.analyze(item)
            
            # Only escalate to Gemini if confidence is low
            if abs(local_sentiment.score) < 0.3:
                # Use Gemini for ambiguous items
                gemini_result = await self.gemini.deep_research(item)
                insights.append(self._parse_gemini(gemini_result))
            else:
                insights.append(self._from_local(local_sentiment))
        
        return insights
```

### 2. Pattern Learning with BigQuery

```sql
-- Find patterns that predict profitable trades
WITH signal_outcomes AS (
    SELECT
        s.signal_type,
        s.direction,
        s.source,
        s.confidence,
        t.pnl_paise > 0 as profitable,
        t.pnl_percent
    FROM gemtrade.signals s
    JOIN gemtrade.trades t ON s.trade_id = t.trade_id
    WHERE s.was_traded = TRUE
)
SELECT
    signal_type,
    direction,
    source,
    AVG(confidence) as avg_confidence,
    COUNT(*) as occurrences,
    AVG(CAST(profitable AS INT64)) as win_rate,
    AVG(pnl_percent) as avg_pnl_percent
FROM signal_outcomes
GROUP BY 1, 2, 3
HAVING occurrences >= 10
ORDER BY win_rate DESC, avg_pnl_percent DESC;
```

### 3. Real-time Alerting

```python
from google.cloud import pubsub_v1

def setup_alerts(project_id: str):
    """Set up Pub/Sub for real-time alerts."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(project_id, "gemtrade-alerts")
    
    # Create topic
    try:
        publisher.create_topic(request={"name": topic_path})
    except Exception:
        pass  # Topic exists
    
    return publisher, topic_path

async def check_and_alert(publisher, topic_path, intelligence):
    """Check for high-confidence signals and alert."""
    result = await intelligence.gather_intelligence(
        IntelligenceQuery(symbols=["XAUUSD"])
    )
    
    for insight in result.get_actionable_insights(min_confidence=0.8):
        if insight.direction in [SignalDirection.STRONG_BUY, SignalDirection.STRONG_SELL]:
            # Publish alert
            data = json.dumps(insight.to_dict()).encode()
            publisher.publish(topic_path, data)
```

## Best Practices

### 1. Caching Strategy

```python
# Cache aggressive for repeated queries
config = GeminiConfig(
    cache_ttl_seconds=300,  # 5 minutes for news
)

# News changes slowly - cache longer
# Prices change fast - don't cache price data
```

### 2. Rate Limit Management

```python
# Use exponential backoff
async def safe_query(client, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await client.generate(prompt)
        except RateLimitError:
            wait = 2 ** attempt
            await asyncio.sleep(wait)
    raise Exception("Rate limit exceeded")
```

### 3. Query Optimization (BigQuery)

```python
# Bad: SELECT * FROM trades
# Good: SELECT only needed columns

# Bad: Query entire table repeatedly  
# Good: Use partitioning and clustering

# Create partitioned table
"""
CREATE TABLE gemtrade.trades
PARTITION BY DATE(entry_time)
CLUSTER BY symbol, strategy
AS SELECT * FROM gemtrade.trades_staging;
"""
```

### 4. Cost Monitoring

```python
# Track token usage
class CostTracker:
    def __init__(self):
        self.tokens_used = 0
        self.requests_made = 0
    
    def record(self, response: GroundedResponse):
        self.tokens_used += response.tokens_used
        self.requests_made += 1
    
    def estimate_cost(self) -> float:
        # Gemini Flash: $0.15/1M tokens
        return (self.tokens_used / 1_000_000) * 0.15
```

## Troubleshooting

### Common Issues

1. **"Quota exceeded" error**
   - Check daily limits in Cloud Console
   - Implement request caching
   - Use Flash-Lite for simple queries

2. **"Permission denied" for BigQuery**
   - Run: `gcloud auth application-default login`
   - Check IAM roles: BigQuery Data Editor

3. **Grounding not working**
   - Ensure `google_search` tool is enabled
   - Check if model supports grounding
   - Verify API key has correct permissions

4. **High latency**
   - Use regional endpoints
   - Implement response caching
   - Use Flash instead of Pro for speed

## Security

```python
# Never commit API keys
# Use environment variables or Secret Manager

from google.cloud import secretmanager

def get_api_key(project_id: str, secret_id: str) -> str:
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{project_id}/secrets/{secret_id}/versions/latest"
    response = client.access_secret_version(request={"name": name})
    return response.payload.data.decode("UTF-8")
```

## Next Steps

1. **Phase 1**: Set up Gemini API with grounding → Test intelligence gathering
2. **Phase 2**: Configure BigQuery → Store and analyze signals
3. **Phase 3**: Deploy to Cloud Run → Production trading
4. **Phase 4**: Add Cloud Functions → Scheduled intelligence + alerts

---

*This architecture is designed to stay within Google Cloud free tier limits while providing professional-grade trading intelligence.*
