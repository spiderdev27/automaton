"""
Gemini-Powered Market Intelligence

This module provides real-time market intelligence using:
- Gemini Web Search Grounding for live news
- Multi-hop reasoning for indirect signals
- Sentiment extraction from diverse sources
- Event-driven signal generation
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any, Tuple
import asyncio
import json
import re

from gemtrade.cloud.gemini_client import (
    GeminiClient, 
    GeminiConfig, 
    GeminiModel,
    GroundedResponse,
)


class SignalDirection(Enum):
    """Trading signal direction."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


class SignalTimeframe(Enum):
    """Signal time horizon."""
    IMMEDIATE = "immediate"      # Minutes
    SHORT_TERM = "short_term"    # Hours
    MEDIUM_TERM = "medium_term"  # Days
    LONG_TERM = "long_term"      # Weeks


class InsightType(Enum):
    """Type of market insight."""
    NEWS = "news"
    SENTIMENT = "sentiment"
    ECONOMIC = "economic"
    TECHNICAL = "technical"
    INDIRECT = "indirect"
    CONTRARIAN = "contrarian"


@dataclass
class MarketInsight:
    """A single market insight."""
    type: InsightType
    symbol: str
    headline: str
    content: str
    
    # Signal properties
    direction: SignalDirection = SignalDirection.NEUTRAL
    timeframe: SignalTimeframe = SignalTimeframe.SHORT_TERM
    confidence: float = 0.5  # 0-1
    
    # Metadata
    source: str = ""
    source_url: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Context
    reasoning: str = ""
    related_symbols: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    def is_actionable(self, min_confidence: float = 0.6) -> bool:
        """Check if insight is actionable."""
        return (
            self.confidence >= min_confidence and
            self.direction != SignalDirection.NEUTRAL
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "type": self.type.value,
            "symbol": self.symbol,
            "headline": self.headline,
            "direction": self.direction.value,
            "confidence": self.confidence,
            "timeframe": self.timeframe.value,
            "source": self.source,
            "reasoning": self.reasoning,
        }


@dataclass
class IntelligenceQuery:
    """Query for market intelligence."""
    symbols: List[str]
    
    # Search parameters
    timeframe: str = "last 24 hours"
    include_indirect: bool = True
    include_contrarian: bool = True
    
    # Focus areas
    focus_news: bool = True
    focus_sentiment: bool = True
    focus_economic: bool = True
    
    # Context
    current_positions: Dict[str, str] = field(default_factory=dict)  # symbol -> "long"|"short"
    market_regime: str = "normal"  # "trending", "ranging", "volatile", "news_active"


@dataclass
class IntelligenceResult:
    """Result of intelligence gathering."""
    query: IntelligenceQuery
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Insights
    insights: List[MarketInsight] = field(default_factory=list)
    
    # Aggregated signals
    signals: Dict[str, SignalDirection] = field(default_factory=dict)  # symbol -> direction
    confidence_scores: Dict[str, float] = field(default_factory=dict)  # symbol -> confidence
    
    # Economic calendar
    upcoming_events: List[Dict] = field(default_factory=list)
    
    # Summary
    market_summary: str = ""
    key_risks: List[str] = field(default_factory=list)
    
    # Metadata
    sources_consulted: int = 0
    tokens_used: int = 0
    cached_responses: int = 0
    
    def get_actionable_insights(self, min_confidence: float = 0.6) -> List[MarketInsight]:
        """Get insights that meet confidence threshold."""
        return [i for i in self.insights if i.is_actionable(min_confidence)]
    
    def get_signal(self, symbol: str) -> Tuple[SignalDirection, float]:
        """Get aggregated signal for symbol."""
        return (
            self.signals.get(symbol, SignalDirection.NEUTRAL),
            self.confidence_scores.get(symbol, 0.0),
        )


