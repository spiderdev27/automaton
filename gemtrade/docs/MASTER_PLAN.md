# GemTrade: Master Implementation Plan

**Version**: 1.0.0  
**Status**: Final Architecture  
**Date**: July 2026

---

## Executive Summary

GemTrade is an autonomous trading AI that combines:
- **GemCode** (Python/ADK): Multi-agent mesh, event bus, habits, triggers, memory, tool synthesis
- **Automaton** (TypeScript): Survival tiers, constitutional limits, financial state management
- **Industry Best Practices**: From OpenTraitor, FinRL, FinRobot analysis

**Architecture Decision**: GemTrade is a **Python package that depends on GemCode**, not a fork or rewrite.

---

## Part 1: Why This Architecture

### 1.1 What We Get from GemCode (Keep)

| Component | Lines | Trading Use |
|-----------|-------|-------------|
| `agent_mesh.py` | 1000+ | Background trading agents, job queue |
| `event_bus.py` | 200+ | Trade signals, price alerts, execution reports |
| `agent_habits.py` | 400+ | Scheduled market scans, position checks |
| `agent_triggers.py` | 300+ | React to regime changes, price alerts |
| `delegation_learning.py` | 200+ | Track which strategies work best |
| `self_healing.py` | 300+ | Auto-verify trades, fix positions |
| `tool_synthesis.py` | 200+ | Create custom indicators from patterns |
| `fleet_reports.py` | 350+ | Persist trade outcomes for learning |
| `org.py` | 400+ | Agent fleet management |
| `session_runtime.py` | 700+ | ADK Runner assembly |
| `tools/` | 3000+ | Foundation for trading tools |

**Total**: ~15,000 lines of infrastructure we don't have to write.

### 1.2 What We Port from Automaton (Adapt)

| Concept | Automaton Location | GemTrade Adaptation |
|---------|-------------------|---------------------|
| Survival Tiers | `src/types.ts:229-237` | `gemtrade/survival.py` |
| Constitution | `constitution.md` | `gemtrade/constitution.py` |
| Financial State | `src/types.ts:221-228` | `gemtrade/state.py` |
| Treasury Policy | `src/types.ts:570-594` | `gemtrade/risk_policy.py` |
| Memory Schema | `src/types.ts:1022-1126` | Extend GemCode memory |
| Policy Engine | `src/agent/policy-engine.ts` | Adapt for Python |
| Circuit Breakers | `src/agent/loop.ts:440-490` | `gemtrade/circuit_breakers.py` |

### 1.3 What We Learn from Reference Projects

#### From OpenTraitor
- Multi-agent pipeline: Analyst → Strategist → Risk Manager → Executor
- Signal scorecard for prediction accuracy
- Confidence calibrator
- Walk-forward optimization
- Domain separation (crypto vs equities)

#### From FinRL
- Three-layer architecture: Environment → Agent → Application
- Multiple RL algorithms (PPO, DDPG, TD3, SAC, A2C)
- Gym-compatible market environments
- Backtesting framework

#### From FinRobot
- Financial Chain-of-Thought prompting
- Document Analysis Agents
- Action/Brain/Perception architecture

---

## Part 2: GemTrade Architecture

### 2.1 Package Structure

