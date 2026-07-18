"""
News Trading Strategy

High-impact news = HIGH RISK + HIGH REWARD opportunity.

Instead of avoiding news, trade it INTELLIGENTLY:
1. Pre-news positioning (directional bet)
2. Straddle (bet on big move either direction)
3. Post-news fade (trade the reversal)
4. Breakout continuation (trade after dust settles)

Key adjustments for news trading:
- SMALLER position (slippage protection)
- WIDER stops (survive the spike)
- QUICK profit taking (don't hold through reversal)
- OR wait for confirmation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Optional, Dict, Any


class NewsImpact(Enum):
    """News event impact level."""
    LOW = "low"           # Minor impact, trade normally
    MEDIUM = "medium"     # Moderate impact, slight adjustments
    HIGH = "high"         # Major impact, news trading mode
    CRITICAL = "critical" # Extreme (FOMC, NFP) - special handling


class NewsStrategy(Enum):
    """How to trade around news."""
    AVOID = "avoid"                    # Stay out completely
    PRE_NEWS_DIRECTIONAL = "pre_dir"   # Take directional bet before
    STRADDLE = "straddle"              # Bet on volatility, not direction
    POST_NEWS_FADE = "fade"            # Trade the reversal after spike
    POST_NEWS_BREAKOUT = "breakout"    # Trade continuation after settle
    SCALP_THE_SPIKE = "scalp"          # Quick in-and-out during spike


@dataclass
class NewsEvent:
    """A scheduled news event."""
    name: str
    currency: str           # "USD", "EUR", etc.
    impact: NewsImpact
    scheduled_time: datetime
    
    # Historical data for this event type
    avg_move_pips: float = 0.0       # Average price move
    avg_spike_pips: float = 0.0      # Initial spike size
    avg_reversal_pct: float = 0.0    # How much it typically reverses
    typical_duration_minutes: int = 30
    
    # Actual outcome (filled after event)
    actual_value: Optional[float] = None
    forecast_value: Optional[float] = None
    previous_value: Optional[float] = None
    actual_move_pips: Optional[float] = None


# Major news events and their typical characteristics for XAU/USD
MAJOR_NEWS_PROFILES: Dict[str, Dict[str, Any]] = {
    "NFP": {
        "full_name": "Non-Farm Payrolls",
        "impact": NewsImpact.CRITICAL,
        "avg_move_pips": 250,      # $25 for gold
        "avg_spike_pips": 150,     # Initial spike $15
        "avg_reversal_pct": 40,    # Often reverses 40% of initial move
        "typical_duration_minutes": 60,
        "best_strategy": NewsStrategy.POST_NEWS_FADE,
    },
    "FOMC": {
        "full_name": "Federal Reserve Decision",
        "impact": NewsImpact.CRITICAL,
        "avg_move_pips": 300,
        "avg_spike_pips": 200,
        "avg_reversal_pct": 30,
        "typical_duration_minutes": 120,
        "best_strategy": NewsStrategy.POST_NEWS_BREAKOUT,
    },
    "CPI": {
        "full_name": "Consumer Price Index",
        "impact": NewsImpact.HIGH,
        "avg_move_pips": 200,
        "avg_spike_pips": 100,
        "avg_reversal_pct": 50,
        "typical_duration_minutes": 45,
        "best_strategy": NewsStrategy.POST_NEWS_FADE,
    },
    "PPI": {
        "full_name": "Producer Price Index",
        "impact": NewsImpact.MEDIUM,
        "avg_move_pips": 100,
        "avg_spike_pips": 50,
        "avg_reversal_pct": 60,
        "typical_duration_minutes": 30,
        "best_strategy": NewsStrategy.POST_NEWS_FADE,
    },
    "RETAIL_SALES": {
        "full_name": "Retail Sales",
        "impact": NewsImpact.MEDIUM,
        "avg_move_pips": 80,
        "avg_spike_pips": 40,
        "avg_reversal_pct": 50,
        "typical_duration_minutes": 30,
        "best_strategy": NewsStrategy.SCALP_THE_SPIKE,
    },
    "GDP": {
        "full_name": "Gross Domestic Product",
        "impact": NewsImpact.HIGH,
        "avg_move_pips": 150,
        "avg_spike_pips": 80,
        "avg_reversal_pct": 35,
        "typical_duration_minutes": 60,
        "best_strategy": NewsStrategy.POST_NEWS_BREAKOUT,
    },
    "UNEMPLOYMENT": {
        "full_name": "Unemployment Claims",
        "impact": NewsImpact.LOW,
        "avg_move_pips": 50,
        "avg_spike_pips": 25,
        "avg_reversal_pct": 70,
        "typical_duration_minutes": 15,
        "best_strategy": NewsStrategy.SCALP_THE_SPIKE,
    },
}


@dataclass
class NewsTradeSetup:
    """
    Setup for trading around a news event.
    
    Adjusts risk parameters specifically for news volatility.
    """
    event: NewsEvent
    strategy: NewsStrategy
    
    # Position sizing (SMALLER for news)
    position_multiplier: float = 0.5    # 50% of normal size
    
    # Stop loss (WIDER for news)
    stop_loss_multiplier: float = 2.0   # 2x normal stop
    
    # Take profit (QUICKER for news)
    take_profit_multiplier: float = 1.5 # 1.5x normal TP (but take faster)
    
    # Timing
    entry_minutes_before: int = 0       # 0 = after news
    exit_minutes_after: int = 30        # Max time in trade
    
    # Partial profits
    take_50_pct_at_rr: float = 1.0     # Take half at 1:1
    take_remaining_at_rr: float = 2.0  # Take rest at 2:1
    
    @classmethod
    def for_strategy(cls, event: NewsEvent, strategy: NewsStrategy) -> "NewsTradeSetup":
        """Create setup based on strategy type."""
        
        if strategy == NewsStrategy.AVOID:
            return cls(
                event=event,
                strategy=strategy,
                position_multiplier=0.0,  # No trading
            )
        
        elif strategy == NewsStrategy.PRE_NEWS_DIRECTIONAL:
            # Take position before news, betting on direction
            # VERY RISKY but can be very profitable
            return cls(
                event=event,
                strategy=strategy,
                position_multiplier=0.3,    # 30% size (high risk)
                stop_loss_multiplier=3.0,   # Wide stop (survive spike)
                take_profit_multiplier=3.0, # Big target
                entry_minutes_before=5,     # Enter 5 min before
                exit_minutes_after=15,      # Quick exit
                take_50_pct_at_rr=1.5,
                take_remaining_at_rr=3.0,
            )
        
        elif strategy == NewsStrategy.STRADDLE:
            # Position for big move either direction
            return cls(
                event=event,
                strategy=strategy,
                position_multiplier=0.25,   # Small each side
                stop_loss_multiplier=1.5,   # Tighter (one side will lose)
                take_profit_multiplier=4.0, # Big target on winner
                entry_minutes_before=2,
                exit_minutes_after=30,
                take_50_pct_at_rr=2.0,
                take_remaining_at_rr=4.0,
            )
        
        elif strategy == NewsStrategy.POST_NEWS_FADE:
            # Wait for spike, then trade reversal
            # SAFEST news strategy
            return cls(
                event=event,
                strategy=strategy,
                position_multiplier=0.5,    # Half size
                stop_loss_multiplier=1.5,   # Medium stop
                take_profit_multiplier=1.5, # Quick target
                entry_minutes_before=-5,    # Enter 5 min AFTER news
                exit_minutes_after=45,
                take_50_pct_at_rr=0.75,     # Quick partial
                take_remaining_at_rr=1.5,
            )
        
        elif strategy == NewsStrategy.POST_NEWS_BREAKOUT:
            # Wait for dust to settle, trade continuation
            return cls(
                event=event,
                strategy=strategy,
                position_multiplier=0.6,    # 60% size
                stop_loss_multiplier=1.5,
                take_profit_multiplier=2.0,
                entry_minutes_before=-15,   # Enter 15 min AFTER
                exit_minutes_after=60,
                take_50_pct_at_rr=1.0,
                take_remaining_at_rr=2.0,
            )
        
        elif strategy == NewsStrategy.SCALP_THE_SPIKE:
            # Quick in-and-out during initial volatility
            return cls(
                event=event,
                strategy=strategy,
                position_multiplier=0.4,
                stop_loss_multiplier=2.0,   # Wide to survive
                take_profit_multiplier=1.0, # Quick target
                entry_minutes_before=0,     # Right at news
                exit_minutes_after=10,      # Very quick
                take_50_pct_at_rr=0.5,      # Very quick partial
                take_remaining_at_rr=1.0,
            )
        
        return cls(event=event, strategy=strategy)


class NewsTradeManager:
    """
    Manages trading around news events.
    
    Philosophy: News = opportunity, not just risk.
    But must be traded DIFFERENTLY than normal conditions.
    """
    
    def __init__(self):
        self.upcoming_events: List[NewsEvent] = []
        self.completed_news_trades: List[Dict] = []
        self.learned_adjustments: Dict[str, Dict] = {}
    
    def analyze_news_opportunity(
        self, 
        event: NewsEvent,
        current_price: float,
        account_balance: float,
        current_position: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Analyze a news event for trading opportunity.
        
        Returns recommendation on how to trade it.
        """
        # Get profile for this event type
        event_key = event.name.upper().replace(" ", "_")
        profile = MAJOR_NEWS_PROFILES.get(event_key, {})
        
        # Calculate expected move
        expected_move_pips = profile.get("avg_move_pips", event.avg_move_pips)
        expected_spike_pips = profile.get("avg_spike_pips", event.avg_spike_pips)
        expected_reversal = profile.get("avg_reversal_pct", event.avg_reversal_pct)
        
        # Determine best strategy
        if event.impact == NewsImpact.CRITICAL:
            # For critical events (NFP, FOMC), post-news strategies are safer
            recommended_strategy = profile.get("best_strategy", NewsStrategy.POST_NEWS_FADE)
        elif event.impact == NewsImpact.HIGH:
            recommended_strategy = profile.get("best_strategy", NewsStrategy.POST_NEWS_FADE)
        elif event.impact == NewsImpact.MEDIUM:
            recommended_strategy = profile.get("best_strategy", NewsStrategy.SCALP_THE_SPIKE)
        else:
            # Low impact - could trade normally or scalp
            recommended_strategy = NewsStrategy.SCALP_THE_SPIKE
        
        # Calculate potential profit
        setup = NewsTradeSetup.for_strategy(event, recommended_strategy)
        
        # Risk amount with news position sizing
        base_risk_pct = 5.0  # Would come from AdaptiveParameters
        news_risk_pct = base_risk_pct * setup.position_multiplier
        risk_amount = account_balance * (news_risk_pct / 100)
        
        # Potential reward
        potential_profit_pips = expected_move_pips * (1 - expected_reversal/100)
        
        # Handle existing position
        position_advice = None
        if current_position:
            # We have an open position going into news
            unrealized_pnl = current_position.get("unrealized_pnl", 0)
            if unrealized_pnl > 0:
                position_advice = "TAKE_PROFIT_BEFORE_NEWS"
            else:
                position_advice = "CLOSE_OR_HEDGE_BEFORE_NEWS"
        
        return {
            "event": event.name,
            "impact": event.impact.value,
            "time_until_minutes": self._minutes_until(event.scheduled_time),
            
            "opportunity": {
                "expected_move_pips": expected_move_pips,
                "expected_spike_pips": expected_spike_pips,
                "expected_reversal_pct": expected_reversal,
                "potential_profit_pips": potential_profit_pips,
            },
            
            "recommendation": {
                "strategy": recommended_strategy.value,
                "position_size_multiplier": setup.position_multiplier,
                "stop_loss_multiplier": setup.stop_loss_multiplier,
                "take_profit_multiplier": setup.take_profit_multiplier,
                "entry_timing": f"{abs(setup.entry_minutes_before)} min {'before' if setup.entry_minutes_before > 0 else 'after'} news",
                "max_hold_minutes": setup.exit_minutes_after,
            },
            
            "risk": {
                "risk_pct": news_risk_pct,
                "risk_amount": risk_amount,
                "warning": "Slippage likely during news - actual risk may be higher",
            },
            
            "existing_position_advice": position_advice,
        }
    
    def get_news_adjusted_parameters(
        self,
        base_risk_pct: float,
        base_sl_pips: float,
        base_tp_pips: float,
        news_event: NewsEvent,
        strategy: NewsStrategy
    ) -> Dict[str, float]:
        """
        Get adjusted trading parameters for news event.
        """
        setup = NewsTradeSetup.for_strategy(news_event, strategy)
        
        return {
            "risk_pct": base_risk_pct * setup.position_multiplier,
            "stop_loss_pips": base_sl_pips * setup.stop_loss_multiplier,
            "take_profit_pips": base_tp_pips * setup.take_profit_multiplier,
            "partial_tp_1_rr": setup.take_50_pct_at_rr,
            "partial_tp_1_size_pct": 50,
            "partial_tp_2_rr": setup.take_remaining_at_rr,
            "max_hold_minutes": setup.exit_minutes_after,
        }
    
    def learn_from_news_trade(
        self,
        event: NewsEvent,
        strategy: NewsStrategy,
        actual_move_pips: float,
        our_pnl_pips: float,
        slippage_pips: float
    ) -> None:
        """
        Learn from news trade outcome to improve future performance.
        """
        event_key = event.name.upper().replace(" ", "_")
        
        if event_key not in self.learned_adjustments:
            self.learned_adjustments[event_key] = {
                "trades": 0,
                "wins": 0,
                "total_slippage": 0,
                "avg_actual_move": 0,
                "best_strategy": {},
            }
        
        adj = self.learned_adjustments[event_key]
        adj["trades"] += 1
        adj["total_slippage"] += slippage_pips
        adj["avg_actual_move"] = (adj["avg_actual_move"] * (adj["trades"] - 1) + actual_move_pips) / adj["trades"]
        
        if our_pnl_pips > 0:
            adj["wins"] += 1
        
        # Track which strategy works best for this event
        strat_key = strategy.value
        if strat_key not in adj["best_strategy"]:
            adj["best_strategy"][strat_key] = {"trades": 0, "wins": 0, "total_pnl": 0}
        
        adj["best_strategy"][strat_key]["trades"] += 1
        adj["best_strategy"][strat_key]["total_pnl"] += our_pnl_pips
        if our_pnl_pips > 0:
            adj["best_strategy"][strat_key]["wins"] += 1
    
    def get_recommended_strategy_for_event(self, event_name: str) -> NewsStrategy:
        """
        Get the best strategy based on our learning.
        """
        event_key = event_name.upper().replace(" ", "_")
        
        # Check if we have learned data
        if event_key in self.learned_adjustments:
            adj = self.learned_adjustments[event_key]
            if adj["best_strategy"]:
                # Find strategy with best win rate and total PnL
                best_strat = max(
                    adj["best_strategy"].items(),
                    key=lambda x: (x[1]["wins"] / max(x[1]["trades"], 1), x[1]["total_pnl"])
                )
                return NewsStrategy(best_strat[0])
        
        # Fall back to profile default
        profile = MAJOR_NEWS_PROFILES.get(event_key, {})
        return profile.get("best_strategy", NewsStrategy.POST_NEWS_FADE)
    
    def _minutes_until(self, event_time: datetime) -> float:
        """Calculate minutes until event."""
        now = datetime.utcnow()
        delta = event_time - now
        return delta.total_seconds() / 60


