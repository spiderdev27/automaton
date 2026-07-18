"""
GemTrade - Autonomous AI Trading Agent

Built on GemCode (multi-agent mesh, event bus, habits, triggers, memory)
with Automaton concepts (survival tiers, constitution, financial state).

Usage:
    gemtrade -C /path/to/project --super
    
Or programmatically:
    from gemtrade import enable_trading
    enable_trading(gemcode_config)
"""

__version__ = "0.1.0"
__author__ = "GemTrade Team"

from gemtrade.core.constitution import CONSTITUTION, ConstitutionalRule, validate_signal
from gemtrade.core.survival import SurvivalTier, get_survival_tier, TIER_CAPABILITIES
from gemtrade.core.state import TradingState, Position
from gemtrade.config import TradingConfig, load_trading_config

__all__ = [
    # Version
    "__version__",
    
    # Constitution
    "CONSTITUTION",
    "ConstitutionalRule", 
    "validate_signal",
    
    # Survival
    "SurvivalTier",
    "get_survival_tier",
    "TIER_CAPABILITIES",
    
    # State
    "TradingState",
    "Position",
    
    # Config
    "TradingConfig",
    "load_trading_config",
]
