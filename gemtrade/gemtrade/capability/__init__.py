"""
Trading Capability for GemCode

This module provides trading as a first-class capability that can be
enabled in GemCode via GEMCODE_TRADING=1.

Architecture mirrors GemCode's codebase_awareness:
- trading_awareness.py → Market understanding (like codebase structure)
- trading_memory.py → Trade journal & patterns (like change journal)
- constitution.py → Immutable safety rules (unique to trading)
- survival.py → Tier-based behavior adaptation

When enabled, GemTrade:
1. Injects market context into every turn
2. Provides trading tools (analysis, execution)
3. Runs trading habits (market scans, risk checks)
4. Triggers on trading events (price alerts, news)
"""

from gemtrade.capability.trading_awareness import (
    build_trading_context,
    record_market_observation,
    record_trade,
    recent_trades,
    get_trading_insights,
)
from gemtrade.capability.constitution import (
    Constitution,
    validate_trade,
    TRADING_LAWS,
)
from gemtrade.capability.survival import (
    SurvivalManager,
    SurvivalTier,
    get_tier_capabilities,
)

__all__ = [
    # Awareness
    "build_trading_context",
    "record_market_observation",
    "record_trade",
    "recent_trades",
    "get_trading_insights",
    # Constitution
    "Constitution",
    "validate_trade",
    "TRADING_LAWS",
    # Survival
    "SurvivalManager",
    "SurvivalTier",
    "get_tier_capabilities",
]
