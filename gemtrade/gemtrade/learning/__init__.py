"""
Learning Module

Pre-loaded historical knowledge and continuous learning systems.
"""

from gemtrade.learning.historical_knowledge import (
    GOLD_KNOWLEDGE,
    PROVEN_PATTERNS,
    HISTORICAL_LESSONS,
    HIGH_LEVERAGE_RULES,
    COMMON_MISTAKES,
    get_trading_knowledge,
    get_knowledge_prompt,
    HistoricalPattern,
)

__all__ = [
    "GOLD_KNOWLEDGE",
    "PROVEN_PATTERNS", 
    "HISTORICAL_LESSONS",
    "HIGH_LEVERAGE_RULES",
    "COMMON_MISTAKES",
    "get_trading_knowledge",
    "get_knowledge_prompt",
    "HistoricalPattern",
]
