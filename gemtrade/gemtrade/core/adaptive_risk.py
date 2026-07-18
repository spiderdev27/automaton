"""
Adaptive Risk Management System

For small capital (₹5,000), we can't afford mediocre trades.
This system:
1. Scores signal QUALITY before taking trades
2. Sizes positions based on CONVICTION
3. Adapts parameters through LEARNING
4. Manages trades ACTIVELY in real-time
5. FEELS market conditions through multiple factors

Philosophy: With small capital, be a SNIPER, not a machine gunner.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


class MarketRegime(Enum):
    """Current market condition."""
    TRENDING_STRONG = "trending_strong"     # Strong trend, go with it
    TRENDING_WEAK = "trending_weak"         # Weak trend, be careful
    RANGING = "ranging"                     # Sideways, fade extremes
    VOLATILE = "volatile"                   # High volatility, reduce size
    QUIET = "quiet"                         # Low volatility, skip or reduce
    NEWS_OPPORTUNITY = "news_opportunity"   # High-impact news = OPPORTUNITY
    NEWS_ACTIVE = "news_active"             # News happening NOW


class SignalQuality(Enum):
    """Quality grade for trade signals."""
    A_PLUS = "A+"    # Perfect setup, max size
    A = "A"          # Great setup, full size
    B = "B"          # Good setup, reduced size
    C = "C"          # Marginal setup, minimum size
    F = "F"          # Poor setup, DO NOT TRADE


@dataclass
class SignalScore:
    """
    Comprehensive scoring of a trade signal.
    
    Only take A+ and A signals with small capital.
    """
    # Technical factors (0-100 each)
    trend_alignment: int = 0        # Is signal with the trend?
    multi_timeframe: int = 0        # Do multiple timeframes agree?
    indicator_confluence: int = 0   # Do multiple indicators agree?
    key_level: int = 0              # At support/resistance?
    pattern_quality: int = 0        # Chart pattern clarity
    
    # Market condition factors (0-100 each)
    volatility_favorable: int = 0   # Is volatility good for this trade?
    session_timing: int = 0         # Good trading session?
    news_clear: int = 0             # No high-impact news pending?
    spread_acceptable: int = 0      # Is spread reasonable?
    
    # Risk factors (0-100 each)
    stop_loss_logical: int = 0      # Stop at logical level?
    risk_reward_ratio: int = 0      # R:R >= 2:1?
    
    @property
    def total_score(self) -> int:
        """Calculate total score (0-1100)."""
        return (
            self.trend_alignment +
            self.multi_timeframe +
            self.indicator_confluence +
            self.key_level +
            self.pattern_quality +
            self.volatility_favorable +
            self.session_timing +
            self.news_clear +
            self.spread_acceptable +
            self.stop_loss_logical +
            self.risk_reward_ratio
        )
    
    @property
    def quality(self) -> SignalQuality:
        """Grade the signal quality."""
        score = self.total_score
        if score >= 900:
            return SignalQuality.A_PLUS
        elif score >= 750:
            return SignalQuality.A
        elif score >= 600:
            return SignalQuality.B
        elif score >= 450:
            return SignalQuality.C
        else:
            return SignalQuality.F
    
    @property
    def position_multiplier(self) -> float:
        """Position size multiplier based on quality."""
        return {
            SignalQuality.A_PLUS: 1.5,   # 150% of base size
            SignalQuality.A: 1.0,        # 100% of base size
            SignalQuality.B: 0.5,        # 50% of base size
            SignalQuality.C: 0.25,       # 25% of base size
            SignalQuality.F: 0.0,        # DO NOT TRADE
        }[self.quality]
    
    @property
    def should_trade(self) -> bool:
        """Should we take this trade?"""
        return self.quality in (SignalQuality.A_PLUS, SignalQuality.A)
    
    def to_dict(self) -> dict:
        return {
            "trend_alignment": self.trend_alignment,
            "multi_timeframe": self.multi_timeframe,
            "indicator_confluence": self.indicator_confluence,
            "key_level": self.key_level,
            "pattern_quality": self.pattern_quality,
            "volatility_favorable": self.volatility_favorable,
            "session_timing": self.session_timing,
            "news_clear": self.news_clear,
            "spread_acceptable": self.spread_acceptable,
            "stop_loss_logical": self.stop_loss_logical,
            "risk_reward_ratio": self.risk_reward_ratio,
            "total_score": self.total_score,
            "quality": self.quality.value,
            "should_trade": self.should_trade,
        }


@dataclass
class AdaptiveParameters:
    """
    Self-learning parameters that adapt based on performance.
    
    These START with defaults but LEARN from each trade.
    """
    # Risk parameters (adapt based on recent performance)
    base_risk_pct: float = 5.0          # Starting risk per trade
    current_risk_pct: float = 5.0       # Current risk (adapts)
    min_risk_pct: float = 2.0           # Never go below
    max_risk_pct: float = 15.0          # Never go above
    
    # Stop loss parameters (adapt based on what works)
    default_sl_atr_multiplier: float = 2.0    # SL = 2x ATR
    current_sl_atr_multiplier: float = 2.0    # Adapts
    min_sl_atr: float = 1.0
    max_sl_atr: float = 4.0
    
    # Take profit parameters
    default_tp_atr_multiplier: float = 4.0    # TP = 4x ATR (2:1 R:R)
    current_tp_atr_multiplier: float = 4.0    # Adapts
    
    # Leverage (adapts with capital growth)
    base_leverage: int = 200
    current_leverage: int = 200
    max_leverage: int = 1000
    
    # Learning rates (how fast to adapt)
    win_adaptation_rate: float = 0.1    # How much to adjust on win
    loss_adaptation_rate: float = 0.15  # How much to adjust on loss (faster)
    
    # Performance tracking for adaptation
    recent_trades: int = 0
    recent_wins: int = 0
    recent_losses: int = 0
    win_streak: int = 0
    loss_streak: int = 0
    
    def adapt_after_win(self, profit_pct: float, trade_data: dict) -> None:
        """Adapt parameters after a winning trade."""
        self.recent_trades += 1
        self.recent_wins += 1
        self.win_streak += 1
        self.loss_streak = 0
        
        # Increase risk slightly after wins (confidence)
        if self.win_streak >= 3:
            adjustment = self.win_adaptation_rate * self.win_streak
            self.current_risk_pct = min(
                self.current_risk_pct * (1 + adjustment),
                self.max_risk_pct
            )
        
        # If take profit hit exactly, our TP might be good
        # If closed early with profit, maybe TP was too ambitious
        
    def adapt_after_loss(self, loss_pct: float, trade_data: dict) -> None:
        """Adapt parameters after a losing trade."""
        self.recent_trades += 1
        self.recent_losses += 1
        self.loss_streak += 1
        self.win_streak = 0
        
        # Decrease risk after losses (protection)
        adjustment = self.loss_adaptation_rate * self.loss_streak
        self.current_risk_pct = max(
            self.current_risk_pct * (1 - adjustment),
            self.min_risk_pct
        )
        
        # If stopped out quickly, maybe SL too tight
        # If stopped out after being in profit, need better trailing
        
    def adapt_stop_loss(self, hit_sl: bool, max_favorable: float, max_adverse: float) -> None:
        """Learn optimal stop loss distance from trade outcomes."""
        if hit_sl:
            # Was the stop logical or too tight?
            if max_favorable > 0:
                # We were in profit but got stopped - SL too tight
                self.current_sl_atr_multiplier = min(
                    self.current_sl_atr_multiplier * 1.1,
                    self.max_sl_atr
                )
        else:
            # Didn't hit SL - could it have been tighter?
            if max_adverse < (self.current_sl_atr_multiplier * 0.5):
                # Price never came close to SL - could tighten
                self.current_sl_atr_multiplier = max(
                    self.current_sl_atr_multiplier * 0.95,
                    self.min_sl_atr
                )
    
    def get_risk_for_quality(self, quality: SignalQuality) -> float:
        """Get risk percentage based on signal quality."""
        multipliers = {
            SignalQuality.A_PLUS: 1.5,
            SignalQuality.A: 1.0,
            SignalQuality.B: 0.5,
            SignalQuality.C: 0.25,
            SignalQuality.F: 0.0,
        }
        return self.current_risk_pct * multipliers[quality]
    
    def reset_streak_tracking(self) -> None:
        """Reset for new trading period."""
        self.recent_trades = 0
        self.recent_wins = 0
        self.recent_losses = 0


@dataclass
class MarketCondition:
    """
    Real-time market condition assessment.
    
    The agent should "feel" these conditions and adapt.
    """
    # Volatility
    current_atr: float = 0.0
    atr_percentile: float = 50.0        # 0-100, where current ATR falls historically
    
    # Trend
    trend_direction: str = "neutral"    # "bullish", "bearish", "neutral"
    trend_strength: float = 0.0         # ADX value
    
    # Session
    current_session: str = "asian"      # "asian", "london", "newyork", "overlap"
    session_volatility: str = "normal"  # "high", "normal", "low"
    
    # News
    high_impact_news_in_hours: float = 999.0  # Hours until next high-impact news
    news_sentiment: str = "neutral"     # "bullish", "bearish", "neutral", "mixed"
    
    # Spread
    current_spread_pips: float = 0.0
    spread_percentile: float = 50.0     # Is spread normal or wide?
    
    # Price action
    at_key_level: bool = False
    near_round_number: bool = False
    
    @property
    def regime(self) -> MarketRegime:
        """Determine current market regime."""
        # News within 30 minutes = OPPORTUNITY (not just risk)
        if 0 < self.high_impact_news_in_hours < 0.5:
            return MarketRegime.NEWS_OPPORTUNITY
        
        # News happening RIGHT NOW (< 5 min ago)
        if -0.083 < self.high_impact_news_in_hours <= 0:
            return MarketRegime.NEWS_ACTIVE
        
        # High volatility
        if self.atr_percentile > 80:
            return MarketRegime.VOLATILE
        
        # Low volatility
        if self.atr_percentile < 20:
            return MarketRegime.QUIET
        
        # Strong trend
        if self.trend_strength > 40:
            return MarketRegime.TRENDING_STRONG
        
        # Weak trend
        if self.trend_strength > 20:
            return MarketRegime.TRENDING_WEAK
        
        return MarketRegime.RANGING
    
    @property
    def should_trade(self) -> bool:
        """Is it a good time to trade?"""
        # Don't trade when spread is too wide (>90th percentile)
        if self.spread_percentile > 90:
            return False
        
        # Don't trade during very quiet markets
        if self.regime == MarketRegime.QUIET and self.current_session == "asian":
            return False
        
        # NEWS IS TRADEABLE - just with different parameters
        # (handled by NewsTradeManager)
        
        return True
    
    @property
    def is_news_opportunity(self) -> bool:
        """Is this a news trading opportunity?"""
        return self.regime in (MarketRegime.NEWS_OPPORTUNITY, MarketRegime.NEWS_ACTIVE)
    
    @property
    def news_trade_type(self) -> str:
        """What type of news trade is this?"""
        if self.high_impact_news_in_hours > 0.5:
            return "none"
        elif self.high_impact_news_in_hours > 0.083:  # > 5 min before
            return "pre_news"  # Can position before
        elif self.high_impact_news_in_hours > -0.083:  # Within 5 min of news
            return "during_news"  # Spike phase
        elif self.high_impact_news_in_hours > -0.25:  # 5-15 min after
            return "post_news_immediate"  # Fade opportunity
        elif self.high_impact_news_in_hours > -1:  # 15-60 min after
            return "post_news_settle"  # Breakout opportunity
        else:
            return "none"
    
    @property
    def position_adjustment(self) -> float:
        """Adjust position size based on conditions."""
        adjustment = 1.0
        
        # Reduce in high volatility
        if self.regime == MarketRegime.VOLATILE:
            adjustment *= 0.5
        
        # Reduce when spread is wide
        if self.spread_percentile > 70:
            adjustment *= 0.8
        
        # Increase during optimal sessions
        if self.current_session in ("london", "overlap"):
            adjustment *= 1.2
        
        # Reduce during asian session for XAU/USD
        if self.current_session == "asian":
            adjustment *= 0.7
        
        return min(adjustment, 1.5)  # Cap at 150%


@dataclass
class ActiveTradeManager:
    """
    Manages a trade DURING its lifetime.
    
    This is where the "feeling" happens - reacting to changing conditions.
    """
    trade_id: str
    entry_price: float
    stop_loss: float
    take_profit: float
    direction: str  # "long" or "short"
    
    # Real-time tracking
    current_price: float = 0.0
    max_favorable_excursion: float = 0.0  # Best unrealized profit
    max_adverse_excursion: float = 0.0    # Worst unrealized loss
    time_in_trade_minutes: int = 0
    
    # Trailing stop
    trailing_stop_active: bool = False
    trailing_stop_level: float = 0.0
    trailing_stop_distance: float = 0.0
    
    # Partial exits
    partial_exits: List[Dict] = field(default_factory=list)
    remaining_size_pct: float = 100.0
    
    # Alerts
    alerts_triggered: List[str] = field(default_factory=list)
    
    def update(self, new_price: float, market_condition: MarketCondition) -> List[str]:
        """
        Update trade state and return any actions to take.
        
        This is the real-time "feeling" - reacting to what's happening.
        """
        actions = []
        self.current_price = new_price
        
        # Calculate current P&L
        if self.direction == "long":
            pnl_pips = new_price - self.entry_price
        else:
            pnl_pips = self.entry_price - new_price
        
        # Track excursions
        if pnl_pips > self.max_favorable_excursion:
            self.max_favorable_excursion = pnl_pips
        if pnl_pips < -self.max_adverse_excursion:
            self.max_adverse_excursion = abs(pnl_pips)
        
        # ─────────────────────────────────────────────────────────────
        # RULE 1: Move to breakeven after 1:1 profit
        # ─────────────────────────────────────────────────────────────
        risk_distance = abs(self.entry_price - self.stop_loss)
        if pnl_pips >= risk_distance and self.stop_loss != self.entry_price:
            actions.append("MOVE_TO_BREAKEVEN")
            self.stop_loss = self.entry_price + (0.0001 if self.direction == "long" else -0.0001)
            self.alerts_triggered.append("Moved stop to breakeven")
        
        # ─────────────────────────────────────────────────────────────
        # RULE 2: Activate trailing stop after 1.5:1 profit
        # ─────────────────────────────────────────────────────────────
        if pnl_pips >= risk_distance * 1.5 and not self.trailing_stop_active:
            self.trailing_stop_active = True
            self.trailing_stop_distance = risk_distance * 0.5  # Trail at 50% of original risk
            self.alerts_triggered.append("Trailing stop activated")
        
        # ─────────────────────────────────────────────────────────────
        # RULE 3: Update trailing stop
        # ─────────────────────────────────────────────────────────────
        if self.trailing_stop_active:
            if self.direction == "long":
                new_trail = new_price - self.trailing_stop_distance
                if new_trail > self.stop_loss:
                    self.stop_loss = new_trail
                    actions.append("UPDATE_TRAILING_STOP")
            else:
                new_trail = new_price + self.trailing_stop_distance
                if new_trail < self.stop_loss:
                    self.stop_loss = new_trail
                    actions.append("UPDATE_TRAILING_STOP")
        
        # ─────────────────────────────────────────────────────────────
        # RULE 4: Partial profit at 2:1
        # ─────────────────────────────────────────────────────────────
        if pnl_pips >= risk_distance * 2 and self.remaining_size_pct == 100.0:
            actions.append("PARTIAL_CLOSE_50")
            self.remaining_size_pct = 50.0
            self.partial_exits.append({
                "price": new_price,
                "size_pct": 50.0,
                "pnl_multiple": 2.0
            })
            self.alerts_triggered.append("Took 50% profit at 2:1")
        
        # ─────────────────────────────────────────────────────────────
        # RULE 5: Tighten stop before news
        # ─────────────────────────────────────────────────────────────
        if market_condition.high_impact_news_in_hours < 0.25:  # 15 minutes
            if "NEWS_WARNING" not in self.alerts_triggered:
                actions.append("TIGHTEN_STOP_NEWS")
                self.alerts_triggered.append("NEWS_WARNING")
                # Move stop to lock in at least some profit if possible
                if pnl_pips > 0:
                    self.stop_loss = self.entry_price  # At minimum breakeven
        
        # ─────────────────────────────────────────────────────────────
        # RULE 6: Close if volatility spikes mid-trade
        # ─────────────────────────────────────────────────────────────
        if market_condition.atr_percentile > 95:
            if "VOLATILITY_SPIKE" not in self.alerts_triggered:
                actions.append("CLOSE_VOLATILITY_SPIKE")
                self.alerts_triggered.append("VOLATILITY_SPIKE")
        
        # ─────────────────────────────────────────────────────────────
        # RULE 7: Time-based management
        # ─────────────────────────────────────────────────────────────
        if self.time_in_trade_minutes > 240:  # 4 hours
            if pnl_pips < risk_distance * 0.5:  # Less than 0.5:1 profit
                if "TIME_WARNING" not in self.alerts_triggered:
                    actions.append("CONSIDER_CLOSE_TIME")
                    self.alerts_triggered.append("TIME_WARNING")
        
        return actions


class AdaptiveRiskManager:
    """
    The main adaptive risk management system.
    
    Combines:
    - Signal quality scoring
    - Adaptive parameters (learning)
    - Market condition awareness
    - Active trade management
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        self.parameters = AdaptiveParameters()
        self.active_trades: Dict[str, ActiveTradeManager] = {}
        self.trade_history: List[Dict] = []
        self.config_path = config_path
        
        if config_path and config_path.exists():
            self.load()
    
    def score_signal(
        self,
        signal: Dict[str, Any],
        market_condition: MarketCondition
    ) -> SignalScore:
        """
        Score a trade signal for quality.
        
        Returns whether to take the trade and at what size.
        """
        score = SignalScore()
        
        # These would be calculated from actual market data
        # For now, showing the structure
        
        # Trend alignment
        if signal.get("direction") == market_condition.trend_direction:
            score.trend_alignment = 100
        elif market_condition.trend_direction == "neutral":
            score.trend_alignment = 50
        else:
            score.trend_alignment = 0
        
        # Multi-timeframe (from signal data)
        score.multi_timeframe = signal.get("mtf_score", 50)
        
        # Indicator confluence
        score.indicator_confluence = signal.get("indicator_score", 50)
        
        # Key level
        score.key_level = 100 if market_condition.at_key_level else 30
        
        # Pattern quality
        score.pattern_quality = signal.get("pattern_score", 50)
        
        # Volatility
        if 30 <= market_condition.atr_percentile <= 70:
            score.volatility_favorable = 100
        elif 20 <= market_condition.atr_percentile <= 80:
            score.volatility_favorable = 70
        else:
            score.volatility_favorable = 30
        
        # Session timing
        if market_condition.current_session in ("london", "overlap"):
            score.session_timing = 100
        elif market_condition.current_session == "newyork":
            score.session_timing = 80
        else:
            score.session_timing = 40
        
        # News clear
        if market_condition.high_impact_news_in_hours > 2:
            score.news_clear = 100
        elif market_condition.high_impact_news_in_hours > 0.5:
            score.news_clear = 50
        else:
            score.news_clear = 0
        
        # Spread
        if market_condition.spread_percentile < 30:
            score.spread_acceptable = 100
        elif market_condition.spread_percentile < 60:
            score.spread_acceptable = 70
        else:
            score.spread_acceptable = 30
        
        # Stop loss logical
        score.stop_loss_logical = signal.get("sl_score", 70)
        
        # Risk reward
        rr = signal.get("risk_reward", 1.0)
        if rr >= 3:
            score.risk_reward_ratio = 100
        elif rr >= 2:
            score.risk_reward_ratio = 80
        elif rr >= 1.5:
            score.risk_reward_ratio = 50
        else:
            score.risk_reward_ratio = 20
        
        return score
    
    def calculate_position_size(
        self,
        signal_score: SignalScore,
        market_condition: MarketCondition,
        account_balance: float,
        stop_loss_distance: float
    ) -> Dict[str, Any]:
        """
        Calculate optimal position size based on all factors.
        
        Small capital = SNIPER MODE
        Only take high-quality trades with appropriate size.
        """
        if not signal_score.should_trade:
            return {
                "should_trade": False,
                "reason": f"Signal quality too low: {signal_score.quality.value}",
                "score": signal_score.to_dict()
            }
        
        if not market_condition.should_trade:
            return {
                "should_trade": False,
                "reason": f"Market conditions unfavorable: {market_condition.regime.value}",
                "score": signal_score.to_dict()
            }
        
        # Base risk from adaptive parameters
        base_risk_pct = self.parameters.get_risk_for_quality(signal_score.quality)
        
        # Adjust for market conditions
        condition_adjustment = market_condition.position_adjustment
        
        # Final risk percentage
        final_risk_pct = base_risk_pct * condition_adjustment
        
        # Calculate position size
        risk_amount = account_balance * (final_risk_pct / 100)
        position_size = risk_amount / stop_loss_distance
        
        return {
            "should_trade": True,
            "signal_quality": signal_score.quality.value,
            "base_risk_pct": base_risk_pct,
            "condition_adjustment": condition_adjustment,
            "final_risk_pct": final_risk_pct,
            "risk_amount": risk_amount,
            "position_size": position_size,
            "score": signal_score.to_dict()
        }
    
    def on_trade_complete(self, trade_result: Dict[str, Any]) -> None:
        """
        Learn from completed trade.
        
        This is where the system adapts its parameters.
        """
        self.trade_history.append(trade_result)
        
        if trade_result["profit"] >= 0:
            self.parameters.adapt_after_win(
                trade_result["profit_pct"],
                trade_result
            )
        else:
            self.parameters.adapt_after_loss(
                trade_result["profit_pct"],
                trade_result
            )
        
        # Learn optimal stop loss
        self.parameters.adapt_stop_loss(
            trade_result.get("hit_stop_loss", False),
            trade_result.get("max_favorable_excursion", 0),
            trade_result.get("max_adverse_excursion", 0)
        )
        
        # Save updated parameters
        if self.config_path:
            self.save()
    
    def save(self) -> None:
        """Persist learned parameters."""
        if self.config_path:
            data = {
                "parameters": {
                    "base_risk_pct": self.parameters.base_risk_pct,
                    "current_risk_pct": self.parameters.current_risk_pct,
                    "current_sl_atr_multiplier": self.parameters.current_sl_atr_multiplier,
                    "current_tp_atr_multiplier": self.parameters.current_tp_atr_multiplier,
                    "current_leverage": self.parameters.current_leverage,
                    "recent_trades": self.parameters.recent_trades,
                    "recent_wins": self.parameters.recent_wins,
                    "recent_losses": self.parameters.recent_losses,
                },
                "updated_at": datetime.utcnow().isoformat()
            }
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w") as f:
                json.dump(data, f, indent=2)
    
    def load(self) -> None:
        """Load learned parameters."""
        if self.config_path and self.config_path.exists():
            with open(self.config_path) as f:
                data = json.load(f)
            params = data.get("parameters", {})
            self.parameters.current_risk_pct = params.get("current_risk_pct", 5.0)
            self.parameters.current_sl_atr_multiplier = params.get("current_sl_atr_multiplier", 2.0)
            self.parameters.current_tp_atr_multiplier = params.get("current_tp_atr_multiplier", 4.0)
            self.parameters.current_leverage = params.get("current_leverage", 200)
            self.parameters.recent_trades = params.get("recent_trades", 0)
            self.parameters.recent_wins = params.get("recent_wins", 0)
            self.parameters.recent_losses = params.get("recent_losses", 0)
