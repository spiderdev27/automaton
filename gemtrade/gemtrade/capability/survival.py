"""
Survival System — Tier-Based Adaptive Trading

The agent must earn to survive. As capital changes, behavior adapts:
- High capital → More capability, higher leverage allowed
- Low capital → Reduced risk, protective mode
- Critical → Close-only mode, survival focus
- Dead → Cannot trade

This creates genuine survival pressure that drives intelligent behavior.
The agent isn't following arbitrary rules — it's adapting to survive.

Inspired by Automaton's survival tiers but adapted for INR small-capital trading.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class SurvivalTier(Enum):
    """Survival tiers based on capital."""
    HIGH = "HIGH"         # > ₹50,000 — earned privileges
    NORMAL = "NORMAL"     # > ₹5,000 — starting tier
    LOW = "LOW"           # > ₹1,000 — reduced capabilities
    CRITICAL = "CRITICAL" # > ₹100 — close-only mode
    DEAD = "DEAD"         # ₹0 — cannot trade


@dataclass
class TierCapabilities:
    """What capabilities are available at each tier."""
    tier: SurvivalTier
    max_leverage: int
    max_positions: int
    max_risk_pct: float
    min_stop_loss_pct: float
    can_open_new: bool
    can_trade_news: bool
    description: str


# INR-based thresholds (in paise for precision)
TIER_THRESHOLDS_PAISE = {
    SurvivalTier.HIGH: 5_000_000,      # ₹50,000
    SurvivalTier.NORMAL: 500_000,       # ₹5,000
    SurvivalTier.LOW: 100_000,          # ₹1,000
    SurvivalTier.CRITICAL: 10_000,      # ₹100
    SurvivalTier.DEAD: 0,               # ₹0
}


TIER_CAPABILITIES = {
    SurvivalTier.HIGH: TierCapabilities(
        tier=SurvivalTier.HIGH,
        max_leverage=1000,
        max_positions=3,
        max_risk_pct=10.0,
        min_stop_loss_pct=0.5,
        can_open_new=True,
        can_trade_news=True,
        description="Maximum capability tier. Earned through profitable trading.",
    ),
    SurvivalTier.NORMAL: TierCapabilities(
        tier=SurvivalTier.NORMAL,
        max_leverage=500,
        max_positions=2,
        max_risk_pct=10.0,
        min_stop_loss_pct=1.0,
        can_open_new=True,
        can_trade_news=True,
        description="Starting tier. Full trading capabilities.",
    ),
    SurvivalTier.LOW: TierCapabilities(
        tier=SurvivalTier.LOW,
        max_leverage=200,
        max_positions=1,
        max_risk_pct=7.5,
        min_stop_loss_pct=1.5,
        can_open_new=True,
        can_trade_news=False,
        description="Reduced capability. Focus on capital preservation.",
    ),
    SurvivalTier.CRITICAL: TierCapabilities(
        tier=SurvivalTier.CRITICAL,
        max_leverage=100,
        max_positions=0,
        max_risk_pct=0.0,
        min_stop_loss_pct=2.0,
        can_open_new=False,
        can_trade_news=False,
        description="CLOSE-ONLY mode. Cannot open new positions.",
    ),
    SurvivalTier.DEAD: TierCapabilities(
        tier=SurvivalTier.DEAD,
        max_leverage=0,
        max_positions=0,
        max_risk_pct=0.0,
        min_stop_loss_pct=0.0,
        can_open_new=False,
        can_trade_news=False,
        description="Cannot trade. Account depleted.",
    ),
}


def calculate_tier(balance_paise: int) -> SurvivalTier:
    """Calculate survival tier based on balance."""
    if balance_paise >= TIER_THRESHOLDS_PAISE[SurvivalTier.HIGH]:
        return SurvivalTier.HIGH
    elif balance_paise >= TIER_THRESHOLDS_PAISE[SurvivalTier.NORMAL]:
        return SurvivalTier.NORMAL
    elif balance_paise >= TIER_THRESHOLDS_PAISE[SurvivalTier.LOW]:
        return SurvivalTier.LOW
    elif balance_paise >= TIER_THRESHOLDS_PAISE[SurvivalTier.CRITICAL]:
        return SurvivalTier.CRITICAL
    else:
        return SurvivalTier.DEAD


def get_tier_capabilities(tier: SurvivalTier) -> TierCapabilities:
    """Get capabilities for a tier."""
    return TIER_CAPABILITIES[tier]


@dataclass
class SurvivalState:
    """Current survival state."""
    tier: SurvivalTier
    balance_paise: int
    peak_balance_paise: int
    drawdown_pct: float
    daily_pnl_paise: int
    weekly_pnl_paise: int
    consecutive_losses: int
    is_halted: bool
    halt_reason: Optional[str]
    
    @property
    def balance_inr(self) -> float:
        return self.balance_paise / 100
    
    @property
    def peak_inr(self) -> float:
        return self.peak_balance_paise / 100
    
    @property
    def daily_pnl_inr(self) -> float:
        return self.daily_pnl_paise / 100
    
    @property
    def weekly_pnl_inr(self) -> float:
        return self.weekly_pnl_paise / 100
    
    def to_dict(self) -> dict:
        return {
            "tier": self.tier.value,
            "balance_inr": self.balance_inr,
            "peak_inr": self.peak_inr,
            "drawdown_pct": self.drawdown_pct,
            "daily_pnl_inr": self.daily_pnl_inr,
            "weekly_pnl_inr": self.weekly_pnl_inr,
            "consecutive_losses": self.consecutive_losses,
            "is_halted": self.is_halted,
            "halt_reason": self.halt_reason,
        }


class SurvivalManager:
    """
    Manages survival state and tier transitions.
    
    Tracks:
    - Current balance and tier
    - Peak balance (for drawdown calculation)
    - Daily/weekly P&L (for loss limits)
    - Consecutive losses (for pause trigger)
    - Halt status
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._state_path = self.project_root / ".gemcode" / "trading" / "survival.json"
        self._state: Optional[SurvivalState] = None
    
    def _load_state(self) -> SurvivalState:
        """Load survival state from disk."""
        if self._state is not None:
            return self._state
        
        if self._state_path.is_file():
            try:
                data = json.loads(self._state_path.read_text(encoding="utf-8"))
                self._state = SurvivalState(
                    tier=SurvivalTier(data.get("tier", "NORMAL")),
                    balance_paise=data.get("balance_paise", 500_000),
                    peak_balance_paise=data.get("peak_balance_paise", 500_000),
                    drawdown_pct=data.get("drawdown_pct", 0),
                    daily_pnl_paise=data.get("daily_pnl_paise", 0),
                    weekly_pnl_paise=data.get("weekly_pnl_paise", 0),
                    consecutive_losses=data.get("consecutive_losses", 0),
                    is_halted=data.get("is_halted", False),
                    halt_reason=data.get("halt_reason"),
                )
                return self._state
            except Exception:
                pass
        
        # Default state: ₹5,000 starting capital
        self._state = SurvivalState(
            tier=SurvivalTier.NORMAL,
            balance_paise=500_000,
            peak_balance_paise=500_000,
            drawdown_pct=0,
            daily_pnl_paise=0,
            weekly_pnl_paise=0,
            consecutive_losses=0,
            is_halted=False,
            halt_reason=None,
        )
        return self._state
    
    def _save_state(self) -> None:
        """Save survival state to disk."""
        if self._state is None:
            return
        
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            "tier": self._state.tier.value,
            "balance_paise": self._state.balance_paise,
            "peak_balance_paise": self._state.peak_balance_paise,
            "drawdown_pct": self._state.drawdown_pct,
            "daily_pnl_paise": self._state.daily_pnl_paise,
            "weekly_pnl_paise": self._state.weekly_pnl_paise,
            "consecutive_losses": self._state.consecutive_losses,
            "is_halted": self._state.is_halted,
            "halt_reason": self._state.halt_reason,
        }
        
        self._state_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
    
    def get_state(self) -> SurvivalState:
        """Get current survival state."""
        return self._load_state()
    
    def get_capabilities(self) -> TierCapabilities:
        """Get current capabilities based on tier."""
        state = self._load_state()
        return get_tier_capabilities(state.tier)
    
    def can_trade(self) -> tuple[bool, Optional[str]]:
        """Check if trading is allowed."""
        state = self._load_state()
        
        if state.is_halted:
            return False, state.halt_reason
        
        if state.tier == SurvivalTier.DEAD:
            return False, "Account depleted. Cannot trade."
        
        if state.tier == SurvivalTier.CRITICAL:
            return False, "CRITICAL tier. Close-only mode."
        
        return True, None
    
    def update_balance(self, new_balance_paise: int) -> SurvivalState:
        """Update balance and recalculate tier."""
        state = self._load_state()
        
        old_tier = state.tier
        state.balance_paise = new_balance_paise
        
        # Update peak
        if new_balance_paise > state.peak_balance_paise:
            state.peak_balance_paise = new_balance_paise
        
        # Calculate drawdown
        if state.peak_balance_paise > 0:
            state.drawdown_pct = (
                (state.peak_balance_paise - new_balance_paise) / 
                state.peak_balance_paise * 100
            )
        
        # Calculate new tier
        state.tier = calculate_tier(new_balance_paise)
        
        # Log tier change
        if state.tier != old_tier:
            self._log_tier_change(old_tier, state.tier)
        
        self._save_state()
        return state
    
    def record_trade_result(self, pnl_paise: int) -> SurvivalState:
        """Record a trade result and update state."""
        state = self._load_state()
        
        # Update balance
        state.balance_paise += pnl_paise
        
        # Update daily/weekly P&L
        state.daily_pnl_paise += pnl_paise
        state.weekly_pnl_paise += pnl_paise
        
        # Update consecutive losses
        if pnl_paise < 0:
            state.consecutive_losses += 1
        else:
            state.consecutive_losses = 0
        
        # Check for halt conditions
        self._check_halt_conditions(state)
        
        # Update tier
        state.tier = calculate_tier(state.balance_paise)
        
        # Update peak
        if state.balance_paise > state.peak_balance_paise:
            state.peak_balance_paise = state.balance_paise
        
        # Update drawdown
        if state.peak_balance_paise > 0:
            state.drawdown_pct = (
                (state.peak_balance_paise - state.balance_paise) / 
                state.peak_balance_paise * 100
            )
        
        self._save_state()
        return state
    
    def _check_halt_conditions(self, state: SurvivalState) -> None:
        """Check if trading should be halted."""
        initial_balance = state.peak_balance_paise  # Use peak as reference
        
        # Daily loss limit (15%)
        daily_loss_pct = abs(state.daily_pnl_paise) / initial_balance * 100
        if state.daily_pnl_paise < 0 and daily_loss_pct >= 15:
            state.is_halted = True
            state.halt_reason = f"Daily loss limit reached ({daily_loss_pct:.1f}%)"
            return
        
        # Weekly loss limit (25%)
        weekly_loss_pct = abs(state.weekly_pnl_paise) / initial_balance * 100
        if state.weekly_pnl_paise < 0 and weekly_loss_pct >= 25:
            state.is_halted = True
            state.halt_reason = f"Weekly loss limit reached ({weekly_loss_pct:.1f}%)"
            return
        
        # Drawdown limit (40%)
        if state.drawdown_pct >= 40:
            state.is_halted = True
            state.halt_reason = f"Maximum drawdown reached ({state.drawdown_pct:.1f}%)"
            return
        
        # Consecutive losses (4)
        if state.consecutive_losses >= 4:
            state.is_halted = True
            state.halt_reason = f"Consecutive loss pause ({state.consecutive_losses} losses)"
            return
    
    def reset_daily(self) -> None:
        """Reset daily P&L (call at start of trading day)."""
        state = self._load_state()
        state.daily_pnl_paise = 0
        
        # Can resume if halted due to daily limit
        if state.halt_reason and "Daily" in state.halt_reason:
            state.is_halted = False
            state.halt_reason = None
        
        self._save_state()
    
    def reset_weekly(self) -> None:
        """Reset weekly P&L (call at start of trading week)."""
        state = self._load_state()
        state.weekly_pnl_paise = 0
        
        # Can resume if halted due to weekly limit
        if state.halt_reason and "Weekly" in state.halt_reason:
            state.is_halted = False
            state.halt_reason = None
        
        self._save_state()
    
    def resume_trading(self, force: bool = False) -> bool:
        """
        Resume trading after halt.
        
        Normally requires waiting period. Force=True overrides (use carefully).
        """
        state = self._load_state()
        
        if not state.is_halted:
            return True
        
        # Check if conditions improved
        if state.tier == SurvivalTier.DEAD:
            return False
        
        if force or "consecutive" in (state.halt_reason or "").lower():
            # Consecutive loss pause can be resumed after reflection
            state.is_halted = False
            state.halt_reason = None
            state.consecutive_losses = 0
            self._save_state()
            return True
        
        return False
    
    def _log_tier_change(self, old_tier: SurvivalTier, new_tier: SurvivalTier) -> None:
        """Log tier changes for tracking."""
        # This would integrate with the trading awareness system
        pass
    
    def format_status(self) -> str:
        """Format current status for display."""
        state = self._load_state()
        caps = get_tier_capabilities(state.tier)
        
        tier_emoji = {
            SurvivalTier.HIGH: "🏆",
            SurvivalTier.NORMAL: "🟢",
            SurvivalTier.LOW: "🟡",
            SurvivalTier.CRITICAL: "🔴",
            SurvivalTier.DEAD: "⚫",
        }
        
        lines = [
            f"═══ SURVIVAL STATUS ═══",
            f"",
            f"Tier: {tier_emoji.get(state.tier, '')} {state.tier.value}",
            f"Balance: ₹{state.balance_inr:,.2f}",
            f"Peak: ₹{state.peak_inr:,.2f}",
            f"Drawdown: {state.drawdown_pct:.1f}%",
            f"",
            f"Daily P&L: ₹{state.daily_pnl_inr:,.2f}",
            f"Weekly P&L: ₹{state.weekly_pnl_inr:,.2f}",
            f"Consecutive losses: {state.consecutive_losses}",
            f"",
            f"Capabilities:",
            f"  Max leverage: 1:{caps.max_leverage}",
            f"  Max positions: {caps.max_positions}",
            f"  Max risk/trade: {caps.max_risk_pct}%",
            f"  Can open new: {'Yes' if caps.can_open_new else 'No'}",
            f"  Can trade news: {'Yes' if caps.can_trade_news else 'No'}",
        ]
        
        if state.is_halted:
            lines.extend([
                f"",
                f"⚠️ TRADING HALTED",
                f"Reason: {state.halt_reason}",
            ])
        
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#                           CONVENIENCE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

_manager: Optional[SurvivalManager] = None


def get_survival_manager(project_root: Optional[Path] = None) -> SurvivalManager:
    """Get or create the global survival manager."""
    global _manager
    if _manager is None or project_root:
        _manager = SurvivalManager(project_root)
    return _manager
