"""
Historical Knowledge Base

Pre-loaded knowledge about market patterns, events, and behaviors
that the AI should know before making any trade.

This gives the AI a "head start" - equivalent to years of trading experience.
"""

from dataclasses import dataclass
from typing import Dict, List, Any


@dataclass
class HistoricalPattern:
    """A known market pattern."""
    name: str
    description: str
    success_rate: float  # Historical win rate
    best_conditions: List[str]
    avoid_when: List[str]
    typical_rr: float  # Risk:Reward ratio


# ══════════════════════════════════════════════════════════════════════════════
#                     GOLD (XAU/USD) SPECIFIC KNOWLEDGE
# ══════════════════════════════════════════════════════════════════════════════

GOLD_KNOWLEDGE = {
    "correlations": {
        "DXY": {
            "relationship": "inverse",
            "strength": 0.85,
            "note": "When USD strengthens, gold typically falls and vice versa",
        },
        "US_REAL_YIELDS": {
            "relationship": "inverse", 
            "strength": 0.90,
            "note": "Rising real yields = gold down, falling real yields = gold up",
        },
        "SP500": {
            "relationship": "weak_inverse",
            "strength": 0.3,
            "note": "Gold rises in risk-off, but correlation is inconsistent",
        },
        "VIX": {
            "relationship": "positive",
            "strength": 0.6,
            "note": "Fear = gold buying",
        },
        "OIL": {
            "relationship": "positive",
            "strength": 0.5,
            "note": "Both commodities, inflation hedge",
        },
    },
    
    "key_levels_2024_2025": {
        "all_time_high": 2790,  # As of late 2024
        "major_support": [2300, 2400, 2450, 2500],
        "major_resistance": [2600, 2700, 2800, 2900, 3000],
        "psychological": [2500, 2600, 2700, 2800, 2900, 3000],
    },
    
    "best_trading_times_ist": {
        "london_open": "13:30-15:30",  # High volatility
        "us_open": "18:30-20:30",  # Highest volatility
        "london_us_overlap": "18:30-21:30",  # Best time
        "avoid": "00:00-08:00",  # Asian session - low volatility for gold
    },
    
    "news_impacts": {
        "FOMC": {
            "impact": "extreme",
            "typical_move": "50-150 pips",
            "strategy": "wait_for_direction_then_follow",
        },
        "NFP": {
            "impact": "very_high",
            "typical_move": "30-100 pips",
            "strategy": "fade_initial_spike_if_contradicts_trend",
        },
        "CPI": {
            "impact": "very_high",
            "typical_move": "30-80 pips",
            "strategy": "trade_breakout_of_range",
        },
        "GDP": {
            "impact": "medium",
            "typical_move": "20-40 pips",
            "strategy": "follow_trend",
        },
        "UNEMPLOYMENT_CLAIMS": {
            "impact": "low",
            "typical_move": "10-20 pips",
            "strategy": "ignore_unless_extreme",
        },
        "FED_SPEAKERS": {
            "impact": "medium_to_high",
            "typical_move": "15-50 pips",
            "strategy": "trade_hawkish_dovish_shift",
        },
        "GEOPOLITICAL_CRISIS": {
            "impact": "extreme",
            "typical_move": "100-300 pips",
            "strategy": "buy_gold_immediately",
        },
    },
}

# ══════════════════════════════════════════════════════════════════════════════
#                         PROVEN PATTERNS
# ══════════════════════════════════════════════════════════════════════════════

