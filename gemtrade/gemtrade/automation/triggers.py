"""
Trading Triggers

Event-driven agent activation for trading.
These integrate with GemCode's trigger system.

Triggers fire when specific events occur, allowing
the agent to react immediately to market conditions.
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TradingTrigger:
    """A trading trigger configuration."""
    name: str
    event: str  # Event bus topic
    agent: str  # Which agent handles this
    prompt: str
    condition: Optional[str] = None  # Optional condition expression
    enabled: bool = True
    description: str = ""


TRADING_TRIGGERS: List[TradingTrigger] = [
    # ── Price Triggers ────────────────────────────────────────────────────────
    TradingTrigger(
        name="price-spike",
        event="trading.price.spike",
        agent="analyst",
        prompt="""Price spike detected: {event_data}

Analyze this price movement:
1. What caused the spike?
2. Is this a breakout or fakeout?
3. Should we trade this move?
4. What are the risks?

Decide on action.""",
        description="React to sudden price movements",
    ),
    
    TradingTrigger(
        name="key-level-touch",
        event="trading.price.level_touch",
        agent="strategist",
        prompt="""Price touched key level: {event_data}

Analyze the level interaction:
1. Is this support or resistance?
2. Is price bouncing or breaking?
3. What's the volume like?
4. Is this a trade opportunity?

Decide on action.""",
        description="React when price hits support/resistance",
    ),
    
    # ── Position Triggers ─────────────────────────────────────────────────────
    TradingTrigger(
        name="stop-loss-hit",
        event="trading.position.stopped",
        agent="learner",
        prompt="""Stop loss hit: {event_data}

Analyze this stopped trade:
1. What went wrong?
2. Was the stop too tight?
3. Was entry timing bad?
4. What can we learn?

Update procedural memory.""",
        description="Learn from stopped trades",
    ),
    
    TradingTrigger(
        name="take-profit-hit",
        event="trading.position.target_hit",
        agent="learner",
        prompt="""Take profit hit: {event_data}

Analyze this winning trade:
1. What went right?
2. Could we have held longer?
3. Was the target optimal?
4. Reinforce what worked.

Update procedural memory.""",
        description="Learn from winning trades",
    ),
    
    TradingTrigger(
        name="breakeven-opportunity",
        event="trading.position.profit_threshold",
        agent="overseer",
        prompt="""Position reached 1:1 profit: {event_data}

Consider moving stop to breakeven:
1. Check if trend is still strong
2. Assess risk of reversal
3. Move stop to breakeven if appropriate

Protect the position.""",
        description="Move stop to breakeven when in profit",
    ),
    
    # ── News Triggers ─────────────────────────────────────────────────────────
    TradingTrigger(
        name="high-impact-news",
        event="trading.news.high_impact",
        agent="strategist",
        prompt="""High-impact news event: {event_data}

Analyze news trading opportunity:
1. What is the expected impact?
2. What's the current market setup?
3. Is this a trading opportunity?
4. What strategy should we use? (fade, breakout, etc.)

Decide on action with appropriate risk management.""",
        description="React to high-impact news events",
    ),
    
    TradingTrigger(
        name="news-imminent",
        event="trading.news.imminent",
        agent="overseer",
        prompt="""News event within 15 minutes: {event_data}

Protect existing positions:
1. Check open positions
2. Move stops to breakeven if in profit
3. Consider closing if risk is high
4. Prepare for volatility

Take protective action.""",
        description="Protect positions before news",
    ),
    
    # ── Risk Triggers ─────────────────────────────────────────────────────────
    TradingTrigger(
        name="daily-loss-warning",
        event="trading.risk.daily_loss_50pct",
        agent="overseer",
        prompt="""Daily loss at 50% of limit.

Review and take action:
1. Analyze today's trades
2. Identify what's going wrong
3. Consider reducing position sizes
4. Tighten risk management

Alert user if needed.""",
        description="Warn when daily loss reaches 50% of limit",
    ),
    
    TradingTrigger(
        name="consecutive-loss-warning",
        event="trading.risk.consecutive_losses",
        agent="overseer",
        prompt="""Multiple consecutive losses: {event_data}

Analyze and respond:
1. What pattern caused these losses?
2. Should we pause trading?
3. Is there a strategy issue?
4. Should we alert the user?

Take protective action.""",
        description="React to consecutive losing trades",
    ),
    
    TradingTrigger(
        name="tier-change",
        event="trading.survival.tier_change",
        agent="overseer",
        prompt="""Survival tier changed: {event_data}

Adapt to new tier:
1. Review new capabilities
2. Adjust position sizing
3. Update risk parameters
4. Alert user

Ensure compliance with new tier limits.""",
        description="Adapt when survival tier changes",
    ),
    
    # ── Signal Triggers ───────────────────────────────────────────────────────
    TradingTrigger(
        name="trade-signal",
        event="trading.signal.generated",
        agent="strategist",
        prompt="""Trade signal generated: {event_data}

Evaluate and decide:
1. Validate signal quality
2. Check if conditions allow trading
3. Calculate position size
4. Execute if appropriate

Follow the decision process.""",
        description="React to generated trade signals",
    ),
]


def get_trading_triggers() -> List[dict]:
    """
    Get trading triggers in GemCode-compatible format.
    
    Returns list of trigger configurations that can be added
    to .gemcode/triggers.json
    """
    return [
        {
            "name": t.name,
            "event": t.event,
            "agent": t.agent,
            "prompt": t.prompt,
            "condition": t.condition,
            "enabled": t.enabled,
        }
        for t in TRADING_TRIGGERS
    ]


def get_triggers_json() -> str:
    """Get triggers as JSON string for .gemcode/triggers.json"""
    import json
    return json.dumps(get_trading_triggers(), indent=2)
