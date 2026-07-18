"""
Gemini Client with Web Search Grounding

Uses Google's Gemini API with web search capability for:
- Real-time news analysis
- Market sentiment scanning
- Deep research on trading topics
- Economic calendar checking

Requires: GOOGLE_API_KEY or GOOGLE_CLOUD_PROJECT environment variable
"""

from __future__ import annotations

import os
import json
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from functools import lru_cache


@dataclass
class GeminiConfig:
    """Configuration for Gemini client."""
    api_key: Optional[str] = None
    model: str = "gemini-2.0-flash"  # Fast, cheap, good
    pro_model: str = "gemini-2.0-pro"  # For deep reasoning
    temperature: float = 0.7
    max_tokens: int = 4096
    enable_search: bool = True
    
    @classmethod
    def from_env(cls) -> "GeminiConfig":
        return cls(
            api_key=os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"),
        )


@dataclass
class SearchResult:
    """A search result from grounding."""
    title: str
    url: str
    snippet: str


@dataclass
class GroundedResponse:
    """Response with grounding sources."""
    text: str
    sources: List[SearchResult] = field(default_factory=list)
    search_queries: List[str] = field(default_factory=list)
    model: str = ""
    usage: Dict[str, int] = field(default_factory=dict)


class GeminiClient:
    """
    Client for Gemini API with web search grounding.
    
    Usage:
        client = GeminiClient()
        response = await client.generate(
            "What's happening with gold prices today?",
            enable_search=True
        )
        print(response.text)
        for source in response.sources:
            print(f"- {source.title}: {source.url}")
    """
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig.from_env()
        self._client = None
        self._rate_limit_reset = 0
        self._requests_this_minute = 0
        
    def _ensure_client(self):
        """Initialize the Gemini client lazily."""
        if self._client is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.config.api_key)
                self._client = genai
            except ImportError:
                raise ImportError(
                    "google-generativeai not installed. "
                    "Install with: pip install google-generativeai"
                )
    
    def _rate_limit(self):
        """Simple rate limiting (15 RPM for free tier)."""
        now = time.time()
        
        if now > self._rate_limit_reset:
            self._rate_limit_reset = now + 60
            self._requests_this_minute = 0
        
        self._requests_this_minute += 1
        
        if self._requests_this_minute > 14:
            sleep_time = self._rate_limit_reset - now
            if sleep_time > 0:
                time.sleep(sleep_time)
                self._rate_limit_reset = time.time() + 60
                self._requests_this_minute = 1
    
    async def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        enable_search: bool = True,
        use_pro: bool = False,
    ) -> GroundedResponse:
        """
        Generate a response, optionally with web search grounding.
        
        Args:
            prompt: The prompt to send
            system_instruction: System-level instruction
            enable_search: Whether to enable web search grounding
            use_pro: Use Pro model for better reasoning
            
        Returns:
            GroundedResponse with text and sources
        """
        self._ensure_client()
        self._rate_limit()
        
        model_name = self.config.pro_model if use_pro else self.config.model
        
        generation_config = {
            "temperature": self.config.temperature,
            "max_output_tokens": self.config.max_tokens,
        }
        
        # Build tools list
        tools = []
        if enable_search and self.config.enable_search:
            tools.append("google_search_retrieval")
        
        try:
            model = self._client.GenerativeModel(
                model_name=model_name,
                generation_config=generation_config,
                system_instruction=system_instruction,
                tools=tools if tools else None,
            )
            
            response = model.generate_content(prompt)
            
            # Extract grounding metadata
            sources = []
            search_queries = []
            
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata'):
                    gm = candidate.grounding_metadata
                    
                    # Extract search queries
                    if hasattr(gm, 'web_search_queries'):
                        search_queries = list(gm.web_search_queries)
                    
                    # Extract sources
                    if hasattr(gm, 'grounding_chunks'):
                        for chunk in gm.grounding_chunks:
                            if hasattr(chunk, 'web'):
                                sources.append(SearchResult(
                                    title=chunk.web.title or "",
                                    url=chunk.web.uri or "",
                                    snippet="",
                                ))
            
            # Extract usage
            usage = {}
            if hasattr(response, 'usage_metadata'):
                um = response.usage_metadata
                usage = {
                    "prompt_tokens": getattr(um, 'prompt_token_count', 0),
                    "completion_tokens": getattr(um, 'candidates_token_count', 0),
                    "total_tokens": getattr(um, 'total_token_count', 0),
                }
            
            return GroundedResponse(
                text=response.text,
                sources=sources,
                search_queries=search_queries,
                model=model_name,
                usage=usage,
            )
            
        except Exception as e:
            return GroundedResponse(
                text=f"Error: {str(e)}",
                model=model_name,
            )
    
    async def analyze_news(
        self,
        topic: str,
        symbols: List[str] = None,
    ) -> GroundedResponse:
        """
        Analyze current news for a topic.
        
        Args:
            topic: Topic to analyze (e.g., "gold prices", "US economy")
            symbols: Related trading symbols
            
        Returns:
            News analysis with sources
        """
        symbols_str = ", ".join(symbols) if symbols else "financial markets"
        
        prompt = f"""Analyze the latest news and developments related to: {topic}

Focus on:
1. Most recent and relevant news (last 24 hours preferred)
2. Impact on {symbols_str}
3. Market sentiment (bullish/bearish/neutral)
4. Key data points or events
5. Potential trading implications

Provide a structured analysis with:
- HEADLINE: One-line summary
- SENTIMENT: bullish/bearish/neutral with confidence %
- KEY_POINTS: Bullet list of important facts
- IMPACT: Expected market impact
- TRADING_IMPLICATION: What this means for trading"""
        
        return await self.generate(
            prompt,
            system_instruction="You are a financial news analyst. Be factual, cite sources, and provide actionable insights.",
            enable_search=True,
        )
    
    async def deep_research(
        self,
        question: str,
    ) -> GroundedResponse:
        """
        Perform deep research on a topic using Pro model.
        
        For complex questions requiring multi-hop reasoning.
        """
        prompt = f"""Research this question thoroughly: {question}

Use web search to gather information and provide:
1. Direct answer
2. Supporting evidence from multiple sources
3. Any conflicting information
4. Confidence level in your conclusion
5. What additional information would help"""
        
        return await self.generate(
            prompt,
            system_instruction="You are a research analyst. Be thorough, cite sources, acknowledge uncertainty.",
            enable_search=True,
            use_pro=True,
        )
    
    async def get_economic_calendar(
        self,
        currencies: List[str] = None,
    ) -> GroundedResponse:
        """
        Get upcoming economic events.
        """
        currencies = currencies or ["USD", "EUR", "GBP", "JPY"]
        currencies_str = ", ".join(currencies)
        
        prompt = f"""What are the upcoming high-impact economic events for: {currencies_str}?

List events for the next 48 hours including:
- Event name
- Date and time (UTC)
- Currency affected
- Expected impact (high/medium/low)
- Forecast vs previous (if available)

Focus on events that move markets: interest rate decisions, employment data, GDP, inflation, etc."""
        
        return await self.generate(
            prompt,
            system_instruction="You are an economic calendar assistant. Be precise about times and dates.",
            enable_search=True,
        )


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


def analyze_news_sync(
    topic: str,
    symbols: List[str] = None,
) -> GroundedResponse:
    """Synchronous wrapper for analyze_news."""
    client = GeminiClient()
    return _run_async(client.analyze_news(topic, symbols))


def deep_research_sync(
    question: str,
) -> GroundedResponse:
    """Synchronous wrapper for deep_research."""
    client = GeminiClient()
    return _run_async(client.deep_research(question))


def get_economic_calendar_sync(
    currencies: List[str] = None,
) -> GroundedResponse:
    """Synchronous wrapper for get_economic_calendar."""
    client = GeminiClient()
    return _run_async(client.get_economic_calendar(currencies))
