"""
Trading Tools

GemCode-compatible tools for trading operations.
These are the primary interface for the agent to interact with markets.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from gemtrade.exchanges import (
    ExchangeConnector,
    ExchangeType,
    get_exchange,
    OrderSide,
    OrderType,
)
from gemtrade.capability.constitution import (
    Constitution,
    validate_trade,
    get_trade_limits,
)
from gemtrade.capability.survival import (
    SurvivalManager,
    get_survival_manager,
)
from gemtrade.capability.trading_awareness import (
    record_market_observation,
    record_trade,
    TradeRecord,
    build_trading_context,
    get_procedural_adjustments,
)


# Global exchange instance
_exchange: Optional[ExchangeConnector] = None


def _get_exchange(project_root: Optional[Path] = None) -> ExchangeConnector:
    """Get or create exchange instance."""
    global _exchange
    if _exchange is None:
        _exchange = get_exchange(
            ExchangeType.PAPER,
            project_root=project_root,
        )
        asyncio.get_event_loop().run_until_complete(_exchange.connect())
    return _exchange


def _run_async(coro):
    """Run async function synchronously."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


# ══════════════════════════════════════════════════════════════════════════════
#                           TRADING TOOLS
# ══════════════════════════════════════════════════════════════════════════════

def analyze_market(
    symbol: str = "XAUUSD",
    include_candles: bool = True,
    candle_timeframe: str = "1h",
    candle_count: int = 20,
) -> Dict[str, Any]:
    """
    Analyze current market conditions for a symbol.
    
    Returns current price, spread, recent candles, and any detected patterns.
    Use this before deciding whether to trade.
    
    Args:
        symbol: Trading symbol (e.g., "XAUUSD", "BTCUSD")
        include_candles: Whether to include recent candles
        candle_timeframe: Timeframe for candles ("1m", "5m", "15m", "1h", "4h", "1d")
        candle_count: Number of candles to fetch
        
    Returns:
        Market analysis with price, spread, candles, and insights
    """
    exchange = _get_exchange()
    project_root = Path.cwd()
    
    async def _analyze():
        tick = await exchange.get_tick(symbol)
        
        result = {
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "price": {
                "bid": tick.bid,
                "ask": tick.ask,
                "mid": tick.mid,
                "spread_pips": tick.spread_pips,
            },
        }
        
        if include_candles:
            candles = await exchange.get_candles(symbol, candle_timeframe, candle_count)
            result["candles"] = [
                {
                    "time": c.timestamp.isoformat(),
                    "open": c.open,
                    "high": c.high,
                    "low": c.low,
                    "close": c.close,
                    "volume": c.volume,
                }
                for c in candles[-10:]  # Last 10 for display
            ]
            
            # Simple analysis
            closes = [c.close for c in candles]
            if len(closes) >= 10:
                sma10 = sum(closes[-10:]) / 10
                current = closes[-1]
                result["analysis"] = {
                    "sma10": sma10,
                    "price_vs_sma": "above" if current > sma10 else "below",
                    "trend": "bullish" if closes[-1] > closes[-5] else "bearish",
                    "volatility": "high" if max(closes[-10:]) - min(closes[-10:]) > current * 0.01 else "normal",
                }
        
        # Record observation
        record_market_observation(
            project_root,
            symbol=symbol,
            price=tick.mid,
            bid=tick.bid,
            ask=tick.ask,
            trend=result.get("analysis", {}).get("trend"),
            volatility=result.get("analysis", {}).get("volatility"),
        )
        
        return result
    
    return _run_async(_analyze())


