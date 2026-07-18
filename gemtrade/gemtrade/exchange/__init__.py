"""
Exchange Connectors

Supports:
- Paper trading (simulated)
- Delta Exchange India (crypto derivatives)
- MT5/MetaTrader 5 (forex, gold, stocks via broker)
"""

from gemtrade.exchange.base import (
    ExchangeConnector,
    Order,
    OrderType,
    OrderSide,
    OrderStatus,
    Position,
    Tick,
    Candle,
)

__all__ = [
    "ExchangeConnector",
    "Order",
    "OrderType",
    "OrderSide",
    "OrderStatus",
    "Position",
    "Tick",
    "Candle",
]