PROVEN_PATTERNS: List[HistoricalPattern] = [
    HistoricalPattern(
        name="DXY Divergence",
        description="Gold moving opposite to expected DXY correlation - often precedes reversal",
        success_rate=0.65,
        best_conditions=["DXY making new highs but gold holding", "Clear divergence for 2+ hours"],
        avoid_when=["Major USD news pending", "FOMC week"],
        typical_rr=2.0,
    ),
    
    HistoricalPattern(
        name="London Open Breakout",
        description="Trade breakout of Asian session range at London open",
        success_rate=0.58,
        best_conditions=["Tight Asian range (<$10)", "Clear trend from previous day"],
        avoid_when=["Major news at London open", "Friday (reduced follow-through)"],
        typical_rr=1.5,
    ),
    
    HistoricalPattern(
        name="US Session Continuation",
        description="US session continues London direction after pullback",
        success_rate=0.62,
        best_conditions=["Strong London move (>$15)", "Pullback to 50% without breaking structure"],
        avoid_when=["US data release imminent", "End of month/quarter"],
        typical_rr=2.0,
    ),
    
    HistoricalPattern(
        name="NFP Fade",
        description="Fade the initial NFP spike after 15-30 minutes",
        success_rate=0.55,
        best_conditions=["Initial spike >$20", "Spike against prevailing trend"],
        avoid_when=["Data significantly beats/misses", "FOMC same week"],
        typical_rr=1.5,
    ),
    
    HistoricalPattern(
        name="Support/Resistance Bounce",
        description="Trade bounce off major support/resistance",
        success_rate=0.60,
        best_conditions=["Price touches level for first time", "RSI divergence at level"],
        avoid_when=["Third touch of level (likely to break)", "News pending"],
        typical_rr=2.5,
    ),
    
    HistoricalPattern(
        name="Breakout Retest",
        description="Trade retest of broken support/resistance",
        success_rate=0.68,
        best_conditions=["Clean break with volume", "Retest within 4-8 hours"],
        avoid_when=["Weak initial break", "Counter-trend"],
        typical_rr=2.0,
    ),
    
    HistoricalPattern(
        name="Rate Decision Momentum",
        description="Trade momentum 30+ minutes after FOMC/central bank decision",
        success_rate=0.58,
        best_conditions=["Clear hawkish/dovish shift", "Initial volatility settled"],
        avoid_when=["Mixed signals", "Press conference ongoing"],
        typical_rr=2.5,
    ),
    
    HistoricalPattern(
        name="Geopolitical Safe Haven",
        description="Buy gold on geopolitical crisis escalation",
        success_rate=0.75,
        best_conditions=["War/conflict news", "Market panic (VIX spike)"],
        avoid_when=["De-escalation news", "Weekend (can reverse)"],
        typical_rr=3.0,
    ),
    
    HistoricalPattern(
        name="Weekly Open Gap",
        description="Trade gap fill on weekly open",
        success_rate=0.70,
        best_conditions=["Gap < $15", "No major weekend news"],
        avoid_when=["Gap caused by major news", "Gap > $20"],
        typical_rr=1.5,
    ),
    
    HistoricalPattern(
        name="Triple Top/Bottom",
        description="Trade reversal on third touch of level",
        success_rate=0.55,
        best_conditions=["Clear three touches", "Momentum divergence"],
        avoid_when=["Strong trend", "News catalyst approaching"],
        typical_rr=3.0,
    ),
]

# ══════════════════════════════════════════════════════════════════════════════
#                     HISTORICAL LESSONS (WHAT WORKED)
# ══════════════════════════════════════════════════════════════════════════════

HISTORICAL_LESSONS = [
    {
        "lesson": "Always respect the trend",
        "detail": "Counter-trend trades have 30% lower win rate",
        "action": "Trade with the 4H trend unless at major level",
    },
    {
        "lesson": "News is opportunity, not obstacle",
        "detail": "Biggest moves happen around news - avoid missing them",
        "action": "Reduce size but stay in market during news",
    },
    {
        "lesson": "Asian session sets up, London/US executes",
        "detail": "Asian range breakouts have 60%+ follow-through",
        "action": "Identify Asian range, trade breakout at London",
    },
    {
        "lesson": "DXY is the leading indicator",
        "detail": "Gold often lags DXY moves by 5-15 minutes",
        "action": "Watch DXY for early signals",
    },
    {
        "lesson": "Round numbers matter",
        "detail": "2500, 2600, 2700 etc. act as psychological barriers",
        "action": "Expect reactions at round numbers",
    },
    {
        "lesson": "Friday is different",
        "detail": "Reduced follow-through, profit-taking common",
        "action": "Tighter targets on Friday, close before weekend",
    },
    {
        "lesson": "Month-end flows",
        "detail": "Last 2-3 days of month have unusual movements",
        "action": "Reduce size during month-end",
    },
    {
        "lesson": "Stop hunts are real",
        "detail": "Price often spikes through obvious levels before reversing",
        "action": "Place stops beyond obvious levels, use wider stops with smaller size",
    },
    {
        "lesson": "Volatility clusters",
        "detail": "High volatility follows high volatility",
        "action": "After big move, expect continuation of volatility",
    },
    {
        "lesson": "The first move is often wrong",
        "detail": "Initial reaction to news frequently reverses",
        "action": "Wait 15-30 min after news before entering",
    },
]

# ══════════════════════════════════════════════════════════════════════════════
#                     HIGH-LEVERAGE WISDOM
# ══════════════════════════════════════════════════════════════════════════════

