"""
Gemini API Client with Web Search Grounding

This module provides a client for Google's Gemini API with:
- Web search grounding for real-time information
- Function calling for trading operations
- Structured output for reliable parsing
- Cost optimization through intelligent caching
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any, Callable
import asyncio
import hashlib
import json
import os

try:
    from google import genai
    from google.genai import types
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False


class GeminiModel(Enum):
    """Available Gemini models with cost/capability tradeoffs."""
    # Flash models - fast and cheap
    FLASH_LITE = "gemini-2.5-flash-lite"      # Cheapest: $0.10/1M input
    FLASH = "gemini-2.5-flash"                 # Fast: $0.30/1M input
    FLASH_3 = "gemini-3-flash"                 # Latest flash
    
    # Pro models - more capable
    PRO = "gemini-2.5-pro"                     # Capable: $1.25/1M input
    PRO_3 = "gemini-3.1-pro"                   # Latest pro: $2.00/1M input
    
    # Preview models
    FLASH_3_5 = "gemini-3.5-flash"             # Newest


@dataclass
class GeminiConfig:
    """Configuration for Gemini client."""
    api_key: Optional[str] = None
    project_id: Optional[str] = None  # For Vertex AI
    
    # Model selection
    default_model: GeminiModel = GeminiModel.FLASH
    reasoning_model: GeminiModel = GeminiModel.PRO
    
    # Features
    enable_grounding: bool = True
    enable_function_calling: bool = True
    
    # Cost optimization
    cache_ttl_seconds: int = 300  # 5 minute cache
    max_retries: int = 3
    rate_limit_rpm: int = 10  # Free tier limit
    
    # Safety
    temperature: float = 0.1  # Low for consistency
    max_output_tokens: int = 2048
    
    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY"),
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
        )


@dataclass
class SearchResult:
    """A single search result from grounding."""
    title: str
    url: str
    snippet: str
    domain: str = ""
    
    @classmethod
    def from_grounding_chunk(cls, chunk: Dict) -> "SearchResult":
        """Create from Gemini grounding chunk."""
        web = chunk.get("web", {})
        return cls(
            title=web.get("title", ""),
            url=web.get("uri", ""),
            snippet=chunk.get("text", ""),
            domain=web.get("domain", ""),
        )


@dataclass
class GroundedResponse:
    """Response from Gemini with grounding metadata."""
    text: str
    model: str
    grounded: bool = False
    
    # Search data
    search_queries: List[str] = field(default_factory=list)
    sources: List[SearchResult] = field(default_factory=list)
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    cached: bool = False
    tokens_used: int = 0
    
    # Confidence
    confidence: float = 0.0
    
    def get_source_urls(self) -> List[str]:
        """Get list of source URLs."""
        return [s.url for s in self.sources]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "text": self.text,
            "model": self.model,
            "grounded": self.grounded,
            "sources": [{"title": s.title, "url": s.url} for s in self.sources],
            "search_queries": self.search_queries,
            "timestamp": self.timestamp.isoformat(),
        }


class GeminiClient:
    """
    Gemini API client optimized for trading intelligence.
    
    Features:
    - Web search grounding for real-time news
    - Function calling for trading actions
    - Response caching for cost optimization
    - Rate limiting for free tier compliance
    """
    
    def __init__(self, config: Optional[GeminiConfig] = None):
        self.config = config or GeminiConfig.from_env()
        
        if not HAS_GEMINI:
            raise ImportError(
                "google-genai not installed. "
                "Run: pip install google-genai"
            )
        
        if not self.config.api_key:
            raise ValueError(
                "Gemini API key required. Set GOOGLE_API_KEY or GEMINI_API_KEY"
            )
        
        # Initialize client
        self.client = genai.Client(api_key=self.config.api_key)
        
        # Cache for responses
        self._cache: Dict[str, GroundedResponse] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
        
        # Rate limiting
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()
        
        # Registered tools for function calling
        self._tools: Dict[str, Callable] = {}
    
    def register_tool(self, name: str, func: Callable, description: str, parameters: Dict):
        """Register a function for function calling."""
        self._tools[name] = {
            "function": func,
            "declaration": types.FunctionDeclaration(
                name=name,
                description=description,
                parameters=parameters,
            )
        }
    
    async def _wait_for_rate_limit(self):
        """Ensure we don't exceed rate limits."""
        async with self._rate_limit_lock:
            now = datetime.utcnow()
            minute_ago = now - timedelta(minutes=1)
            
            # Remove old timestamps
            self._request_times = [
                t for t in self._request_times if t > minute_ago
            ]
            
            if len(self._request_times) >= self.config.rate_limit_rpm:
                # Wait until oldest request expires
                sleep_time = (self._request_times[0] - minute_ago).total_seconds()
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time + 0.1)
            
            self._request_times.append(now)
    
    def _get_cache_key(self, prompt: str, model: str, grounded: bool) -> str:
        """Generate cache key for request."""
        key_data = f"{prompt}:{model}:{grounded}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _check_cache(self, cache_key: str) -> Optional[GroundedResponse]:
        """Check if we have a valid cached response."""
        if cache_key not in self._cache:
            return None
        
        timestamp = self._cache_timestamps.get(cache_key)
        if not timestamp:
            return None
        
        if datetime.utcnow() - timestamp > timedelta(seconds=self.config.cache_ttl_seconds):
            del self._cache[cache_key]
            del self._cache_timestamps[cache_key]
            return None
        
        response = self._cache[cache_key]
        response.cached = True
        return response
    
    async def generate(
        self,
        prompt: str,
        model: Optional[GeminiModel] = None,
        grounded: bool = True,
        use_cache: bool = True,
        system_instruction: Optional[str] = None,
    ) -> GroundedResponse:
        """
        Generate a response from Gemini.
        
        Args:
            prompt: The input prompt
            model: Which model to use (default: config.default_model)
            grounded: Whether to use web search grounding
            use_cache: Whether to use response caching
            system_instruction: Optional system prompt
            
        Returns:
            GroundedResponse with text and source citations
        """
        model = model or self.config.default_model
        model_name = model.value
        
        # Check cache
        if use_cache:
            cache_key = self._get_cache_key(prompt, model_name, grounded)
            cached = self._check_cache(cache_key)
            if cached:
                return cached
        
        # Rate limiting
        await self._wait_for_rate_limit()
        
        # Build tools
        tools = []
        if grounded and self.config.enable_grounding:
            tools.append(types.Tool(google_search=types.GoogleSearch()))
        
        # Generate
        try:
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=tools if tools else None,
                    temperature=self.config.temperature,
                    max_output_tokens=self.config.max_output_tokens,
                    system_instruction=system_instruction,
                )
            )
            
            result = self._parse_response(response, model_name)
            
            # Cache result
            if use_cache:
                self._cache[cache_key] = result
                self._cache_timestamps[cache_key] = datetime.utcnow()
            
            return result
            
        except Exception as e:
            # Return error response
            return GroundedResponse(
                text=f"Error: {str(e)}",
                model=model_name,
                grounded=False,
            )
    
    def _parse_response(self, response: Any, model: str) -> GroundedResponse:
        """Parse Gemini response into GroundedResponse."""
        text = ""
        sources = []
        search_queries = []
        grounded = False
        
        # Extract text
        if hasattr(response, "text"):
            text = response.text
        elif hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, "content") and candidate.content.parts:
                text = candidate.content.parts[0].text
        
        # Extract grounding metadata
        if hasattr(response, "candidates") and response.candidates:
            candidate = response.candidates[0]
            
            if hasattr(candidate, "grounding_metadata"):
                metadata = candidate.grounding_metadata
                grounded = True
                
                # Search queries
                if hasattr(metadata, "web_search_queries"):
                    search_queries = list(metadata.web_search_queries or [])
                
                # Grounding chunks (sources)
                if hasattr(metadata, "grounding_chunks"):
                    for chunk in (metadata.grounding_chunks or []):
                        sources.append(SearchResult.from_grounding_chunk(
                            chunk if isinstance(chunk, dict) else {}
                        ))
        
        # Token usage
        tokens = 0
        if hasattr(response, "usage_metadata"):
            tokens = getattr(response.usage_metadata, "total_token_count", 0)
        
        return GroundedResponse(
            text=text,
            model=model,
            grounded=grounded,
            search_queries=search_queries,
            sources=sources,
            tokens_used=tokens,
        )
    
    async def analyze_news(
        self,
        query: str,
        symbols: List[str],
        timeframe: str = "last 24 hours",
    ) -> GroundedResponse:
        """
        Analyze recent news for trading signals.
        
        Uses web search grounding to get real-time information.
        """
        system_prompt = """You are a financial analyst AI specializing in real-time market intelligence.
Your task is to analyze news and extract actionable trading signals.

For each piece of news, determine:
1. SENTIMENT: bullish, bearish, or neutral
2. IMPACT: high, medium, or low
3. TIMEFRAME: immediate (minutes), short-term (hours), medium-term (days)
4. CONFIDENCE: 0-100%
5. REASONING: Brief explanation

Focus on facts that could move prices. Ignore speculation without substance."""

        prompt = f"""Search for and analyze the latest news about {', '.join(symbols)} from the {timeframe}.

Query: {query}

Return a JSON object with this structure:
{{
    "news_items": [
        {{
            "headline": "...",
            "source": "...",
            "sentiment": "bullish|bearish|neutral",
            "impact": "high|medium|low",
            "timeframe": "immediate|short-term|medium-term",
            "confidence": 0-100,
            "affected_symbols": ["..."],
            "reasoning": "..."
        }}
    ],
    "overall_sentiment": "bullish|bearish|neutral",
    "key_events": ["..."],
    "risk_factors": ["..."]
}}"""

        return await self.generate(
            prompt=prompt,
            model=GeminiModel.FLASH,  # Fast for news
            grounded=True,
            system_instruction=system_prompt,
        )
    
    async def deep_research(
        self,
        topic: str,
        context: Optional[str] = None,
    ) -> GroundedResponse:
        """
        Perform deep research on a topic.
        
        Uses the Pro model for better reasoning.
        """
        system_prompt = """You are a senior financial research analyst with 20+ years of experience.
Conduct thorough research and provide actionable insights.
Always cite your sources and distinguish between facts and analysis."""

        prompt = f"""Research this topic thoroughly: {topic}

{f'Context: {context}' if context else ''}

Provide:
1. Key findings with source citations
2. Historical precedents if relevant
3. Potential market implications
4. Contrarian viewpoints
5. What the consensus might be missing"""

        return await self.generate(
            prompt=prompt,
            model=GeminiModel.PRO,  # Better reasoning
            grounded=True,
            system_instruction=system_prompt,
        )
    
    async def get_economic_calendar(self, days_ahead: int = 7) -> GroundedResponse:
        """Get upcoming economic events."""
        prompt = f"""Search for the economic calendar for the next {days_ahead} days.

List all HIGH IMPACT events including:
- Central bank decisions (Fed, ECB, BoE, BoJ)
- Employment data (NFP, unemployment)
- Inflation data (CPI, PPI)
- GDP releases
- PMI data
- Retail sales
- Housing data

For each event, provide:
- Date and time (UTC)
- Event name
- Country/region
- Previous value
- Consensus forecast
- Potential market impact"""

        return await self.generate(
            prompt=prompt,
            model=GeminiModel.FLASH,
            grounded=True,
        )
    
    def clear_cache(self):
        """Clear the response cache."""
        self._cache.clear()
        self._cache_timestamps.clear()
