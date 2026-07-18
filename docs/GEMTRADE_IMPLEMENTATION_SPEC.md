# GemTrade: Technical Implementation Specification

**Version**: 0.2.0  
**Status**: Design Document  
**Base**: GemCode v0.4.25 + Automaton Concepts

---

## 1. Architecture Overview

### 1.1 Core Decision: GemCode as Foundation

GemTrade extends **GemCode** (not Automaton) because GemCode provides:

| GemCode Feature | Trading Application |
|-----------------|---------------------|
| Agent Mesh (background thread + async) | Trading agents run 24/7 without blocking |
| Event Bus (`job.report`, `org.report`) | Trading signals, price alerts, execution reports |
| Self-Healing Loop | Auto-verify trades, auto-fix positions |
| Tool Synthesis | Create custom indicators from patterns |
| Codebase Awareness | → **Market Awareness** (structure graph → market structure) |
| Habits & Triggers | Trading schedules, news event triggers |
| Delegation Learning | Strategy performance tracking |
| Fleet Reports | Trade reports persisted for learning |

**What we port from Automaton:**

| Automaton Concept | GemTrade Implementation |
|-------------------|-------------------------|
| Survival Tiers | Operating modes based on capital |
| Constitutional Limits | Immutable risk rules (Overseer) |
| Financial State | Capital tracking, P&L |
| Treasury Policy | Risk policy engine |
| Child Spawning | Strategy instance spawning |
| Memory System | Trading journal, procedural memory |

### 1.2 Directory Structure

```
gemcode/
├── src/
│   └── gemcode/
│       ├── trading/                    # NEW: Trading Extension
│       │   ├── __init__.py
│       │   ├── config.py              # TradingConfig, risk limits
│       │   ├── constitution.py        # Immutable risk rules
│       │   ├── survival.py            # Survival tiers, operating modes
│       │   │
│       │   ├── agents/                # Trading-specific org members
│       │   │   ├── __init__.py
│       │   │   ├── overseer.py        # Constitutional enforcement
│       │   │   ├── analyst.py         # Market analysis
│       │   │   ├── strategist.py      # Decision making
│       │   │   ├── executor.py        # Order execution
│       │   │   └── learner.py         # Post-trade analysis
│       │   │
│       │   ├── exchange/              # Exchange connectors
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # ExchangeConnector interface
│       │   │   ├── paper.py           # Paper trading
│       │   │   └── oanda.py           # OANDA for XAU/USD
│       │   │
│       │   ├── strategies/            # Trading strategies
│       │   │   ├── __init__.py
│       │   │   ├── base.py            # Strategy interface
│       │   │   ├── ema_crossover.py   # Simple starting strategy
│       │   │   └── registry.py        # Strategy registry
│       │   │
│       │   ├── indicators/            # Technical indicators
│       │   │   ├── __init__.py
│       │   │   ├── ema.py
│       │   │   ├── rsi.py
│       │   │   ├── atr.py
│       │   │   └── macd.py
│       │   │
│       │   ├── memory/                # Trading-specific memory
│       │   │   ├── __init__.py
│       │   │   ├── trade_journal.py   # Episodic: trade records
│       │   │   ├── regime_memory.py   # Semantic: market regimes
│       │   │   ├── procedural.py      # "Feeling": behavioral adjustments
│       │   │   └── error_patterns.py  # Mistakes to avoid
│       │   │
│       │   └── tools/                 # Trading tools for agents
│       │       ├── __init__.py
│       │       ├── market_data.py     # Price feeds, candles
│       │       ├── order_tools.py     # Place/modify/cancel orders
│       │       ├── position_tools.py  # Position management
│       │       ├── analysis_tools.py  # Indicator calculations
│       │       └── risk_tools.py      # Position sizing, risk calc
│       │
│       ├── tools/
│       │   └── trading_tools.py       # Integration with GemCode tools
│       │
│       └── agent_mesh.py              # Extended with trading awareness
│
└── .gemcode/
    └── trading/                       # Trading state files
        ├── config.json                # Trading configuration
        ├── state.json                 # Current trading state
        ├── constitution.json          # Immutable risk rules
        ├── trade_journal.jsonl        # Trade history
        ├── regime_memory.json         # Market regime memory
        ├── procedural_memory.json     # Behavioral adjustments
        ├── error_patterns.json        # Mistakes learned
        └── strategies/                # Strategy configs
```

---

## 2. GemCode Integration Points

### 2.1 Agent Mesh Extension

The Agent Mesh is the perfect foundation for trading agents. We extend it to:

```python
# gemcode/src/gemcode/trading/mesh_integration.py

from gemcode.agent_mesh import AgentMesh, AgentJob
from gemcode.event_bus import get_bus
from gemcode.trading.constitution import TradingConstitution
from gemcode.trading.survival import SurvivalManager

class TradingMesh:
    """Extends AgentMesh with trading-specific coordination."""
    
    def __init__(self, cfg, trading_config):
        self.mesh = get_mesh(cfg)  # Reuse existing mesh
        self.bus = get_bus()
        self.constitution = TradingConstitution(trading_config)
        self.survival = SurvivalManager(trading_config)
        
        # Subscribe to trading-specific events
        self.bus.subscribe("trade.signal", "trading", self._handle_trade_signal)
        self.bus.subscribe("trade.executed", "trading", self._handle_trade_executed)
        self.bus.subscribe("market.regime_change", "trading", self._handle_regime_change)
        self.bus.subscribe("price.alert", "trading", self._handle_price_alert)
        
    async def _handle_trade_signal(self, msg):
        """Process trade signal from Strategist."""
        signal = msg.payload
        
        # Constitutional check (cannot be bypassed)
        validation = self.constitution.validate_signal(signal)
        if validation.rejected:
            self.bus.publish("trade.rejected", {
                "signal": signal,
                "reason": validation.reason,
                "rule": validation.rule
            })
            return
            
        # Check survival tier
        if not self.survival.can_trade():
            self.bus.publish("trade.rejected", {
                "signal": signal,
                "reason": f"Survival tier too low: {self.survival.current_tier}"
            })
            return
            
        # Forward to Executor
        job = AgentJob(
            job_id=f"execute-{signal['id']}",
            prompt=f"Execute trade signal: {signal}",
            member_name="executor",
            priority=1,  # High priority
            meta={"signal": signal}
        )
        self.mesh.enqueue(job)
```

### 2.2 Event Bus Topics for Trading

Extend GemCode's event bus with trading-specific topics:

```python
# Trading-specific event topics

TRADING_TOPICS = {
    # Price & Market Data
    "price.tick": "Real-time price update",
    "price.alert": "Price threshold crossed",
    "market.regime_change": "Market regime changed",
    "market.news": "High-impact news event",
    
    # Trading Signals & Execution
    "trade.signal": "New trade signal from Strategist",
    "trade.validated": "Signal passed Overseer validation",
    "trade.rejected": "Signal rejected by Overseer",
    "trade.executed": "Order filled by exchange",
    "trade.closed": "Position closed",
    
    # Risk & Survival
    "risk.limit_warning": "Approaching risk limit",
    "risk.circuit_breaker": "Circuit breaker activated",
    "survival.tier_change": "Survival tier changed",
    
    # Learning
    "learn.trade_complete": "Trade completed, ready for analysis",
    "learn.pattern_detected": "New error/success pattern detected",
    "learn.procedural_update": "Procedural memory updated"
}
```

### 2.3 Trading Habits (Scheduled Tasks)

Use GemCode's habit system for trading schedules:

```python
# .gemcode/habits.json (trading entries)

{
  "habits": [
    {
      "name": "market-scan",
      "agent": "analyst",
      "prompt": "Scan XAU/USD for trade setups. Report regime and any signals.",
      "every_minutes": 15,
      "enabled": true
    },
    {
      "name": "position-check",
      "agent": "executor",
      "prompt": "Check all open positions. Update stops if needed.",
      "every_minutes": 5,
      "enabled": true
    },
    {
      "name": "daily-review",
      "agent": "learner",
      "prompt": "Review all trades from today. Update procedural memory.",
      "daily_at": "22:00",
      "enabled": true
    },
    {
      "name": "risk-audit",
      "agent": "overseer",
      "prompt": "Audit current risk exposure. Check all limits.",
      "every_minutes": 30,
      "enabled": true
    }
  ]
}
```

### 2.4 Trading Triggers (Event-Driven)

Use GemCode's trigger system for market events:

```python
# .gemcode/triggers.json (trading entries)

{
  "triggers": [
    {
      "agent": "overseer",
      "on_topic": "trade.signal",
      "when": {},
      "action": "Validate this trade signal against constitutional limits.",
      "cooldown_s": 0,
      "enabled": true
    },
    {
      "agent": "learner",
      "on_topic": "trade.closed",
      "when": {},
      "action": "Analyze this completed trade. Update memory.",
      "cooldown_s": 10,
      "enabled": true
    },
    {
      "agent": "strategist",
      "on_topic": "market.regime_change",
      "when": {},
      "action": "Regime changed. Re-evaluate all open positions and pending signals.",
      "cooldown_s": 60,
      "enabled": true
    }
  ]
}
```

---

## 3. Survival System (From Automaton)

### 3.1 Survival Tiers

Port Automaton's survival concept to GemCode:

```python
# gemcode/src/gemcode/trading/survival.py

from enum import Enum
from dataclasses import dataclass
from typing import Optional
import time

class SurvivalTier(Enum):
    """Operating modes based on capital."""
    DEAD = "dead"           # Cannot trade, must recover
    CRITICAL = "critical"   # Minimal operations only
    LOW = "low"             # Reduced position sizes
    NORMAL = "normal"       # Standard operations
    HIGH = "high"           # Full capabilities

SURVIVAL_THRESHOLDS = {
    SurvivalTier.HIGH: 10000,      # > $100 (in cents)
    SurvivalTier.NORMAL: 5000,     # > $50
    SurvivalTier.LOW: 1000,        # > $10
    SurvivalTier.CRITICAL: 100,    # > $1
    SurvivalTier.DEAD: 0,          # $0 or negative
}

TIER_CAPABILITIES = {
    SurvivalTier.HIGH: {
        "max_position_pct": 5.0,
        "can_open_new": True,
        "can_add_to_position": True,
        "analysis_depth": "full",
    },
    SurvivalTier.NORMAL: {
        "max_position_pct": 3.0,
        "can_open_new": True,
        "can_add_to_position": True,
        "analysis_depth": "standard",
    },
    SurvivalTier.LOW: {
        "max_position_pct": 1.0,
        "can_open_new": True,
        "can_add_to_position": False,
        "analysis_depth": "minimal",
    },
    SurvivalTier.CRITICAL: {
        "max_position_pct": 0.5,
        "can_open_new": False,  # Close-only mode
        "can_add_to_position": False,
        "analysis_depth": "none",
    },
    SurvivalTier.DEAD: {
        "max_position_pct": 0,
        "can_open_new": False,
        "can_add_to_position": False,
        "analysis_depth": "none",
    },
}

@dataclass
class FinancialState:
    """Current financial state."""
    balance_cents: int
    equity_cents: int
    unrealized_pnl_cents: int
    daily_pnl_cents: int
    weekly_pnl_cents: int
    drawdown_pct: float
    last_updated: float

class SurvivalManager:
    """Manages survival tier based on financial state."""
    
    def __init__(self, config):
        self.config = config
        self.current_tier = SurvivalTier.NORMAL
        self.financial_state: Optional[FinancialState] = None
        
    def update_state(self, state: FinancialState) -> SurvivalTier:
        """Update financial state and recalculate tier."""
        self.financial_state = state
        
        # Determine tier from balance
        new_tier = SurvivalTier.DEAD
        for tier, threshold in sorted(SURVIVAL_THRESHOLDS.items(), 
                                       key=lambda x: x[1], reverse=True):
            if state.balance_cents >= threshold:
                new_tier = tier
                break
                
        # Downgrade for excessive drawdown
        if state.drawdown_pct >= self.config.max_drawdown_pct:
            new_tier = SurvivalTier.CRITICAL
            
        # Downgrade for daily loss limit
        daily_loss_pct = abs(state.daily_pnl_cents) / max(state.balance_cents, 1) * 100
        if state.daily_pnl_cents < 0 and daily_loss_pct >= self.config.max_daily_loss_pct:
            new_tier = min(new_tier, SurvivalTier.CRITICAL, key=lambda x: x.value)
            
        self.current_tier = new_tier
        return new_tier
        
    def can_trade(self) -> bool:
        """Check if trading is allowed in current tier."""
        return TIER_CAPABILITIES[self.current_tier]["can_open_new"]
        
    def get_max_position_pct(self) -> float:
        """Get maximum position size percentage for current tier."""
        return TIER_CAPABILITIES[self.current_tier]["max_position_pct"]
```

### 3.2 Constitution (Immutable Rules)

Port Automaton's constitution concept:

