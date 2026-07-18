"""
Base Exchange Connector

Abstract base class for all exchange connectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any


class OrderType(Enum):
    """Order types."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class OrderSide(Enum):
    """Order side (direction)."""
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass
class Order:
    """An order on the exchange."""
    id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    size: float
    price: Optional[float] = None  # For limit orders
    stop_price: Optional[float] = None  # For stop orders
    
    # Stop loss and take profit
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Status
    status: OrderStatus = OrderStatus.PENDING
    filled_size: float = 0.0
    filled_price: Optional[float] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    filled_at: Optional[datetime] = None
    
    # Exchange info
    exchange_order_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "size": self.size,
            "price": self.price,
            "stop_price": self.stop_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "status": self.status.value,
            "filled_size": self.filled_size,
            "filled_price": self.filled_price,
            "created_at": self.created_at.isoformat(),
            "exchange_order_id": self.exchange_order_id,
        }


@dataclass
class Position:
    """An open position."""
    id: str
    symbol: str
    side: OrderSide  # BUY = long, SELL = short
    size: float
    entry_price: float
    
    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Current state
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    
    # Margin
    margin_used: float = 0.0
    leverage: int = 1
    
    # Timestamps
    opened_at: datetime = field(default_factory=datetime.utcnow)
    
    # Exchange info
    exchange_position_id: Optional[str] = None
    
    def update_price(self, new_price: float) -> None:
        """Update current price and recalculate P&L."""
        self.current_price = new_price
        
        if self.side == OrderSide.BUY:
            self.unrealized_pnl = (new_price - self.entry_price) * self.size
        else:
            self.unrealized_pnl = (self.entry_price - new_price) * self.size
            
        position_value = self.entry_price * self.size
        if position_value > 0:
            self.unrealized_pnl_pct = (self.unrealized_pnl / position_value) * 100
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "symbol": self.symbol,
            "side": self.side.value,
            "size": self.size,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "current_price": self.current_price,
            "unrealized_pnl": self.unrealized_pnl,
            "unrealized_pnl_pct": self.unrealized_pnl_pct,
            "leverage": self.leverage,
            "opened_at": self.opened_at.isoformat(),
        }


@dataclass
class Tick:
    """A price tick."""
    symbol: str
    bid: float
    ask: float
    last: float
    volume: float
    timestamp: datetime
    
    @property
    def spread(self) -> float:
        return self.ask - self.bid
    
    @property
    def mid(self) -> float:
        return (self.bid + self.ask) / 2


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
    volume: float
    
    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "timeframe": self.timeframe,
            "timestamp": self.timestamp.isoformat(),
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
        }


class ExchangeConnector(ABC):
    """
    Abstract base class for exchange connectors.
    
    Implementations:
    - PaperConnector: Simulated trading
    - DeltaConnector: Delta Exchange India
    - MT5Connector: MetaTrader 5
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._connected = False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Connection
    # ═══════════════════════════════════════════════════════════════════════════
    
    @abstractmethod
    async def connect(self) -> bool:
        """Connect to the exchange. Returns True on success."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect from the exchange."""
        pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Account
    # ═══════════════════════════════════════════════════════════════════════════
    
    @abstractmethod
    async def get_balance(self) -> Dict[str, float]:
        """
        Get account balance.
        
        Returns:
            Dict with keys: 'balance', 'equity', 'margin', 'free_margin'
        """
        pass
    
    @abstractmethod
    async def get_positions(self) -> List[Position]:
        """Get all open positions."""
        pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Market Data
    # ═══════════════════════════════════════════════════════════════════════════
    
    @abstractmethod
    async def get_tick(self, symbol: str) -> Optional[Tick]:
        """Get current tick for symbol."""
        pass
    
    @abstractmethod
    async def get_candles(
        self, 
        symbol: str, 
        timeframe: str, 
        count: int = 100
    ) -> List[Candle]:
        """
        Get historical candles.
        
        Args:
            symbol: Trading symbol (e.g., "XAUUSD")
            timeframe: Candle timeframe (e.g., "H1", "M15")
            count: Number of candles to fetch
        """
        pass
    
    @abstractmethod
    async def get_symbols(self) -> List[str]:
        """Get list of available symbols."""
        pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Orders
    # ═══════════════════════════════════════════════════════════════════════════
    
    @abstractmethod
    async def place_order(self, order: Order) -> Order:
        """
        Place an order.
        
        Args:
            order: Order to place
            
        Returns:
            Updated order with exchange info
        """
        pass
    
    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order. Returns True on success."""
        pass
    
    @abstractmethod
    async def modify_order(
        self, 
        order_id: str, 
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """Modify an order's stop loss or take profit."""
        pass
    
    @abstractmethod
    async def get_open_orders(self) -> List[Order]:
        """Get all open orders."""
        pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Positions
    # ═══════════════════════════════════════════════════════════════════════════
    
    @abstractmethod
    async def close_position(
        self, 
        position_id: str, 
        size: Optional[float] = None
    ) -> bool:
        """
        Close a position (fully or partially).
        
        Args:
            position_id: Position to close
            size: Size to close (None = full close)
        """
        pass
    
    @abstractmethod
    async def modify_position(
        self,
        position_id: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> bool:
        """Modify a position's stop loss or take profit."""
        pass
    
    # ═══════════════════════════════════════════════════════════════════════════
    # Utilities
    # ═══════════════════════════════════════════════════════════════════════════
    
    def calculate_margin(
        self, 
        symbol: str, 
        size: float, 
        leverage: int
    ) -> float:
        """Calculate required margin for a position."""
        # Override in subclass for exchange-specific calculation
        return size / leverage
    
    def calculate_pip_value(self, symbol: str, size: float) -> float:
        """Calculate pip value for a position."""
        # Override in subclass for exchange-specific calculation
        return size * 0.0001  # Default for forex
