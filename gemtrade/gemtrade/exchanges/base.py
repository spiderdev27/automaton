"""
Base Exchange Connector Interface

All exchange implementations must follow this interface.
This ensures the agent can use the same tools regardless of exchange.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any


class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order sides."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order statuses."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Order:
    """An order."""
    order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    filled_price: Optional[float] = None
    
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    exchange_order_id: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "stop_price": self.stop_price,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "filled_price": self.filled_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "created_at": self.created_at.isoformat(),
        }


@dataclass
class Position:
    """An open position."""
    symbol: str
    side: str  # "long" or "short"
    quantity: float
    entry_price: float
    current_price: float
    
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    margin_used: float = 0.0
    leverage: float = 1.0
    
    opened_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict:
        return {
            "symbol": self.symbol,
            "side": self.side,
            "quantity": self.quantity,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "leverage": self.leverage,
        }


@dataclass
class Tick:
    """A price tick."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def spread_pips(self) -> float:
        """Spread in pips (assuming 4 decimal places)."""
        return self.spread * 10000


@dataclass
class Candle:
    """An OHLCV candle."""
    symbol: str
    timeframe: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    
    @property
    def body(self) -> float:
        return abs(self.close - self.open)
    
    @property
    def range(self) -> float:
        return self.high - self.low
    
    @property
    def is_bullish(self) -> bool:
        return self.close > self.open


class ExchangeError(Exception):
    """Exchange-related error."""
    pass


class ExchangeConnector(ABC):
    """
    Abstract base class for exchange connectors.
    
    All exchanges must implement this interface.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Exchange name."""
        pass
    
    @property
    @abstractmethod
    def is_paper(self) -> bool:
        """Whether this is paper trading."""
        pass
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the exchange."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the exchange."""
        pass
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, float]:
        """
        Get account balance.
        
        Returns dict with at least:
        - "total": Total balance
        - "available": Available for trading
        - "margin_used": Margin in use
        """
        pass
    
    @abstractmethod
    async def get_tick(self, symbol: str) -> Tick:
        """Get current tick for a symbol."""
        pass
    
    @abstractmethod
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> List[Candle]:
        """Get historical candles."""
        pass
    
    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: float,
        price: Optional[float] = None,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Order:
        """Place an order."""
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order."""
        pass
    
    @abstractmethod
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        pass
    
    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders."""
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions."""
        pass
    
    @abstractmethod
    async def close_position(
        self,
        symbol: str,
        quantity: Optional[float] = None,
    ) -> Order:
        """Close a position (or part of it)."""
        pass
    
    @abstractmethod
    async def modify_position(
        self,
        symbol: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> bool:
        """Modify position stop loss / take profit."""
        pass
    
    # ── Convenience Methods ───────────────────────────────────────────────────
    
    async def buy(
        self,
        symbol: str,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Order:
        """Market buy."""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
    
    async def sell(
        self,
        symbol: str,
        quantity: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> Order:
        """Market sell."""
        return await self.place_order(
            symbol=symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
    
    async def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for a specific symbol."""
        positions = await self.get_positions()
        for pos in positions:
            if pos.symbol == symbol:
                return pos
        return None
    
    async def close_all_positions(self) -> List[Order]:
        """Close all open positions."""
        positions = await self.get_positions()
        orders = []
        for pos in positions:
            order = await self.close_position(pos.symbol)
            orders.append(order)
        return orders