```python
# gemcode/src/gemcode/trading/constitution.py

from dataclasses import dataclass
from typing import Optional, List
import json
from pathlib import Path

@dataclass
class ConstitutionalRule:
    """An immutable trading rule."""
    id: str
    name: str
    description: str
    check: str  # Python expression to evaluate
    action: str  # What happens if violated
    severity: str  # "block", "warn", "log"

@dataclass 
class ValidationResult:
    """Result of constitutional validation."""
    rejected: bool
    reason: Optional[str] = None
    rule: Optional[str] = None
    warnings: List[str] = None

# These rules CANNOT be modified by agents
CONSTITUTIONAL_RULES = [
    ConstitutionalRule(
        id="max_position_size",
        name="Maximum Position Size",
        description="No single position may exceed 5% of account",
        check="signal.position_pct <= 5.0",
        action="Reject trade signal",
        severity="block"
    ),
    ConstitutionalRule(
        id="stop_loss_required",
        name="Stop Loss Required",
        description="Every trade must have a stop loss",
        check="signal.stop_loss is not None and signal.stop_loss > 0",
        action="Reject trade signal",
        severity="block"
    ),
    ConstitutionalRule(
        id="max_daily_loss",
        name="Maximum Daily Loss",
        description="Halt trading if daily loss exceeds 3%",
        check="state.daily_loss_pct < 3.0",
        action="Activate circuit breaker",
        severity="block"
    ),
    ConstitutionalRule(
        id="max_weekly_loss",
        name="Maximum Weekly Loss",
        description="Halt trading if weekly loss exceeds 10%",
        check="state.weekly_loss_pct < 10.0",
        action="Activate circuit breaker",
        severity="block"
    ),
    ConstitutionalRule(
        id="max_drawdown",
        name="Maximum Drawdown",
        description="Emergency halt if drawdown exceeds 20%",
        check="state.drawdown_pct < 20.0",
        action="Emergency halt, alert human",
        severity="block"
    ),
    ConstitutionalRule(
        id="max_concurrent_positions",
        name="Maximum Concurrent Positions",
        description="No more than 3 positions at once",
        check="state.open_positions <= 3",
        action="Reject new trade signal",
        severity="block"
    ),
    ConstitutionalRule(
        id="minimum_reserve",
        name="Minimum Reserve",
        description="Must maintain 50% reserve at all times",
        check="state.exposure_pct <= 50.0",
        action="Reject new trade signal",
        severity="block"
    ),
]

class TradingConstitution:
    """Enforces immutable trading rules. Cannot be modified by agents."""
    
    def __init__(self, config):
        self.config = config
        self.rules = CONSTITUTIONAL_RULES.copy()
        # Rules are frozen - agents cannot modify them
        
    def validate_signal(self, signal: dict, state: dict) -> ValidationResult:
        """Validate a trade signal against constitutional rules."""
        warnings = []
        
        for rule in self.rules:
            try:
                # Create evaluation context
                context = {"signal": signal, "state": state}
                
                # Evaluate rule
                passed = eval(rule.check, {"__builtins__": {}}, context)
                
                if not passed:
                    if rule.severity == "block":
                        return ValidationResult(
                            rejected=True,
                            reason=f"{rule.name}: {rule.description}",
                            rule=rule.id
                        )
                    else:
                        warnings.append(f"{rule.name}: {rule.description}")
                        
            except Exception as e:
                # Rule evaluation failed - err on side of caution
                return ValidationResult(
                    rejected=True,
                    reason=f"Rule evaluation failed: {rule.id} - {str(e)}",
                    rule=rule.id
                )
                
        return ValidationResult(rejected=False, warnings=warnings)
        
    def check_circuit_breakers(self, state: dict) -> Optional[str]:
        """Check if any circuit breaker should activate."""
        if state.get("daily_loss_pct", 0) >= 3.0:
            return "daily_loss_limit"
        if state.get("weekly_loss_pct", 0) >= 10.0:
            return "weekly_loss_limit"
        if state.get("drawdown_pct", 0) >= 20.0:
            return "max_drawdown"
        if state.get("consecutive_losses", 0) >= 5:
            return "consecutive_losses"
        return None
```

---

## 4. Trading Agents (Org Members)

### 4.1 Agent Fleet Setup

Trading agents are registered as GemCode org members:

```python
# gemcode/src/gemcode/trading/agents/__init__.py

from gemcode.org import hire_member

def setup_trading_fleet(cfg):
    """Setup the trading agent fleet."""
    
    # Overseer - Constitutional enforcement (highest authority)
    hire_member(
        cfg,
        name="overseer",
        title="Risk Overseer",
        kind="subagent",
        description="""Constitutional risk enforcement agent.
        
        AUTHORITY: Highest. Can halt all trading. Cannot be overridden.
        
        RESPONSIBILITIES:
        - Validate all trade signals against constitutional rules
        - Monitor risk limits (position size, daily loss, drawdown)
        - Activate circuit breakers when limits breached
        - Alert human operator on critical events
        
        CANNOT:
        - Place trades
        - Modify strategies
        - Be shut down by other agents
        """,
        skill_name="trading/overseer"
    )
    
    # Analyst - Market analysis (data only)
    hire_member(
        cfg,
        name="analyst",
        title="Market Analyst",
        kind="subagent",
        description="""Market data analysis agent.
        
        RESPONSIBILITIES:
        - Fetch and process market data
        - Identify market regime (trending, ranging, volatile)
        - Calculate technical indicators
        - Monitor news and events
        - Provide analysis to Strategist
        
        CANNOT:
        - Place orders
        - Decide to trade
        - Access execution systems
        """,
        skill_name="trading/analyst"
    )
    
    # Strategist - Decision making
    hire_member(
        cfg,
        name="strategist",
        title="Trading Strategist",
        kind="subagent",
        description="""Trading decision agent.
        
        RESPONSIBILITIES:
        - Receive analysis from Analyst
        - Decide whether to trade based on strategy rules
        - Select which strategy to use
        - Generate trade signals with entry/stop/target
        - Send signals to Overseer for validation
        
        CANNOT:
        - Execute trades directly
        - Bypass Overseer validation
        - Modify constitutional rules
        """,
        skill_name="trading/strategist"
    )
    
    # Executor - Order execution
    hire_member(
        cfg,
        name="executor",
        title="Trade Executor",
        kind="subagent",
        description="""Order execution agent.
        
        RESPONSIBILITIES:
        - Execute validated signals from Overseer
        - Manage order lifecycle (place, modify, cancel)
        - Handle partial fills
        - Manage stop losses and take profits
        - Report execution to Learner
        
        CANNOT:
        - Decide to trade independently
        - Exceed position limits
        - Modify strategy parameters
        """,
        skill_name="trading/executor"
    )
    
    # Learner - Post-trade analysis
    hire_member(
        cfg,
        name="learner",
        title="Trade Learner",
        kind="subagent",
        description="""Post-trade analysis and learning agent.
        
        RESPONSIBILITIES:
        - Analyze completed trades (win/lose)
        - Evaluate process quality (not just outcome)
        - Update procedural memory ("feeling" system)
        - Identify error patterns to avoid
        - Propose strategy parameter adjustments
        
        CANNOT:
        - Trade
        - Modify live strategies
        - Access real capital
        """,
        skill_name="trading/learner"
    )
```

