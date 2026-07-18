"""
Exchange Connectors for GemTrade

Unified interface for multiple exchanges:
- Paper Trading (built-in simulator)
- MT5 (forex, gold, CFDs)
- Delta Exchange India (crypto derivatives)
- Fyers (Indian equities - future)
- Groww (Indian equities - future)

All connectors implement the same interface so the agent
can trade on any exchange with the same tools.
"""

from gemtrade.exchanges.base import (
    ExchangeConnector,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    Position,
    Tick,
    Candle,
    ExchangeError,
)
from gemtrade.exchanges.paper import PaperExchange
from gemtrade.exchanges.factory import get_exchange, ExchangeType

__all__ = [
    # Base
    "ExchangeConnector",
    "Order",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "Position",
    "Tick",
    "Candle",
    "ExchangeError",
    # Implementations
    "PaperExchange",
    # Factory
    "get_exchange",
    "ExchangeType",
]
