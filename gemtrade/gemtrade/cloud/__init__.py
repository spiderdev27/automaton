"""
Google Cloud Integration for GemTrade

Leverages Google Cloud services for intelligent trading:
- Gemini API with Web Search Grounding for real-time intelligence
- AI-powered decision making (no predefined rules)
- News analysis and sentiment scanning
- Economic calendar integration

Configuration:
- GOOGLE_API_KEY or GEMINI_API_KEY: API key for Gemini
"""

from gemtrade.cloud.gemini_client import (
    GeminiClient,
    GeminiConfig,
    GroundedResponse,
    SearchResult,
    analyze_news_sync,
    deep_research_sync,
    get_economic_calendar_sync,
)
from gemtrade.cloud.intelligence import (
    GeminiIntelligence,
    IntelligenceQuery,
    IntelligenceResult,
    MarketInsight,
    SignalType,
    MarketCondition,
    get_intelligence,
    gather_intelligence_sync,
    quick_scan_sync,
    full_analysis_sync,
)

__all__ = [
    # Gemini Client
    "GeminiClient",
    "GeminiConfig",
    "GroundedResponse",
    "SearchResult",
    "analyze_news_sync",
    "deep_research_sync",
    "get_economic_calendar_sync",
    # Intelligence
    "GeminiIntelligence",
    "IntelligenceQuery",
    "IntelligenceResult",
    "MarketInsight",
    "SignalType",
    "MarketCondition",
    "get_intelligence",
    "gather_intelligence_sync",
    "quick_scan_sync",
    "full_analysis_sync",
]
