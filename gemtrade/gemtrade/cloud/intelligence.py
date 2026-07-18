"""
Gemini-Powered Market Intelligence

The brain of autonomous trading decisions.
Uses Gemini's web search grounding to gather real-time intelligence
and make informed trading decisions without predefined rules.

This replaces traditional indicator-based strategies with
AI-driven reasoning about market conditions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from gemtrade.cloud.gemini_client import GeminiClient, GroundedResponse


class SignalType(Enum):
    """Trading signal types."""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    HOLD = "hold"
    SELL = "sell"
    STRONG_SELL = "strong_sell"
    AVOID = "avoid"  # Don't trade


class MarketCondition(Enum):
    """Current market condition."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    RANGING = "ranging"
    HIGH_VOLATILITY = "high_volatility"
    NEWS_DRIVEN = "news_driven"
    UNCERTAIN = "uncertain"


@dataclass
class MarketInsight:
    """A market insight from analysis."""
    topic: str
    insight: str
    sentiment: float  # -1 to 1
    confidence: float  # 0 to 1
    sources: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class IntelligenceQuery:
    """A query for market intelligence."""
    symbol: str = "XAUUSD"
    include_news: bool = True
    include_sentiment: bool = True
    include_economic: bool = True
    include_contrarian: bool = True
    depth: str = "medium"  # quick, medium, thorough


@dataclass
class IntelligenceResult:
    """Complete intelligence result."""
    symbol: str
    timestamp: datetime
    
    # Analysis
    condition: MarketCondition
    signal: SignalType
    confidence: float
    
    # Reasoning
    reasoning: str
    key_factors: List[str]
    
    # Insights
    news_insights: List[MarketInsight] = field(default_factory=list)
    sentiment_insights: List[MarketInsight] = field(default_factory=list)
    economic_insights: List[MarketInsight] = field(default_factory=list)
    
    # Sources
    sources: List[str] = field(default_factory=list)
    
    # Action
    recommended_action: Optional[str] = None
    risk_factors: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "condition": self.condition.value,
            "signal": self.signal.value,
            "confidence": self.confidence,
            "reasoning": self.reasoning,
            "key_factors": self.key_factors,
            "recommended_action": self.recommended_action,
            "risk_factors": self.risk_factors,
        }