### 4.2 Agent Communication Flow

```
                    ┌─────────────────────────────────────────────┐
                    │              GemCode Event Bus               │
                    └─────────────────────────────────────────────┘
                           ▲                    │
                           │                    ▼
    ┌──────────┐    ┌──────────────┐    ┌───────────────┐    ┌──────────┐
    │ Analyst  │───▶│  Strategist  │───▶│   Overseer    │───▶│ Executor │
    │          │    │              │    │ (Constitution) │    │          │
    │ market   │    │ trade.signal │    │ trade.validated│    │ trade    │
    │ analysis │    │              │    │ or rejected    │    │ executed │
    └──────────┘    └──────────────┘    └───────────────┘    └──────────┘
         │                                                         │
         │                                                         │
         │              ┌──────────────┐                          │
         └─────────────▶│   Learner    │◀─────────────────────────┘
                        │              │
                        │ trade.closed │
                        │ learn pattern│
                        └──────────────┘
```

---

## 5. Trading Memory System

### 5.1 Extending GemCode's Memory

GemCode already has memory layers. We add trading-specific memory:

```python
# gemcode/src/gemcode/trading/memory/trade_journal.py

"""Trade Journal - Episodic memory for trades."""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass, asdict

@dataclass
class TradeRecord:
    """A single trade record."""
    id: str
    symbol: str
    direction: str  # "long" or "short"
    strategy: str
    
    # Entry
    entry_time: str
    entry_price: float
    entry_reason: str
    market_regime: str
    
    # Exit
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    
    # Position
    position_size: float = 0.0
    stop_loss: float = 0.0
    take_profit: Optional[float] = None
    
    # Outcome
    profit_loss: Optional[float] = None
    profit_loss_pct: Optional[float] = None
    max_adverse: Optional[float] = None
    max_favorable: Optional[float] = None
    hold_duration_s: Optional[int] = None
    
    # Process evaluation (THE KEY INSIGHT)
    followed_rules: bool = True
    entry_quality: Optional[float] = None  # 0-1
    exit_quality: Optional[float] = None   # 0-1
    behavioral_flags: List[str] = None
    
    # Learning
    lesson_learned: Optional[str] = None
    pattern_identified: Optional[str] = None
    
class TradeJournal:
    """Episodic memory for trades."""
    
    def __init__(self, project_root: Path):
        self.path = project_root / ".gemcode" / "trading" / "trade_journal.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
    def record(self, trade: TradeRecord) -> None:
        """Record a trade."""
        with open(self.path, "a") as f:
            f.write(json.dumps(asdict(trade)) + "\n")
            
    def get_recent(self, limit: int = 20) -> List[TradeRecord]:
        """Get recent trades."""
        if not self.path.exists():
            return []
        trades = []
        with open(self.path) as f:
            for line in f:
                trades.append(TradeRecord(**json.loads(line)))
        return trades[-limit:]
        
    def get_by_strategy(self, strategy: str, limit: int = 50) -> List[TradeRecord]:
        """Get trades for a specific strategy."""
        all_trades = self.get_recent(500)
        return [t for t in all_trades if t.strategy == strategy][-limit:]
        
    def calculate_stats(self, trades: List[TradeRecord]) -> dict:
        """Calculate performance statistics."""
        if not trades:
            return {}
            
        closed = [t for t in trades if t.profit_loss is not None]
        if not closed:
            return {}
            
        wins = [t for t in closed if t.profit_loss > 0]
        losses = [t for t in closed if t.profit_loss < 0]
        
        total_profit = sum(t.profit_loss for t in wins)
        total_loss = abs(sum(t.profit_loss for t in losses))
        
        return {
            "total_trades": len(closed),
            "win_rate": len(wins) / len(closed) if closed else 0,
            "profit_factor": total_profit / total_loss if total_loss > 0 else float('inf'),
            "avg_win": total_profit / len(wins) if wins else 0,
            "avg_loss": total_loss / len(losses) if losses else 0,
            "process_score": sum(t.entry_quality or 0.5 for t in closed) / len(closed),
        }
```

