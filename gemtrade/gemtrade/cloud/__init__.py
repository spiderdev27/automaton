"""
Google Cloud Integration for GemTrade

Leverages Google Cloud services for intelligent trading:
- Gemini API with Web Search Grounding for real-time intelligence
- BigQuery for trade data warehousing and analytics
- Cloud Functions for event-driven triggers
- Vertex AI for advanced ML workloads
"""

from gemtrade.cloud.gemini_client import (
    GeminiClient,
    GeminiConfig,
    GroundedResponse,
    SearchResult,
)
from gemtrade.cloud.intelligence import (
    GeminiIntelligence,
    IntelligenceQuery,
    IntelligenceResult,
    MarketInsight,
)
from gemtrade.cloud.bigquery_store import (
    BigQueryStore,
    TradeRecord,
    SignalRecord,
    PerformanceMetrics,
)

__all__ = [
    # Gemini Client
    "GeminiClient",
    "GeminiConfig",
    "GroundedResponse",
    "SearchResult",
    # Intelligence
    "GeminiIntelligence",
    "IntelligenceQuery",
    "IntelligenceResult",
    "MarketInsight",
    # BigQuery
    "BigQueryStore",
    "TradeRecord",
    "SignalRecord",
    "PerformanceMetrics",
]
