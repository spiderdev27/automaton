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
# Install
pip install gemtrade

# Set API keys
export GOOGLE_API_KEY="your-key"

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
| 🟢 HIGH | > ₹50,000 | 1:500 | 10% (₹5,000) | **Earned** through 10x growth |
| 🟢 NORMAL | > ₹5,000 | 1:200 | 10% (₹500) | Starting tier - aggressive |
| 🟠 LOW | > ₹1,000 | 1:100 | 7.5% (₹75) | Reduced, 1 position only |
| 🔴 CRITICAL | > ₹100 | 1:50 | 0% | Close-only mode |
| ⚫ DEAD | ₹0 | N/A | N/A | Cannot trade |

**Risk Philosophy**: 
- **Aggressive per-trade risk** (up to 10%) to make meaningful profits
- **Hard circuit breakers** to prevent account wipeout
- **Stop losses are MANDATORY** - this is what makes aggression survivable

## Procedural Memory ("Feeling")

GemTrade doesn't just remember trades - it develops **behavioral adjustments**:

```python
# Example: After 15 trades in high volatility
ProceduralMemory(
    condition="volatility_percentile > 80",
    adjustment="position_size * 0.5",  # Half size
    confidence=0.85,
    outcome_when_applied=+2.3%,
    outcome_when_ignored=-4.1%
)
```

The agent "feels" caution in high volatility without explicit reasoning.

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
| 1. Infrastructure | Exchange connectors | 🔄 In Progress |
| 2. Agents | Full agent fleet | 📋 Planned |
| 3. Strategies | EMA crossover | 📋 Planned |
| 4. Paper Trading | 100 trades | 📋 Planned |
| 5. Live | Real money ($500) | 📋 Planned |

## Risk Warning

**Trading involves significant risk of loss.** GemTrade is experimental software. Never trade with money you cannot afford to lose. Paper trade extensively before using real capital.

## License

Apache 2.0

## Related Projects

- [GemCode](https://github.com/Veoksha/GemCode) - Multi-agent coding assistant
- [Automaton](https://github.com/spiderdev27/automaton) - Self-sovereign AI agent
- [FinRL](https://github.com/AI4Finance-Foundation/FinRL) - Reinforcement learning for trading
- [OpenTraitor](https://github.com/liljestk/open-traitor) - Multi-agent LLM trading