### 5.2 Procedural Memory ("Feeling" System)

This is the core insight - behavioral adjustments that influence future decisions:

```python
# gemcode/src/gemcode/trading/memory/procedural.py

"""Procedural Memory - The "Feeling" System.

This implements behavioral adjustments that influence trading decisions
without explicit retrieval. The agent doesn't "remember" these facts -
it "feels" them through modified behavior.
"""

import json
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, asdict

@dataclass
class ProceduralMemory:
    """A behavioral adjustment learned from experience."""
    id: str
    condition_type: str      # When this applies
    condition_params: dict   # Parameters for condition
    adjustment_type: str     # What to adjust
    adjustment_value: float  # How much to adjust
    
    # Evidence
    supporting_trades: int = 0
    outcome_when_applied: Optional[float] = None
    outcome_when_ignored: Optional[float] = None
    
    # Confidence
    confidence: float = 0.5
    enabled: bool = True

# Example procedural memories that might be learned:
EXAMPLE_MEMORIES = [
    ProceduralMemory(
        id="high_volatility_reduce_size",
        condition_type="volatility_percentile",
        condition_params={"above": 80},
        adjustment_type="position_size_multiplier",
        adjustment_value=0.5,  # Half size in high volatility
        supporting_trades=15,
        outcome_when_applied=2.3,
        outcome_when_ignored=-4.1,
        confidence=0.85
    ),
    ProceduralMemory(
        id="after_loss_wait",
        condition_type="previous_trade_result",
        condition_params={"result": "loss"},
        adjustment_type="entry_delay_minutes",
        adjustment_value=30,  # Wait 30 min after loss
        supporting_trades=12,
        outcome_when_applied=1.8,
        outcome_when_ignored=-2.5,
        confidence=0.78
    ),
    ProceduralMemory(
        id="news_event_skip",
        condition_type="time_to_news",
        condition_params={"within_minutes": 30, "impact": "high"},
        adjustment_type="skip_trade",
        adjustment_value=1.0,
        supporting_trades=8,
        outcome_when_applied=0.0,  # No loss from skipped trades
        outcome_when_ignored=-3.2,
        confidence=0.72
    ),
]

class ProceduralMemoryManager:
    """Manages procedural trading memory."""
    
    def __init__(self, project_root: Path):
        self.path = project_root / ".gemcode" / "trading" / "procedural_memory.json"
        self.memories: List[ProceduralMemory] = []
        self._load()
        
    def _load(self):
        if self.path.exists():
            data = json.loads(self.path.read_text())
            self.memories = [ProceduralMemory(**m) for m in data]
            
    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(m) for m in self.memories]
        self.path.write_text(json.dumps(data, indent=2))
        
    def get_active_adjustments(self, context: dict) -> List[tuple]:
        """
        Get all behavioral adjustments that apply to current context.
        Returns list of (adjustment_type, adjustment_value, confidence).
        
        This is the "feeling" - the agent's behavior is modified without
        explicit reasoning about why.
        """
        adjustments = []
        
        for memory in self.memories:
            if not memory.enabled or memory.confidence < 0.5:
                continue
                
            if self._condition_matches(memory, context):
                adjustments.append((
                    memory.adjustment_type,
                    memory.adjustment_value,
                    memory.confidence
                ))
                
        return adjustments
        
    def _condition_matches(self, memory: ProceduralMemory, context: dict) -> bool:
        """Check if a memory's condition matches current context."""
        ctype = memory.condition_type
        params = memory.condition_params
        
        if ctype == "volatility_percentile":
            return context.get("volatility_percentile", 50) >= params.get("above", 80)
            
        if ctype == "previous_trade_result":
            return context.get("previous_result") == params.get("result")
            
        if ctype == "time_to_news":
            minutes = context.get("minutes_to_news", float('inf'))
            return minutes <= params.get("within_minutes", 30)
            
        if ctype == "consecutive_losses":
            return context.get("consecutive_losses", 0) >= params.get("count", 3)
            
        if ctype == "time_of_day":
            hour = context.get("hour", 12)
            return params.get("start", 0) <= hour < params.get("end", 24)
            
        return False
        
    def update_from_trade(self, context: dict, outcome: float, adjustment_applied: bool):
        """Update procedural memory based on trade outcome."""
        for memory in self.memories:
            if not self._condition_matches(memory, context):
                continue
                
            memory.supporting_trades += 1
            
            if adjustment_applied:
                # Update outcome when applied
                if memory.outcome_when_applied is None:
                    memory.outcome_when_applied = outcome
                else:
                    # Running average
                    n = memory.supporting_trades
                    memory.outcome_when_applied = (
                        (memory.outcome_when_applied * (n - 1) + outcome) / n
                    )
            else:
                # Update outcome when ignored
                if memory.outcome_when_ignored is None:
                    memory.outcome_when_ignored = outcome
                else:
                    n = memory.supporting_trades
                    memory.outcome_when_ignored = (
                        (memory.outcome_when_ignored * (n - 1) + outcome) / n
                    )
                    
            # Update confidence based on comparative outcomes
            if memory.outcome_when_applied is not None and memory.outcome_when_ignored is not None:
                if memory.outcome_when_applied > memory.outcome_when_ignored:
                    memory.confidence = min(0.95, memory.confidence + 0.02)
                else:
                    memory.confidence = max(0.3, memory.confidence - 0.03)
                    
        self._save()
```

