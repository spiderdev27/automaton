# GemTrade

**Autonomous AI Trading Agent for Indian Markets**

Built on [GemCode](https://github.com/Veoksha/GemCode) (multi-agent mesh, event bus, habits, triggers) with [Automaton](https://github.com/spiderdev27/automaton) concepts (survival tiers, constitution, financial state management).

---

## What is GemTrade?

GemTrade is a self-learning, self-managing trading AI designed for:

- **Starting capital**: ₹5,000 INR (~$60 USD)
- **High leverage**: Supports 1:100 to 1:2000 (broker dependent)
- **Primary focus**: XAU/USD (Gold) on MT5
- **Secondary**: Crypto derivatives on Delta Exchange India

Key features:
- **Runs autonomously** via GemCode's agent mesh and habit scheduler
- **Enforces immutable risk rules** (constitution) that no agent can override
- **Adapts to capital levels** with INR-based survival tiers
- **Leverage is EARNED** - starts at 1:100, increases only with proven profits
- **Learns from every trade** through procedural memory ("feeling", not just remembering)
- **Coordinates multiple agents** (Analyst, Strategist, Overseer, Executor, Learner)

## Quick Start

```bash
# Install (basic)
pip install gemtrade

# Install with Google Cloud intelligence
pip install gemtrade[cloud]

# Install everything (cloud + local ML)
pip install gemtrade[all]

# Set API keys
export GOOGLE_API_KEY="your-gemini-api-key"  # Get from https://aistudio.google.com/apikey
export GOOGLE_CLOUD_PROJECT="your-project-id"  # For BigQuery

# For Delta Exchange
export DELTA_API_KEY="your-delta-key"
export DELTA_API_SECRET="your-delta-secret"

# For MT5 (forex/gold)
export MT5_LOGIN="your-login"
export MT5_PASSWORD="your-password"
export MT5_SERVER="your-broker-server"

# Initialize with INR 5,000 starting capital
gemtrade init

# Run paper trading
gemtrade run --paper

# Check status
gemtrade status

# View trade journal
gemtrade journal

# Get real-time market intelligence
gemtrade intel XAUUSD --timeframe "6 hours"
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      GemTrade Architecture                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              OVERSEER (Constitution Layer)               │   │
│  │  - Enforces immutable risk rules                         │   │
│  │  - Can HALT all trading                                  │   │
│  │  - Cannot be overridden by other agents                  │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│        ┌─────────────────────┼─────────────────────┐           │
│        ▼                     ▼                     ▼           │
│  ┌───────────┐       ┌───────────────┐      ┌───────────────┐  │
│  │ ANALYST   │       │ STRATEGIST    │      │ EXECUTOR      │  │
│  │           │       │               │      │               │  │
│  │ Market    │──────▶│ Trade         │─────▶│ Order         │  │
│  │ data &    │       │ signals       │      │ execution     │  │
│  │ regime    │       │               │      │               │  │
│  └───────────┘       └───────────────┘      └───────────────┘  │
│                              │                     │           │
│                              └──────────┬──────────┘           │
│                                         ▼                      │
│                              ┌───────────────────┐             │
│                              │     LEARNER       │             │
│                              │ Procedural memory │             │
│                              │ Error patterns    │             │
│                              └───────────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## The Constitution (Aggressive but Protected)

These rules are **IMMUTABLE** - no agent can bypass them:

| Rule | Limit | With ₹5,000 |
|------|-------|-------------|
| **Stop Loss Required** | Every trade | Non-negotiable |
| **Max Risk/Trade** | 10% | ₹500 max loss per trade |
| **Max Position** | 25% | ₹1,250 position value |
| **Max Concurrent** | 2 | Focus beats diversification |
| **Daily Loss Halt** | 15% | Stop after ₹750 loss/day |
| **Weekly Loss Halt** | 25% | Stop after ₹1,250 loss/week |
| **Max Drawdown** | 40% | Emergency at ₹2,000 from peak |
| **Reserve** | 30% | Keep ₹1,500 as buffer |

**Philosophy**: Be aggressive with individual trades, but have HARD STOPS that prevent wipeout.

## Survival Tiers (INR)

GemTrade automatically adjusts behavior based on capital:

| Tier | Balance | Max Leverage | Risk/Trade | Capabilities |
|------|---------|--------------|------------|--------------|
| 🟢 HIGH | > ₹50,000 | **1:1000** | 10% (₹5,000) | **Earned** - near max leverage |
| 🟢 NORMAL | > ₹5,000 | **1:500** | 10% (₹500) | Starting tier - full power |
| 🟠 LOW | > ₹1,000 | **1:200** | 7.5% (₹75) | Reduced, 1 position only |
| 🔴 CRITICAL | > ₹100 | **1:100** | 0% | Close-only mode |
| ⚫ DEAD | ₹0 | N/A | N/A | Cannot trade |

**Risk Philosophy**: 
- **High leverage** = small margin = more flexibility (risk is controlled by STOP LOSS, not leverage)
- **Aggressive per-trade risk** (up to 10%) to make meaningful profits
- **Hard circuit breakers** to prevent account wipeout
- **Stop losses are MANDATORY** - this is what makes high leverage survivable

## Adaptive Intelligence ("Feeling" the Market)

With small capital, GemTrade operates in **SNIPER MODE** - few trades, high accuracy:

### Signal Quality Scoring (Only Trade A+ and A Signals)

```python
SignalScore:
    trend_alignment: 100     # With the trend?
    multi_timeframe: 90      # Multiple timeframes agree?
    indicator_confluence: 85 # Multiple indicators agree?
    key_level: 100           # At support/resistance?
    volatility_favorable: 70 # Good volatility?
    session_timing: 100      # London/NY session?
    news_clear: 100          # No news pending?
    risk_reward_ratio: 80    # >= 2:1 R:R?
    ─────────────────────────
    Total: 825/1100 → Grade: A → TAKE TRADE
```

### Mid-Trade Adaptation (Real-Time "Feeling")

```python
ActiveTradeManager:
    # Move to breakeven after 1:1 profit
    if pnl >= risk_distance:
        stop_loss = entry_price
    
    # Activate trailing stop after 1.5:1
    if pnl >= risk_distance * 1.5:
        trailing_stop = True
    
    # Take 50% profit at 2:1
    if pnl >= risk_distance * 2:
        close_50_percent()
    
    # Tighten stop before news
    if news_in_minutes < 15:
        move_stop_to_breakeven()
    
    # Close on volatility spike
    if volatility_percentile > 95:
        close_trade()
```

### Self-Learning Parameters

```python
# Parameters ADAPT based on what works:
after_win:
    risk_pct += 10% (confidence)
    if TP hit exactly → TP distance good
    
after_loss:
    risk_pct -= 15% (protection)
    if stopped after being in profit → need better trailing
    if stopped quickly → SL too tight, widen next time
```

### Market Condition Awareness

| Condition | Action |
|-----------|--------|
| News in < 30 min | DON'T TRADE |
| Spread > 90th percentile | DON'T TRADE |
| Asian session + quiet | DON'T TRADE |
| High volatility | Reduce size 50% |
| London/NY overlap | Increase size 20% |

## Google Cloud Integration (NEW!)

GemTrade leverages your Google Cloud credits for **real-time market intelligence**:

### Gemini API with Web Search Grounding

```python
from gemtrade.cloud import GeminiIntelligence, IntelligenceQuery

# Initialize (uses GOOGLE_API_KEY env var)
intelligence = GeminiIntelligence()

# Get real-time market intelligence
result = await intelligence.gather_intelligence(
    IntelligenceQuery(
        symbols=["XAUUSD"],
        timeframe="last 6 hours",
        include_indirect=True,     # Detect indirect signals
        include_contrarian=True,   # Challenge consensus
    )
)

# Access signals
for symbol, direction in result.signals.items():
    confidence = result.confidence_scores[symbol]
    print(f"{symbol}: {direction.value} ({confidence:.0%})")

# Get actionable insights
for insight in result.get_actionable_insights(min_confidence=0.7):
    print(f"[{insight.confidence:.0%}] {insight.headline}")
```

### BigQuery for Trade Analytics

```python
from gemtrade.cloud import BigQueryStore

store = BigQueryStore(project_id="your-project")

# Get performance metrics
metrics = store.get_performance_metrics(
    start_date=datetime(2026, 1, 1),
    end_date=datetime.utcnow(),
)

# Find winning patterns
patterns = store.get_best_performing_patterns(
    min_occurrences=5,
    min_win_rate=0.6,
)
```

### Cost: **₹0** (Free Tier)

| Service | Usage | Free Tier |
|---------|-------|-----------|
| Gemini API (Flash) | ~2,500 requests/month | 45,000/month |
| BigQuery Queries | ~10 GB/month | 1,000 GB/month |
| BigQuery Storage | ~1 GB/month | 10 GB/month |

See [GOOGLE_CLOUD_ARCHITECTURE.md](docs/GOOGLE_CLOUD_ARCHITECTURE.md) for full details.

## GemCode Integration

GemTrade extends GemCode, so you get:

- **Agent Mesh**: Background trading agents
- **Event Bus**: Trade signals, price alerts
- **Habits**: Scheduled market scans, position checks
- **Triggers**: React to regime changes, risk events
- **Delegation Learning**: Track which strategies work
- **Self-Healing**: Auto-verify trades

## Configuration

```json
// .gemcode/trading/config.json
{
  "name": "gemtrade",
  "currency": "INR",
  "initial_balance_paise": 500000,
  "default_symbol": "XAUUSD",
  "primary_exchange": {
    "type": "mt5",
    "sandbox": true
  },
  "risk": {
    "max_position_pct": 3.0,
    "max_concurrent_positions": 2,
    "max_daily_loss_pct": 3.0,
    "max_drawdown_pct": 20.0,
    "max_risk_per_trade_pct": 2.0,
    "leverage": {
      "broker_max": 2000,
      "starting_max": 100,
      "earned_max": 500
    }
  },
  "strategies": [
    {
      "name": "ema_crossover",
      "enabled": true,
      "symbols": ["XAUUSD"]
    }
  ]
}
```

## Supported Exchanges

| Exchange | Type | Instruments | Leverage | Python Package |
|----------|------|-------------|----------|----------------|
| **MT5** | Forex/CFD | XAU/USD, Forex | 1:500+ | `MetaTrader5` |
| **Delta Exchange India** | Crypto | BTC, ETH perps | 1:100 | `delta-rest-client` |
| **Paper** | Simulated | All | Any | Built-in |

## Trading Habits

```json
// .gemcode/habits.json
[
  {
    "name": "market-scan",
    "agent": "analyst",
    "prompt": "Scan XAU/USD for setups",
    "every_minutes": 15
  },
  {
    "name": "risk-check",
    "agent": "overseer",
    "prompt": "Audit risk exposure",
    "every_minutes": 30
  },
  {
    "name": "daily-review",
    "agent": "learner",
    "prompt": "Review today's trades",
    "daily_at": "22:00"
  }
]
```

## Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| 0. Setup | Bootable package | ✅ Done |
| 1. Intelligence | Gemini + Web Search Grounding | ✅ Done |
| 2. Data Store | BigQuery analytics | ✅ Done |
| 3. Infrastructure | Exchange connectors | 🔄 In Progress |
| 4. Agents | Full agent fleet | 📋 Planned |
| 5. Strategies | EMA crossover + News | 📋 Planned |
| 6. Paper Trading | 100 trades | 📋 Planned |
| 7. Live | Real money (₹5,000) | 📋 Planned |

## Risk Warning

**Trading involves significant risk of loss.** GemTrade is experimental software. Never trade with money you cannot afford to lose. Paper trade extensively before using real capital.

## License

Apache 2.0

## Related Projects

- [GemCode](https://github.com/Veoksha/GemCode) - Multi-agent coding assistant
- [Automaton](https://github.com/spiderdev27/automaton) - Self-sovereign AI agent
- [FinRL](https://github.com/AI4Finance-Foundation/FinRL) - Reinforcement learning for trading
- [OpenTraitor](https://github.com/liljestk/open-traitor) - Multi-agent LLM trading
