"""
Survival Tiers - Operating Modes Based on Capital

Adapted from Automaton's survival mechanics. The agent's capabilities
are automatically adjusted based on available capital.

When capital is high, the agent can:
- Trade with larger positions
- Use more sophisticated models
- Analyze more frequently

When capital is low, the agent must:
- Reduce position sizes
- Use faster/cheaper models
- Eventually enter close-only mode
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class SurvivalTier(Enum):
    """Operating tiers based on account capital."""
    HIGH = "high"           # Plenty of capital, full capabilities
    NORMAL = "normal"       # Standard operations
    LOW = "low"             # Reduced risk, smaller positions
    CRITICAL = "critical"   # Close-only mode, minimal operations
    DEAD = "dead"           # Cannot trade, must recover externally


# Thresholds in cents (to avoid float precision issues)
SURVIVAL_THRESHOLDS: Dict[SurvivalTier, int] = {
    SurvivalTier.HIGH: 50000,      # > $500
    SurvivalTier.NORMAL: 5000,     # > $50
    SurvivalTier.LOW: 1000,        # > $10
    SurvivalTier.CRITICAL: 100,    # > $1
    SurvivalTier.DEAD: 0,          # $0 or negative
}


@dataclass
class TierCapabilities:
    """Capabilities available at each survival tier."""
    
    # Position sizing
    max_position_pct: float      # Maximum position size as % of equity
    can_open_new: bool           # Can open new positions
    can_add_to_position: bool    # Can add to existing positions
    
    # Analysis
    analysis_frequency_minutes: int  # How often to run market scans
    
    # Model selection (for GemCode model routing)
    model_tier: str              # "quality", "balanced", "fast", "none"
    
    # Risk
    max_concurrent_positions: int
    position_size_multiplier: float  # Applied to calculated position sizes


TIER_CAPABILITIES: Dict[SurvivalTier, TierCapabilities] = {
    SurvivalTier.HIGH: TierCapabilities(
        max_position_pct=5.0,
        can_open_new=True,
        can_add_to_position=True,
        analysis_frequency_minutes=15,
        model_tier="quality",
        max_concurrent_positions=3,
        position_size_multiplier=1.0
    ),
    
    SurvivalTier.NORMAL: TierCapabilities(
        max_position_pct=3.0,
        can_open_new=True,
        can_add_to_position=True,
        analysis_frequency_minutes=30,
        model_tier="balanced",
        max_concurrent_positions=3,
        position_size_multiplier=0.75
    ),
    
    SurvivalTier.LOW: TierCapabilities(
        max_position_pct=1.0,
        can_open_new=True,
        can_add_to_position=False,
        analysis_frequency_minutes=60,
        model_tier="fast",
        max_concurrent_positions=2,
        position_size_multiplier=0.5
    ),
    
    SurvivalTier.CRITICAL: TierCapabilities(
        max_position_pct=0.5,
        can_open_new=False,  # CLOSE-ONLY MODE
        can_add_to_position=False,
        analysis_frequency_minutes=120,
        model_tier="fast",
        max_concurrent_positions=1,
        position_size_multiplier=0.25
    ),
    
    SurvivalTier.DEAD: TierCapabilities(
        max_position_pct=0,
        can_open_new=False,
        can_add_to_position=False,
        analysis_frequency_minutes=0,  # No analysis
        model_tier="none",
        max_concurrent_positions=0,
        position_size_multiplier=0
    ),
}


def get_survival_tier(balance_cents: int) -> SurvivalTier:
    """
    Determine survival tier from account balance.
    
    Args:
        balance_cents: Account balance in cents (e.g., $100 = 10000)
        
    Returns:
        The appropriate SurvivalTier
    """
    if balance_cents <= 0:
        return SurvivalTier.DEAD
        
    # Check tiers from highest to lowest
    for tier in [SurvivalTier.HIGH, SurvivalTier.NORMAL, 
                 SurvivalTier.LOW, SurvivalTier.CRITICAL]:
        if balance_cents >= SURVIVAL_THRESHOLDS[tier]:
            return tier
            
    return SurvivalTier.DEAD


def get_capabilities(tier: SurvivalTier) -> TierCapabilities:
    """Get capabilities for a given tier."""
    return TIER_CAPABILITIES[tier]


def can_trade(tier: SurvivalTier) -> bool:
    """Check if trading is allowed at this tier."""
    caps = TIER_CAPABILITIES[tier]
    return caps.can_open_new


def get_max_position_size(tier: SurvivalTier, equity_cents: int) -> int:
    """
    Calculate maximum position size for a tier.
    
    Args:
        tier: Current survival tier
        equity_cents: Current equity in cents
        
    Returns:
        Maximum position size in cents
    """
    caps = TIER_CAPABILITIES[tier]
    return int(equity_cents * caps.max_position_pct / 100)


def format_tier_status(tier: SurvivalTier, balance_cents: int) -> str:
    """Format a human-readable tier status message."""
    caps = TIER_CAPABILITIES[tier]
    balance_usd = balance_cents / 100
    
    if tier == SurvivalTier.DEAD:
        return f"⚫ DEAD - Balance: ${balance_usd:.2f} - Cannot trade"
    
    if tier == SurvivalTier.CRITICAL:
        return (
            f"🔴 CRITICAL - Balance: ${balance_usd:.2f}\n"
            f"   Close-only mode. No new positions allowed.\n"
            f"   Max position: {caps.max_position_pct}%"
        )
    
    if tier == SurvivalTier.LOW:
        return (
            f"🟠 LOW - Balance: ${balance_usd:.2f}\n"
            f"   Reduced risk mode. Position multiplier: {caps.position_size_multiplier}x\n"
            f"   Max position: {caps.max_position_pct}%"
        )
    
    if tier == SurvivalTier.NORMAL:
        return (
            f"🟢 NORMAL - Balance: ${balance_usd:.2f}\n"
            f"   Standard operations.\n"
            f"   Max position: {caps.max_position_pct}%"
        )
    
    return (
        f"🟢 HIGH - Balance: ${balance_usd:.2f}\n"
        f"   Full capabilities enabled.\n"
        f"   Max position: {caps.max_position_pct}%"
    )


class SurvivalManager:
    """
    Manages survival tier based on financial state.
    
    Tracks tier changes and enforces tier-based restrictions.
    """
    
    def __init__(self, initial_balance_cents: int = 0):
        self._balance_cents = initial_balance_cents
        self._tier = get_survival_tier(initial_balance_cents)
        self._tier_history: list = []
        
    @property
    def tier(self) -> SurvivalTier:
        """Current survival tier."""
        return self._tier
        
    @property
    def balance_cents(self) -> int:
        """Current balance in cents."""
        return self._balance_cents
        
    @property
    def capabilities(self) -> TierCapabilities:
        """Current tier capabilities."""
        return TIER_CAPABILITIES[self._tier]
        
    def update_balance(self, new_balance_cents: int) -> bool:
        """
        Update balance and recalculate tier.
        
        Args:
            new_balance_cents: New balance in cents
            
        Returns:
            True if tier changed, False otherwise
        """
        old_tier = self._tier
        self._balance_cents = new_balance_cents
        self._tier = get_survival_tier(new_balance_cents)
        
        if self._tier != old_tier:
            self._tier_history.append({
                "from": old_tier.value,
                "to": self._tier.value,
                "balance": new_balance_cents,
            })
            return True
            
        return False
        
    def can_open_position(self) -> bool:
        """Check if we can open new positions."""
        return self.capabilities.can_open_new
        
    def get_position_multiplier(self) -> float:
        """Get position size multiplier for current tier."""
        return self.capabilities.position_size_multiplier
        
    def get_status(self) -> str:
        """Get formatted status string."""
        return format_tier_status(self._tier, self._balance_cents)