```
gemtrade/
├── pyproject.toml              # Dependencies: gemcode>=0.4.25
├── README.md
├── LICENSE
│
├── gemtrade/
│   ├── __init__.py             # Package init, version
│   ├── __main__.py             # CLI entry point
│   ├── cli.py                  # gemtrade CLI (extends gemcode)
│   ├── config.py               # TradingConfig
│   │
│   ├── core/                   # Core trading infrastructure
│   │   ├── __init__.py
│   │   ├── constitution.py     # Immutable risk rules (from Automaton)
│   │   ├── survival.py         # Survival tiers (from Automaton)
│   │   ├── state.py            # Trading state management
│   │   ├── risk_policy.py      # Risk limits and policies
│   │   └── circuit_breakers.py # Emergency stops
│   │
│   ├── agents/                 # Trading-specific agents
│   │   ├── __init__.py
│   │   ├── base.py             # TradingAgent base class
│   │   ├── overseer.py         # Constitutional enforcement
│   │   ├── analyst.py          # Market analysis
│   │   ├── strategist.py       # Decision making
│   │   ├── executor.py         # Order execution
│   │   └── learner.py          # Post-trade learning
│   │
│   ├── exchange/               # Exchange connectors
│   │   ├── __init__.py
│   │   ├── base.py             # ExchangeConnector ABC
│   │   ├── paper.py            # Paper trading
│   │   ├── oanda.py            # OANDA (forex, XAU/USD)
│   │   ├── alpaca.py           # Alpaca (stocks)
│   │   └── binance.py          # Binance (crypto)
│   │
│   ├── strategies/             # Trading strategies
│   │   ├── __init__.py
│   │   ├── base.py             # Strategy ABC
│   │   ├── registry.py         # Strategy registry
│   │   ├── ema_crossover.py    # Simple EMA crossover
│   │   ├── regime_adaptive.py  # Regime-aware strategy
│   │   └── mean_reversion.py   # Mean reversion
│   │
│   ├── indicators/             # Technical indicators
│   │   ├── __init__.py
│   │   ├── base.py             # Indicator ABC
│   │   ├── trend.py            # EMA, SMA, MACD
│   │   ├── momentum.py         # RSI, Stochastic
│   │   ├── volatility.py       # ATR, Bollinger
│   │   └── volume.py           # OBV, VWAP
│   │
│   ├── memory/                 # Trading-specific memory
│   │   ├── __init__.py
│   │   ├── trade_journal.py    # Trade history (episodic)
│   │   ├── regime_memory.py    # Market regimes (semantic)
│   │   ├── procedural.py       # "Feeling" system
│   │   ├── error_patterns.py   # Mistakes to avoid
│   │   └── strategy_memory.py  # Strategy performance
│   │
│   ├── tools/                  # Trading tools for agents
│   │   ├── __init__.py
│   │   ├── market_data.py      # Price feeds, candles
│   │   ├── order.py            # Place/modify/cancel
│   │   ├── position.py         # Position management
│   │   ├── analysis.py         # Indicator calculations
│   │   ├── risk.py             # Position sizing
│   │   └── backtest.py         # Backtesting tools
│   │
│   ├── skills/                 # GemCode skills for trading
│   │   ├── overseer.md
│   │   ├── analyst.md
│   │   ├── strategist.md
│   │   ├── executor.md
│   │   └── learner.md
│   │
│   └── integration/            # GemCode integration
│       ├── __init__.py
│       ├── mesh_extension.py   # Extend AgentMesh
│       ├── event_topics.py     # Trading event topics
│       ├── habits.py           # Default trading habits
│       └── triggers.py         # Default trading triggers
│
├── docs/
│   ├── MASTER_PLAN.md          # This document
│   ├── ARCHITECTURE.md         # Technical architecture
│   ├── QUICKSTART.md           # Getting started
│   ├── CONFIGURATION.md        # Configuration reference
│   └── API.md                  # API documentation
│
├── tests/
│   ├── test_constitution.py
│   ├── test_survival.py
│   ├── test_agents.py
│   ├── test_exchange.py
│   ├── test_strategies.py
│   └── test_memory.py
│
└── examples/
    ├── paper_trading.py        # Paper trading example
    ├── backtest.py             # Backtesting example
    └── custom_strategy.py      # Custom strategy example
```

### 2.2 Dependency Chain

