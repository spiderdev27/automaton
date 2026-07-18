"""
Trading State Management

Tracks financial state, open positions, and trading metrics.
Provides persistence to disk and state updates.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pathlib import Path
import json


@dataclass
class Position:
    """An open trading position."""
    id: str
    symbol: str
    direction: str  # "long" or "short"
    
    # Entry
    entry_price: float
    entry_time: datetime
    
    # Current
    current_price: float
    
    # Size
    size: float  # Units/lots
    value: float  # Current value in account currency
    
    # Risk management
    stop_loss: float
    take_profit: Optional[float] = None
    
    # P&L
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    # Tracking
    max_favorable_excursion: float = 0.0
    max_adverse_excursion: float = 0.0
    
    def update_price(self, new_price: float) -> None:
        """Update current price and recalculate P&L."""
        self.current_price = new_price
        
        if self.direction == "long":
            self.unrealized_pnl = (new_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - new_price) * self.size
            
        self.unrealized_pnl_pct = (self.unrealized_pnl / self.value) * 100 if self.value else 0
        
        # Track excursions
        if self.unrealized_pnl > self.max_favorable_excursion:
            self.max_favorable_excursion = self.unrealized_pnl
        if self.unrealized_pnl < -self.max_adverse_excursion:
            self.max_adverse_excursion = abs(self.unrealized_pnl)
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "direction": self.direction,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat(),
            "current_price": self.current_price,
            "size": self.size,
            "value": self.value,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Position":
        """Create from dictionary."""
        data = data.copy()
        data["entry_time"] = datetime.fromisoformat(data["entry_time"])
        return cls(**data)


@dataclass
class TradingState:
    """
    Complete trading state.
    
    Tracks account, positions, P&L, risk metrics, and circuit breakers.
    """
    
    # Account
    balance_cents: int = 0
    equity_cents: int = 0
    margin_used_cents: int = 0
    free_margin_cents: int = 0
    
    # Positions
    open_positions: List[Position] = field(default_factory=list)
    
    # P&L Tracking
    daily_pnl_cents: int = 0
    weekly_pnl_cents: int = 0
    monthly_pnl_cents: int = 0
    total_pnl_cents: int = 0
    
    # Starting values (for calculating percentages)
    day_start_equity_cents: int = 0
    week_start_equity_cents: int = 0
    month_start_equity_cents: int = 0
    
    # Risk Metrics
    peak_equity_cents: int = 0
    current_drawdown_cents: int = 0
    
    # Counters
    trades_today: int = 0
    trades_this_week: int = 0
    wins_today: int = 0
    losses_today: int = 0
    consecutive_losses: int = 0
    consecutive_wins: int = 0
    
    # Circuit Breakers
    circuit_breaker_active: Optional[str] = None
    circuit_breaker_until: Optional[datetime] = None
    trading_halted: bool = False
    halt_reason: Optional[str] = None
    
    # Timestamps
    last_trade_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.utcnow)
    day_reset_at: Optional[datetime] = None
    week_reset_at: Optional[datetime] = None
    
    # ─── Computed Properties ────────────────────────────────────────
    
    @property
    def open_position_count(self) -> int:
        """Number of open positions."""
        return len(self.open_positions)
    
    @property
    def exposure_cents(self) -> int:
        """Total exposure in cents."""
        return sum(int(p.value * 100) for p in self.open_positions)
    
    @property
    def exposure_pct(self) -> float:
        """Exposure as percentage of equity."""
        if self.equity_cents <= 0:
            return 0.0
        return (self.exposure_cents / self.equity_cents) * 100
    
    @property
    def drawdown_pct(self) -> float:
        """Current drawdown as percentage."""
        if self.peak_equity_cents <= 0:
            return 0.0
        return (self.current_drawdown_cents / self.peak_equity_cents) * 100
    
    @property
    def daily_loss_pct(self) -> float:
        """Daily P&L as percentage of starting equity."""
        if self.day_start_equity_cents <= 0:
            return 0.0
        return (self.daily_pnl_cents / self.day_start_equity_cents) * 100
    
    @property
    def weekly_loss_pct(self) -> float:
        """Weekly P&L as percentage of starting equity."""
        if self.week_start_equity_cents <= 0:
            return 0.0
        return (self.weekly_pnl_cents / self.week_start_equity_cents) * 100
    
    # ─── Update Methods ─────────────────────────────────────────────
    
    def update_equity(self, new_equity_cents: int) -> None:
        """Update equity and recalculate drawdown."""
        self.equity_cents = new_equity_cents
        self.last_updated = datetime.utcnow()
        
        # Update peak and drawdown
        if new_equity_cents > self.peak_equity_cents:
            self.peak_equity_cents = new_equity_cents
            self.current_drawdown_cents = 0
        else:
            self.current_drawdown_cents = self.peak_equity_cents - new_equity_cents
    
    def record_trade_result(self, pnl_cents: int) -> None:
        """Record a completed trade result."""
        self.daily_pnl_cents += pnl_cents
        self.weekly_pnl_cents += pnl_cents
        self.monthly_pnl_cents += pnl_cents
        self.total_pnl_cents += pnl_cents
        
        self.trades_today += 1
        self.trades_this_week += 1
        self.last_trade_at = datetime.utcnow()
        
        if pnl_cents >= 0:
            self.wins_today += 1
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        else:
            self.losses_today += 1
            self.consecutive_losses += 1
            self.consecutive_wins = 0
    
    def reset_daily(self) -> None:
        """Reset daily counters (call at day boundary)."""
        self.day_start_equity_cents = self.equity_cents
        self.daily_pnl_cents = 0
        self.trades_today = 0
        self.wins_today = 0
        self.losses_today = 0
        self.day_reset_at = datetime.utcnow()
    
    def reset_weekly(self) -> None:
        """Reset weekly counters (call at week boundary)."""
        self.week_start_equity_cents = self.equity_cents
        self.weekly_pnl_cents = 0
        self.trades_this_week = 0
        self.week_reset_at = datetime.utcnow()
    
    def activate_circuit_breaker(self, breaker_type: str, duration_hours: int = 4) -> None:
        """Activate a circuit breaker."""
        self.circuit_breaker_active = breaker_type
        self.circuit_breaker_until = datetime.utcnow() + timedelta(hours=duration_hours)
    
    def check_circuit_breaker(self) -> bool:
        """Check if circuit breaker is still active."""
        if not self.circuit_breaker_active:
            return False
        if self.circuit_breaker_until and datetime.utcnow() >= self.circuit_breaker_until:
            self.circuit_breaker_active = None
            self.circuit_breaker_until = None
            return False
        return True
    
    def halt_trading(self, reason: str) -> None:
        """Halt all trading (requires manual intervention to resume)."""
        self.trading_halted = True
        self.halt_reason = reason
    
    def resume_trading(self) -> None:
        """Resume trading after halt."""
        self.trading_halted = False
        self.halt_reason = None
    
    # ─── Serialization ──────────────────────────────────────────────
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "balance_cents": self.balance_cents,
            "equity_cents": self.equity_cents,
            "margin_used_cents": self.margin_used_cents,
            "free_margin_cents": self.free_margin_cents,
            "open_positions": [p.to_dict() for p in self.open_positions],
            "daily_pnl_cents": self.daily_pnl_cents,
            "weekly_pnl_cents": self.weekly_pnl_cents,
            "monthly_pnl_cents": self.monthly_pnl_cents,
            "total_pnl_cents": self.total_pnl_cents,
            "day_start_equity_cents": self.day_start_equity_cents,
            "week_start_equity_cents": self.week_start_equity_cents,
            "peak_equity_cents": self.peak_equity_cents,
            "current_drawdown_cents": self.current_drawdown_cents,
            "trades_today": self.trades_today,
            "trades_this_week": self.trades_this_week,
            "consecutive_losses": self.consecutive_losses,
            "consecutive_wins": self.consecutive_wins,
            "circuit_breaker_active": self.circuit_breaker_active,
            "circuit_breaker_until": self.circuit_breaker_until.isoformat() if self.circuit_breaker_until else None,
            "trading_halted": self.trading_halted,
            "halt_reason": self.halt_reason,
            "last_trade_at": self.last_trade_at.isoformat() if self.last_trade_at else None,
            "last_updated": self.last_updated.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "TradingState":
        """Create from dictionary."""
        data = data.copy()
        
        # Parse positions
        if "open_positions" in data:
            data["open_positions"] = [Position.from_dict(p) for p in data["open_positions"]]
        
        # Parse datetimes
        for field_name in ["circuit_breaker_until", "last_trade_at", "last_updated", 
                          "day_reset_at", "week_reset_at"]:
            if field_name in data and data[field_name]:
                data[field_name] = datetime.fromisoformat(data[field_name])
        
        return cls(**data)
    
    def save(self, path: Path) -> None:
        """Save state to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    @classmethod
    def load(cls, path: Path) -> "TradingState":
        """Load state from disk."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)
    
    # ─── For Constitution Validation ────────────────────────────────
    
    def to_validation_dict(self) -> Dict[str, Any]:
        """Convert to dict format expected by constitution validation."""
        return {
            "open_position_count": self.open_position_count,
            "exposure_pct": self.exposure_pct,
            "daily_loss_pct": abs(self.daily_loss_pct) if self.daily_pnl_cents < 0 else 0,
            "weekly_loss_pct": abs(self.weekly_loss_pct) if self.weekly_pnl_cents < 0 else 0,
            "drawdown_pct": self.drawdown_pct,
            "consecutive_losses": self.consecutive_losses,
        }
