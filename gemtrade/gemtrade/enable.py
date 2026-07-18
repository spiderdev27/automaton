"""
Enable GemTrade Capability

This module provides the integration point with GemCode.
When GEMCODE_TRADING=1, GemTrade:
1. Registers trading tools with the agent
2. Injects trading context into prompts
3. Enables trading habits and triggers
4. Activates the constitutional safety system

Usage:
    # In .gemcode/config.json or environment:
    GEMCODE_TRADING=1
    
    # Or programmatically:
    from gemtrade.enable import enable_trading
    enable_trading(project_root)
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from gemtrade.tools import get_trading_tools, get_intelligence_tools
from gemtrade.automation import get_trading_habits, get_trading_triggers
from gemtrade.capability.trading_awareness import build_trading_context
from gemtrade.capability.constitution import Constitution
from gemtrade.capability.survival import SurvivalManager, get_survival_manager


def is_trading_enabled() -> bool:
    """Check if trading capability is enabled."""
    return os.environ.get("GEMCODE_TRADING", "").lower() in ("1", "true", "yes")


def enable_trading(
    project_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Enable GemTrade capability for a project.
    
    This:
    1. Creates necessary directories and files
    2. Initializes the survival system
    3. Sets up constitution validation
    4. Returns registration info for GemCode
    
    Args:
        project_root: Project root directory
        
    Returns:
        Dict with tools, habits, triggers, and context builder
    """
    project_root = project_root or Path.cwd()
    
    # Create .gemcode/trading directory
    trading_dir = project_root / ".gemcode" / "trading"
    trading_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize survival manager
    survival = get_survival_manager(project_root)
    
    # Initialize constitution
    constitution = Constitution(project_root)
    
    # Get all tools
    trading_tools = get_trading_tools()
    intelligence_tools = get_intelligence_tools()
    all_tools = trading_tools + intelligence_tools
    
    # Get habits and triggers
    habits = get_trading_habits()
    triggers = get_trading_triggers()
    
    # Create config file if not exists
    config_path = trading_dir / "config.json"
    if not config_path.is_file():
        config = {
            "symbol": "XAUUSD",
            "exchange": "paper",
            "initial_balance_paise": 500_000,
            "risk_profile": "aggressive",
            "alerts": {
                "telegram_enabled": False,
            },
            "created_at": str(Path.cwd()),
        }
        config_path.write_text(
            json.dumps(config, indent=2) + "\n",
            encoding="utf-8"
        )
    
    return {
        "tools": all_tools,
        "habits": habits,
        "triggers": triggers,
        "context_builder": lambda: build_trading_context(project_root),
        "survival": survival,
        "constitution": constitution,
    }


def get_trading_system_prompt() -> str:
    """
    Get the trading system prompt to inject into the agent.
    
    This provides the agent with trading context and rules.
    """
    return """# Trading Capability Enabled

You have access to trading tools and can execute trades on financial markets.

## Available Tools

### Trading
- `analyze_market(symbol)` - Get current price, spread, trend analysis
- `execute_trade(symbol, side, risk_percent, stop_loss_pips)` - Execute a trade
- `close_trade(symbol, reason)` - Close a position
- `modify_trade(symbol, stop_loss, take_profit)` - Modify stop loss / TP
- `get_positions()` - View open positions
- `get_balance()` - Check balance and survival tier
- `get_trade_history()` - Recent trade history

### Intelligence
- `market_intelligence(symbol, depth)` - AI-powered market analysis
- `analyze_news_impact(topic)` - News analysis with web search
- `economic_calendar()` - Upcoming economic events
- `research_question(question)` - Deep research on any topic
- `should_trade_now(symbol)` - Quick trade feasibility check

## Constitutional Rules (IMMUTABLE)

1. **EVERY trade MUST have a stop loss** - No exceptions
2. Maximum 10% risk per trade
3. Maximum 3 concurrent positions
4. Minimum 20% reserve capital
5. Daily loss limit: 15%
6. Weekly loss limit: 25%
7. Maximum drawdown: 30%
8. After 3 consecutive losses: mandatory pause

## Survival Tiers

Your capabilities depend on your account balance:
- HIGH (>₹8,000): Full capabilities, 100x leverage
- NORMAL (₹5,000-8,000): Standard, 50x leverage
- LOW (₹3,000-5,000): Reduced, 25x leverage
- CRITICAL (<₹3,000): Survival mode, 10x leverage
- DEAD (<₹1,500): Trading halted

## Decision Process

Before every trade:
1. Gather intelligence using `market_intelligence()` or `should_trade_now()`
2. Check balance and survival tier with `get_balance()`
3. Execute with mandatory stop loss using `execute_trade()`
4. Monitor and manage with `modify_trade()` or `close_trade()`

Learn from every outcome. Your procedural memory adjusts based on results.
"""


def get_trading_context_injection(project_root: Optional[Path] = None) -> str:
    """
    Get current trading context to inject into prompts.
    
    This provides the agent with current state on every turn.
    """
    project_root = project_root or Path.cwd()
    
    try:
        return build_trading_context(project_root)
    except Exception as e:
        return f"[Trading context unavailable: {e}]"


# ══════════════════════════════════════════════════════════════════════════════
#                           GEMCODE INTEGRATION
# ══════════════════════════════════════════════════════════════════════════════

def register_with_gemcode():
    """
    Register GemTrade with GemCode.
    
    This is called automatically when GEMCODE_TRADING=1.
    
    For manual registration, import and call this function.
    """
    if not is_trading_enabled():
        return None
    
    project_root = Path.cwd()
    
    # Enable trading
    registration = enable_trading(project_root)
    
    # Return in GemCode-expected format
    return {
        "capability": "trading",
        "version": "0.1.0",
        "tools": registration["tools"],
        "habits": registration["habits"],
        "triggers": registration["triggers"],
        "system_prompt_extension": get_trading_system_prompt(),
        "context_injection": lambda: get_trading_context_injection(project_root),
        "check_before_action": registration["constitution"].validate_action,
    }