```
┌─────────────────────────────────────────────────────────────────┐
│                         GemTrade                                │
│  (Trading logic, agents, strategies, memory)                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │ depends on
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         GemCode                                 │
│  (Agent mesh, event bus, habits, triggers, tools, memory)       │
└───────────────────────────┬─────────────────────────────────────┘
                            │ depends on
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Google ADK                                 │
│  (LlmAgent, Runner, Session, Tools)                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ depends on
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Google Gemini                              │
│  (LLM inference)                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Part 3: Core Components (From Automaton)

### 3.1 Constitution (Immutable Rules)

```python
# gemtrade/core/constitution.py

"""
Trading Constitution - Immutable Risk Rules

These rules CANNOT be modified by any agent. They are the foundation
of survival and must be enforced by the Overseer at all times.

Inspired by Automaton's constitution.md
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

class RuleSeverity(Enum):
    BLOCK = "block"      # Reject immediately
    HALT = "halt"        # Stop all trading
    WARN = "warn"        # Log warning, allow
    LOG = "log"          # Log only

@dataclass(frozen=True)  # Immutable
class ConstitutionalRule:
    id: str
    name: str
    description: str
    severity: RuleSeverity
    
# THE CONSTITUTION - These cannot be changed by agents
CONSTITUTION = [
    ConstitutionalRule(
        id="LAW_1_STOP_LOSS",
        name="First Law: Stop Loss Required",
        description="Every trade MUST have a stop loss. No exceptions.",
        severity=RuleSeverity.BLOCK
    ),
    ConstitutionalRule(
        id="LAW_2_MAX_POSITION",
        name="Second Law: Position Limit",
        description="No single position may exceed 5% of account equity.",
        severity=RuleSeverity.BLOCK
    ),
    ConstitutionalRule(
        id="LAW_3_DAILY_LOSS",
        name="Third Law: Daily Loss Limit",
        description="Halt all trading if daily loss exceeds 3%.",
        severity=RuleSeverity.HALT
    ),
    ConstitutionalRule(
        id="LAW_4_WEEKLY_LOSS",
        name="Fourth Law: Weekly Loss Limit",
        description="Halt all trading if weekly loss exceeds 10%.",
        severity=RuleSeverity.HALT
    ),
    ConstitutionalRule(
        id="LAW_5_DRAWDOWN",
        name="Fifth Law: Maximum Drawdown",
        description="Emergency halt if drawdown exceeds 20%. Require human intervention.",
        severity=RuleSeverity.HALT
    ),
    ConstitutionalRule(
        id="LAW_6_RESERVE",
        name="Sixth Law: Reserve Requirement",
        description="Must maintain 50% of capital as reserve at all times.",
        severity=RuleSeverity.BLOCK
    ),
    ConstitutionalRule(
        id="LAW_7_CONCURRENT",
        name="Seventh Law: Concurrent Positions",
        description="Maximum 3 concurrent positions.",
        severity=RuleSeverity.BLOCK
    ),
]
```

### 3.2 Survival Tiers

```python
# gemtrade/core/survival.py

"""
Survival Tiers - Operating Modes Based on Capital

Adapted from Automaton's survival mechanics.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any

class SurvivalTier(Enum):
    HIGH = "high"           # > $500 (50000 cents)
    NORMAL = "normal"       # > $50 (5000 cents)
    LOW = "low"             # > $10 (1000 cents)
    CRITICAL = "critical"   # > $1 (100 cents)
    DEAD = "dead"           # $0 or negative

SURVIVAL_THRESHOLDS = {
    SurvivalTier.HIGH: 50000,      # cents
    SurvivalTier.NORMAL: 5000,
    SurvivalTier.LOW: 1000,
    SurvivalTier.CRITICAL: 100,
    SurvivalTier.DEAD: 0,
}

@dataclass
class TierCapabilities:
    max_position_pct: float
    can_open_new: bool
    can_add_to_position: bool
    analysis_frequency_minutes: int
    model_tier: str  # "quality", "balanced", "fast"

