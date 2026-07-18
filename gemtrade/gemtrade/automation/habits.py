"""
Trading Habits

Scheduled recurring tasks for autonomous trading.
These integrate with GemCode's habit scheduler.

Habits run automatically in the background, allowing
the agent to monitor markets and manage risk continuously.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TradingHabit:
    """A trading habit configuration."""
    name: str
    agent: str  # Which agent runs this
    prompt: str
    every_minutes: Optional[int] = None
    daily_at: Optional[str] = None  # HH:MM format
    enabled: bool = True
    description: str = ""


TRADING_HABITS: List[TradingHabit] = [
    # ── Market Scanning ───────────────────────────────────────────────────────
    TradingHabit(
        name="market-scan",
        agent="analyst",
        prompt="""Analyze current market conditions for XAUUSD:
1. Check current price and spread
2. Identify trend direction
3. Note any significant price levels
4. Check for upcoming news events
5. Assess volatility conditions

Report findings and any potential trade setups.""",
        every_minutes=15,
        description="Regular market analysis scan",
    ),
    
    TradingHabit(
        name="news-check",
        agent="analyst",
        prompt="""Check for high-impact news events:
1. Use web search to find upcoming economic events
2. Identify events affecting gold (XAU) and USD
3. Note times and expected impact
4. Flag any imminent events (within 30 minutes)

Report news calendar and any trading implications.""",
        every_minutes=60,
        description="Economic calendar check",
    ),
    
    # ── Risk Management ───────────────────────────────────────────────────────
    TradingHabit(
        name="risk-check",
        agent="overseer",
        prompt="""Perform risk audit:
1. Check current positions and their status
2. Verify all positions have stop losses
3. Calculate current exposure vs limits
4. Check daily and weekly P&L against limits
5. Verify survival tier is correct

Report any risk concerns or violations.""",
        every_minutes=30,
        description="Risk exposure audit",
    ),
    
    TradingHabit(
        name="position-monitor",
        agent="overseer",
        prompt="""Monitor open positions:
1. Check unrealized P&L on all positions
2. Evaluate if stops should be moved to breakeven
3. Check if any take profits should be adjusted
4. Assess if any positions should be closed early

Take protective actions if needed.""",
        every_minutes=5,
        enabled=False,  # Enable when positions are open
        description="Active position monitoring",
    ),
    
    # ── Learning & Review ─────────────────────────────────────────────────────
    TradingHabit(
        name="daily-review",
        agent="learner",
        prompt="""End of day trading review:
1. Review all trades from today
2. Analyze what worked and what didn't
3. Identify patterns in winning vs losing trades
4. Note any mistakes to avoid
5. Update procedural memory based on learnings
6. Reset daily P&L counter

Generate insights for tomorrow.""",
        daily_at="22:00",  # 10 PM UTC (after major markets close)
        description="Daily trade review and learning",
    ),
    
    TradingHabit(
        name="weekly-review",
        agent="learner",
        prompt="""Weekly trading review:
1. Summarize week's performance
2. Calculate win rate and profit factor
3. Review survival tier changes
4. Identify best and worst trades
5. Analyze strategy effectiveness
6. Update long-term patterns
7. Reset weekly P&L counter

Generate weekly report and strategy adjustments.""",
        daily_at="23:00",  # Run on Sundays at 11 PM UTC
        description="Weekly performance review",
    ),
    
    # ── System Health ─────────────────────────────────────────────────────────
    TradingHabit(
        name="connection-check",
        agent="executor",
        prompt="""Verify system connectivity:
1. Check exchange connection
2. Verify price feed is working
3. Test order placement capability (paper)
4. Check alert system functionality

Report any issues.""",
        every_minutes=60,
        description="System health check",
    ),
]


def get_trading_habits() -> List[dict]:
    """
    Get trading habits in GemCode-compatible format.
    
    Returns list of habit configurations that can be added
    to .gemcode/habits.json
    """
    return [
        {
            "name": h.name,
            "agent": h.agent,
            "prompt": h.prompt,
            "every_minutes": h.every_minutes,
            "daily_at": h.daily_at,
            "enabled": h.enabled,
        }
        for h in TRADING_HABITS
    ]


def get_habits_json() -> str:
    """Get habits as JSON string for .gemcode/habits.json"""
    import json
    return json.dumps(get_trading_habits(), indent=2)
