"""Core trading infrastructure - Constitution, Survival, State, Adaptive Risk."""

from gemtrade.core.constitution import (
    CONSTITUTION,
    ConstitutionalRule,
    RuleSeverity,
    validate_signal,
    check_constitutional_limits,
)
from gemtrade.core.survival import (
    SurvivalTier,
    SURVIVAL_THRESHOLDS_PAISE,
    TIER_CAPABILITIES,
    TierCapabilities,
    get_survival_tier,
    SurvivalManager,
)
from gemtrade.core.state import (
    TradingState,
    Position,
)
from gemtrade.core.adaptive_risk import (
    AdaptiveRiskManager,
    AdaptiveParameters,
    SignalScore,
    SignalQuality,
    MarketCondition,
    MarketRegime,
    ActiveTradeManager,
)

__all__ = [
    # Constitution
    "CONSTITUTION",
    "ConstitutionalRule",
    "RuleSeverity",
    "validate_signal",
    "check_constitutional_limits",
    # Survival
    "SurvivalTier",
    "SURVIVAL_THRESHOLDS_PAISE",
    "TIER_CAPABILITIES",
    "TierCapabilities",
    "get_survival_tier",
    "SurvivalManager",
    # State
    "TradingState",
    "Position",
    # Adaptive Risk
    "AdaptiveRiskManager",
    "AdaptiveParameters",
    "SignalScore",
    "SignalQuality",
    "MarketCondition",
    "MarketRegime",
    "ActiveTradeManager",
]