TIER_CAPABILITIES: Dict[SurvivalTier, TierCapabilities] = {
    SurvivalTier.HIGH: TierCapabilities(
        max_position_pct=5.0,
        can_open_new=True,
        can_add_to_position=True,
        analysis_frequency_minutes=15,
        model_tier="quality"
    ),
    SurvivalTier.NORMAL: TierCapabilities(
        max_position_pct=3.0,
        can_open_new=True,
        can_add_to_position=True,
        analysis_frequency_minutes=30,
        model_tier="balanced"
    ),
    SurvivalTier.LOW: TierCapabilities(
        max_position_pct=1.0,
        can_open_new=True,
        can_add_to_position=False,
        analysis_frequency_minutes=60,
        model_tier="fast"
    ),
    SurvivalTier.CRITICAL: TierCapabilities(
        max_position_pct=0.5,
        can_open_new=False,  # Close-only mode
        can_add_to_position=False,
        analysis_frequency_minutes=120,
        model_tier="fast"
    ),
    SurvivalTier.DEAD: TierCapabilities(
        max_position_pct=0,
        can_open_new=False,
        can_add_to_position=False,
        analysis_frequency_minutes=0,  # No analysis
        model_tier="none"
    ),
}

def get_survival_tier(balance_cents: int) -> SurvivalTier:
    """Determine survival tier from balance."""
    for tier in [SurvivalTier.HIGH, SurvivalTier.NORMAL, 
                 SurvivalTier.LOW, SurvivalTier.CRITICAL]:
        if balance_cents >= SURVIVAL_THRESHOLDS[tier]:
            return tier
    return SurvivalTier.DEAD
```

### 3.3 Trading State

```python
# gemtrade/core/state.py

"""
Trading State Management

Tracks financial state, open positions, and trading metrics.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from pathlib import Path
import json

@dataclass
class Position:
    id: str
    symbol: str
    direction: str  # "long" or "short"
    entry_price: float
    current_price: float
    size: float
    stop_loss: float
    take_profit: Optional[float]
    unrealized_pnl: float
    opened_at: datetime

@dataclass
class TradingState:
    # Account
    balance_cents: int
    equity_cents: int
    
    # Positions
    open_positions: List[Position] = field(default_factory=list)
    
    # P&L Tracking
    daily_pnl_cents: int = 0
    weekly_pnl_cents: int = 0
    monthly_pnl_cents: int = 0
    
    # Risk Metrics
    current_drawdown_pct: float = 0.0
    peak_equity_cents: int = 0
    
    # Counters
    trades_today: int = 0
    consecutive_losses: int = 0
    consecutive_wins: int = 0
    
    # Circuit Breakers
    circuit_breaker_active: Optional[str] = None
    circuit_breaker_until: Optional[datetime] = None
    
    # Timestamps
    last_trade_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)
    
    def save(self, path: Path) -> None:
        """Persist state to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
            
    @classmethod
    def load(cls, path: Path) -> "TradingState":
        """Load state from disk."""
        if not path.exists():
            return cls(balance_cents=0, equity_cents=0)
        with open(path) as f:
            data = json.load(f)
        return cls(**data)
        
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "balance_cents": self.balance_cents,
            "equity_cents": self.equity_cents,
            "daily_pnl_cents": self.daily_pnl_cents,
            "weekly_pnl_cents": self.weekly_pnl_cents,
            "current_drawdown_pct": self.current_drawdown_pct,
            "trades_today": self.trades_today,
            "consecutive_losses": self.consecutive_losses,
            "circuit_breaker_active": self.circuit_breaker_active,
        }
```

---

## Part 4: GemCode Integration

### 4.1 Event Bus Topics

```python
# gemtrade/integration/event_topics.py

"""Trading-specific event bus topics for GemCode integration."""

