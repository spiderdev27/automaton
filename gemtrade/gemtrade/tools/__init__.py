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

__all__ = [
    "get_trading_tools",
    "analyze_market",
    "execute_trade",
    "close_trade",
    "modify_trade",
    "get_positions",
    "get_balance",
    "get_trade_history",
]
