"""
Trading Automation

Habits, triggers, and alerts for autonomous trading.
Integrates with GemCode's existing habit and trigger systems.
"""

from gemtrade.automation.habits import (
    TRADING_HABITS,
    get_trading_habits,
)
from gemtrade.automation.triggers import (
    TRADING_TRIGGERS,
    get_trading_triggers,
)
from gemtrade.automation.alerts import (
    AlertManager,
    AlertChannel,
    AlertPriority,
    send_alert,
)

__all__ = [
    # Habits
    "TRADING_HABITS",
    "get_trading_habits",
    # Triggers
    "TRADING_TRIGGERS",
    "get_trading_triggers",
    # Alerts
    "AlertManager",
    "AlertChannel",
    "AlertPriority",
    "send_alert",
]