TRADING_TOPICS = {
    # Price & Market Data
    "price.tick": "Real-time price update",
    "price.alert": "Price threshold crossed",
    "market.regime_change": "Market regime changed (trending/ranging/volatile)",
    "market.news": "High-impact news event",
    
    # Trading Signals
    "trade.signal": "New trade signal from Strategist",
    "trade.validated": "Signal passed Overseer validation",
    "trade.rejected": "Signal rejected by Overseer (with reason)",
    "trade.pending": "Order submitted to exchange",
    "trade.executed": "Order filled by exchange",
    "trade.modified": "Stop/TP modified",
    "trade.closed": "Position closed",
    
    # Risk Events
    "risk.limit_warning": "Approaching risk limit (70% threshold)",
    "risk.limit_breach": "Risk limit breached",
    "risk.circuit_breaker": "Circuit breaker activated",
    "risk.emergency_halt": "Emergency halt (human intervention needed)",
    
    # Survival Events
    "survival.tier_change": "Survival tier changed",
    "survival.critical": "Entered critical tier",
    "survival.dead": "Account dead (zero balance)",
    
    # Learning Events
    "learn.trade_complete": "Trade completed, ready for analysis",
    "learn.pattern_detected": "New pattern detected",
    "learn.procedural_update": "Procedural memory updated",
    "learn.strategy_scored": "Strategy performance scored",
}
```

### 4.2 Default Habits

```python
# gemtrade/integration/habits.py

"""Default trading habits for GemCode integration."""

DEFAULT_TRADING_HABITS = [
    {
        "name": "market-scan-quick",
        "agent": "analyst",
        "prompt": "Quick scan of XAU/USD. Report current price, regime, and any setup.",
        "every_minutes": 15,
        "enabled": True
    },
    {
        "name": "position-monitor",
        "agent": "executor",
        "prompt": "Check all open positions. Update trailing stops if appropriate.",
        "every_minutes": 5,
        "enabled": True
    },
    {
        "name": "risk-check",
        "agent": "overseer",
        "prompt": "Audit current exposure. Check all constitutional limits.",
        "every_minutes": 30,
        "enabled": True
    },
    {
        "name": "daily-review",
        "agent": "learner",
        "prompt": "Review all trades from today. Update procedural memory with lessons.",
        "daily_at": "22:00",
        "enabled": True
    },
    {
        "name": "weekly-strategy-review",
        "agent": "learner",
        "prompt": "Weekly strategy performance review. Propose parameter adjustments.",
        "cron": "0 0 * * 0",  # Sunday midnight
        "enabled": True
    },
]
```

### 4.3 Default Triggers

```python
# gemtrade/integration/triggers.py

"""Default trading triggers for GemCode integration."""