class GeminiIntelligence:
    """
    AI-powered market intelligence.
    
    This is the decision-making brain that:
    1. Gathers real-time information via web search
    2. Analyzes sentiment and news
    3. Performs multi-hop reasoning
    4. Generates trading signals
    5. Explains its reasoning
    
    No predefined rules - just intelligent analysis.
    """
    
    def __init__(self):
        self.client = GeminiClient()
        self._cache: Dict[str, IntelligenceResult] = {}
        self._cache_ttl_seconds = 300  # 5 minutes
    
    async def gather_intelligence(
        self,
        query: IntelligenceQuery,
    ) -> IntelligenceResult:
        """
        Gather comprehensive market intelligence.
        
        This is the main entry point for getting trading decisions.
        """
        # Check cache
        cache_key = f"{query.symbol}:{query.depth}"
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.utcnow() - cached.timestamp).total_seconds()
            if age < self._cache_ttl_seconds:
                return cached
        
        # Gather insights in parallel
        insights = {
            "news": [],
            "sentiment": [],
            "economic": [],
            "contrarian": [],
        }
        sources = []
        
        if query.include_news:
            news_result = await self._gather_news(query.symbol)
            insights["news"] = news_result.get("insights", [])
            sources.extend(news_result.get("sources", []))
        
        if query.include_sentiment:
            sentiment_result = await self._gather_sentiment(query.symbol)
            insights["sentiment"] = sentiment_result.get("insights", [])
            sources.extend(sentiment_result.get("sources", []))
        
        if query.include_economic:
            economic_result = await self._gather_economic()
            insights["economic"] = economic_result.get("insights", [])
            sources.extend(economic_result.get("sources", []))
        
        if query.include_contrarian:
            contrarian = await self._contrarian_analysis(query.symbol, insights)
            insights["contrarian"] = contrarian.get("insights", [])
        
        # Synthesize into final decision
        result = await self._synthesize_decision(query.symbol, insights, sources)
        
        # Cache result
        self._cache[cache_key] = result
        
        return result
    
    async def _gather_news(self, symbol: str) -> Dict[str, Any]:
        """Gather and analyze news."""
        symbol_name = {
            "XAUUSD": "gold",
            "BTCUSD": "bitcoin",
            "EURUSD": "euro dollar",
        }.get(symbol, symbol)
        
        response = await self.client.analyze_news(
            f"{symbol_name} price market",
            symbols=[symbol]
        )
        
        insights = []
        
        # Parse the response
        if response.text:
            # Extract sentiment from response
            sentiment = 0.0
            if "bullish" in response.text.lower():
                sentiment = 0.5
            elif "bearish" in response.text.lower():
                sentiment = -0.5
            
            insights.append(MarketInsight(
                topic=f"{symbol} News",
                insight=response.text[:500],  # Truncate for storage
                sentiment=sentiment,
                confidence=0.7,
                sources=[s.url for s in response.sources[:3]],
            ))
        
        return {
            "insights": insights,
            "sources": [s.url for s in response.sources],
        }
    
    async def _gather_sentiment(self, symbol: str) -> Dict[str, Any]:
        """Gather market sentiment."""
        prompt = f"""Analyze current market sentiment for {symbol}:

1. Search for what traders and analysts are saying
2. Check social media sentiment (Twitter/X, Reddit)
3. Look at positioning data if available
4. Check institutional vs retail sentiment

Provide:
- OVERALL_SENTIMENT: bullish/bearish/neutral (0-100% confidence)
- RETAIL_SENTIMENT: What retail traders think
- INSTITUTIONAL_SENTIMENT: What institutions are doing
- CONTRARIAN_SIGNAL: If sentiment is extreme (potential reversal)"""
        
        response = await self.client.generate(prompt, enable_search=True)
        
        insights = []
        if response.text:
            sentiment = 0.0
            if "bullish" in response.text.lower():
                sentiment = 0.3
            elif "bearish" in response.text.lower():
                sentiment = -0.3
            
            insights.append(MarketInsight(
                topic="Market Sentiment",
                insight=response.text[:500],
                sentiment=sentiment,
                confidence=0.6,
                sources=[s.url for s in response.sources[:3]],
            ))
        
        return {
            "insights": insights,
            "sources": [s.url for s in response.sources],
        }
    
    async def _gather_economic(self) -> Dict[str, Any]:
        """Gather economic calendar and data."""
        response = await self.client.get_economic_calendar(["USD", "EUR"])
        
        insights = []
        if response.text:
            insights.append(MarketInsight(
                topic="Economic Calendar",
                insight=response.text[:500],
                sentiment=0.0,
                confidence=0.8,
                sources=[s.url for s in response.sources[:3]],
            ))
        
        return {
            "insights": insights,
            "sources": [s.url for s in response.sources],
        }
    
    async def _contrarian_analysis(
        self,
        symbol: str,
        current_insights: Dict[str, List[MarketInsight]],
    ) -> Dict[str, Any]:
        """Perform contrarian analysis - challenge the consensus."""
        # Determine current consensus
        total_sentiment = 0.0
        count = 0
        for category in current_insights.values():
            for insight in category:
                total_sentiment += insight.sentiment
                count += 1
        
        avg_sentiment = total_sentiment / count if count > 0 else 0.0
        
        if abs(avg_sentiment) > 0.4:  # Strong consensus
            direction = "bullish" if avg_sentiment > 0 else "bearish"
            
            prompt = f"""The current consensus on {symbol} is strongly {direction}.

Play devil's advocate:
1. What could go wrong for the consensus view?
2. Are there any overlooked risks?
3. Is sentiment too extreme (contrarian signal)?
4. What would cause a reversal?

Be critical and challenge the prevailing view."""
            
            response = await self.client.generate(prompt, enable_search=True)
            
            if response.text:
                return {
                    "insights": [MarketInsight(
                        topic="Contrarian Analysis",
                        insight=response.text[:500],
                        sentiment=-avg_sentiment * 0.3,  # Counter the consensus slightly
                        confidence=0.5,
                        sources=[s.url for s in response.sources[:3]],
                    )],
                    "sources": [],
                }
        
        return {"insights": [], "sources": []}
    
    async def _synthesize_decision(
        self,
        symbol: str,
        insights: Dict[str, List[MarketInsight]],
        sources: List[str],
    ) -> IntelligenceResult:
        """Synthesize all insights into a final decision."""
        # Prepare context for Gemini
        context_parts = []
        
        for category, insight_list in insights.items():
            if insight_list:
                context_parts.append(f"=== {category.upper()} ===")
                for insight in insight_list:
                    context_parts.append(f"- {insight.topic}: {insight.insight}")
                    context_parts.append(f"  Sentiment: {insight.sentiment:.2f}, Confidence: {insight.confidence:.2f}")
                context_parts.append("")
        
        context = "\n".join(context_parts)
        
        prompt = f"""Based on this market intelligence for {symbol}:

{context}

Make a trading decision. You must decide:

1. MARKET_CONDITION: One of: trending_up, trending_down, ranging, high_volatility, news_driven, uncertain

2. SIGNAL: One of: strong_buy, buy, hold, sell, strong_sell, avoid

3. CONFIDENCE: 0.0 to 1.0 (how confident are you?)

4. REASONING: Explain your decision in 2-3 sentences

5. KEY_FACTORS: List 3-5 key factors driving this decision

6. RECOMMENDED_ACTION: Specific action to take (or "wait")

7. RISK_FACTORS: List potential risks

Be decisive. Avoid "hold" unless genuinely uncertain.
Format your response as JSON."""
        
        response = await self.client.generate(
            prompt,
            system_instruction="You are a senior trader making real money decisions. Be decisive and clear.",
            enable_search=False,  # We have the context
            use_pro=True,  # Use Pro for final decision
        )
        
        # Parse the response
        try:
            # Try to extract JSON from response
            text = response.text
            json_start = text.find("{")
            json_end = text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                data = json.loads(text[json_start:json_end])
            else:
                data = {}
        except json.JSONDecodeError:
            data = {}
        
        # Build result with fallbacks
        condition_str = data.get("MARKET_CONDITION", "uncertain").lower()
        try:
            condition = MarketCondition(condition_str)
        except ValueError:
            condition = MarketCondition.UNCERTAIN
        
        signal_str = data.get("SIGNAL", "hold").lower()
        try:
            signal = SignalType(signal_str)
        except ValueError:
            signal = SignalType.HOLD
        
        # Flatten insights
        all_insights = []
        for category in insights.values():
            all_insights.extend(category)
        
        return IntelligenceResult(
            symbol=symbol,
            timestamp=datetime.utcnow(),
            condition=condition,
            signal=signal,
            confidence=float(data.get("CONFIDENCE", 0.5)),
            reasoning=data.get("REASONING", response.text[:200]),
            key_factors=data.get("KEY_FACTORS", []),
            news_insights=insights.get("news", []),
            sentiment_insights=insights.get("sentiment", []),
            economic_insights=insights.get("economic", []),
            sources=list(set(sources))[:10],
            recommended_action=data.get("RECOMMENDED_ACTION"),
            risk_factors=data.get("RISK_FACTORS", []),
        )
    
    async def quick_scan(self, symbol: str) -> Dict[str, Any]:
        """Quick market scan for immediate decision."""
        query = IntelligenceQuery(
            symbol=symbol,
            include_news=True,
            include_sentiment=False,
            include_economic=False,
            include_contrarian=False,
            depth="quick",
        )
        result = await self.gather_intelligence(query)
        return result.to_dict()
    
    async def full_analysis(self, symbol: str) -> Dict[str, Any]:
        """Full market analysis for major decisions."""
        query = IntelligenceQuery(
            symbol=symbol,
            include_news=True,
            include_sentiment=True,
            include_economic=True,
            include_contrarian=True,
            depth="thorough",
        )
        result = await self.gather_intelligence(query)
        return result.to_dict()


# ══════════════════════════════════════════════════════════════════════════════
#                           SYNCHRONOUS WRAPPERS
# ══════════════════════════════════════════════════════════════════════════════

def _run_async(coro):
    """Run async function synchronously."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


_intelligence: Optional[GeminiIntelligence] = None


def get_intelligence() -> GeminiIntelligence:
    """Get or create intelligence instance."""
    global _intelligence
    if _intelligence is None:
        _intelligence = GeminiIntelligence()
    return _intelligence


def gather_intelligence_sync(
    symbol: str = "XAUUSD",
    depth: str = "medium",
) -> Dict[str, Any]:
    """Synchronous wrapper for gather_intelligence."""
    intel = get_intelligence()
    query = IntelligenceQuery(symbol=symbol, depth=depth)
    result = _run_async(intel.gather_intelligence(query))
    return result.to_dict()


def quick_scan_sync(symbol: str = "XAUUSD") -> Dict[str, Any]:
    """Quick market scan."""
    intel = get_intelligence()
    return _run_async(intel.quick_scan(symbol))


def full_analysis_sync(symbol: str = "XAUUSD") -> Dict[str, Any]:
    """Full market analysis."""
    intel = get_intelligence()
    return _run_async(intel.full_analysis(symbol))