HIGH_LEVERAGE_RULES = {
    "when_to_use_max_leverage": [
        "Clear trend + pullback to key level",
        "News-driven momentum confirmed",
        "Breakout of major consolidation",
        "Geopolitical safe-haven flow",
    ],
    
    "when_to_reduce_leverage": [
        "Ranging market",
        "Counter-trend trade",
        "Before major news",
        "End of session (less follow-through)",
        "Friday afternoon",
    ],
    
    "stop_loss_rules": {
        "high_leverage": "Tight stop (10-20 pips) is MANDATORY",
        "calculation": "Risk amount / Stop distance = Position size",
        "never": "Never move stop against position",
        "breakeven": "Move to breakeven at 1:1 profit",
    },
    
    "scaling": {
        "entry": "Enter with 50% size, add on confirmation",
        "exit": "Take 50% at 1:1, let rest run with trailing",
    },
}

# ══════════════════════════════════════════════════════════════════════════════
#                         MISTAKES TO AVOID
# ══════════════════════════════════════════════════════════════════════════════

COMMON_MISTAKES = [
    {
        "mistake": "Revenge trading after loss",
        "frequency": "Very common",
        "cost": "Often doubles the loss",
        "prevention": "Mandatory 1-hour pause after loss",
    },
    {
        "mistake": "Moving stop loss further away",
        "frequency": "Common",
        "cost": "Small loss becomes big loss",
        "prevention": "Stops are immutable once set",
    },
    {
        "mistake": "Overtrading in ranging market",
        "frequency": "Very common",
        "cost": "Death by 1000 cuts (spread + small losses)",
        "prevention": "Trade only when ADR > average",
    },
    {
        "mistake": "Fighting strong trend",
        "frequency": "Common",
        "cost": "Multiple stop-outs",
        "prevention": "Only trade with 4H trend",
    },
    {
        "mistake": "No stop loss",
        "frequency": "Common among beginners",
        "cost": "Account blow-up",
        "prevention": "Constitutional law - impossible without stop",
    },
    {
        "mistake": "Closing winners too early",
        "frequency": "Very common",
        "cost": "Reduced profit factor",
        "prevention": "Use trailing stop, don't close manually",
    },
    {
        "mistake": "Averaging down losing position",
        "frequency": "Common",
        "cost": "Exponential loss",
        "prevention": "Constitutional law - no adding to losers",
    },
]


def get_trading_knowledge() -> Dict[str, Any]:
    """Get all pre-loaded trading knowledge."""
    return {
        "gold": GOLD_KNOWLEDGE,
        "patterns": [p.__dict__ for p in PROVEN_PATTERNS],
        "lessons": HISTORICAL_LESSONS,
        "high_leverage_rules": HIGH_LEVERAGE_RULES,
        "mistakes_to_avoid": COMMON_MISTAKES,
    }


def get_knowledge_prompt() -> str:
    """Get knowledge as system prompt injection."""
    
    patterns_text = "\n".join([
        f"- {p.name} ({p.success_rate:.0%} win rate, {p.typical_rr}:1 R:R): {p.description}"
        for p in PROVEN_PATTERNS
    ])
    
    lessons_text = "\n".join([
        f"- {l['lesson']}: {l['action']}"
        for l in HISTORICAL_LESSONS
    ])
    
    return f"""## Pre-Loaded Trading Knowledge

### Gold (XAU/USD) Correlations
- DXY (US Dollar Index): INVERSE correlation (0.85 strength) - Key leading indicator
- US Real Yields: INVERSE correlation (0.90 strength) - Most important fundamental
- VIX (Fear Index): POSITIVE correlation - Gold rises in panic

### Best Trading Times (IST)
- London Open: 13:30-15:30 (High volatility)
- US Open: 18:30-20:30 (Highest volatility)  
- London-US Overlap: 18:30-21:30 (BEST time to trade)
- Avoid: 00:00-08:00 (Low volatility)

### Proven Patterns
{patterns_text}

### Key Lessons
{lessons_text}

### High Leverage Rules
- USE max leverage when: Clear trend + pullback, news momentum confirmed, breakout
- REDUCE leverage when: Ranging, counter-trend, before news, Friday

### Critical Rules
- Always trade with the 4H trend
- Wait 15-30 min after news before entering
- Expect stop hunts beyond obvious levels
- Friday has reduced follow-through
- The first move after news is often wrong
"""
