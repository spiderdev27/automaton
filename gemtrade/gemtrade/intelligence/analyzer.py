"""
Intelligence Analyzer

Takes raw intelligence and extracts actionable signals:
1. Classifies signal type (direct/indirect/contrarian)
2. Scores signal strength
3. Estimates time-to-impact
4. Determines affected symbols
5. Suggests trading action

Uses LLM for complex interpretation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any


class SignalType(Enum):
    """Type of intelligence signal."""
    DIRECT_BULLISH = "direct_bullish"       # Clear positive for asset
    DIRECT_BEARISH = "direct_bearish"       # Clear negative for asset
    INDIRECT_BULLISH = "indirect_bullish"   # Inferred positive
    INDIRECT_BEARISH = "indirect_bearish"   # Inferred negative
    CONTRARIAN = "contrarian"               # Crowd is wrong
    CONFIRMATION = "confirmation"           # Confirms existing thesis
    INVALIDATION = "invalidation"           # Invalidates existing thesis
    NOISE = "noise"                         # Not actionable


class SignalStrength(Enum):
    """Strength of the signal."""
    EXTREME = "extreme"     # Act immediately, high conviction
    STRONG = "strong"       # High conviction signal
    MODERATE = "moderate"   # Worth considering
    WEAK = "weak"           # Low confidence
    NEGLIGIBLE = "negligible"  # Ignore


class TimeHorizon(Enum):
    """Expected time for signal to impact price."""
    IMMEDIATE = "immediate"     # Seconds to minutes
    SHORT = "short"             # Hours
    MEDIUM = "medium"           # Days
    LONG = "long"               # Weeks
    STRUCTURAL = "structural"   # Months (trend change)


@dataclass
class IntelligenceSignal:
    """
    An analyzed, actionable intelligence signal.
    
    This is what the trading system acts on.
    """
    id: str
    timestamp: datetime
    
    # Classification
    signal_type: SignalType
    strength: SignalStrength
    time_horizon: TimeHorizon
    
    # Target
    primary_symbol: str
    affected_symbols: List[str] = field(default_factory=list)
    
    # Direction and confidence
    direction: str = "neutral"  # "bullish", "bearish", "neutral"
    confidence: float = 0.0     # 0-1
    
    # Analysis
    headline: str = ""
    reasoning: str = ""
    key_factors: List[str] = field(default_factory=list)
    
    # Source
    source_ids: List[str] = field(default_factory=list)
    source_credibility: float = 0.5
    
    # Actionability
    suggested_action: str = "none"  # "buy", "sell", "close", "hedge", "none"
    urgency: str = "low"  # "immediate", "high", "medium", "low"
    
    # Risk
    potential_upside_pct: float = 0.0
    potential_downside_pct: float = 0.0
    risk_factors: List[str] = field(default_factory=list)
    
    # Learning
    outcome: Optional[str] = None  # Filled later: "correct", "incorrect", "partial"
    actual_price_move_pct: Optional[float] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "signal_type": self.signal_type.value,
            "strength": self.strength.value,
            "time_horizon": self.time_horizon.value,
            "primary_symbol": self.primary_symbol,
            "direction": self.direction,
            "confidence": self.confidence,
            "headline": self.headline,
            "reasoning": self.reasoning,
            "suggested_action": self.suggested_action,
            "urgency": self.urgency,
        }


class IntelligenceAnalyzer:
    """
    Analyzes raw intelligence to extract actionable signals.
    
    Uses LLM for complex interpretation and reasoning.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.signal_history: List[IntelligenceSignal] = []
        
        # Learned patterns: news type → typical price impact
        self.learned_patterns: Dict[str, Dict] = {}
        
    async def analyze(
        self,
        raw_intelligence: List[Any],  # RawIntelligence items
        sentiment_data: Dict[str, Any],
        current_positions: List[Dict],
        market_context: Dict[str, Any]
    ) -> List[IntelligenceSignal]:
        """
        Analyze raw intelligence and generate signals.
        
        This is where the LLM reasoning happens.
        """
        signals = []
        
        # Step 1: Cluster related intelligence
        clusters = self._cluster_intelligence(raw_intelligence)
        
        # Step 2: Analyze each cluster
        for cluster in clusters:
            signal = await self._analyze_cluster(
                cluster, 
                sentiment_data, 
                market_context
            )
            if signal and signal.signal_type != SignalType.NOISE:
                signals.append(signal)
        
        # Step 3: Check for contrarian signals
        contrarian = self._check_contrarian_signals(sentiment_data)
        signals.extend(contrarian)
        
        # Step 4: Check for confirmation/invalidation of existing positions
        position_signals = self._check_position_relevance(
            signals, 
            current_positions
        )
        signals.extend(position_signals)
        
        # Step 5: Rank by importance
        signals = self._rank_signals(signals)
        
        return signals
    
    def _cluster_intelligence(
        self, 
        intelligence: List[Any]
    ) -> List[List[Any]]:
        """
        Cluster related intelligence items.
        
        Example: 5 news articles about same Fed speech → 1 cluster
        """
        clusters = []
        # Would use semantic similarity to cluster
        # For now, simple grouping by symbol
        return clusters
    
    async def _analyze_cluster(
        self,
        cluster: List[Any],
        sentiment: Dict,
        context: Dict
    ) -> Optional[IntelligenceSignal]:
        """
        Analyze a cluster of related intelligence.
        
        Uses LLM to:
        1. Summarize the key information
        2. Determine market impact
        3. Estimate direction and magnitude
        4. Consider indirect effects
        """
        # This would call the LLM with a prompt like:
        """
        Analyze this market intelligence and determine:
        1. What is the key information?
        2. Which assets are affected (directly and indirectly)?
        3. What is the likely price impact (direction, magnitude, timing)?
        4. What trading action is suggested?
        5. What are the risks?
        
        Intelligence:
        {cluster_content}
        
        Current market context:
        {context}
        
        Sentiment data:
        {sentiment}
        
        Respond with structured analysis.
        """
        return None
    
    def _check_contrarian_signals(
        self, 
        sentiment: Dict[str, Any]
    ) -> List[IntelligenceSignal]:
        """
        Check for contrarian opportunities.
        
        When crowd is extremely one-sided, often wrong.
        
        Examples:
        - 95% bullish → market top signal
        - 95% bearish → market bottom signal
        - Authenticity score low → coordinated manipulation
        """
        signals = []
        
        for symbol, data in sentiment.items():
            if not isinstance(data, dict):
                continue
                
            bullish_pct = data.get("bullish_pct", 50)
            authenticity = data.get("authenticity_score", 100)
            
            # Extreme bullishness (potential top)
            if bullish_pct > 90:
                signals.append(IntelligenceSignal(
                    id=f"contrarian_{symbol}_{datetime.utcnow().timestamp()}",
                    timestamp=datetime.utcnow(),
                    signal_type=SignalType.CONTRARIAN,
                    strength=SignalStrength.MODERATE,
                    time_horizon=TimeHorizon.SHORT,
                    primary_symbol=symbol,
                    direction="bearish",
                    confidence=0.6,
                    headline=f"Extreme bullish sentiment on {symbol} - contrarian warning",
                    reasoning=f"Sentiment at {bullish_pct}% bullish. Historical reversals common at extremes.",
                    suggested_action="reduce_long" if bullish_pct > 95 else "caution",
                    urgency="medium",
                ))
            
            # Extreme bearishness (potential bottom)
            elif bullish_pct < 10:
                signals.append(IntelligenceSignal(
                    id=f"contrarian_{symbol}_{datetime.utcnow().timestamp()}",
                    timestamp=datetime.utcnow(),
                    signal_type=SignalType.CONTRARIAN,
                    strength=SignalStrength.MODERATE,
                    time_horizon=TimeHorizon.SHORT,
                    primary_symbol=symbol,
                    direction="bullish",
                    confidence=0.6,
                    headline=f"Extreme bearish sentiment on {symbol} - contrarian opportunity",
                    reasoning=f"Sentiment at {bullish_pct}% bullish. Historical bounces common at extremes.",
                    suggested_action="consider_long" if bullish_pct < 5 else "watch",
                    urgency="medium",
                ))
            
            # Low authenticity (coordinated manipulation)
            if authenticity < 30:
                signals.append(IntelligenceSignal(
                    id=f"manipulation_{symbol}_{datetime.utcnow().timestamp()}",
                    timestamp=datetime.utcnow(),
                    signal_type=SignalType.CONTRARIAN,
                    strength=SignalStrength.STRONG,
                    time_horizon=TimeHorizon.SHORT,
                    primary_symbol=symbol,
                    direction="opposite_of_sentiment",
                    confidence=0.7,
                    headline=f"Coordinated sentiment detected on {symbol}",
                    reasoning=f"Authenticity score {authenticity}. Likely manipulation. Fade the move.",
                    risk_factors=["manipulation", "coordinated_attack"],
                    suggested_action="fade",
                    urgency="high",
                ))
        
        return signals
    
    def _check_position_relevance(
        self,
        signals: List[IntelligenceSignal],
        positions: List[Dict]
    ) -> List[IntelligenceSignal]:
        """
        Check if signals confirm or invalidate existing positions.
        """
        position_signals = []
        
        for position in positions:
            symbol = position.get("symbol")
            direction = position.get("direction")  # "long" or "short"
            
            for signal in signals:
                if signal.primary_symbol != symbol:
                    continue
                
                # Check if signal confirms or invalidates position
                if direction == "long" and signal.direction == "bullish":
                    # Confirmation
                    position_signals.append(IntelligenceSignal(
                        id=f"confirm_{signal.id}",
                        timestamp=datetime.utcnow(),
                        signal_type=SignalType.CONFIRMATION,
                        strength=signal.strength,
                        time_horizon=signal.time_horizon,
                        primary_symbol=symbol,
                        direction="bullish",
                        confidence=signal.confidence,
                        headline=f"Long position confirmed: {signal.headline}",
                        reasoning=signal.reasoning,
                        suggested_action="hold_or_add",
                        urgency="low",
                    ))
                
                elif direction == "long" and signal.direction == "bearish":
                    # Invalidation
                    position_signals.append(IntelligenceSignal(
                        id=f"invalidate_{signal.id}",
                        timestamp=datetime.utcnow(),
                        signal_type=SignalType.INVALIDATION,
                        strength=signal.strength,
                        time_horizon=signal.time_horizon,
                        primary_symbol=symbol,
                        direction="bearish",
                        confidence=signal.confidence,
                        headline=f"Long position challenged: {signal.headline}",
                        reasoning=signal.reasoning,
                        suggested_action="review_position",
                        urgency="high" if signal.strength == SignalStrength.STRONG else "medium",
                    ))
        
        return position_signals
    
    def _rank_signals(
        self, 
        signals: List[IntelligenceSignal]
    ) -> List[IntelligenceSignal]:
        """Rank signals by importance."""
        def signal_score(s: IntelligenceSignal) -> float:
            strength_scores = {
                SignalStrength.EXTREME: 5,
                SignalStrength.STRONG: 4,
                SignalStrength.MODERATE: 3,
                SignalStrength.WEAK: 2,
                SignalStrength.NEGLIGIBLE: 1,
            }
            urgency_scores = {
                "immediate": 3,
                "high": 2,
                "medium": 1,
                "low": 0,
            }
            return (
                strength_scores.get(s.strength, 1) * 2 +
                urgency_scores.get(s.urgency, 0) +
                s.confidence * 3
            )
        
        return sorted(signals, key=signal_score, reverse=True)
    
    def learn_from_outcome(
        self,
        signal: IntelligenceSignal,
        actual_outcome: str,
        actual_move_pct: float
    ) -> None:
        """
        Learn from signal outcome.
        
        Updates internal patterns to improve future analysis.
        """
        signal.outcome = actual_outcome
        signal.actual_price_move_pct = actual_move_pct
        
        # Extract pattern
        pattern_key = f"{signal.signal_type.value}_{signal.primary_symbol}"
        
        if pattern_key not in self.learned_patterns:
            self.learned_patterns[pattern_key] = {
                "total": 0,
                "correct": 0,
                "avg_move": 0,
                "examples": [],
            }
        
        pattern = self.learned_patterns[pattern_key]
        pattern["total"] += 1
        if actual_outcome == "correct":
            pattern["correct"] += 1
        pattern["avg_move"] = (
            (pattern["avg_move"] * (pattern["total"] - 1) + actual_move_pct) 
            / pattern["total"]
        )
        pattern["examples"].append({
            "headline": signal.headline,
            "predicted": signal.direction,
            "actual_move": actual_move_pct,
            "correct": actual_outcome == "correct",
        })
        
        # Keep only recent examples
        pattern["examples"] = pattern["examples"][-50:]