def execute_trade(
    symbol: str,
    side: str,  # "buy" or "sell"
    risk_percent: float = 5.0,
    stop_loss_pips: Optional[float] = None,
    take_profit_pips: Optional[float] = None,
    reason: str = "",
) -> Dict[str, Any]:
    """
    Execute a trade with constitutional validation.
    
    This is the main trading function. It:
    1. Validates against the constitution
    2. Calculates position size based on risk
    3. Places the order with stop loss / take profit
    4. Records the trade
    
    Args:
        symbol: Trading symbol
        side: "buy" for long, "sell" for short
        risk_percent: Percentage of capital to risk (max 10%)
        stop_loss_pips: Stop loss distance in pips (REQUIRED)
        take_profit_pips: Take profit distance in pips
        reason: Why this trade is being taken
        
    Returns:
        Trade execution result or rejection reason
    """
    exchange = _get_exchange()
    project_root = Path.cwd()
    survival = get_survival_manager(project_root)
    constitution = Constitution(project_root)
    
    # Check if we can trade
    can_trade, halt_reason = survival.can_trade()
    if not can_trade:
        return {
            "success": False,
            "error": f"Trading halted: {halt_reason}",
            "action": "none",
        }
    
    # MANDATORY: Stop loss required
    if stop_loss_pips is None:
        return {
            "success": False,
            "error": "CONSTITUTIONAL VIOLATION: Stop loss is MANDATORY. No trade without stop loss.",
            "action": "none",
        }
    
    async def _execute():
        # Get current state
        state = survival.get_state()
        balance = await exchange.get_balance()
        positions = await exchange.get_positions()
        tick = await exchange.get_tick(symbol)
        
        # Get procedural adjustments (learned "feelings")
        adjustments = get_procedural_adjustments(project_root)
        adjusted_risk = risk_percent * adjustments.get("risk_comfort", 1.0)
        adjusted_risk = min(adjusted_risk, 10.0)  # Cap at constitutional limit
        
        # Calculate position size
        available = balance["available"]
        risk_amount = available * (adjusted_risk / 100)
        
        # Validate against constitution
        validation = constitution.validate_trade(
            has_stop_loss=True,
            risk_per_trade_pct=adjusted_risk,
            position_size_pct=(risk_amount / available) * 100,
            current_positions=len(positions),
            reserve_remaining_pct=(available / balance["total"]) * 100,
            daily_loss_pct=abs(state.daily_pnl_paise / state.balance_paise * 100) if state.daily_pnl_paise < 0 else 0,
            weekly_loss_pct=abs(state.weekly_pnl_paise / state.balance_paise * 100) if state.weekly_pnl_paise < 0 else 0,
            current_drawdown_pct=state.drawdown_pct,
            consecutive_losses=state.consecutive_losses,
        )
        
        if not validation.can_proceed:
            return {
                "success": False,
                "error": "CONSTITUTIONAL VIOLATION",
                "violations": validation.violations,
                "action": "blocked",
            }
        
        # Calculate stop loss / take profit prices
        pip_value = 0.0001 if "JPY" not in symbol else 0.01
        if symbol in ("XAUUSD",):
            pip_value = 0.01  # Gold uses 0.01
        
        if side.lower() == "buy":
            entry_price = tick.ask
            stop_loss = entry_price - (stop_loss_pips * pip_value)
            take_profit = entry_price + (take_profit_pips * pip_value) if take_profit_pips else None
            order_side = OrderSide.BUY
        else:
            entry_price = tick.bid
            stop_loss = entry_price + (stop_loss_pips * pip_value)
            take_profit = entry_price - (take_profit_pips * pip_value) if take_profit_pips else None
            order_side = OrderSide.SELL
        
        # Calculate quantity based on risk
        risk_per_pip = risk_amount / stop_loss_pips
        quantity = risk_per_pip / pip_value
        quantity = round(quantity, 2)
        
        # Place order
        order = await exchange.place_order(
            symbol=symbol,
            side=order_side,
            order_type=OrderType.MARKET,
            quantity=quantity,
            stop_loss=stop_loss,
            take_profit=take_profit,
        )
        
        if order.status.value == "filled":
            return {
                "success": True,
                "order_id": order.order_id,
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "entry_price": order.filled_price,
                "stop_loss": stop_loss,
                "take_profit": take_profit,
                "risk_amount": risk_amount,
                "risk_percent": adjusted_risk,
                "reason": reason,
            }
        else:
            return {
                "success": False,
                "error": f"Order not filled: {order.status.value}",
                "order": order.to_dict(),
            }
    
    return _run_async(_execute())


