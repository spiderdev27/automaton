"""
Alert System

Multi-channel alerts for trading events.
Supports Telegram, and can be extended for other channels.

Configuration via environment variables:
- TELEGRAM_BOT_TOKEN: Bot token from @BotFather
- TELEGRAM_CHAT_ID: Your chat ID
"""

from __future__ import annotations

import asyncio
import os
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request
import urllib.parse


class AlertChannel(Enum):
    """Alert delivery channels."""
    TELEGRAM = "telegram"
    CONSOLE = "console"
    FILE = "file"


class AlertPriority(Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class Alert:
    """An alert message."""
    title: str
    message: str
    priority: AlertPriority = AlertPriority.MEDIUM
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_text(self) -> str:
        """Format alert as text."""
        emoji = {
            AlertPriority.LOW: "ℹ️",
            AlertPriority.MEDIUM: "⚠️",
            AlertPriority.HIGH: "🚨",
            AlertPriority.CRITICAL: "🔴",
        }[self.priority]
        
        lines = [
            f"{emoji} *{self.title}*",
            "",
            self.message,
        ]
        
        if self.data:
            lines.append("")
            for key, value in self.data.items():
                lines.append(f"• {key}: `{value}`")
        
        lines.append("")
        lines.append(f"_{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC_")
        
        return "\n".join(lines)


class AlertManager:
    """
    Manages alert delivery across channels.
    
    Usage:
        manager = AlertManager()
        await manager.send(Alert(
            title="Trade Executed",
            message="Bought XAUUSD",
            priority=AlertPriority.MEDIUM,
            data={"price": 2450.00, "quantity": 0.1}
        ))
    """
    
    def __init__(
        self,
        project_root: Optional[Path] = None,
        channels: Optional[List[AlertChannel]] = None,
    ):
        self.project_root = project_root or Path.cwd()
        self.channels = channels or [AlertChannel.CONSOLE, AlertChannel.FILE]
        
        # Telegram config from environment
        self._telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
        self._telegram_chat_id = os.environ.get("TELEGRAM_CHAT_ID")
        
        if self._telegram_token and self._telegram_chat_id:
            self.channels.append(AlertChannel.TELEGRAM)
        
        # Alert history
        self._history: List[Alert] = []
        
        # Rate limiting
        self._last_sent: Dict[str, datetime] = {}
        self._cooldown_seconds = {
            AlertPriority.LOW: 300,      # 5 minutes
            AlertPriority.MEDIUM: 60,    # 1 minute
            AlertPriority.HIGH: 10,      # 10 seconds
            AlertPriority.CRITICAL: 0,   # No cooldown
        }
    
    def _log_path(self) -> Path:
        p = self.project_root / ".gemcode" / "trading" / "alerts.log"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p
    
    def _should_send(self, alert: Alert) -> bool:
        """Check rate limiting."""
        key = f"{alert.title}:{alert.priority.value}"
        last = self._last_sent.get(key)
        
        if last:
            cooldown = self._cooldown_seconds[alert.priority]
            elapsed = (datetime.utcnow() - last).total_seconds()
            if elapsed < cooldown:
                return False
        
        return True
    
    async def send(self, alert: Alert) -> bool:
        """
        Send an alert through all configured channels.
        
        Returns True if sent to at least one channel.
        """
        if not self._should_send(alert):
            return False
        
        self._history.append(alert)
        self._last_sent[f"{alert.title}:{alert.priority.value}"] = datetime.utcnow()
        
        sent = False
        
        for channel in self.channels:
            try:
                if channel == AlertChannel.CONSOLE:
                    await self._send_console(alert)
                    sent = True
                elif channel == AlertChannel.FILE:
                    await self._send_file(alert)
                    sent = True
                elif channel == AlertChannel.TELEGRAM:
                    success = await self._send_telegram(alert)
                    sent = sent or success
            except Exception as e:
                print(f"Alert error ({channel.value}): {e}")
        
        return sent
    
    async def _send_console(self, alert: Alert) -> None:
        """Print alert to console."""
        print("\n" + "=" * 50)
        print(alert.to_text().replace("*", "").replace("`", ""))
        print("=" * 50 + "\n")
    
    async def _send_file(self, alert: Alert) -> None:
        """Write alert to log file."""
        log_entry = {
            "timestamp": alert.timestamp.isoformat(),
            "title": alert.title,
            "message": alert.message,
            "priority": alert.priority.value,
            "data": alert.data,
        }
        
        with open(self._log_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    async def _send_telegram(self, alert: Alert) -> bool:
        """Send alert via Telegram."""
        if not self._telegram_token or not self._telegram_chat_id:
            return False
        
        url = f"https://api.telegram.org/bot{self._telegram_token}/sendMessage"
        
        data = {
            "chat_id": self._telegram_chat_id,
            "text": alert.to_text(),
            "parse_mode": "Markdown",
        }
        
        try:
            req = urllib.request.Request(
                url,
                data=urllib.parse.urlencode(data).encode("utf-8"),
                method="POST",
            )
            
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.status == 200
        except Exception as e:
            print(f"Telegram error: {e}")
            return False
    
    def get_history(self, limit: int = 50) -> List[Alert]:
        """Get recent alert history."""
        return self._history[-limit:]


# ══════════════════════════════════════════════════════════════════════════════
#                           CONVENIENCE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

_manager: Optional[AlertManager] = None


def get_alert_manager(project_root: Optional[Path] = None) -> AlertManager:
    """Get or create alert manager."""
    global _manager
    if _manager is None:
        _manager = AlertManager(project_root)
    return _manager


def send_alert(
    title: str,
    message: str,
    priority: AlertPriority = AlertPriority.MEDIUM,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """
    Send an alert (convenience function).
    
    Args:
        title: Alert title
        message: Alert message
        priority: Alert priority
        data: Additional data
        
    Returns:
        True if sent successfully
    """
    manager = get_alert_manager()
    alert = Alert(
        title=title,
        message=message,
        priority=priority,
        data=data or {},
    )
    
    # Run async in sync context
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(manager.send(alert))


# ══════════════════════════════════════════════════════════════════════════════
#                           PRE-DEFINED ALERTS
# ══════════════════════════════════════════════════════════════════════════════

def alert_trade_executed(
    symbol: str,
    side: str,
    price: float,
    quantity: float,
    stop_loss: float,
    take_profit: Optional[float] = None,
) -> bool:
    """Alert for trade execution."""
    return send_alert(
        title="Trade Executed",
        message=f"{side.upper()} {symbol}",
        priority=AlertPriority.MEDIUM,
        data={
            "symbol": symbol,
            "side": side,
            "price": price,
            "quantity": quantity,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
        },
    )


def alert_trade_closed(
    symbol: str,
    pnl: float,
    reason: str,
) -> bool:
    """Alert for trade closure."""
    priority = AlertPriority.HIGH if pnl < 0 else AlertPriority.MEDIUM
    emoji = "🟢" if pnl > 0 else "🔴"
    
    return send_alert(
        title=f"Trade Closed {emoji}",
        message=f"{symbol}: {'Profit' if pnl > 0 else 'Loss'} ₹{abs(pnl):.2f}",
        priority=priority,
        data={
            "symbol": symbol,
            "pnl": pnl,
            "reason": reason,
        },
    )


def alert_risk_warning(
    warning_type: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
) -> bool:
    """Alert for risk warnings."""
    return send_alert(
        title=f"Risk Warning: {warning_type}",
        message=message,
        priority=AlertPriority.HIGH,
        data=data or {},
    )


def alert_tier_change(
    old_tier: str,
    new_tier: str,
    balance: float,
) -> bool:
    """Alert for survival tier change."""
    is_downgrade = ["HIGH", "NORMAL", "LOW", "CRITICAL", "DEAD"].index(new_tier) > \
                   ["HIGH", "NORMAL", "LOW", "CRITICAL", "DEAD"].index(old_tier)
    
    priority = AlertPriority.HIGH if is_downgrade else AlertPriority.MEDIUM
    
    return send_alert(
        title="Survival Tier Changed",
        message=f"{old_tier} → {new_tier}",
        priority=priority,
        data={
            "old_tier": old_tier,
            "new_tier": new_tier,
            "balance_inr": balance,
        },
    )


def alert_system_halt(
    reason: str,
) -> bool:
    """Alert for trading halt."""
    return send_alert(
        title="TRADING HALTED",
        message=reason,
        priority=AlertPriority.CRITICAL,
        data={"reason": reason},
    )


def alert_opportunity(
    symbol: str,
    signal_type: str,
    confidence: float,
) -> bool:
    """Alert for trading opportunity."""
    return send_alert(
        title="Trading Opportunity",
        message=f"{signal_type} signal on {symbol}",
        priority=AlertPriority.LOW,
        data={
            "symbol": symbol,
            "signal_type": signal_type,
            "confidence": f"{confidence:.1%}",
        },
    )
