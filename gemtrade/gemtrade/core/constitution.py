"""
Trading Constitution - Immutable Risk Rules

These rules CANNOT be modified by any agent. They are the foundation
of survival and must be enforced by the Overseer at all times.

Inspired by Automaton's constitution.md - the three laws hierarchy.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, List, Dict, Any


class RuleSeverity(Enum):
    """Severity of constitutional rule violation."""
    BLOCK = "block"      # Reject trade immediately
    HALT = "halt"        # Stop all trading, may need human
    WARN = "warn"        # Log warning, allow with caution
    LOG = "log"          # Log only, informational


@dataclass(frozen=True)  # Immutable - cannot be changed at runtime
class ConstitutionalRule:
    """An immutable trading rule that cannot be modified by agents."""
    id: str
    name: str
    description: str
    severity: RuleSeverity
    check_code: str  # Python expression to evaluate


# THE CONSTITUTION
# These rules are IMMUTABLE and cannot be changed by any agent.
# Designed for AGGRESSIVE small capital trading (₹5,000) with HIGH LEVERAGE.
# 
# Philosophy: Allow aggressive per-trade risk, but have HARD STOPS to prevent wipeout.

CONSTITUTION: List[ConstitutionalRule] = [
    # ═══════════════════════════════════════════════════════════════
    # FIRST LAW: Every Trade Has a Stop Loss (Non-Negotiable)
    # ═══════════════════════════════════════════════════════════════
    
    ConstitutionalRule(
        id="LAW_1_STOP_LOSS",
        name="First Law: Stop Loss Required",
        description="Every trade MUST have a stop loss defined before entry. No exceptions. "
                    "This is the ONLY thing that makes aggressive trading survivable.",
        severity=RuleSeverity.BLOCK,
        check_code="signal.get('stop_loss') is not None and signal['stop_loss'] > 0"
    ),
    
    ConstitutionalRule(
        id="LAW_1_MAX_LOSS_PER_TRADE",
        name="First Law: Maximum Loss Per Trade",
        description="No single trade may risk more than 10% of account equity. "
                    "With ₹5,000 this means max ₹500 risk per trade.",
        severity=RuleSeverity.BLOCK,
        check_code="signal.get('risk_pct', 100) <= 10.0"
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # SECOND LAW: Position Limits (Aggressive but Controlled)
    # ═══════════════════════════════════════════════════════════════
    
    ConstitutionalRule(
        id="LAW_2_MAX_POSITION",
        name="Second Law: Position Size Limit",
        description="No single position may exceed 25% of account equity (with leverage).",
        severity=RuleSeverity.BLOCK,
        check_code="signal.get('position_pct', 100) <= 25.0"
    ),
    
    ConstitutionalRule(
        id="LAW_2_MAX_CONCURRENT",
        name="Second Law: Concurrent Position Limit",
        description="Maximum 2 concurrent open positions. Focus beats diversification at small size.",
        severity=RuleSeverity.BLOCK,
        check_code="state.get('open_position_count', 0) < 2"
    ),
    
    ConstitutionalRule(
        id="LAW_2_RESERVE",
        name="Second Law: Reserve Requirement",
        description="Must maintain 30% of capital as reserve. Allows 70% deployment.",
        severity=RuleSeverity.BLOCK,
        check_code="state.get('exposure_pct', 100) <= 70.0"
    ),
    
    # ═══════════════════════════════════════════════════════════════
    # THIRD LAW: Circuit Breakers (Prevents Wipeout)
    # ═══════════════════════════════════════════════════════════════
    
    ConstitutionalRule(
        id="LAW_3_DAILY_LOSS",
        name="Third Law: Daily Loss Limit",
        description="STOP trading for the day if daily loss exceeds 15%. "
                    "With ₹5,000 this means stop after losing ₹750 in a day.",
        severity=RuleSeverity.HALT,
        check_code="abs(state.get('daily_loss_pct', 0)) < 15.0"
    ),
    
    ConstitutionalRule(
        id="LAW_3_WEEKLY_LOSS",
        name="Third Law: Weekly Loss Limit",
        description="STOP trading for the week if weekly loss exceeds 25%. "
                    "With ₹5,000 this means stop after losing ₹1,250 in a week.",
        severity=RuleSeverity.HALT,
        check_code="abs(state.get('weekly_loss_pct', 0)) < 25.0"
    ),
    
    ConstitutionalRule(
        id="LAW_3_MAX_DRAWDOWN",
        name="Third Law: Maximum Drawdown",
        description="EMERGENCY HALT if drawdown exceeds 40%. "
                    "With ₹5,000 this triggers at ₹2,000 loss from peak. "
                    "Requires human review to resume - prevents total wipeout.",
        severity=RuleSeverity.HALT,
        check_code="state.get('drawdown_pct', 0) < 40.0"
    ),
    
    ConstitutionalRule(
        id="LAW_3_CONSECUTIVE_LOSSES",
        name="Third Law: Consecutive Loss Limit",
        description="Pause trading for 2 hours after 4 consecutive losses. "
                    "Cool down, reassess, don't revenge trade.",
        severity=RuleSeverity.HALT,
        check_code="state.get('consecutive_losses', 0) < 4"
    ),
]


@dataclass
class ValidationResult:
    """Result of constitutional validation."""
    allowed: bool
    violated_rules: List[ConstitutionalRule]
    warnings: List[str]
    must_halt: bool
    
    @property
    def reason(self) -> Optional[str]:
        """Human-readable reason for rejection."""
        if self.allowed:
            return None
        if not self.violated_rules:
            return "Unknown violation"
        rule = self.violated_rules[0]
        return f"{rule.name}: {rule.description}"


def validate_signal(
    signal: Dict[str, Any],
    state: Dict[str, Any]
) -> ValidationResult:
    """
    Validate a trade signal against the constitution.
    
    Args:
        signal: Trade signal dict with keys like 'stop_loss', 'position_pct', etc.
        state: Current trading state dict with keys like 'daily_loss_pct', etc.
        
    Returns:
        ValidationResult with allowed=True if signal passes all rules.
    """
    violated_rules: List[ConstitutionalRule] = []
    warnings: List[str] = []
    must_halt = False
    
    # Create evaluation context
    context = {"signal": signal, "state": state}
    
    for rule in CONSTITUTION:
        try:
            # Evaluate the rule's check code
            passed = eval(rule.check_code, {"__builtins__": {}}, context)
            
            if not passed:
                violated_rules.append(rule)
                
                if rule.severity == RuleSeverity.HALT:
                    must_halt = True
                elif rule.severity == RuleSeverity.WARN:
                    warnings.append(f"{rule.name}: {rule.description}")
                    
        except Exception as e:
            # Rule evaluation failed - err on the side of caution
            violated_rules.append(rule)
            warnings.append(f"Rule {rule.id} evaluation failed: {e}")
    
    # Determine if allowed
    blocking_violations = [
        r for r in violated_rules 
        if r.severity in (RuleSeverity.BLOCK, RuleSeverity.HALT)
    ]
    
    return ValidationResult(
        allowed=len(blocking_violations) == 0,
        violated_rules=violated_rules,
        warnings=warnings,
        must_halt=must_halt
    )


def check_constitutional_limits(state: Dict[str, Any]) -> ValidationResult:
    """
    Check if current state violates any constitutional limits.
    Used for ongoing monitoring, not signal validation.
    
    Args:
        state: Current trading state
        
    Returns:
        ValidationResult indicating if trading should continue
    """
    # Use empty signal - we're just checking state limits
    return validate_signal({}, state)


def get_rule_by_id(rule_id: str) -> Optional[ConstitutionalRule]:
    """Get a constitutional rule by its ID."""
    for rule in CONSTITUTION:
        if rule.id == rule_id:
            return rule
    return None


def format_constitution() -> str:
    """Format the constitution as human-readable text."""
    lines = [
        "=" * 60,
        "GEMTRADE TRADING CONSTITUTION",
        "=" * 60,
        "",
        "These rules are IMMUTABLE and cannot be modified by any agent.",
        "",
    ]
    
    current_law = ""
    for rule in CONSTITUTION:
        law_prefix = rule.id.split("_")[0] + "_" + rule.id.split("_")[1]
        if law_prefix != current_law:
            current_law = law_prefix
            lines.append("-" * 40)
            
        lines.append(f"[{rule.severity.value.upper()}] {rule.name}")
        lines.append(f"  {rule.description}")
        lines.append("")
    
    lines.append("=" * 60)
    return "\n".join(lines)
