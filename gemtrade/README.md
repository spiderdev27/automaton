# GemTrade

**Autonomous AI Trading Agent**

Built on [GemCode](https://github.com/Veoksha/GemCode) (multi-agent mesh, event bus, habits, triggers) with [Automaton](https://github.com/spiderdev27/automaton) concepts (survival tiers, constitution, financial state management).

---

## What is GemTrade?

GemTrade is a self-learning, self-managing trading AI that:

- **Runs autonomously** via GemCode's agent mesh and habit scheduler
- **Enforces immutable risk rules** (constitution) that no agent can override
- **Adapts to capital levels** with survival tiers (HIGH → CRITICAL → DEAD)
- **Learns from every trade** through procedural memory ("feeling", not just remembering)
- **Coordinates multiple agents** (Analyst, Strategist, Overseer, Executor, Learner)

## Quick Start

```bash
# Install
pip install gemtrade

# Set API key
export GOOGLE_API_KEY="your-key"

# Run in super mode (paper trading)
gemtrade -C /path/to/project --super

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

## The Constitution

These rules are **IMMUTABLE** - no agent can modify or bypass them:

| Rule | Description |
|------|-------------|
| Stop Loss Required | Every trade MUST have a stop loss |
| Max Position 5% | No single position > 5% of equity |
| Daily Loss 3% | Halt if daily loss exceeds 3% |
| Weekly Loss 10% | Halt if weekly loss exceeds 10% |
| Max Drawdown 20% | Emergency halt if drawdown > 20% |
| 50% Reserve | Must maintain 50% cash reserve |
| Max 3 Positions | Maximum 3 concurrent positions |

## Survival Tiers

GemTrade automatically adjusts behavior based on capital:

| Tier | Balance | Capabilities |
|------|---------|--------------|
| 🟢 HIGH | > $500 | Full power: 5% positions, quality models |
| 🟢 NORMAL | > $50 | Standard: 3% positions, balanced models |
| 🟠 LOW | > $10 | Reduced: 1% positions, fast models |
| 🔴 CRITICAL | > $1 | Close-only mode, no new positions |
| ⚫ DEAD | $0 | Cannot trade, requires recovery |

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
  "default_symbol": "XAU/USD",
  "exchange": {
    "type": "paper",
    "sandbox": true
  },
  "risk": {
    "max_position_pct": 5.0,
    "max_daily_loss_pct": 3.0,
    "max_drawdown_pct": 20.0
  },
  "strategies": [
    {
      "name": "ema_crossover",
      "enabled": true,
      "symbols": ["XAU/USD"]
    }
  ]
}
```

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