def close_trade(
    symbol: str,
    reason: str = "",
    partial_percent: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Close a position.
    
    Args:
        symbol: Symbol to close
        reason: Why closing
        partial_percent: Close only this percentage (e.g., 50 for half)
        
    Returns:
        Close result with P&L
    """
    exchange = _get_exchange()
    project_root = Path.cwd()
    survival = get_survival_manager(project_root)
    
    async def _close():
        position = await exchange.get_position(symbol)
        if not position:
            return {
                "success": False,
                "error": f"No position for {symbol}",
            }
        
        close_qty = position.quantity
        if partial_percent:
            close_qty = position.quantity * (partial_percent / 100)
        
        order = await exchange.close_position(symbol, close_qty)
        
        if order.status.value == "filled":
            # Calculate P&L
            if position.side == "long":
                pnl = (order.filled_price - position.entry_price) * close_qty
            else:
                pnl = (position.entry_price - order.filled_price) * close_qty
            
            pnl_paise = int(pnl * 100)
            
            # Update survival state
            survival.record_trade_result(pnl_paise)
            
            # Record trade
            record_trade(
                project_root,
                TradeRecord(
                    trade_id=order.order_id,
                    symbol=symbol,
                    side=position.side,
                    entry_time=position.opened_at.isoformat(),
                    entry_price=position.entry_price,
                    exit_time=datetime.utcnow().isoformat(),
                    exit_price=order.filled_price,
                    quantity=close_qty,
                    pnl_paise=pnl_paise,
                    pnl_percent=(pnl / (position.entry_price * close_qty)) * 100,
                    exit_reason=reason,
                    was_stopped=False,
                )
            )
            
            return {
                "success": True,
                "symbol": symbol,
                "closed_quantity": close_qty,
                "exit_price": order.filled_price,
                "pnl": pnl,
                "pnl_paise": pnl_paise,
                "pnl_inr": pnl_paise / 100,
                "reason": reason,
            }
        else:
            return {
                "success": False,
                "error": f"Close failed: {order.status.value}",
            }
    
    return _run_async(_close())


def modify_trade(
    symbol: str,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Modify stop loss or take profit for an open position.
    
    Args:
        symbol: Symbol to modify
        stop_loss: New stop loss price
        take_profit: New take profit price
        
    Returns:
        Modification result
    """
    exchange = _get_exchange()
    
    async def _modify():
        success = await exchange.modify_position(symbol, stop_loss, take_profit)
        
        if success:
            position = await exchange.get_position(symbol)
            return {
                "success": True,
                "symbol": symbol,
                "new_stop_loss": stop_loss,
                "new_take_profit": take_profit,
                "position": position.to_dict() if position else None,
            }
        else:
            return {
                "success": False,
                "error": f"No position for {symbol}",
            }
    
    return _run_async(_modify())


def get_positions() -> Dict[str, Any]:
    """
    Get all open positions with current P&L.
    
    Returns:
        List of positions with unrealized P&L
    """
    exchange = _get_exchange()
    
    async def _get():
        positions = await exchange.get_positions()
        return {
            "positions": [p.to_dict() for p in positions],
            "count": len(positions),
            "total_unrealized_pnl": sum(p.unrealized_pnl for p in positions),
        }
    
    return _run_async(_get())


def get_balance() -> Dict[str, Any]:
    """
    Get current account balance and survival status.
    
    Returns:
        Balance info and survival tier
    """
    exchange = _get_exchange()
    project_root = Path.cwd()
    survival = get_survival_manager(project_root)
    
    async def _get():
        balance = await exchange.get_balance()
        state = survival.get_state()
        caps = survival.get_capabilities()
        
        return {
            "balance": balance,
            "survival": {
                "tier": state.tier.value,
                "balance_inr": state.balance_inr,
                "drawdown_pct": state.drawdown_pct,
                "daily_pnl_inr": state.daily_pnl_inr,
                "weekly_pnl_inr": state.weekly_pnl_inr,
                "is_halted": state.is_halted,
                "halt_reason": state.halt_reason,
            },
            "capabilities": {
                "max_leverage": caps.max_leverage,
                "max_positions": caps.max_positions,
                "max_risk_pct": caps.max_risk_pct,
                "can_open_new": caps.can_open_new,
                "can_trade_news": caps.can_trade_news,
            },
        }
    
    return _run_async(_get())


def get_trade_history(limit: int = 20) -> Dict[str, Any]:
    """
    Get recent trade history.
    
    Args:
        limit: Number of trades to return
        
    Returns:
        Recent trades with P&L
    """
    exchange = _get_exchange()
    
    if hasattr(exchange, 'get_trade_history'):
        trades = exchange.get_trade_history(limit)
    else:
        trades = []
    
    total_pnl = sum(t.get("pnl", 0) for t in trades)
    wins = sum(1 for t in trades if t.get("pnl", 0) > 0)
    losses = sum(1 for t in trades if t.get("pnl", 0) < 0)
    
    return {
        "trades": trades,
        "count": len(trades),
        "total_pnl": total_pnl,
        "total_pnl_inr": total_pnl,
        "wins": wins,
        "losses": losses,
        "win_rate": wins / len(trades) if trades else 0,
    }


# ══════════════════════════════════════════════════════════════════════════════
#                           TOOL REGISTRATION
# ══════════════════════════════════════════════════════════════════════════════

def get_trading_tools() -> List[callable]:
    """
    Get all trading tools for registration with GemCode.
    
    These tools are registered when GEMCODE_TRADING=1.
    """
    return [
        analyze_market,
        execute_trade,
        close_trade,
        modify_trade,
        get_positions,
        get_balance,
        get_trade_history,
    ]
