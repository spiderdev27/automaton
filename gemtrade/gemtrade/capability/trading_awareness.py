"""
Trading Awareness — Persistent, incrementally-built market understanding.

Mirrors GemCode's codebase_awareness but for trading:

1. MARKET STRUCTURE — What symbols we trade, current positions, key levels.
   Built incrementally from price data, order flow, technical analysis.
   Not a full market model — just what matters for decisions.

2. TRADE JOURNAL — What trades we made, why, what happened.
   Built from every order, fill, and close.
   Enables: "what did we trade recently?" and "what worked?"

3. TRADING INSIGHTS — Learned facts about markets and our trading.
   "XAU/USD moves 50 pips on NFP." "News fades work better than breakouts."
   "We lose when we trade during Asian session."
   Built from trade outcomes, news correlations, pattern analysis.

The awareness is injected into the agent's context as a compact summary,
giving the agent memory of what it has learned about trading.

Storage: .gemcode/trading/
  market.json    — current market state
  journal.jsonl  — trade log
  insights.json  — learned patterns
  patterns.jsonl — procedural memory adjustments
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional
from dataclasses import dataclass, asdict


# ── Market Structure ──────────────────────────────────────────────────────────

def _trading_dir(project_root: Path) -> Path:
    d = project_root / ".gemcode" / "trading"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _market_path(project_root: Path) -> Path:
    return _trading_dir(project_root) / "market.json"


def _load_market(project_root: Path) -> dict[str, Any]:
    p = _market_path(project_root)
    if not p.is_file():
        return {
            "symbols": {},
            "positions": {},
            "levels": {},
            "regime": "unknown",
            "updated_ms": 0,
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"symbols": {}, "positions": {}, "levels": {}, "regime": "unknown", "updated_ms": 0}


def _save_market(project_root: Path, market: dict[str, Any]) -> None:
    market["updated_ms"] = int(time.time() * 1000)
    p = _market_path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(market, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_market_observation(
    project_root: Path,
    *,
    symbol: str,
    price: float,
    bid: Optional[float] = None,
    ask: Optional[float] = None,
    volume: Optional[float] = None,
    atr: Optional[float] = None,
    trend: Optional[str] = None,  # "up", "down", "ranging"
    volatility: Optional[str] = None,  # "low", "normal", "high"
) -> None:
    """Record market observation. Called after price checks."""
    if not _enabled():
        return
    try:
        market = _load_market(project_root)
        symbols = market.setdefault("symbols", {})
        
        spread = None
        if bid and ask:
            spread = round((ask - bid) / price * 10000, 1)  # Spread in pips
        
        symbols[symbol] = {
            "price": price,
            "bid": bid,
            "ask": ask,
            "spread_pips": spread,
            "volume": volume,
            "atr": atr,
            "trend": trend,
            "volatility": volatility,
            "seen_ms": int(time.time() * 1000),
        }
        
        _save_market(project_root, market)
    except Exception:
        pass


def record_position(
    project_root: Path,
    *,
    symbol: str,
    side: str,  # "long" or "short"
    entry_price: float,
    quantity: float,
    stop_loss: Optional[float] = None,
    take_profit: Optional[float] = None,
    unrealized_pnl: Optional[float] = None,
) -> None:
    """Record current position state."""
    if not _enabled():
        return
    try:
        market = _load_market(project_root)
        positions = market.setdefault("positions", {})
        
        positions[symbol] = {
            "side": side,
            "entry_price": entry_price,
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "unrealized_pnl": unrealized_pnl,
            "opened_ms": int(time.time() * 1000),
        }
        
        _save_market(project_root, market)
    except Exception:
        pass


def clear_position(project_root: Path, symbol: str) -> None:
    """Clear a position after close."""
    if not _enabled():
        return
    try:
        market = _load_market(project_root)
        market.get("positions", {}).pop(symbol, None)
        _save_market(project_root, market)
    except Exception:
        pass


def record_key_level(
    project_root: Path,
    *,
    symbol: str,
    level_type: str,  # "support", "resistance", "pivot"
    price: float,
    strength: int = 1,  # 1-5
) -> None:
    """Record an important price level."""
    if not _enabled():
        return
    try:
        market = _load_market(project_root)
        levels = market.setdefault("levels", {})
        symbol_levels = levels.setdefault(symbol, [])
        
        # Update or add level
        for lvl in symbol_levels:
            if abs(lvl["price"] - price) < price * 0.001:  # Within 0.1%
                lvl["strength"] = min(5, lvl["strength"] + 1)
                lvl["seen_ms"] = int(time.time() * 1000)
                _save_market(project_root, market)
                return
        
        symbol_levels.append({
            "type": level_type,
            "price": price,
            "strength": strength,
            "seen_ms": int(time.time() * 1000),
        })
        
        # Keep only top 10 levels per symbol
        levels[symbol] = sorted(symbol_levels, key=lambda x: -x["strength"])[:10]
        _save_market(project_root, market)
    except Exception:
        pass


def set_market_regime(
    project_root: Path,
    regime: str,  # "trending_up", "trending_down", "ranging", "volatile", "news_active"
) -> None:
    """Set the current market regime."""
    if not _enabled():
        return
    try:
        market = _load_market(project_root)
        market["regime"] = regime
        _save_market(project_root, market)
    except Exception:
        pass


# ── Trade Journal ─────────────────────────────────────────────────────────────

def _journal_path(project_root: Path) -> Path:
    return _trading_dir(project_root) / "journal.jsonl"


@dataclass
class TradeRecord:
    """A completed trade record."""
    trade_id: str
    symbol: str
    side: str
    entry_time: str
    entry_price: float
    exit_time: Optional[str] = None
    exit_price: Optional[float] = None
    quantity: float = 0.0
    pnl_paise: int = 0
    pnl_percent: float = 0.0
    entry_reason: str = ""
    exit_reason: str = ""
    was_stopped: bool = False
    was_news_trade: bool = False
    market_regime: str = ""
    signals_used: list = None
    
    def __post_init__(self):
        if self.signals_used is None:
            self.signals_used = []


def record_trade(
    project_root: Path,
    trade: TradeRecord,
) -> None:
    """Record a completed trade to the journal."""
    if not _enabled():
        return
    try:
        entry = asdict(trade)
        entry["recorded_ms"] = int(time.time() * 1000)
        
        p = _journal_path(project_root)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        
        # Trim if too large
        _trim_journal(p, max_entries=1000)
        
        # Update insights based on trade outcome
        _learn_from_trade(project_root, trade)
    except Exception:
        pass


def _trim_journal(path: Path, max_entries: int = 1000) -> None:
    try:
        lines = path.read_text(encoding="utf-8").strip().splitlines()
        if len(lines) > max_entries:
            path.write_text("\n".join(lines[-max_entries:]) + "\n", encoding="utf-8")
    except Exception:
        pass


def recent_trades(project_root: Path, limit: int = 20) -> list[dict[str, Any]]:
    """Get recent trades from the journal."""
    p = _journal_path(project_root)
    if not p.is_file():
        return []
    try:
        lines = p.read_text(encoding="utf-8").strip().splitlines()
        entries = []
        for line in reversed(lines):
            try:
                entries.append(json.loads(line))
            except Exception:
                continue
            if len(entries) >= limit:
                break
        return entries
    except Exception:
        return []


def get_trade_stats(project_root: Path, days: int = 30) -> dict[str, Any]:
    """Calculate trading statistics."""
    trades = recent_trades(project_root, limit=500)
    if not trades:
        return {"total": 0, "wins": 0, "losses": 0, "win_rate": 0, "total_pnl": 0}
    
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    recent = [t for t in trades if t.get("entry_time", "") > cutoff]
    
    wins = sum(1 for t in recent if t.get("pnl_paise", 0) > 0)
    losses = sum(1 for t in recent if t.get("pnl_paise", 0) < 0)
    total_pnl = sum(t.get("pnl_paise", 0) for t in recent)
    
    return {
        "total": len(recent),
        "wins": wins,
        "losses": losses,
        "win_rate": wins / len(recent) if recent else 0,
        "total_pnl_paise": total_pnl,
        "total_pnl_inr": total_pnl / 100,
    }


# ── Trading Insights ──────────────────────────────────────────────────────────

def _insights_path(project_root: Path) -> Path:
    return _trading_dir(project_root) / "insights.json"


def _load_insights(project_root: Path) -> dict[str, Any]:
    p = _insights_path(project_root)
    if not p.is_file():
        return {
            "facts": [],
            "patterns": {},
            "mistakes": [],
            "procedural": {
                "risk_comfort": 1.0,
                "news_sensitivity": 1.0,
                "spread_tolerance": 1.0,
                "volatility_preference": 1.0,
            },
        }
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {"facts": [], "patterns": {}, "mistakes": [], "procedural": {}}


def _save_insights(project_root: Path, insights: dict[str, Any]) -> None:
    p = _insights_path(project_root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(insights, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def record_trading_insight(project_root: Path, fact: str) -> None:
    """Record a learned fact about trading."""
    if not _enabled():
        return
    try:
        insights = _load_insights(project_root)
        facts = insights.setdefault("facts", [])
        if fact not in facts:
            facts.append(fact)
        if len(facts) > 100:
            insights["facts"] = facts[-75:]
        _save_insights(project_root, insights)
    except Exception:
        pass


def record_trading_mistake(project_root: Path, mistake: str, severity: int = 1) -> None:
    """Record a trading mistake to avoid repeating."""
    if not _enabled():
        return
    try:
        insights = _load_insights(project_root)
        mistakes = insights.setdefault("mistakes", [])
        mistakes.append({
            "mistake": mistake,
            "severity": severity,
            "ts_ms": int(time.time() * 1000),
        })
        if len(mistakes) > 50:
            insights["mistakes"] = mistakes[-40:]
        _save_insights(project_root, insights)
    except Exception:
        pass


def record_pattern_outcome(
    project_root: Path,
    pattern: str,
    outcome: str,  # "win" or "loss"
    context: Optional[str] = None,
) -> None:
    """Record whether a pattern/setup worked or not."""
    if not _enabled():
        return
    try:
        insights = _load_insights(project_root)
        patterns = insights.setdefault("patterns", {})
        
        if pattern not in patterns:
            patterns[pattern] = {"wins": 0, "losses": 0, "contexts": []}
        
        if outcome == "win":
            patterns[pattern]["wins"] += 1
        else:
            patterns[pattern]["losses"] += 1
        
        if context:
            contexts = patterns[pattern].setdefault("contexts", [])
            contexts.append(context)
            patterns[pattern]["contexts"] = contexts[-10:]
        
        _save_insights(project_root, insights)
    except Exception:
        pass


def _learn_from_trade(project_root: Path, trade: TradeRecord) -> None:
    """
    Adjust procedural memory ("feelings") based on trade outcome.
    
    This is the key to the agent developing intuition.
    """
    try:
        insights = _load_insights(project_root)
        proc = insights.setdefault("procedural", {
            "risk_comfort": 1.0,
            "news_sensitivity": 1.0,
            "spread_tolerance": 1.0,
            "volatility_preference": 1.0,
        })
        
        was_profitable = trade.pnl_paise > 0
        
        # Adjust risk comfort
        if was_profitable:
            proc["risk_comfort"] = min(1.5, proc.get("risk_comfort", 1.0) * 1.05)
        else:
            proc["risk_comfort"] = max(0.5, proc.get("risk_comfort", 1.0) * 0.92)
        
        # Adjust news sensitivity
        if trade.was_news_trade:
            if was_profitable:
                proc["news_sensitivity"] = min(1.5, proc.get("news_sensitivity", 1.0) * 1.1)
            else:
                proc["news_sensitivity"] = max(0.5, proc.get("news_sensitivity", 1.0) * 0.85)
        
        # Adjust based on stop behavior
        if trade.was_stopped:
            # If stopped quickly (within minutes), maybe stop was too tight
            # If stopped after being in profit, need better trailing
            proc["spread_tolerance"] = max(0.5, proc.get("spread_tolerance", 1.0) * 0.95)
        
        _save_insights(project_root, insights)
    except Exception:
        pass


def get_procedural_adjustments(project_root: Path) -> dict[str, float]:
    """Get current procedural memory adjustments."""
    insights = _load_insights(project_root)
    return insights.get("procedural", {
        "risk_comfort": 1.0,
        "news_sensitivity": 1.0,
        "spread_tolerance": 1.0,
        "volatility_preference": 1.0,
    })


def get_trading_insights(project_root: Path) -> dict[str, Any]:
    """Get all trading insights."""
    return _load_insights(project_root)


# ── Context Builder ───────────────────────────────────────────────────────────

def build_trading_context(project_root: Path, *, max_chars: int = 4000) -> str:
    """
    Build a compact trading context for injection into the agent.
    
    This replaces the need for repeated market analysis. The agent starts
    each turn knowing current positions, recent trades, and learned insights.
    """
    if not _enabled():
        return ""
    
    parts: list[str] = []
    
    # Current market state
    market = _load_market(project_root)
    
    # Positions
    positions = market.get("positions", {})
    if positions:
        pos_lines = []
        for symbol, pos in positions.items():
            pnl = pos.get("unrealized_pnl")
            pnl_str = f" (₹{pnl/100:.2f})" if pnl else ""
            pos_lines.append(
                f"  {symbol}: {pos['side'].upper()} @ {pos['entry_price']}{pnl_str}"
            )
        parts.append("Current positions:\n" + "\n".join(pos_lines))
    else:
        parts.append("No open positions")
    
    # Recent prices
    symbols = market.get("symbols", {})
    if symbols:
        price_lines = []
        for symbol, data in list(symbols.items())[:5]:
            spread = data.get("spread_pips")
            spread_str = f" (spread: {spread})" if spread else ""
            trend = data.get("trend", "?")
            price_lines.append(f"  {symbol}: {data['price']} [{trend}]{spread_str}")
        parts.append("Market:\n" + "\n".join(price_lines))
    
    # Regime
    regime = market.get("regime", "unknown")
    if regime != "unknown":
        parts.append(f"Market regime: {regime}")
    
    # Trade stats
    stats = get_trade_stats(project_root, days=7)
    if stats["total"] > 0:
        parts.append(
            f"Last 7 days: {stats['total']} trades, "
            f"{stats['win_rate']:.0%} win rate, "
            f"₹{stats['total_pnl_inr']:.2f} P&L"
        )
    
    # Recent trades
    trades = recent_trades(project_root, limit=3)
    if trades:
        trade_lines = []
        for t in trades:
            pnl = t.get("pnl_paise", 0) / 100
            emoji = "✓" if pnl > 0 else "✗"
            trade_lines.append(
                f"  {emoji} {t.get('symbol')}: ₹{pnl:.2f} — {t.get('exit_reason', '?')[:40]}"
            )
        parts.append("Recent trades:\n" + "\n".join(trade_lines))
    
    # Insights
    insights = _load_insights(project_root)
    
    # Procedural adjustments
    proc = insights.get("procedural", {})
    if proc:
        adj_parts = []
        if proc.get("risk_comfort", 1.0) != 1.0:
            adj_parts.append(f"risk comfort: {proc['risk_comfort']:.2f}")
        if proc.get("news_sensitivity", 1.0) != 1.0:
            adj_parts.append(f"news sensitivity: {proc['news_sensitivity']:.2f}")
        if adj_parts:
            parts.append("Learned adjustments: " + ", ".join(adj_parts))
    
    # Recent mistakes (to avoid)
    mistakes = insights.get("mistakes", [])[-3:]
    if mistakes:
        parts.append("Avoid: " + "; ".join(m["mistake"][:50] for m in mistakes))
    
    # Key facts
    facts = insights.get("facts", [])[-5:]
    if facts:
        parts.append("Learned:\n" + "\n".join(f"  - {f}" for f in facts))
    
    if not parts:
        return ""
    
    text = "[Trading awareness]\n" + "\n".join(parts)
    return text[:max_chars]


# ── Config ────────────────────────────────────────────────────────────────────

def _enabled() -> bool:
    return os.environ.get("GEMCODE_TRADING", "0").strip().lower() in (
        "1", "true", "yes", "on",
    )
