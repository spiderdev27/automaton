"""
Intelligence Tools

GemCode-compatible tools for AI-powered market intelligence.
These tools use Gemini with web search to gather and analyze
real-time market information.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from gemtrade.cloud.intelligence import (
    get_intelligence,
    IntelligenceQuery,
    SignalType,
)
from gemtrade.cloud.gemini_client import (
    GeminiClient,
    analyze_news_sync,
    deep_research_sync,
    get_economic_calendar_sync,
)


def _run_async(coro):
    """Run async function synchronously."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


def market_intelligence(
    symbol: str = "XAUUSD",
    depth: str = "medium",
) -> Dict[str, Any]:
    """
    Gather comprehensive market intelligence for a symbol.
    
    This is the primary tool for making trading decisions.
    Uses AI-powered analysis with real-time web search.
    
    Args:
        symbol: Trading symbol (e.g., "XAUUSD", "BTCUSD")
        depth: Analysis depth - "quick" (1-2 min), "medium" (2-3 min), "thorough" (3-5 min)
        
    Returns:
        Complete intelligence report with:
        - Market condition
        - Trading signal (strong_buy, buy, hold, sell, strong_sell, avoid)
        - Confidence level
        - Key factors driving the decision
        - Recommended action
        - Risk factors
        - News and sentiment insights
        - Sources
    """
    intel = get_intelligence()
    query = IntelligenceQuery(
        symbol=symbol,
        include_news=True,
        include_sentiment=depth != "quick",
        include_economic=depth == "thorough",
        include_contrarian=depth == "thorough",
        depth=depth,
    )
    
    result = _run_async(intel.gather_intelligence(query))
    
    output = result.to_dict()
    
    # Add actionable summary
    action_map = {
        SignalType.STRONG_BUY: "ENTER LONG with confidence",
        SignalType.BUY: "Consider LONG position",
        SignalType.HOLD: "Wait for better setup",
        SignalType.SELL: "Consider SHORT position",
        SignalType.STRONG_SELL: "ENTER SHORT with confidence",
        SignalType.AVOID: "Do NOT trade - unfavorable conditions",
    }
    
    output["action_summary"] = action_map.get(result.signal, "Unclear")
    output["sources_count"] = len(result.sources)
    
    return output


def analyze_news_impact(
    topic: str,
    symbols: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Analyze news impact on trading.
    
    Uses web search to find and analyze recent news.
    
    Args:
        topic: News topic (e.g., "Fed interest rates", "gold demand")
        symbols: Related trading symbols
        
    Returns:
        News analysis with:
        - Key headlines
        - Sentiment
        - Market impact assessment
        - Trading implications
        - Sources
    """
    symbols = symbols or ["XAUUSD"]
    
    response = analyze_news_sync(topic, symbols)
    
    return {
        "topic": topic,
        "symbols": symbols,
        "analysis": response.text,
        "sources": [
            {"title": s.title, "url": s.url}
            for s in response.sources
        ],
        "search_queries": response.search_queries,
        "timestamp": datetime.utcnow().isoformat(),
    }


def economic_calendar() -> Dict[str, Any]:
    """
    Get upcoming economic events.
    
    Returns events that could impact trading, including:
    - Interest rate decisions
    - Employment data
    - GDP releases
    - Inflation reports
    - Central bank speeches
    
    Returns:
        Economic calendar with:
        - Event name
        - Date/time (UTC)
        - Expected impact
        - Currencies affected
    """
    response = get_economic_calendar_sync(["USD", "EUR", "GBP", "JPY"])
    
    return {
        "calendar": response.text,
        "sources": [
            {"title": s.title, "url": s.url}
            for s in response.sources
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


def research_question(
    question: str,
) -> Dict[str, Any]:
    """
    Deep research on any trading-related question.
    
    Uses Gemini Pro with web search for complex questions.
    
    Args:
        question: Question to research
        
    Returns:
        Research results with:
        - Answer
        - Supporting evidence
        - Sources
        
    Examples:
        - "What's driving gold prices this week?"
        - "How do rising interest rates affect gold?"
        - "What's the correlation between DXY and XAUUSD?"
    """
    response = deep_research_sync(question)
    
    return {
        "question": question,
        "answer": response.text,
        "sources": [
            {"title": s.title, "url": s.url}
            for s in response.sources
        ],
        "model": response.model,
        "timestamp": datetime.utcnow().isoformat(),
    }


def should_trade_now(
    symbol: str = "XAUUSD",
) -> Dict[str, Any]:
    """
    Quick check if conditions are favorable for trading.
    
    This is a rapid assessment tool for checking if now
    is a good time to trade, considering:
    - Market volatility
    - Upcoming news events
    - Current sentiment
    - Time of day / market hours
    
    Args:
        symbol: Symbol to check
        
    Returns:
        Quick assessment with:
        - should_trade: True/False
        - reason: Why or why not
        - wait_until: If not now, when (optional)
    """
    intel = get_intelligence()
    result = _run_async(intel.quick_scan(symbol))
    
    # Simple decision logic based on signal
    signal = result.get("signal", "hold")
    confidence = result.get("confidence", 0.5)
    
    should = signal in ("strong_buy", "buy", "strong_sell", "sell")
    should = should and confidence > 0.5
    
    return {
        "should_trade": should,
        "signal": signal,
        "confidence": confidence,
        "reason": result.get("reasoning", ""),
        "risk_factors": result.get("risk_factors", []),
        "recommended_action": result.get("recommended_action", ""),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_intelligence_tools() -> List[callable]:
    """
    Get all intelligence tools for registration with GemCode.
    
    These tools are registered when GEMCODE_TRADING=1.
    """
    return [
        market_intelligence,
        analyze_news_impact,
        economic_calendar,
        research_question,
        should_trade_now,
    ]
