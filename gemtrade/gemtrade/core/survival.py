"""
Survival Tiers - Operating Modes Based on Capital (INR)

Adapted from Automaton's survival mechanics. The agent's capabilities
are automatically adjusted based on available capital.

IMPORTANT: Starting capital is INR 5,000 with high leverage (up to 1:2000).
This means:
- Position sizing is CRITICAL
- Even 0.05% adverse move at full leverage = 100% loss
- Leverage must be earned through consistent profits

Tier progression:
- Start at NORMAL tier with conservative leverage
- Earn HIGH tier through profitable trading
- Protect capital by auto-reducing in LOW/CRITICAL tiers
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict


class SurvivalTier(Enum):
    """Operating tiers based on account capital (INR)."""
    HIGH = "high"           # > INR 50,000 - Earned through profits
    NORMAL = "normal"       # > INR 5,000 - Starting tier
    LOW = "low"             # > INR 1,000 - Reduced risk
    CRITICAL = "critical"   # > INR 100 - Close-only mode
    DEAD = "dead"           # INR 0 or negative - Cannot trade


# Thresholds in paise (1 INR = 100 paise) to avoid float precision issues
SURVIVAL_THRESHOLDS_PAISE: Dict[SurvivalTier, int] = {
    SurvivalTier.HIGH: 5000000,      # INR 50,000 (10x starting capital)
    SurvivalTier.NORMAL: 500000,     # INR 5,000 (starting capital)
    SurvivalTier.LOW: 100000,        # INR 1,000
    SurvivalTier.CRITICAL: 10000,    # INR 100
    SurvivalTier.DEAD: 0,            # INR 0
}

# Also keep USD thresholds for international exchanges
SURVIVAL_THRESHOLDS_CENTS: Dict[SurvivalTier, int] = {
    SurvivalTier.HIGH: 60000,      # $600 (~INR 50,000)
    SurvivalTier.NORMAL: 6000,     # $60 (~INR 5,000)
    SurvivalTier.LOW: 1200,        # $12 (~INR 1,000)
    SurvivalTier.CRITICAL: 120,    # $1.20 (~INR 100)
    SurvivalTier.DEAD: 0,
}


@dataclass
class TierCapabilities:
    """Capabilities available at each survival tier."""
    
    # Position sizing
    max_position_pct: float      # Maximum position size as % of equity
    can_open_new: bool           # Can open new positions
    can_add_to_position: bool    # Can add to existing positions
    
    # Leverage limits (CRITICAL for high leverage accounts)
    max_effective_leverage: int  # Maximum allowed leverage
    
    # Analysis
    analysis_frequency_minutes: int  # How often to run market scans
    
    # Model selection (for GemCode model routing)
    model_tier: str              # "quality", "balanced", "fast", "none"
    
    # Risk
    max_concurrent_positions: int
    position_size_multiplier: float  # Applied to calculated position sizes
    
    # Stop loss
    min_stop_loss_pct: float     # Minimum stop loss distance from entry


TIER_CAPABILITIES: Dict[SurvivalTier, TierCapabilities] = {
    SurvivalTier.HIGH: TierCapabilities(
        max_position_pct=5.0,
        can_open_new=True,
        can_add_to_position=True,
        max_effective_leverage=500,    # Earned through profits
        analysis_frequency_minutes=15,
        model_tier="quality",
        max_concurrent_positions=3,
        position_size_multiplier=1.0,
        min_stop_loss_pct=0.5
    ),
    
    SurvivalTier.NORMAL: TierCapabilities(
        max_position_pct=3.0,
        can_open_new=True,
        can_add_to_position=True,
        max_effective_leverage=100,    # Start conservative despite broker offering more
        analysis_frequency_minutes=30,
        model_tier="balanced",
        max_concurrent_positions=2,
        position_size_multiplier=0.5,  # Start at half size
        min_stop_loss_pct=1.0
    ),
    
    SurvivalTier.LOW: TierCapabilities(
        max_position_pct=2.0,
        can_open_new=True,
        can_add_to_position=False,
        max_effective_leverage=50,     # Reduce leverage when losing
        analysis_frequency_minutes=60,
        model_tier="fast",
        max_concurrent_positions=1,
        position_size_multiplier=0.25,
        min_stop_loss_pct=2.0
    ),
    
    SurvivalTier.CRITICAL: TierCapabilities(
        max_position_pct=1.0,
        can_open_new=False,  # CLOSE-ONLY MODE
        can_add_to_position=False,
        max_effective_leverage=10,     # Minimal leverage
        analysis_frequency_minutes=120,
        model_tier="fast",
        max_concurrent_positions=0,    # Close existing only
        position_size_multiplier=0,
        min_stop_loss_pct=5.0
    ),
    
    SurvivalTier.DEAD: TierCapabilities(
        max_position_pct=0,
        can_open_new=False,
        can_add_to_position=False,
        max_effective_leverage=0,
        analysis_frequency_minutes=0,
        model_tier="none",
        max_concurrent_positions=0,
        position_size_multiplier=0,
        min_stop_loss_pct=0
    ),
}


def get_survival_tier(balance_paise: int, currency: str = "INR") -> SurvivalTier:
    """
    Determine survival tier from account balance.
    
    Args:
        balance_paise: Account balance in smallest unit (paise for INR, cents for USD)
        currency: "INR" or "USD"
        
    Returns:
        The appropriate SurvivalTier
    """
    if balance_paise <= 0:
        return SurvivalTier.DEAD
    
    thresholds = SURVIVAL_THRESHOLDS_PAISE if currency == "INR" else SURVIVAL_THRESHOLDS_CENTS
    
    # Check tiers from highest to lowest
    for tier in [SurvivalTier.HIGH, SurvivalTier.NORMAL, 
                 SurvivalTier.LOW, SurvivalTier.CRITICAL]:
        if balance_paise >= thresholds[tier]:
            return tier
            
    return SurvivalTier.DEAD


def get_capabilities(tier: SurvivalTier) -> TierCapabilities:
    """Get capabilities for a given tier."""
    return TIER_CAPABILITIES[tier]


def can_trade(tier: SurvivalTier) -> bool:
    """Check if trading is allowed at this tier."""
    caps = TIER_CAPABILITIES[tier]
    return caps.can_open_new


def get_max_leverage(tier: SurvivalTier) -> int:
    """Get maximum allowed leverage for this tier."""
    return TIER_CAPABILITIES[tier].max_effective_leverage


def calculate_safe_position_size(
    tier: SurvivalTier,
    equity_paise: int,
    stop_loss_pct: float,
    max_risk_pct: float = 2.0
) -> int:
    """
    Calculate safe position size based on tier and risk parameters.
    
    Uses the formula:
    Position Size = (Equity × Risk%) / Stop Loss%
    
    Then applies tier multiplier.
    
    Args:
        tier: Current survival tier
        equity_paise: Account equity in paise
        stop_loss_pct: Stop loss distance as percentage
        max_risk_pct: Maximum risk per trade as percentage (default 2%)
        
    Returns:
        Maximum position size in paise
    """
    caps = TIER_CAPABILITIES[tier]
    
    # Ensure minimum stop loss
    actual_stop_loss = max(stop_loss_pct, caps.min_stop_loss_pct)
    
    # Calculate based on risk
    risk_based_size = (equity_paise * max_risk_pct / 100) / (actual_stop_loss / 100)
    
    # Apply tier multiplier
    adjusted_size = int(risk_based_size * caps.position_size_multiplier)
    
    # Cap at max position percentage
    max_size = int(equity_paise * caps.max_position_pct / 100)
    
    return min(adjusted_size, max_size)


def format_tier_status(tier: SurvivalTier, balance_paise: int, currency: str = "INR") -> str:
    """Format a human-readable tier status message."""
    caps = TIER_CAPABILITIES[tier]
    
    if currency == "INR":
        balance_display = f"₹{balance_paise / 100:,.2f}"
    else:
        balance_display = f"${balance_paise / 100:.2f}"
    
    if tier == SurvivalTier.DEAD:
        return f"⚫ DEAD - Balance: {balance_display} - Cannot trade"
    
    if tier == SurvivalTier.CRITICAL:
        return (
            f"🔴 CRITICAL - Balance: {balance_display}\n"
            f"   Close-only mode. No new positions allowed.\n"
            f"   Max leverage: 1:{caps.max_effective_leverage}"
        )
    
    if tier == SurvivalTier.LOW:
        return (
            f"🟠 LOW - Balance: {balance_display}\n"
            f"   Reduced risk mode. Position multiplier: {caps.position_size_multiplier}x\n"
            f"   Max leverage: 1:{caps.max_effective_leverage}"
        )
    
    if tier == SurvivalTier.NORMAL:
        return (
            f"🟢 NORMAL - Balance: {balance_display}\n"
            f"   Standard operations. Starting tier.\n"
            f"   Max leverage: 1:{caps.max_effective_leverage}\n"
            f"   Max position: {caps.max_position_pct}%"
        )
    
    return (
        f"🟢 HIGH - Balance: {balance_display}\n"
        f"   Full capabilities EARNED through profits!\n"
        f"   Max leverage: 1:{caps.max_effective_leverage}\n"
        f"   Max position: {caps.max_position_pct}%"
    )


class SurvivalManager:
    """
    Manages survival tier based on financial state.
    
    Tracks tier changes and enforces tier-based restrictions.
    """
    
    def __init__(self, initial_balance_paise: int = 500000, currency: str = "INR"):
        """
        Initialize survival manager.
        
        Args:
            initial_balance_paise: Starting balance (default INR 5,000 = 500000 paise)
            currency: "INR" or "USD"
        """
        self._balance_paise = initial_balance_paise
        self._currency = currency
        self._tier = get_survival_tier(initial_balance_paise, currency)
        self._tier_history: list = []
        self._peak_balance = initial_balance_paise
        
    @property
    def tier(self) -> SurvivalTier:
        """Current survival tier."""
        return self._tier
        
    @property
    def balance_paise(self) -> int:
        """Current balance in smallest unit."""
        return self._balance_paise
        
    @property
    def balance_display(self) -> str:
        """Balance formatted for display."""
        if self._currency == "INR":
            return f"₹{self._balance_paise / 100:,.2f}"
        return f"${self._balance_paise / 100:.2f}"
        
    @property
    def capabilities(self) -> TierCapabilities:
        """Current tier capabilities."""
        return TIER_CAPABILITIES[self._tier]
        
    def update_balance(self, new_balance_paise: int) -> bool:
        """
        Update balance and recalculate tier.
        
        Args:
            new_balance_paise: New balance in paise/cents
            
        Returns:
            True if tier changed, False otherwise
        """
        old_tier = self._tier
        self._balance_paise = new_balance_paise
        self._tier = get_survival_tier(new_balance_paise, self._currency)
        
        # Track peak
        if new_balance_paise > self._peak_balance:
            self._peak_balance = new_balance_paise
        
        if self._tier != old_tier:
            self._tier_history.append({
                "from": old_tier.value,
                "to": self._tier.value,
                "balance_paise": new_balance_paise,
            })
            return True
            
        return False
        
    def can_open_position(self) -> bool:
        """Check if we can open new positions."""
        return self.capabilities.can_open_new
        
    def get_max_leverage(self) -> int:
        """Get maximum allowed leverage for current tier."""
        return self.capabilities.max_effective_leverage
        
    def get_position_multiplier(self) -> float:
        """Get position size multiplier for current tier."""
        return self.capabilities.position_size_multiplier
        
    def get_status(self) -> str:
        """Get formatted status string."""
        return format_tier_status(self._tier, self._balance_paise, self._currency)
    
    def get_safe_position_size(self, stop_loss_pct: float, max_risk_pct: float = 2.0) -> int:
        """Calculate safe position size for current tier."""
        return calculate_safe_position_size(
            self._tier, 
            self._balance_paise, 
            stop_loss_pct, 
            max_risk_pct
        )
