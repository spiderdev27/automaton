"""
GemTrade - Autonomous AI Trading Agent

Built on GemCode (multi-agent mesh, event bus, habits, triggers, memory)
with Automaton concepts (survival tiers, constitution, financial state).

Enable trading with:
    GEMCODE_TRADING=1 gemcode -C /path/to/project
    
Or programmatically:
    from gemtrade import enable_trading
    enable_trading(project_root)

Configuration:
    GOOGLE_API_KEY: Gemini API key for intelligence
    TELEGRAM_BOT_TOKEN: For alerts (optional)
    TELEGRAM_CHAT_ID: For alerts (optional)
"""

__version__ = "0.1.0"
__author__ = "GemTrade Team"

# Core components
from gemtrade.core.constitution import CONSTITUTION, ConstitutionalRule, validate_signal
from gemtrade.core.survival import SurvivalTier, get_survival_tier, TIER_CAPABILITIES
from gemtrade.core.state import TradingState, Position
from gemtrade.config import TradingConfig, load_trading_config

# Capability (GemCode integration)
from gemtrade.capability.constitution import Constitution, validate_trade
from gemtrade.capability.survival import SurvivalManager, get_survival_manager
from gemtrade.capability.trading_awareness import build_trading_context, record_trade

# Enable function
from gemtrade.enable import (
    enable_trading,
    is_trading_enabled,
    register_with_gemcode,
    get_trading_system_prompt,
)

# Tools
from gemtrade.tools import (
    get_trading_tools,
    get_intelligence_tools,
    analyze_market,
    execute_trade,
    close_trade,
    get_positions,
    get_balance,
    market_intelligence,
    should_trade_now,
)

# Exchanges
from gemtrade.exchanges import (
    ExchangeConnector,
    PaperExchange,
    get_exchange,
    ExchangeType,
)

# Cloud Intelligence
from gemtrade.cloud import (
    GeminiClient,
    GeminiIntelligence,
    gather_intelligence_sync,
    quick_scan_sync,
)

# Automation
from gemtrade.automation import (
    TRADING_HABITS,
    TRADING_TRIGGERS,
    send_alert,
    AlertPriority,
)

__all__ = [
    # Version
    "__version__",
    
    # Enable
    "enable_trading",
    "is_trading_enabled",
    "register_with_gemcode",
    "get_trading_system_prompt",
    
    # Constitution
    "CONSTITUTION",
    "ConstitutionalRule", 
    "validate_signal",
    "Constitution",
    "validate_trade",
    
    # Survival
    "SurvivalTier",
    "get_survival_tier",
    "TIER_CAPABILITIES",
    "SurvivalManager",
    "get_survival_manager",
    
    # State
    "TradingState",
    "Position",
    
    # Config
    "TradingConfig",
    "load_trading_config",
    
    # Tools
    "get_trading_tools",
    "get_intelligence_tools",
    "analyze_market",
    "execute_trade",
    "close_trade",
    "get_positions",
    "get_balance",
    "market_intelligence",
    "should_trade_now",
    
    # Exchanges
    "ExchangeConnector",
    "PaperExchange",
    "get_exchange",
    "ExchangeType",
    
    # Cloud
    "GeminiClient",
    "GeminiIntelligence",
    "gather_intelligence_sync",
    "quick_scan_sync",
    
    # Awareness
    "build_trading_context",
    "record_trade",
    
    # Automation
    "TRADING_HABITS",
    "TRADING_TRIGGERS",
    "send_alert",
    "AlertPriority",
]