# Quick reference for XAU/USD news impact
GOLD_NEWS_IMPACT = """
╔══════════════════════════════════════════════════════════════════╗
║                    XAU/USD NEWS IMPACT GUIDE                     ║
╠══════════════════════════════════════════════════════════════════╣
║  EVENT          │ AVG MOVE  │ BEST STRATEGY    │ TIMING          ║
╠══════════════════════════════════════════════════════════════════╣
║  NFP            │ $25-30    │ Fade reversal    │ 5 min after     ║
║  FOMC           │ $30-50    │ Breakout         │ 15 min after    ║
║  CPI            │ $15-25    │ Fade reversal    │ 5 min after     ║
║  PPI            │ $8-12     │ Fade reversal    │ Immediate       ║
║  GDP            │ $12-18    │ Breakout         │ 10 min after    ║
║  Retail Sales   │ $6-10     │ Scalp spike      │ Immediate       ║
║  Unemployment   │ $4-8      │ Scalp spike      │ Immediate       ║
╠══════════════════════════════════════════════════════════════════╣
║  KEY RULES:                                                      ║
║  1. Position size = 30-50% of normal                             ║
║  2. Stop loss = 1.5-2x normal (survive spike)                    ║
║  3. Take profit QUICKLY (reversal common)                        ║
║  4. Expect slippage - account for it                             ║
╚══════════════════════════════════════════════════════════════════╝
"""
