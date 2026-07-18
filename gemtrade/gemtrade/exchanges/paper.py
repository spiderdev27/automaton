"""
Paper Trading Exchange

A simulated exchange for testing strategies without real money.
Includes realistic features:
- Spread simulation
- Slippage
- Order fills
- Position tracking
- P&L calculation

Uses real-time price data when available, otherwise generates realistic prices.
"""

from __future__ import annotations

import asyncio
import json
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

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


class PaperExchange(ExchangeConnector):
    """
    Paper trading exchange for strategy testing.
    
    Features:
    - Realistic spread simulation
    - Configurable slippage
    - Stop loss / take profit execution
    - Full position tracking
    - Trade history persistence
    """
    
    def __init__(
        self,
        initial_balance_paise: int = 500_000,  # ₹5,000
        project_root: Optional[Path] = None,
        spread_pips: float = 2.0,
        slippage_pips: float = 0.5,
        commission_pct: float = 0.0,
    ):
        self.project_root = project_root or Path.cwd()
        self._balance_paise = initial_balance_paise
        self._spread_pips = spread_pips
        self._slippage_pips = slippage_pips
        self._commission_pct = commission_pct
        
        self._connected = False
        self._orders: Dict[str, Order] = {}
        self._positions: Dict[str, Position] = {}
        self._trade_history: List[Dict] = []
        
        # Simulated prices (will be updated by price feed)
        self._prices: Dict[str, float] = {
            "XAUUSD": 2450.00,
            "BTCUSD": 67000.00,
            "EURUSD": 1.0850,
        }
        
        # Load state if exists
        self._load_state()
    
    @property
    def name(self) -> str:
        return "Paper Trading"
    
    @property
    def is_paper(self) -> bool:
        return True
    
    def _state_path(self) -> Path:
        p = self.project_root / ".gemcode" / "trading" / "paper_state.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    
    def _load_state(self) -> None:
        """Load state from disk."""
        path = self._state_path()
        if not path.is_file():
            return
        
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self._balance_paise = data.get("balance_paise", self._balance_paise)
            self._trade_history = data.get("trade_history", [])
            
            # Restore positions
            for pos_data in data.get("positions", []):
                pos = Position(
                    symbol=pos_data["symbol"],
                    side=pos_data["side"],
                    quantity=pos_data["quantity"],
                    entry_price=pos_data["entry_price"],
                    current_price=pos_data.get("current_price", pos_data["entry_price"]),
                    stop_loss=pos_data.get("stop_loss"),
                    take_profit=pos_data.get("take_profit"),
                    leverage=pos_data.get("leverage", 1.0),
                )
                self._positions[pos.symbol] = pos
        except Exception:
            pass
    
    def _save_state(self) -> None:
        """Save state to disk."""
        data = {
            "balance_paise": self._balance_paise,
            "positions": [
                {
                    "symbol": p.symbol,
                    "side": p.side,
                    "quantity": p.quantity,
                    "entry_price": p.entry_price,
                    "current_price": p.current_price,
                    "stop_loss": p.stop_loss,
                    "take_profit": p.take_profit,
                    "leverage": p.leverage,
                }
                for p in self._positions.values()
            ],
            "trade_history": self._trade_history[-100:],  # Keep last 100
            "updated_at": datetime.utcnow().isoformat(),
        }
        
        self._state_path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8"
        )
    
    async def connect(self) -> bool:
        """Connect to paper exchange."""
        self._connected = True
        return True
    
    async def disconnect(self) -> None:
        """Disconnect from paper exchange."""
        self._save_state()
        self._connected = False
    
    async def get_balance(self) -> Dict[str, float]:
        """Get account balance in INR."""
        margin_used = sum(
            abs(p.quantity * p.entry_price / p.leverage)
            for p in self._positions.values()
        )
        
        total_inr = self._balance_paise / 100
        margin_inr = margin_used  # Already in base currency
        
        # Add unrealized P&L
        unrealized = sum(p.unrealized_pnl for p in self._positions.values())
        
        return {
            "total": total_inr + unrealized,
            "available": total_inr - margin_inr,
            "margin_used": margin_inr,
            "unrealized_pnl": unrealized,
            "currency": "INR",
        }
    
    async def get_tick(self, symbol: str) -> Tick:
        """Get current tick with simulated spread."""
        base_price = self._prices.get(symbol, 100.0)
        
        # Add some random movement
        base_price *= 1 + random.uniform(-0.0001, 0.0001)
        self._prices[symbol] = base_price
        
        # Calculate spread
        spread = self._spread_pips / 10000 * base_price
        
        return Tick(
            symbol=symbol,
            bid=base_price - spread / 2,
            ask=base_price + spread / 2,
            last=base_price,
            timestamp=datetime.utcnow(),
        )
    
    async def get_candles(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
    ) -> List[Candle]:
        """Generate simulated candles."""
        candles = []
        base_price = self._prices.get(symbol, 100.0)
        
        # Timeframe to minutes
        tf_minutes = {
            "1m": 1, "5m": 5, "15m": 15, "30m": 30,
            "1h": 60, "4h": 240, "1d": 1440,
        }.get(timeframe, 60)
        
        now = datetime.utcnow()
        
        for i in range(limit, 0, -1):
            timestamp = now - timedelta(minutes=i * tf_minutes)
            
            # Random price movement
            change = random.uniform(-0.002, 0.002)
            base_price *= (1 + change)
            
            # Generate OHLC
            volatility = base_price * 0.001
            open_price = base_price * (1 + random.uniform(-0.0005, 0.0005))
            close_price = base_price * (1 + random.uniform(-0.0005, 0.0005))
            high_price = max(open_price, close_price) + random.uniform(0, volatility)
            low_price = min(open_price, close_price) - random.uniform(0, volatility)
            
            candles.append(Candle(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=timestamp,
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=random.uniform(1000, 10000),
            ))
        
        return candles
    
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
        order_id = str(uuid.uuid4())[:8]
        
        order = Order(
            order_id=order_id,
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            status=OrderStatus.PENDING,
        )
        
        # For market orders, fill immediately
        if order_type == OrderType.MARKET:
            tick = await self.get_tick(symbol)
            
            # Apply slippage
            slippage = self._slippage_pips / 10000 * tick.last
            
            if side == OrderSide.BUY:
                fill_price = tick.ask + slippage
            else:
                fill_price = tick.bid - slippage
            
            order.status = OrderStatus.FILLED
            order.filled_quantity = quantity
            order.filled_price = fill_price
            order.updated_at = datetime.utcnow()
            
            # Create or update position
            await self._update_position(order)
        else:
            # Limit/stop orders stay pending
            order.status = OrderStatus.OPEN
        
        self._orders[order_id] = order
        self._save_state()
        
        return order
    
    async def _update_position(self, order: Order) -> None:
        """Update position based on filled order."""
        symbol = order.symbol
        existing = self._positions.get(symbol)
        
        if existing:
            # Update existing position
            if (order.side == OrderSide.BUY and existing.side == "long") or \
               (order.side == OrderSide.SELL and existing.side == "short"):
                # Adding to position
                total_qty = existing.quantity + order.filled_quantity
                avg_price = (
                    existing.entry_price * existing.quantity +
                    order.filled_price * order.filled_quantity
                ) / total_qty
                existing.quantity = total_qty
                existing.entry_price = avg_price
            else:
                # Reducing position
                if order.filled_quantity >= existing.quantity:
                    # Close position
                    pnl = self._calculate_pnl(existing, order.filled_price)
                    self._balance_paise += int(pnl * 100)
                    self._record_trade(existing, order.filled_price, pnl)
                    del self._positions[symbol]
                else:
                    # Partial close
                    close_qty = order.filled_quantity
                    pnl = self._calculate_pnl(existing, order.filled_price, close_qty)
                    self._balance_paise += int(pnl * 100)
                    existing.quantity -= close_qty
        else:
            # New position
            side = "long" if order.side == OrderSide.BUY else "short"
            position = Position(
                symbol=symbol,
                side=side,
                quantity=order.filled_quantity,
                entry_price=order.filled_price,
                current_price=order.filled_price,
                stop_loss=order.stop_loss,
                take_profit=order.take_profit,
                leverage=100.0,  # Default leverage
            )
            self._positions[symbol] = position
    
    def _calculate_pnl(
        self,
        position: Position,
        exit_price: float,
        quantity: Optional[float] = None,
    ) -> float:
        """Calculate P&L for a position."""
        qty = quantity or position.quantity
        
        if position.side == "long":
            pnl = (exit_price - position.entry_price) * qty
        else:
            pnl = (position.entry_price - exit_price) * qty
        
        # Apply commission
        pnl -= abs(pnl) * self._commission_pct / 100
        
        return pnl
    
    def _record_trade(
        self,
        position: Position,
        exit_price: float,
        pnl: float,
    ) -> None:
        """Record completed trade."""
        self._trade_history.append({
            "symbol": position.symbol,
            "side": position.side,
            "quantity": position.quantity,
            "entry_price": position.entry_price,
            "exit_price": exit_price,
            "pnl": pnl,
            "pnl_paise": int(pnl * 100),
            "closed_at": datetime.utcnow().isoformat(),
        })
    
    async def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        order = self._orders.get(order_id)
        if not order:
            return False
        
        if order.status in (OrderStatus.PENDING, OrderStatus.OPEN):
            order.status = OrderStatus.CANCELLED
            order.updated_at = datetime.utcnow()
            return True
        
        return False
    
    async def get_order(self, order_id: str) -> Optional[Order]:
        """Get order by ID."""
        return self._orders.get(order_id)
    
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Order]:
        """Get all open orders."""
        orders = [
            o for o in self._orders.values()
            if o.status in (OrderStatus.PENDING, OrderStatus.OPEN)
        ]
        if symbol:
            orders = [o for o in orders if o.symbol == symbol]
        return orders
    
    async def get_positions(self) -> List[Position]:
        """Get all open positions with updated P&L."""
        for pos in self._positions.values():
            tick = await self.get_tick(pos.symbol)
            pos.current_price = tick.last
            
            if pos.side == "long":
                pos.unrealized_pnl = (tick.last - pos.entry_price) * pos.quantity
            else:
                pos.unrealized_pnl = (pos.entry_price - tick.last) * pos.quantity
            
            pos.unrealized_pnl_pct = pos.unrealized_pnl / (pos.entry_price * pos.quantity) * 100
            
            # Check stop loss / take profit
            await self._check_sl_tp(pos, tick)
        
        return list(self._positions.values())
    
    async def _check_sl_tp(self, position: Position, tick: Tick) -> None:
        """Check and execute stop loss / take profit."""
        triggered = False
        exit_price = None
        
        if position.side == "long":
            if position.stop_loss and tick.bid <= position.stop_loss:
                triggered = True
                exit_price = position.stop_loss
            elif position.take_profit and tick.bid >= position.take_profit:
                triggered = True
                exit_price = position.take_profit
        else:  # short
            if position.stop_loss and tick.ask >= position.stop_loss:
                triggered = True
                exit_price = position.stop_loss
            elif position.take_profit and tick.ask <= position.take_profit:
                triggered = True
                exit_price = position.take_profit
        
        if triggered and exit_price:
            pnl = self._calculate_pnl(position, exit_price)
            self._balance_paise += int(pnl * 100)
            self._record_trade(position, exit_price, pnl)
            del self._positions[position.symbol]
            self._save_state()
    
    async def close_position(
        self,
        symbol: str,
        quantity: Optional[float] = None,
    ) -> Order:
        """Close a position."""
        position = self._positions.get(symbol)
        if not position:
            raise ExchangeError(f"No position for {symbol}")
        
        close_qty = quantity or position.quantity
        side = OrderSide.SELL if position.side == "long" else OrderSide.BUY
        
        return await self.place_order(
            symbol=symbol,
            side=side,
            order_type=OrderType.MARKET,
            quantity=close_qty,
        )
    
    async def modify_position(
        self,
        symbol: str,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
    ) -> bool:
        """Modify position stop loss / take profit."""
        position = self._positions.get(symbol)
        if not position:
            return False
        
        if stop_loss is not None:
            position.stop_loss = stop_loss
        if take_profit is not None:
            position.take_profit = take_profit
        
        self._save_state()
        return True
    
    def set_price(self, symbol: str, price: float) -> None:
        """Set price for a symbol (for testing)."""
        self._prices[symbol] = price
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get recent trade history."""
        return self._trade_history[-limit:]
    
    def reset(self, initial_balance_paise: int = 500_000) -> None:
        """Reset the paper exchange."""
        self._balance_paise = initial_balance_paise
        self._orders.clear()
        self._positions.clear()
        self._trade_history.clear()
        self._save_state()
