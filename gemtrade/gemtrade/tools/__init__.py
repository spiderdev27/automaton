"""
Trading Tools for GemCode

These tools are registered with GemCode when GEMCODE_TRADING=1.
They provide the agent with trading capabilities.
"""

from gemtrade.tools.trading_tools import (
    get_trading_tools,
    analyze_market,
    execute_trade,
    close_trade,
    modify_trade,
    get_positions,
    get_balance,
    get_trade_history,
)

from gemtrade.tools.intelligence_tools import (
    get_intelligence_tools,
    market_intelligence,
    analyze_news_impact,
    economic_calendar,
    research_question,
    should_trade_now,
)

__all__ = [
    # Trading Tools
    "get_trading_tools",
    "analyze_market",
    "execute_trade",
    "close_trade",
    "modify_trade",
    "get_positions",
    "get_balance",
    "get_trade_history",
    # Intelligence Tools
    "get_intelligence_tools",
    "market_intelligence",
    "analyze_news_impact",
    "economic_calendar",
    "research_question",
    "should_trade_now",
]
