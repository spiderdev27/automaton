"""
Trading Constitution — Immutable Safety Rules

These rules CANNOT be overridden by any agent, any reasoning, any circumstance.
They are the hard limits that prevent account wipeout.

Philosophy:
- Be aggressive with individual trades (high leverage, meaningful risk)
- But have ABSOLUTE limits that prevent catastrophe
- Stop losses are MANDATORY — this is what makes high leverage survivable

The Constitution is inspired by Automaton's survival-first approach but
adapted for aggressive small-capital trading.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class LawCategory(Enum):
    """Categories of constitutional laws."""
    POSITION = "position"      # Per-trade limits
    EXPOSURE = "exposure"      # Portfolio-level limits
    DRAWDOWN = "drawdown"      # Loss limits
    EXECUTION = "execution"    # How trades must be executed


@dataclass
class Law:
    """A single constitutional law."""
    id: str
    category: LawCategory
    name: str
    description: str
    parameter: str
    limit: float
    unit: str
    severity: str = "CRITICAL"  # CRITICAL = blocks action, WARNING = alerts
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category.value,
            "name": self.name,
            "description": self.description,
            "parameter": self.parameter,
            "limit": self.limit,
            "unit": self.unit,
            "severity": self.severity,
        }


# ══════════════════════════════════════════════════════════════════════════════
#                           THE IMMUTABLE LAWS
# ══════════════════════════════════════════════════════════════════════════════

TRADING_LAWS = [
    # ── EXECUTION LAWS ────────────────────────────────────────────────────────
    Law(
        id="LAW_0_STOP_LOSS",
        category=LawCategory.EXECUTION,
        name="Mandatory Stop Loss",
        description="Every trade MUST have a stop loss. No exceptions. Ever.",
        parameter="has_stop_loss",
        limit=1.0,  # Boolean: must be true (1.0)
        unit="boolean",
        severity="CRITICAL",
    ),
    
    # ── POSITION LAWS ─────────────────────────────────────────────────────────
    Law(
        id="LAW_1_MAX_RISK",
        category=LawCategory.POSITION,
        name="Maximum Risk Per Trade",
        description="Maximum capital that can be lost on any single trade.",
        parameter="risk_per_trade_pct",
        limit=10.0,
        unit="percent",
        severity="CRITICAL",
    ),
    Law(
        id="LAW_2_MAX_POSITION",
        category=LawCategory.POSITION,
        name="Maximum Position Size",
        description="Maximum position size as percentage of available capital.",
        parameter="position_size_pct",
        limit=25.0,
        unit="percent",
        severity="CRITICAL",
    ),
    
    # ── EXPOSURE LAWS ─────────────────────────────────────────────────────────
    Law(
        id="LAW_3_MAX_CONCURRENT",
        category=LawCategory.EXPOSURE,
        name="Maximum Concurrent Positions",
        description="Maximum number of positions open at once. Focus beats diversification.",
        parameter="concurrent_positions",
        limit=2,
        unit="count",
        severity="CRITICAL",
    ),
    Law(
        id="LAW_4_MIN_RESERVE",
        category=LawCategory.EXPOSURE,
        name="Minimum Reserve",
        description="Minimum capital that must remain untouched as buffer.",
        parameter="reserve_pct",
        limit=30.0,
        unit="percent",
        severity="CRITICAL",
    ),
    
    # ── DRAWDOWN LAWS ─────────────────────────────────────────────────────────
    Law(
        id="LAW_5_DAILY_LOSS",
        category=LawCategory.DRAWDOWN,
        name="Daily Loss Limit",
        description="Maximum loss allowed in a single day. Trading halts after this.",
        parameter="daily_loss_pct",
        limit=15.0,
        unit="percent",
        severity="CRITICAL",
    ),
    Law(
        id="LAW_6_WEEKLY_LOSS",
        category=LawCategory.DRAWDOWN,
        name="Weekly Loss Limit",
        description="Maximum loss allowed in a week. Trading halts after this.",
        parameter="weekly_loss_pct",
        limit=25.0,
        unit="percent",
        severity="CRITICAL",
    ),
    Law(
        id="LAW_7_MAX_DRAWDOWN",
        category=LawCategory.DRAWDOWN,
        name="Maximum Drawdown",
        description="Maximum drawdown from peak before emergency mode.",
        parameter="max_drawdown_pct",
        limit=40.0,
        unit="percent",
        severity="CRITICAL",
    ),
    Law(
        id="LAW_8_CONSECUTIVE_LOSSES",
        category=LawCategory.DRAWDOWN,
        name="Consecutive Loss Pause",
        description="Pause trading after this many consecutive losses.",
        parameter="consecutive_losses",
        limit=4,
        unit="count",
        severity="CRITICAL",
    ),
]


# ══════════════════════════════════════════════════════════════════════════════
#                           VALIDATION ENGINE
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class ValidationResult:
    """Result of constitutional validation."""
    is_valid: bool
    violations: list[dict]
    warnings: list[dict]
    
    @property
    def can_proceed(self) -> bool:
        """Can proceed only if no CRITICAL violations."""
        return len(self.violations) == 0
    
    def to_dict(self) -> dict:
        return {
            "is_valid": self.is_valid,
            "can_proceed": self.can_proceed,
            "violations": self.violations,
            "warnings": self.warnings,
        }


class Constitution:
    """
    The Trading Constitution — enforcer of immutable rules.
    
    This class is the GATEKEEPER. Every trade must pass through it.
    It cannot be bypassed, overridden, or reasoned with.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self.laws = {law.id: law for law in TRADING_LAWS}
        
        # Load any custom limits (can only be MORE restrictive, not less)
        self._load_custom_limits()
    
    def _load_custom_limits(self) -> None:
        """Load custom limits if they exist. Can only be MORE restrictive."""
        config_path = self.project_root / ".gemcode" / "trading" / "constitution.json"
        if not config_path.is_file():
            return
        
        try:
            custom = json.loads(config_path.read_text(encoding="utf-8"))
            for law_id, new_limit in custom.get("limits", {}).items():
                if law_id in self.laws:
                    law = self.laws[law_id]
                    # Can only make limits MORE restrictive
                    if law.unit == "percent" and new_limit < law.limit:
                        # For percentages, lower is more restrictive
                        law.limit = new_limit
                    elif law.unit == "count" and new_limit < law.limit:
                        # For counts, lower is more restrictive
                        law.limit = new_limit
        except Exception:
            pass
    
    def validate_trade(
        self,
        *,
        has_stop_loss: bool,
        risk_per_trade_pct: float,
        position_size_pct: float,
        current_positions: int,
        reserve_remaining_pct: float,
        daily_loss_pct: float,
        weekly_loss_pct: float,
        current_drawdown_pct: float,
        consecutive_losses: int,
    ) -> ValidationResult:
        """
        Validate a proposed trade against the constitution.
        
        Returns ValidationResult with violations that BLOCK and warnings that ALERT.
        """
        violations = []
        warnings = []
        
        checks = [
            ("LAW_0_STOP_LOSS", 1.0 if has_stop_loss else 0.0),
            ("LAW_1_MAX_RISK", risk_per_trade_pct),
            ("LAW_2_MAX_POSITION", position_size_pct),
            ("LAW_3_MAX_CONCURRENT", current_positions + 1),  # +1 for new position
            ("LAW_4_MIN_RESERVE", 100 - reserve_remaining_pct),  # Inverted: using more = higher value
            ("LAW_5_DAILY_LOSS", daily_loss_pct),
            ("LAW_6_WEEKLY_LOSS", weekly_loss_pct),
            ("LAW_7_MAX_DRAWDOWN", current_drawdown_pct),
            ("LAW_8_CONSECUTIVE_LOSSES", consecutive_losses),
        ]
        
        for law_id, value in checks:
            law = self.laws[law_id]
            
            if law.unit == "boolean":
                violated = value < law.limit  # For boolean, must be >= limit (1.0)
            else:
                violated = value > law.limit  # For others, must be <= limit
            
            if violated:
                violation = {
                    "law_id": law.id,
                    "law_name": law.name,
                    "description": law.description,
                    "limit": law.limit,
                    "actual": value,
                    "unit": law.unit,
                }
                
                if law.severity == "CRITICAL":
                    violations.append(violation)
                else:
                    warnings.append(violation)
        
        return ValidationResult(
            is_valid=len(violations) == 0,
            violations=violations,
            warnings=warnings,
        )
    
    def get_trade_limits(self, capital_paise: int, current_drawdown_pct: float = 0) -> dict:
        """
        Get current trading limits based on constitution and capital.
        
        Returns practical limits in absolute terms.
        """
        capital_inr = capital_paise / 100
        
        max_risk_law = self.laws["LAW_1_MAX_RISK"]
        max_position_law = self.laws["LAW_2_MAX_POSITION"]
        reserve_law = self.laws["LAW_4_MIN_RESERVE"]
        
        # Available capital (after reserve)
        available_pct = 100 - reserve_law.limit
        available_inr = capital_inr * (available_pct / 100)
        
        # Max risk per trade
        max_risk_inr = capital_inr * (max_risk_law.limit / 100)
        
        # Max position size
        max_position_inr = capital_inr * (max_position_law.limit / 100)
        
        return {
            "capital_inr": capital_inr,
            "available_inr": available_inr,
            "reserve_inr": capital_inr - available_inr,
            "max_risk_per_trade_inr": max_risk_inr,
            "max_position_inr": max_position_inr,
            "max_concurrent": int(self.laws["LAW_3_MAX_CONCURRENT"].limit),
            "daily_loss_limit_inr": capital_inr * (self.laws["LAW_5_DAILY_LOSS"].limit / 100),
            "weekly_loss_limit_inr": capital_inr * (self.laws["LAW_6_WEEKLY_LOSS"].limit / 100),
        }
    
    def format_laws(self) -> str:
        """Format all laws for display."""
        lines = ["═══ TRADING CONSTITUTION ═══", ""]
        
        for category in LawCategory:
            category_laws = [l for l in self.laws.values() if l.category == category]
            if not category_laws:
                continue
            
            lines.append(f"── {category.value.upper()} LAWS ──")
            for law in category_laws:
                unit_str = f"{law.limit}{law.unit[0]}" if law.unit != "boolean" else "Required"
                lines.append(f"  {law.name}: {unit_str}")
                lines.append(f"    {law.description}")
            lines.append("")
        
        return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#                           CONVENIENCE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

_constitution: Optional[Constitution] = None


def get_constitution(project_root: Optional[Path] = None) -> Constitution:
    """Get or create the global constitution instance."""
    global _constitution
    if _constitution is None or project_root:
        _constitution = Constitution(project_root)
    return _constitution


def validate_trade(**kwargs) -> ValidationResult:
    """Validate a trade against the constitution."""
    return get_constitution().validate_trade(**kwargs)


def get_trade_limits(capital_paise: int, **kwargs) -> dict:
    """Get current trade limits."""
    return get_constitution().get_trade_limits(capital_paise, **kwargs)
