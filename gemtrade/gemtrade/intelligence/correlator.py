"""
Pattern Correlator

Learns correlations between news/events and price movements:
1. Stores historical news → price impact data
2. Identifies recurring patterns
3. Predicts impact of similar future events
4. Improves predictions through feedback

This is the "memory" that makes the system smarter over time.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any, Tuple
from pathlib import Path
import json


@dataclass
class NewsPattern:
    """
    A learned pattern: type of news → typical price impact.
    """
    pattern_id: str
    
    # Pattern definition
    keywords: List[str]          # Keywords that identify this pattern
    news_category: str           # "fed", "earnings", "geopolitical", etc.
    affected_symbols: List[str]
    
    # Historical statistics
    occurrences: int = 0
    
    # Price impact
    avg_immediate_move_pct: float = 0.0    # First 15 minutes
    avg_1h_move_pct: float = 0.0           # First hour
    avg_4h_move_pct: float = 0.0           # First 4 hours
    avg_24h_move_pct: float = 0.0          # First day
    
    # Direction
    bullish_pct: float = 50.0              # % of times bullish
    
    # Reliability
    prediction_accuracy: float = 0.5       # How often we predict correctly
    
    # Timing
    avg_reaction_delay_minutes: float = 0  # How long before price reacts
    
    # Examples
    examples: List[Dict] = field(default_factory=list)
    
    def expected_move(self, timeframe: str = "1h") -> Tuple[str, float]:
        """
        Get expected move direction and magnitude.
        
        Returns: (direction, magnitude_pct)
        """
        direction = "bullish" if self.bullish_pct > 55 else (
            "bearish" if self.bullish_pct < 45 else "neutral"
        )
        
        if timeframe == "immediate":
            mag = abs(self.avg_immediate_move_pct)
        elif timeframe == "1h":
            mag = abs(self.avg_1h_move_pct)
        elif timeframe == "4h":
            mag = abs(self.avg_4h_move_pct)
        else:
            mag = abs(self.avg_24h_move_pct)
        
        return direction, mag
    
    def is_reliable(self) -> bool:
        """Check if pattern is statistically reliable."""
        return self.occurrences >= 10 and self.prediction_accuracy >= 0.6


@dataclass
class HistoricalCorrelation:
    """
    A recorded correlation: specific event → price outcome.
    """
    id: str
    timestamp: datetime
    
    # Event
    event_type: str
    event_description: str
    keywords: List[str]
    
    # Symbols affected
    primary_symbol: str
    
    # Price data
    price_before: float
    price_15m_after: float
    price_1h_after: float
    price_4h_after: float
    price_24h_after: float
    
    # Calculated moves
    @property
    def move_15m_pct(self) -> float:
        return ((self.price_15m_after - self.price_before) / self.price_before) * 100
    
    @property
    def move_1h_pct(self) -> float:
        return ((self.price_1h_after - self.price_before) / self.price_before) * 100
    
    @property
    def move_4h_pct(self) -> float:
        return ((self.price_4h_after - self.price_before) / self.price_before) * 100
    
    @property
    def move_24h_pct(self) -> float:
        return ((self.price_24h_after - self.price_before) / self.price_before) * 100


class PatternCorrelator:
    """
    Learns and recalls patterns from news → price correlations.
    
    This is the system's market memory.
    """
    
    def __init__(self, memory_path: Optional[Path] = None):
        self.memory_path = memory_path
        self.patterns: Dict[str, NewsPattern] = {}
        self.correlations: List[HistoricalCorrelation] = []
        
        # Pre-defined pattern templates
        self._init_base_patterns()
        
        # Load learned data
        if memory_path and memory_path.exists():
            self.load()
    
    def _init_base_patterns(self):
        """Initialize with known market patterns."""
        
        # Gold patterns
        self.patterns["fed_hawkish_gold"] = NewsPattern(
            pattern_id="fed_hawkish_gold",
            keywords=["fed", "hawkish", "rate hike", "taper", "tightening"],
            news_category="fed_policy",
            affected_symbols=["XAUUSD"],
            avg_immediate_move_pct=-0.5,
            avg_1h_move_pct=-0.8,
            bullish_pct=25,
            occurrences=50,  # Pre-trained
            prediction_accuracy=0.7,
        )
        
        self.patterns["fed_dovish_gold"] = NewsPattern(
            pattern_id="fed_dovish_gold",
            keywords=["fed", "dovish", "rate cut", "stimulus", "easing", "pause"],
            news_category="fed_policy",
            affected_symbols=["XAUUSD"],
            avg_immediate_move_pct=0.6,
            avg_1h_move_pct=1.0,
            bullish_pct=75,
            occurrences=50,
            prediction_accuracy=0.7,
        )
        
        self.patterns["inflation_high_gold"] = NewsPattern(
            pattern_id="inflation_high_gold",
            keywords=["inflation", "CPI", "above expectations", "higher than expected"],
            news_category="economic_data",
            affected_symbols=["XAUUSD"],
            avg_immediate_move_pct=0.4,
            avg_1h_move_pct=0.6,
            bullish_pct=65,  # Initially bullish, then depends on Fed reaction
            occurrences=30,
            prediction_accuracy=0.6,
        )
        
        self.patterns["geopolitical_risk_gold"] = NewsPattern(
            pattern_id="geopolitical_risk_gold",
            keywords=["war", "conflict", "sanctions", "attack", "military", "nuclear"],
            news_category="geopolitical",
            affected_symbols=["XAUUSD"],
            avg_immediate_move_pct=1.0,
            avg_1h_move_pct=1.5,
            bullish_pct=85,  # Gold is safe haven
            occurrences=40,
            prediction_accuracy=0.75,
        )
        
        self.patterns["dollar_strength_gold"] = NewsPattern(
            pattern_id="dollar_strength_gold",
            keywords=["dollar", "DXY", "USD strength", "dollar rally"],
            news_category="forex",
            affected_symbols=["XAUUSD"],
            avg_immediate_move_pct=-0.4,
            avg_1h_move_pct=-0.6,
            bullish_pct=20,  # Gold and USD inverse
            occurrences=60,
            prediction_accuracy=0.7,
        )
        
        # Bitcoin patterns
        self.patterns["btc_etf_approval"] = NewsPattern(
            pattern_id="btc_etf_approval",
            keywords=["bitcoin ETF", "ETF approved", "SEC approval"],
            news_category="regulatory",
            affected_symbols=["BTCUSD"],
            avg_immediate_move_pct=5.0,
            avg_1h_move_pct=8.0,
            bullish_pct=95,
            occurrences=5,
            prediction_accuracy=0.9,
        )
        
        self.patterns["btc_exchange_hack"] = NewsPattern(
            pattern_id="btc_exchange_hack",
            keywords=["hack", "breach", "stolen", "exchange hack"],
            news_category="security",
            affected_symbols=["BTCUSD"],
            avg_immediate_move_pct=-3.0,
            avg_1h_move_pct=-5.0,
            bullish_pct=10,
            occurrences=15,
            prediction_accuracy=0.8,
        )
        
        self.patterns["whale_movement"] = NewsPattern(
            pattern_id="whale_movement",
            keywords=["whale", "large transfer", "exchange inflow", "exchange outflow"],
            news_category="on_chain",
            affected_symbols=["BTCUSD"],
            avg_immediate_move_pct=0.5,  # Depends on direction
            avg_1h_move_pct=1.0,
            bullish_pct=50,  # Inflow bearish, outflow bullish
            occurrences=100,
            prediction_accuracy=0.6,
        )
    
    def find_matching_patterns(
        self, 
        text: str, 
        symbol: str
    ) -> List[Tuple[NewsPattern, float]]:
        """
        Find patterns that match the given text.
        
        Returns: List of (pattern, match_score) tuples
        """
        matches = []
        text_lower = text.lower()
        
        for pattern_id, pattern in self.patterns.items():
            if symbol not in pattern.affected_symbols:
                continue
            
            # Calculate match score
            keyword_matches = sum(
                1 for kw in pattern.keywords 
                if kw.lower() in text_lower
            )
            
            if keyword_matches > 0:
                match_score = keyword_matches / len(pattern.keywords)
                matches.append((pattern, match_score))
        
        # Sort by match score
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches
    
    def predict_impact(
        self,
        text: str,
        symbol: str,
        timeframe: str = "1h"
    ) -> Dict[str, Any]:
        """
        Predict price impact based on historical patterns.
        """
        matches = self.find_matching_patterns(text, symbol)
        
        if not matches:
            return {
                "prediction": "unknown",
                "confidence": 0.0,
                "reasoning": "No matching historical patterns found",
            }
        
        best_pattern, match_score = matches[0]
        direction, magnitude = best_pattern.expected_move(timeframe)
        
        # Adjust confidence by match score and pattern reliability
        confidence = (
            match_score * 0.4 +
            best_pattern.prediction_accuracy * 0.4 +
            min(best_pattern.occurrences / 50, 1.0) * 0.2
        )
        
        return {
            "prediction": direction,
            "expected_move_pct": magnitude if direction == "bullish" else -magnitude,
            "confidence": confidence,
            "pattern_id": best_pattern.pattern_id,
            "pattern_accuracy": best_pattern.prediction_accuracy,
            "pattern_occurrences": best_pattern.occurrences,
            "timeframe": timeframe,
            "reasoning": f"Matched pattern '{best_pattern.pattern_id}' with {match_score:.0%} keyword match. "
                        f"Historical accuracy: {best_pattern.prediction_accuracy:.0%} over {best_pattern.occurrences} events.",
        }
    
    def record_correlation(
        self,
        event_type: str,
        event_description: str,
        keywords: List[str],
        symbol: str,
        prices: Dict[str, float]
    ) -> HistoricalCorrelation:
        """
        Record a new correlation for learning.
        """
        correlation = HistoricalCorrelation(
            id=f"{symbol}_{datetime.utcnow().timestamp()}",
            timestamp=datetime.utcnow(),
            event_type=event_type,
            event_description=event_description,
            keywords=keywords,
            primary_symbol=symbol,
            price_before=prices["before"],
            price_15m_after=prices.get("15m", prices["before"]),
            price_1h_after=prices.get("1h", prices["before"]),
            price_4h_after=prices.get("4h", prices["before"]),
            price_24h_after=prices.get("24h", prices["before"]),
        )
        
        self.correlations.append(correlation)
        
        # Update patterns
        self._update_patterns_from_correlation(correlation)
        
        return correlation
    
    def _update_patterns_from_correlation(
        self, 
        correlation: HistoricalCorrelation
    ) -> None:
        """
        Update pattern statistics from new correlation.
        """
        matches = self.find_matching_patterns(
            correlation.event_description,
            correlation.primary_symbol
        )
        
        for pattern, match_score in matches:
            if match_score < 0.3:
                continue
            
            # Update statistics
            n = pattern.occurrences
            pattern.occurrences += 1
            
            # Update average moves (running average)
            pattern.avg_immediate_move_pct = (
                (pattern.avg_immediate_move_pct * n + correlation.move_15m_pct) 
                / (n + 1)
            )
            pattern.avg_1h_move_pct = (
                (pattern.avg_1h_move_pct * n + correlation.move_1h_pct) 
                / (n + 1)
            )
            pattern.avg_4h_move_pct = (
                (pattern.avg_4h_move_pct * n + correlation.move_4h_pct) 
                / (n + 1)
            )
            pattern.avg_24h_move_pct = (
                (pattern.avg_24h_move_pct * n + correlation.move_24h_pct) 
                / (n + 1)
            )
            
            # Update direction stats
            is_bullish = correlation.move_1h_pct > 0
            pattern.bullish_pct = (
                (pattern.bullish_pct * n + (100 if is_bullish else 0)) 
                / (n + 1)
            )
            
            # Store example
            pattern.examples.append({
                "timestamp": correlation.timestamp.isoformat(),
                "description": correlation.event_description[:100],
                "move_1h": correlation.move_1h_pct,
            })
            pattern.examples = pattern.examples[-20:]  # Keep recent 20
    
    def save(self) -> None:
        """Save learned patterns to disk."""
        if not self.memory_path:
            return
        
        self.memory_path.mkdir(parents=True, exist_ok=True)
        
        # Save patterns
        patterns_data = {}
        for pid, pattern in self.patterns.items():
            patterns_data[pid] = {
                "pattern_id": pattern.pattern_id,
                "keywords": pattern.keywords,
                "news_category": pattern.news_category,
                "affected_symbols": pattern.affected_symbols,
                "occurrences": pattern.occurrences,
                "avg_immediate_move_pct": pattern.avg_immediate_move_pct,
                "avg_1h_move_pct": pattern.avg_1h_move_pct,
                "avg_4h_move_pct": pattern.avg_4h_move_pct,
                "avg_24h_move_pct": pattern.avg_24h_move_pct,
                "bullish_pct": pattern.bullish_pct,
                "prediction_accuracy": pattern.prediction_accuracy,
                "examples": pattern.examples,
            }
        
        with open(self.memory_path / "patterns.json", "w") as f:
            json.dump(patterns_data, f, indent=2)
    
    def load(self) -> None:
        """Load learned patterns from disk."""
        if not self.memory_path:
            return
        
        patterns_file = self.memory_path / "patterns.json"
        if patterns_file.exists():
            with open(patterns_file) as f:
                patterns_data = json.load(f)
            
            for pid, data in patterns_data.items():
                self.patterns[pid] = NewsPattern(**data)