class GeminiIntelligence:
    """
    Market intelligence system powered by Gemini.
    
    Uses web search grounding to get real-time information
    and multi-hop reasoning to detect indirect signals.
    """
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.client = GeminiClient(config)
        
        # Symbol relationships for indirect signal detection
        self.symbol_relationships = {
            "XAUUSD": {
                "positive_correlations": ["DXY inverse", "inflation fears", "geopolitical risk"],
                "negative_correlations": ["risk-on sentiment", "crypto rally", "strong dollar"],
                "related_searches": [
                    "gold price news",
                    "federal reserve interest rates",
                    "inflation data",
                    "geopolitical tensions",
                    "central bank gold purchases",
                ],
            },
            "BTCUSD": {
                "positive_correlations": ["crypto adoption", "ETF flows", "macro liquidity"],
                "negative_correlations": ["regulation crackdown", "exchange hack", "tether fears"],
                "related_searches": [
                    "bitcoin news",
                    "crypto regulation",
                    "bitcoin ETF flows",
                    "whale movements",
                    "crypto exchange news",
                ],
            },
        }
    
    async def gather_intelligence(
        self, 
        query: IntelligenceQuery
    ) -> IntelligenceResult:
        """
        Gather comprehensive market intelligence.
        
        This is the main entry point for getting trading signals.
        """
        result = IntelligenceResult(query=query)
        
        # Parallel gathering
        tasks = []
        
        for symbol in query.symbols:
            # Direct news
            if query.focus_news:
                tasks.append(self._gather_news(symbol, query.timeframe))
            
            # Sentiment
            if query.focus_sentiment:
                tasks.append(self._gather_sentiment(symbol))
            
            # Indirect signals
            if query.include_indirect:
                tasks.append(self._gather_indirect_signals(symbol))
        
        # Economic calendar (once for all)
        if query.focus_economic:
            tasks.append(self._gather_economic_events())
        
        # Execute all
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process responses
        for response in responses:
            if isinstance(response, Exception):
                continue
            if isinstance(response, list):
                result.insights.extend(response)
            elif isinstance(response, dict) and "events" in response:
                result.upcoming_events = response["events"]
        
        # Aggregate signals
        result.signals, result.confidence_scores = self._aggregate_signals(
            result.insights, 
            query.symbols
        )
        
        # Generate summary
        result.market_summary = await self._generate_summary(result)
        
        # Contrarian analysis
        if query.include_contrarian:
            contrarian_insights = await self._contrarian_analysis(
                result.insights,
                query.current_positions
            )
            result.insights.extend(contrarian_insights)
        
        return result
    
    async def _gather_news(
        self, 
        symbol: str, 
        timeframe: str
    ) -> List[MarketInsight]:
        """Gather news for a symbol."""
        insights = []
        
        # Get related search terms
        related = self.symbol_relationships.get(symbol, {})
        searches = related.get("related_searches", [f"{symbol} news"])
        
        # Main query
        query = f"Latest {symbol} trading news and price analysis {timeframe}"
        
        response = await self.client.analyze_news(
            query=query,
            symbols=[symbol],
            timeframe=timeframe,
        )
        
        # Parse response
        parsed = self._parse_news_response(response, symbol)
        insights.extend(parsed)
        
        return insights
    
    async def _gather_sentiment(self, symbol: str) -> List[MarketInsight]:
        """Gather sentiment data."""
        prompt = f"""Search for current market sentiment on {symbol}.

Look for:
1. Social media sentiment (Reddit, Twitter/X)
2. Analyst opinions and price targets
3. Institutional positioning
4. Retail trader sentiment
5. Options market sentiment (put/call ratios)

Return JSON:
{{
    "overall_sentiment": "bullish|bearish|neutral",
    "confidence": 0-100,
    "social_sentiment": "...",
    "institutional_view": "...",
    "retail_sentiment": "...",
    "key_points": ["..."]
}}"""

        response = await self.client.generate(
            prompt=prompt,
            model=GeminiModel.FLASH,
            grounded=True,
        )
        
        insights = []
        try:
            # Extract JSON from response
            data = self._extract_json(response.text)
            if data:
                direction = self._sentiment_to_direction(data.get("overall_sentiment", "neutral"))
                confidence = data.get("confidence", 50) / 100
                
                insights.append(MarketInsight(
                    type=InsightType.SENTIMENT,
                    symbol=symbol,
                    headline=f"Market Sentiment: {data.get('overall_sentiment', 'neutral').title()}",
                    content=json.dumps(data),
                    direction=direction,
                    confidence=confidence,
                    source="Gemini Web Search",
                    reasoning="; ".join(data.get("key_points", [])),
                ))
        except Exception:
            pass
        
        return insights
    
    async def _gather_indirect_signals(self, symbol: str) -> List[MarketInsight]:
        """Gather indirect signals that might affect the symbol."""
        related = self.symbol_relationships.get(symbol, {})
        if not related:
            return []
        
        positive_correlations = related.get("positive_correlations", [])
        negative_correlations = related.get("negative_correlations", [])
        
        prompt = f"""Search for news about factors that indirectly affect {symbol}.

POSITIVE for {symbol}:
{', '.join(positive_correlations)}

NEGATIVE for {symbol}:
{', '.join(negative_correlations)}

Look for recent news about these factors and analyze their impact on {symbol}.

Return JSON:
{{
    "indirect_signals": [
        {{
            "factor": "...",
            "news": "...",
            "impact_on_{symbol.lower()}": "positive|negative|neutral",
            "strength": "strong|moderate|weak",
            "reasoning": "..."
        }}
    ],
    "net_impact": "positive|negative|neutral",
    "confidence": 0-100
}}"""

        response = await self.client.generate(
            prompt=prompt,
            model=GeminiModel.FLASH,
            grounded=True,
        )
        
        insights = []
        try:
            data = self._extract_json(response.text)
            if data and "indirect_signals" in data:
                for signal in data["indirect_signals"]:
                    impact = signal.get(f"impact_on_{symbol.lower()}", "neutral")
                    direction = self._sentiment_to_direction(impact)
                    strength = signal.get("strength", "moderate")
                    confidence = {"strong": 0.8, "moderate": 0.6, "weak": 0.4}.get(strength, 0.5)
                    
                    insights.append(MarketInsight(
                        type=InsightType.INDIRECT,
                        symbol=symbol,
                        headline=f"Indirect: {signal.get('factor', 'Unknown factor')}",
                        content=signal.get("news", ""),
                        direction=direction,
                        confidence=confidence,
                        source="Gemini Analysis",
                        reasoning=signal.get("reasoning", ""),
                        tags=["indirect", signal.get("factor", "").lower()],
                    ))
        except Exception:
            pass
        
        return insights
    
    async def _gather_economic_events(self) -> Dict:
        """Gather upcoming economic events."""
        response = await self.client.get_economic_calendar(days_ahead=7)
        
        events = []
        try:
            # Parse events from response
            lines = response.text.split("\n")
            current_event = {}
            
            for line in lines:
                line = line.strip()
                if not line:
                    if current_event:
                        events.append(current_event)
                        current_event = {}
                    continue
                
                # Simple parsing - would need more robust parsing in production
                if "Date:" in line or "Time:" in line:
                    current_event["datetime"] = line.split(":", 1)[-1].strip()
                elif "Event:" in line:
                    current_event["event"] = line.split(":", 1)[-1].strip()
                elif "Impact:" in line:
                    current_event["impact"] = line.split(":", 1)[-1].strip()
        except Exception:
            pass
        
        return {"events": events}
    
    async def _contrarian_analysis(
        self,
        insights: List[MarketInsight],
        positions: Dict[str, str],
    ) -> List[MarketInsight]:
        """
        Perform contrarian analysis.
        
        Looks for reasons why the consensus might be wrong.
        """
        contrarian_insights = []
        
        # Group insights by symbol
        by_symbol: Dict[str, List[MarketInsight]] = {}
        for insight in insights:
            if insight.symbol not in by_symbol:
                by_symbol[insight.symbol] = []
            by_symbol[insight.symbol].append(insight)
        
        for symbol, symbol_insights in by_symbol.items():
            # Determine consensus
            bullish = sum(1 for i in symbol_insights if i.direction in [SignalDirection.BUY, SignalDirection.STRONG_BUY])
            bearish = sum(1 for i in symbol_insights if i.direction in [SignalDirection.SELL, SignalDirection.STRONG_SELL])
            
            if bullish == 0 and bearish == 0:
                continue
            
            consensus = "bullish" if bullish > bearish else "bearish" if bearish > bullish else "mixed"
            
            prompt = f"""The current consensus on {symbol} is {consensus} based on {len(symbol_insights)} signals.

Key bullish points: {bullish} signals
Key bearish points: {bearish} signals

Search for contrarian arguments - reasons why this consensus might be wrong.

Look for:
1. Ignored risks or opportunities
2. Historical parallels where consensus was wrong
3. Contrarian positioning by smart money
4. Technical divergences
5. Sentiment extremes that often precede reversals

Return JSON:
{{
    "contrarian_view": "...",
    "key_arguments": ["..."],
    "probability_consensus_wrong": 0-100,
    "potential_catalyst": "..."
}}"""

            response = await self.client.generate(
                prompt=prompt,
                model=GeminiModel.PRO,  # Better reasoning for contrarian analysis
                grounded=True,
            )
            
            try:
                data = self._extract_json(response.text)
                if data:
                    prob = data.get("probability_consensus_wrong", 30)
                    if prob > 40:  # Only include meaningful contrarian signals
                        # Contrarian direction is opposite of consensus
                        if consensus == "bullish":
                            direction = SignalDirection.SELL
                        elif consensus == "bearish":
                            direction = SignalDirection.BUY
                        else:
                            direction = SignalDirection.NEUTRAL
                        
                        contrarian_insights.append(MarketInsight(
                            type=InsightType.CONTRARIAN,
                            symbol=symbol,
                            headline=f"Contrarian: {data.get('contrarian_view', 'Consider opposite view')}",
                            content=data.get("potential_catalyst", ""),
                            direction=direction,
                            confidence=prob / 100,
                            source="Gemini Contrarian Analysis",
                            reasoning="; ".join(data.get("key_arguments", [])),
                            tags=["contrarian", consensus],
                        ))
            except Exception:
                pass
        
        return contrarian_insights
    
    def _aggregate_signals(
        self,
        insights: List[MarketInsight],
        symbols: List[str],
    ) -> Tuple[Dict[str, SignalDirection], Dict[str, float]]:
        """Aggregate insights into trading signals."""
        signals = {}
        confidences = {}
        
        for symbol in symbols:
            symbol_insights = [i for i in insights if i.symbol == symbol]
            if not symbol_insights:
                signals[symbol] = SignalDirection.NEUTRAL
                confidences[symbol] = 0.0
                continue
            
            # Weight by confidence and type
            type_weights = {
                InsightType.NEWS: 1.0,
                InsightType.SENTIMENT: 0.8,
                InsightType.ECONOMIC: 1.2,
                InsightType.INDIRECT: 0.6,
                InsightType.CONTRARIAN: 0.5,
            }
            
            direction_scores = {
                SignalDirection.STRONG_BUY: 2,
                SignalDirection.BUY: 1,
                SignalDirection.NEUTRAL: 0,
                SignalDirection.SELL: -1,
                SignalDirection.STRONG_SELL: -2,
            }
            
            weighted_score = 0.0
            total_weight = 0.0
            
            for insight in symbol_insights:
                weight = type_weights.get(insight.type, 1.0) * insight.confidence
                score = direction_scores.get(insight.direction, 0)
                weighted_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                avg_score = weighted_score / total_weight
                
                # Convert score back to direction
                if avg_score >= 1.5:
                    signals[symbol] = SignalDirection.STRONG_BUY
                elif avg_score >= 0.5:
                    signals[symbol] = SignalDirection.BUY
                elif avg_score <= -1.5:
                    signals[symbol] = SignalDirection.STRONG_SELL
                elif avg_score <= -0.5:
                    signals[symbol] = SignalDirection.SELL
                else:
                    signals[symbol] = SignalDirection.NEUTRAL
                
                # Confidence based on agreement
                confidences[symbol] = min(1.0, total_weight / len(symbol_insights))
            else:
                signals[symbol] = SignalDirection.NEUTRAL
                confidences[symbol] = 0.0
        
        return signals, confidences
    
    async def _generate_summary(self, result: IntelligenceResult) -> str:
        """Generate human-readable summary."""
        if not result.insights:
            return "No significant market insights gathered."
        
        # Simple summary without another API call
        lines = [f"Market Intelligence Summary ({len(result.insights)} insights):"]
        
        for symbol in result.query.symbols:
            direction, confidence = result.get_signal(symbol)
            lines.append(f"  {symbol}: {direction.value} (confidence: {confidence:.0%})")
        
        actionable = result.get_actionable_insights()
        if actionable:
            lines.append(f"\nActionable signals: {len(actionable)}")
        
        if result.upcoming_events:
            lines.append(f"\nUpcoming events: {len(result.upcoming_events)}")
        
        return "\n".join(lines)
    
    def _parse_news_response(
        self, 
        response: GroundedResponse, 
        symbol: str
    ) -> List[MarketInsight]:
        """Parse news analysis response into insights."""
        insights = []
        
        try:
            data = self._extract_json(response.text)
            if data and "news_items" in data:
                for item in data["news_items"]:
                    sentiment = item.get("sentiment", "neutral")
                    direction = self._sentiment_to_direction(sentiment)
                    
                    impact_multiplier = {
                        "high": 1.0,
                        "medium": 0.7,
                        "low": 0.4,
                    }.get(item.get("impact", "medium"), 0.7)
                    
                    confidence = (item.get("confidence", 50) / 100) * impact_multiplier
                    
                    timeframe_map = {
                        "immediate": SignalTimeframe.IMMEDIATE,
                        "short-term": SignalTimeframe.SHORT_TERM,
                        "medium-term": SignalTimeframe.MEDIUM_TERM,
                    }
                    timeframe = timeframe_map.get(
                        item.get("timeframe", "short-term"),
                        SignalTimeframe.SHORT_TERM
                    )
                    
                    insights.append(MarketInsight(
                        type=InsightType.NEWS,
                        symbol=symbol,
                        headline=item.get("headline", "Unknown"),
                        content=item.get("reasoning", ""),
                        direction=direction,
                        timeframe=timeframe,
                        confidence=confidence,
                        source=item.get("source", "Unknown"),
                        reasoning=item.get("reasoning", ""),
                        related_symbols=item.get("affected_symbols", []),
                    ))
        except Exception:
            # If parsing fails, create a generic insight from the raw response
            if response.text and len(response.text) > 50:
                insights.append(MarketInsight(
                    type=InsightType.NEWS,
                    symbol=symbol,
                    headline=f"News analysis for {symbol}",
                    content=response.text[:500],
                    source="Gemini Web Search",
                ))
        
        return insights
    
    def _sentiment_to_direction(self, sentiment: str) -> SignalDirection:
        """Convert sentiment string to SignalDirection."""
        sentiment = sentiment.lower()
        if sentiment in ["bullish", "positive", "buy"]:
            return SignalDirection.BUY
        elif sentiment in ["very bullish", "strong buy", "strongly positive"]:
            return SignalDirection.STRONG_BUY
        elif sentiment in ["bearish", "negative", "sell"]:
            return SignalDirection.SELL
        elif sentiment in ["very bearish", "strong sell", "strongly negative"]:
            return SignalDirection.STRONG_SELL
        else:
            return SignalDirection.NEUTRAL
    
    def _extract_json(self, text: str) -> Optional[Dict]:
        """Extract JSON from text that may contain other content."""
        # Try to find JSON in the text
        try:
            # First try direct parse
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Look for JSON block
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
            r'\{[^{}]*\}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if '```' in pattern else match.group(0))
                except json.JSONDecodeError:
                    continue
        
        return None


# Convenience function
async def get_market_intelligence(
    symbols: List[str],
    timeframe: str = "last 24 hours",
    api_key: Optional[str] = None,
) -> IntelligenceResult:
    """
    Quick function to get market intelligence.
    
    Example:
        result = await get_market_intelligence(["XAUUSD"], "last 6 hours")
        print(result.market_summary)
    """
    config = GeminiConfig(api_key=api_key) if api_key else None
    intelligence = GeminiIntelligence(config)
    
    query = IntelligenceQuery(
        symbols=symbols,
        timeframe=timeframe,
    )
    
    return await intelligence.gather_intelligence(query)
