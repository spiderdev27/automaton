"""
GemTrade Intelligence System

A super-intelligent information processing layer that:
1. Scans global news, social media, and market chatter
2. Detects DIRECT and INDIRECT signals
3. Correlates news patterns with historical price movements  
4. Learns which signals actually move prices
5. Reasons deeply before acting

Architecture:
- Uses GemCode agent mesh for parallel processing
- Multiple specialized intelligence agents
- Shared memory for learned correlations
- LLM reasoning for complex inference

Philosophy: The money is in information BEFORE it becomes obvious.
"""

from gemtrade.intelligence.scanner import (
    IntelligenceScanner,
    NewsSource,
    SentimentSource,
    SocialSource,
)
from gemtrade.intelligence.analyzer import (
    IntelligenceAnalyzer,
    SignalType,
    SignalStrength,
    IntelligenceSignal,
)
from gemtrade.intelligence.correlator import (
    PatternCorrelator,
    HistoricalCorrelation,
    NewsPattern,
)
from gemtrade.intelligence.reasoner import (
    DeepReasoner,
    ReasoningChain,
    Inference,
)

__all__ = [
    "IntelligenceScanner",
    "NewsSource",
    "SentimentSource",
    "SocialSource",
    "IntelligenceAnalyzer",
    "SignalType",
    "SignalStrength",
    "IntelligenceSignal",
    "PatternCorrelator",
    "HistoricalCorrelation",
    "NewsPattern",
    "DeepReasoner",
    "ReasoningChain",
    "Inference",
]