DEFAULT_TRADING_TRIGGERS = [
    {
        "agent": "overseer",
        "on_topic": "trade.signal",
        "when": {},
        "action": "Validate this trade signal against ALL constitutional rules.",
        "cooldown_s": 0,  # No cooldown - must validate every signal
        "enabled": True
    },
    {
        "agent": "executor",
        "on_topic": "trade.validated",
        "when": {},
        "action": "Execute this validated trade signal on the exchange.",
        "cooldown_s": 0,
        "enabled": True
    },
    {
        "agent": "learner",
        "on_topic": "trade.closed",
        "when": {},
        "action": "Analyze this completed trade. Evaluate process quality.",
        "cooldown_s": 5,
        "enabled": True
    },
    {
        "agent": "strategist",
        "on_topic": "market.regime_change",
        "when": {},
        "action": "Regime changed. Re-evaluate all pending signals and open positions.",
        "cooldown_s": 60,
        "enabled": True
    },
    {
        "agent": "overseer",
        "on_topic": "risk.limit_warning",
        "when": {},
        "action": "Risk warning triggered. Evaluate if position reduction needed.",
        "cooldown_s": 30,
        "enabled": True
    },
]
```

---

## Part 5: Execution Roadmap

### Phase 0: Project Setup (Week 1)

**Goal**: Bootable GemTrade package that extends GemCode.

| Task | Priority | Status |
|------|----------|--------|
| Create `pyproject.toml` with gemcode dependency | P0 | TODO |
| Create `gemtrade/__init__.py` | P0 | TODO |
| Create `gemtrade/cli.py` extending gemcode CLI | P0 | TODO |
| Create `gemtrade/config.py` | P0 | TODO |
| Create `gemtrade/core/constitution.py` | P0 | TODO |
| Create `gemtrade/core/survival.py` | P0 | TODO |
| Create `gemtrade/core/state.py` | P0 | TODO |
| Verify `gemtrade --help` works | P0 | TODO |

**Exit Criteria**: `pip install -e .` works, `gemtrade --version` shows version.

### Phase 1: Trading Infrastructure (Week 2-3)

**Goal**: Exchange connector and basic market data.

| Task | Priority | Status |
|------|----------|--------|
| Create `exchange/base.py` ABC | P0 | TODO |
| Create `exchange/paper.py` | P0 | TODO |
| Create `tools/market_data.py` | P0 | TODO |
| Create `indicators/trend.py` (EMA, SMA) | P0 | TODO |
| Create `indicators/volatility.py` (ATR) | P0 | TODO |
| Create `integration/event_topics.py` | P0 | TODO |
| Test paper trading connector | P0 | TODO |

**Exit Criteria**: Can fetch candles, calculate EMA, place paper orders.

### Phase 2: Trading Agents (Week 4-5)

**Goal**: Full agent fleet registered as GemCode org members.

| Task | Priority | Status |
|------|----------|--------|
| Create `agents/base.py` TradingAgent | P0 | TODO |
| Create `agents/overseer.py` | P0 | TODO |
| Create `agents/analyst.py` | P0 | TODO |
| Create `agents/strategist.py` | P0 | TODO |
| Create `agents/executor.py` | P0 | TODO |
| Create `agents/learner.py` | P0 | TODO |
| Create skill files for each agent | P0 | TODO |
| Register agents via GemCode org system | P0 | TODO |
| Test agent-to-agent communication | P0 | TODO |

**Exit Criteria**: All 5 agents registered, can delegate tasks between them.

### Phase 3: Strategy & Memory (Week 6-7)

**Goal**: Working strategy with learning loop.

| Task | Priority | Status |
|------|----------|--------|
| Create `strategies/base.py` ABC | P0 | TODO |
| Create `strategies/ema_crossover.py` | P0 | TODO |
| Create `memory/trade_journal.py` | P0 | TODO |
| Create `memory/procedural.py` | P0 | TODO |
| Create `tools/order.py` | P0 | TODO |
| Create `tools/position.py` | P0 | TODO |
| Integrate with GemCode habits | P0 | TODO |
| Integrate with GemCode triggers | P0 | TODO |

**Exit Criteria**: Strategy generates signals, Learner analyzes outcomes.

### Phase 4: Paper Trading (Week 8-10)

**Goal**: 100 paper trades with metrics tracking.

| Task | Priority | Status |
|------|----------|--------|
| Run continuous paper trading on XAU/USD | P0 | TODO |
| Track all metrics (Sharpe, drawdown, win rate) | P0 | TODO |
| Verify constitutional limits enforced | P0 | TODO |
| Verify circuit breakers work | P0 | TODO |
| Tune procedural memory thresholds | P1 | TODO |
| Analyze strategy performance | P1 | TODO |

**Exit Criteria**: 
- 100+ paper trades completed
- Sharpe ratio > 0.5
- Max drawdown < 25%
- No constitutional violations
- Procedural memory showing improvement

### Phase 5: Live Trading (Week 11+)

**Goal**: Real money trading with minimal capital.

| Task | Priority | Status |
|------|----------|--------|
| Implement `exchange/oanda.py` | P0 | TODO |
| Start with $500-1000 | P0 | TODO |
| Human oversight dashboard | P1 | TODO |
| Compare live vs paper performance | P1 | TODO |
| Gradual position size scaling | P2 | TODO |

**Exit Criteria**:
- 50+ live trades
- Slippage within acceptable range
- No system failures
- P&L within 20% of paper expectations

---

## Part 6: Risk Register

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GemCode API changes | Medium | High | Pin version, test upgrades |
| Exchange API failures | High | Medium | Retry logic, circuit breakers |
| Data feed delays | High | Medium | Latency monitoring, skip stale signals |
| Memory corruption | Low | High | SQLite WAL, backups |
| Agent coordination failures | Medium | Medium | Event bus retry, fallback paths |

### Market Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Flash crash | Low | Critical | Max position limits, wide stops |
| Regime change | High | High | Multi-regime strategies |
| Black swan | Low | Critical | Never risk >20% total |
| Slippage | High | Medium | Avoid high-impact news |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Run out of capital | Medium | Critical | Survival tiers, auto-reduce |
| Human unavailability | Medium | Medium | Automated alerts, SMS |
| Regulatory changes | Low | High | Legal review |

---

## Part 7: Success Metrics

### Trading Performance

| Metric | Target | Method |
|--------|--------|--------|
| Sharpe Ratio | ≥1.0 | (Return - Rf) / StdDev |
| Sortino Ratio | ≥1.5 | Return / Downside StdDev |
| Max Drawdown | ≤20% | Peak-to-trough |
| Win Rate | ≥45% | Wins / Total |
| Profit Factor | ≥1.5 | Gross Profit / Gross Loss |

### System Health

| Metric | Target | Frequency |
|--------|--------|-----------|
| Uptime | ≥99% | Continuous |
| Data Latency | ≤200ms | Per tick |
| Order Latency | ≤500ms | Per order |
| Constitution Violations | 0 | Continuous |
| Circuit Breaker False Positives | ≤5% | Weekly |

### Learning Effectiveness

| Metric | Target | Evaluation |
|--------|--------|------------|
| Error Pattern Recurrence | Decreasing | Same error ≤3x |
| Procedural Memory Accuracy | ≥70% | Adjustment outcomes |
| Strategy Improvement | Positive | Before/after metrics |

---

## Appendix A: Key Files Summary

| File | Purpose | Lines (est) |
|------|---------|-------------|
| `gemtrade/__init__.py` | Package init | 50 |
| `gemtrade/cli.py` | CLI | 200 |
| `gemtrade/config.py` | Configuration | 150 |
| `gemtrade/core/constitution.py` | Immutable rules | 100 |
| `gemtrade/core/survival.py` | Survival tiers | 100 |
| `gemtrade/core/state.py` | State management | 200 |
| `gemtrade/agents/*.py` | 5 agents | 1000 |
| `gemtrade/exchange/*.py` | 4 connectors | 800 |
| `gemtrade/strategies/*.py` | 3 strategies | 500 |
| `gemtrade/indicators/*.py` | 4 modules | 400 |
| `gemtrade/memory/*.py` | 5 modules | 600 |
| `gemtrade/tools/*.py` | 6 modules | 600 |
| `gemtrade/integration/*.py` | 4 modules | 300 |
| **Total** | | ~5000 |

Plus ~15,000 lines from GemCode = ~20,000 lines total infrastructure.

---

## Appendix B: Command Reference

```bash
# Install
pip install gemtrade  # or pip install -e . for dev

# Run trading mode
gemtrade -C /path/to/project --super

# Check status
gemtrade status

# View trade journal
gemtrade journal

# View signals
gemtrade signals

# Manual analysis
gemtrade analyze XAU/USD

# Backtest
gemtrade backtest --strategy ema_crossover --from 2025-01-01

# Paper trading
gemtrade paper --duration 1w

# Live trading (after paper validation)
gemtrade live --capital 1000 --confirm
```

---

*This plan was developed through analysis of GemCode, Automaton, OpenTraitor, FinRL, and FinRobot, combined with professional trading experience.*