---

## 6. Trading Tools

### 6.1 Tool Registration

Add trading tools to GemCode's tool system:

```python
# gemcode/src/gemcode/tools/trading_tools.py

"""Trading tools for GemCode agents."""

from gemcode.config import GemCodeConfig
from gemcode.trading.exchange.base import get_exchange
from gemcode.trading.memory.trade_journal import TradeJournal
from gemcode.trading.memory.procedural import ProceduralMemoryManager

def make_trading_tools(cfg: GemCodeConfig):
    """Build trading function tools."""
    
    exchange = get_exchange(cfg)
    journal = TradeJournal(cfg.project_root)
    procedural = ProceduralMemoryManager(cfg.project_root)
    
    def get_market_data(symbol: str, timeframe: str = "H1", limit: int = 100) -> dict:
        """
        Get OHLCV market data for a symbol.
        
        Args:
            symbol: Trading pair (e.g., "XAU/USD")
            timeframe: Candle timeframe (M1, M5, M15, H1, H4, D1)
            limit: Number of candles to fetch
            
        Returns:
            Dict with candles array and metadata
        """
        candles = exchange.get_ohlcv(symbol, timeframe, limit)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": candles,
            "latest_price": candles[-1]["close"] if candles else None
        }
        
    def get_account_status() -> dict:
        """
        Get current account status including balance, equity, and positions.
        
        Returns:
            Dict with account info and open positions
        """
        info = exchange.get_account_info()
        positions = exchange.get_open_positions()
        return {
            "balance": info["balance"],
            "equity": info["equity"],
            "free_margin": info["free_margin"],
            "open_positions": len(positions),
            "positions": positions
        }
        
    def calculate_indicators(symbol: str, indicators: list) -> dict:
        """
        Calculate technical indicators for a symbol.
        
        Args:
            symbol: Trading pair
            indicators: List of indicator configs, e.g. [{"name": "EMA", "period": 20}]
            
        Returns:
            Dict with indicator values
        """
        from gemcode.trading.indicators import calculate_indicator
        
        candles = exchange.get_ohlcv(symbol, "H1", 200)
        results = {}
        
        for ind in indicators:
            results[f"{ind['name']}_{ind.get('period', '')}"] = calculate_indicator(
                candles, ind["name"], ind.get("period"), ind.get("params", {})
            )
            
        return results
        
    def submit_trade_signal(
        symbol: str,
        direction: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float = None,
        position_pct: float = 2.0,
        strategy: str = "manual",
        reason: str = ""
    ) -> dict:
        """
        Submit a trade signal for validation and execution.
        
        This does NOT execute the trade directly. The signal goes to:
        1. Overseer for constitutional validation
        2. If approved, Executor for execution
        
        Args:
            symbol: Trading pair
            direction: "long" or "short"
            entry_price: Target entry price
            stop_loss: Stop loss price (REQUIRED)
            take_profit: Take profit price (optional)
            position_pct: Position size as % of account (max 5%)
            strategy: Strategy name that generated this signal
            reason: Explanation for the trade
            
        Returns:
            Dict with signal ID and status
        """
        from gemcode.event_bus import get_bus
        import uuid
        
        signal_id = str(uuid.uuid4())[:8]
        signal = {
            "id": signal_id,
            "symbol": symbol,
            "direction": direction,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "position_pct": position_pct,
            "strategy": strategy,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish to bus for Overseer validation
        bus = get_bus()
        bus.publish("trade.signal", signal)
        
        return {
            "signal_id": signal_id,
            "status": "submitted",
            "message": "Signal submitted to Overseer for validation"
        }
        
    def get_trade_history(limit: int = 20, strategy: str = None) -> dict:
        """
        Get recent trade history from the journal.
        
        Args:
            limit: Maximum trades to return
            strategy: Filter by strategy name
            
        Returns:
            Dict with trades and statistics
        """
        if strategy:
            trades = journal.get_by_strategy(strategy, limit)
        else:
            trades = journal.get_recent(limit)
            
        stats = journal.calculate_stats(trades)
        
        return {
            "trades": [t.__dict__ for t in trades],
            "statistics": stats
        }
        
    def get_behavioral_adjustments() -> dict:
        """
        Get active behavioral adjustments (procedural memory).
        
        These represent learned patterns that modify trading behavior
        without explicit reasoning - the "feeling" system.
        
        Returns:
            Dict with active adjustments and their sources
        """
        from gemcode.trading.survival import SurvivalManager
        
        # Build current context
        context = {
            "volatility_percentile": 50,  # Would be calculated
            "previous_result": journal.get_recent(1)[0].profit_loss > 0 if journal.get_recent(1) else None,
            "consecutive_losses": 0,  # Would be calculated
        }
        
        adjustments = procedural.get_active_adjustments(context)
        
        return {
            "context": context,
            "adjustments": [
                {"type": a[0], "value": a[1], "confidence": a[2]}
                for a in adjustments
            ]
        }
        
    return [
        get_market_data,
        get_account_status,
        calculate_indicators,
        submit_trade_signal,
        get_trade_history,
        get_behavioral_adjustments,
    ]
```

---

## 7. Startup & Configuration

### 7.1 Trading Mode Activation

```python
# gemcode/src/gemcode/trading/__init__.py

"""GemTrade - Trading extension for GemCode."""

from pathlib import Path
from gemcode.config import GemCodeConfig

def enable_trading(cfg: GemCodeConfig) -> None:
    """Enable trading mode for GemCode."""
    from gemcode.trading.agents import setup_trading_fleet
    from gemcode.trading.config import load_trading_config
    from gemcode.trading.constitution import TradingConstitution
    from gemcode.trading.survival import SurvivalManager
    
    # Load trading config
    trading_config = load_trading_config(cfg.project_root)
    
    # Setup trading agents as org members
    setup_trading_fleet(cfg)
    
    # Initialize subsystems
    cfg.trading_constitution = TradingConstitution(trading_config)
    cfg.trading_survival = SurvivalManager(trading_config)
    
    # Add trading tools to tool inventory
    from gemcode.tools.trading_tools import make_trading_tools
    cfg.extra_tools.extend(make_trading_tools(cfg))
    
    # Load trading habits and triggers
    _load_trading_habits(cfg)
    _load_trading_triggers(cfg)
    
    print(f"[gemtrade] Trading mode enabled for {trading_config.default_symbol}")

def _load_trading_habits(cfg):
    """Load default trading habits."""
    habits_path = cfg.project_root / ".gemcode" / "habits.json"
    # Add trading habits if not present
    # ...
    
def _load_trading_triggers(cfg):
    """Load default trading triggers."""
    triggers_path = cfg.project_root / ".gemcode" / "triggers.json"
    # Add trading triggers if not present
    # ...
```

### 7.2 CLI Integration

```bash
# Enable trading mode
gemcode -C /path/to/project --trading

# Or in super mode
gemcode -C /path/to/project --super --trading

# Trading-specific commands
gemcode trade status          # Account status
gemcode trade signals         # Pending signals
gemcode trade journal         # Trade history
gemcode trade analyze         # Run analysis
```

---

## 8. Execution Roadmap

### Phase 0: Foundation (GemCode Extension)
- [ ] Create `gemcode/src/gemcode/trading/` module structure
- [ ] Implement `TradingConstitution` with immutable rules
- [ ] Implement `SurvivalManager` with tiers
- [ ] Create trading agent skill files
- [ ] Register trading agents as org members

### Phase 1: Market Infrastructure
- [ ] Implement `ExchangeConnector` interface
- [ ] Implement `PaperTradingConnector`
- [ ] Add market data tools
- [ ] Add indicator calculations
- [ ] Setup trading habits and triggers

### Phase 2: Memory & Learning
- [ ] Implement `TradeJournal` (episodic memory)
- [ ] Implement `ProceduralMemoryManager` ("feeling" system)
- [ ] Implement error pattern detection
- [ ] Integrate with GemCode's delegation learning

### Phase 3: Paper Trading
- [ ] Full agent coordination flow
- [ ] Paper trade XAU/USD with EMA crossover
- [ ] 100 paper trades validation
- [ ] Tune procedural memory thresholds

### Phase 4: Live Integration
- [ ] Implement OANDA connector
- [ ] Micro-live testing ($500-1000)
- [ ] Human oversight dashboard
- [ ] Gradual scaling

---

This specification shows how GemTrade properly **extends GemCode** rather than being built on Automaton. The key is leveraging GemCode's existing multi-agent mesh, event bus, habits, triggers, and memory systems while adding Automaton's survival and constitutional concepts as new capabilities.
