"""
Intelligence Scanner

Scans multiple sources for market-moving information:
- Financial news (Reuters, Bloomberg, etc.)
- Social media (Reddit, X/Twitter, StockTwits)
- Crypto communities
- Prediction markets (Polymarket)
- Economic data releases
- Corporate filings
- Insider activity
- Unusual options activity

The scanner doesn't interpret - it collects and normalizes.
Interpretation is done by the Analyzer.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Any
import asyncio


class NewsSource(Enum):
    """News data sources."""
    REUTERS = "reuters"
    BLOOMBERG = "bloomberg"
    BENZINGA = "benzinga"
    FINVIZ = "finviz"
    SEEKING_ALPHA = "seeking_alpha"
    ZEROHEDGE = "zerohedge"
    FED = "federal_reserve"
    ECB = "ecb"
    EARNINGS = "earnings_calls"


class SocialSource(Enum):
    """Social media sources."""
    REDDIT_WSB = "reddit_wsb"           # WallStreetBets
    REDDIT_STOCKS = "reddit_stocks"     # r/stocks
    REDDIT_INVESTING = "reddit_investing"
    REDDIT_CRYPTO = "reddit_crypto"
    TWITTER_FINTWIT = "twitter_fintwit"
    STOCKTWITS = "stocktwits"
    DISCORD = "discord"
    TELEGRAM = "telegram"


class SentimentSource(Enum):
    """Sentiment API providers."""
    ADANOS = "adanos"           # Reddit+X+news+Polymarket unified
    ROLLI_IQ = "rolli_iq"       # Authenticity-scored signals
    STOCKGEIST = "stockgeist"   # Social + news
    FINNHUB = "finnhub"         # Social sentiment
    QUIVER = "quiver"           # Reddit/Congress/insider


@dataclass
class RawIntelligence:
    """
    Raw intelligence item before analysis.
    
    This is the raw data - uninterpreted, unscored.
    """
    id: str
    source: str
    source_type: str  # "news", "social", "filing", "data"
    
    # Content
    title: str
    content: str
    url: Optional[str] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    author: Optional[str] = None
    
    # Relevance hints
    mentioned_symbols: List[str] = field(default_factory=list)
    mentioned_entities: List[str] = field(default_factory=list)
    
    # Raw sentiment (if available from source)
    raw_sentiment: Optional[float] = None  # -1 to 1
    
    # Engagement metrics (for social)
    upvotes: Optional[int] = None
    comments: Optional[int] = None
    shares: Optional[int] = None
    
    # Credibility hints
    is_verified: bool = False
    author_credibility: Optional[float] = None  # 0-1


@dataclass
class SentimentData:
    """
    Aggregated sentiment from API providers.
    """
    symbol: str
    source: SentimentSource
    timestamp: datetime
    
    # Scores
    buzz_score: float = 0.0        # 0-100, attention level
    bullish_pct: float = 50.0      # % bullish
    bearish_pct: float = 50.0      # % bearish
    
    # Trend
    sentiment_change_24h: float = 0.0
    volume_change_24h: float = 0.0
    
    # Authenticity (from Rolli IQ style providers)
    authenticity_score: Optional[float] = None  # 0-100
    coordination_probability: Optional[float] = None  # 0-100
    
    # Source breakdown
    reddit_sentiment: Optional[float] = None
    twitter_sentiment: Optional[float] = None
    news_sentiment: Optional[float] = None
    
    def is_organic(self) -> bool:
        """Check if sentiment appears organic vs coordinated."""
        if self.coordination_probability is not None:
            return self.coordination_probability < 40
        return True  # Assume organic if we don't have data
    
    def net_sentiment(self) -> float:
        """Net sentiment from -100 (bearish) to +100 (bullish)."""
        return self.bullish_pct - self.bearish_pct


class IntelligenceScanner:
    """
    Scans multiple sources for market intelligence.
    
    Uses GemCode's agent mesh for parallel scanning.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.api_keys = config.get("api_keys", {})
        
        # Rate limiting
        self.last_scan: Dict[str, datetime] = {}
        self.min_scan_interval = timedelta(minutes=5)
        
        # Cache
        self.intelligence_cache: List[RawIntelligence] = []
        self.sentiment_cache: Dict[str, SentimentData] = {}
        
    async def scan_all(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Scan all sources for given symbols.
        
        Returns aggregated intelligence.
        """
        tasks = [
            self._scan_news(symbols),
            self._scan_social(symbols),
            self._scan_sentiment_apis(symbols),
            self._scan_economic_calendar(),
            self._scan_unusual_activity(symbols),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        return {
            "news": results[0] if not isinstance(results[0], Exception) else [],
            "social": results[1] if not isinstance(results[1], Exception) else [],
            "sentiment": results[2] if not isinstance(results[2], Exception) else {},
            "economic": results[3] if not isinstance(results[3], Exception) else [],
            "unusual_activity": results[4] if not isinstance(results[4], Exception) else [],
            "scanned_at": datetime.utcnow().isoformat(),
        }
    
    async def _scan_news(self, symbols: List[str]) -> List[RawIntelligence]:
        """Scan news sources."""
        intelligence = []
        
        # Would integrate with news APIs:
        # - Finnhub news API
        # - Alpha Vantage news
        # - Benzinga API
        # - Custom RSS feeds
        
        # Placeholder structure
        return intelligence
    
    async def _scan_social(self, symbols: List[str]) -> List[RawIntelligence]:
        """Scan social media sources."""
        intelligence = []
        
        # Would integrate with:
        # - Reddit API (PRAW)
        # - Twitter/X API
        # - StockTwits API
        
        return intelligence
    
    async def _scan_sentiment_apis(self, symbols: List[str]) -> Dict[str, SentimentData]:
        """Get sentiment from unified APIs."""
        sentiment = {}
        
        # Adanos API integration
        if "adanos" in self.api_keys:
            for symbol in symbols:
                # Would call: https://api.adanos.org/v1/sentiment/{symbol}
                # Returns: buzz_score, bullish_pct, bearish_pct, trend
                pass
        
        # Rolli IQ integration (authenticity scoring)
        if "rolli_iq" in self.api_keys:
            # Would call for authenticity-scored signals
            pass
        
        return sentiment
    
    async def _scan_economic_calendar(self) -> List[Dict]:
        """Scan upcoming economic events."""
        events = []
        
        # Would integrate with:
        # - Forex Factory calendar
        # - Investing.com calendar
        # - Fed/ECB announcement schedules
        
        return events
    
    async def _scan_unusual_activity(self, symbols: List[str]) -> List[Dict]:
        """
        Scan for unusual activity that might indicate insider knowledge:
        - Unusual options volume
        - Dark pool activity
        - Large block trades
        - Insider trading filings
        """
        activity = []
        
        # Would integrate with:
        # - Unusual Whales API
        # - FINRA dark pool data
        # - SEC Form 4 filings
        
        return activity
    
    async def scan_for_indirect_signals(
        self, 
        primary_symbol: str,
        related_entities: List[str]
    ) -> List[RawIntelligence]:
        """
        Scan for INDIRECT signals that might affect the primary symbol.
        
        Example: News about a gold mine accident in South Africa
                 → indirect signal for XAU/USD
                 
        Example: News about chip shortage
                 → indirect signal for tech stocks, crypto mining
        """
        intelligence = []
        
        # Scan for news about:
        # - Suppliers/customers of companies we trade
        # - Geographic regions relevant to commodities
        # - Policy makers and their statements
        # - Competitor news
        # - Industry trends
        
        # This requires LLM reasoning to connect dots
        # Will be handled by DeepReasoner
        
        return intelligence


# Data source configurations
NEWS_SOURCES_CONFIG = {
    "finnhub": {
        "base_url": "https://finnhub.io/api/v1",
        "endpoints": {
            "news": "/news",
            "company_news": "/company-news",
            "sentiment": "/news-sentiment",
        },
        "rate_limit": 60,  # requests per minute
    },
    "alpha_vantage": {
        "base_url": "https://www.alphavantage.co/query",
        "endpoints": {
            "news": "NEWS_SENTIMENT",
        },
        "rate_limit": 5,  # requests per minute (free tier)
    },
}

SENTIMENT_SOURCES_CONFIG = {
    "adanos": {
        "base_url": "https://api.adanos.org/v1",
        "endpoints": {
            "sentiment": "/sentiment/{symbol}",
            "buzz": "/buzz/{symbol}",
            "trend": "/trend/{symbol}",
        },
        "free_tier": 250,  # requests per month
    },
    "stockgeist": {
        "base_url": "https://api.stockgeist.ai/v1",
        "endpoints": {
            "sentiment": "/sentiment",
            "messages": "/messages",
        },
    },
}


# Symbols and their related entities for indirect signal detection
SYMBOL_RELATIONSHIPS = {
    "XAUUSD": {
        "direct": ["gold", "XAU", "precious metals"],
        "indirect": [
            "federal reserve", "interest rates", "inflation", "CPI",
            "dollar", "USD", "DXY", "treasury yields",
            "geopolitical", "war", "conflict", "sanctions",
            "mining", "gold miners", "GDX", "Newmont", "Barrick",
            "central banks", "gold reserves", "ETF flows", "GLD",
        ],
        "inverse": ["risk-on", "stock rally", "crypto pump"],
    },
    "BTCUSD": {
        "direct": ["bitcoin", "BTC", "crypto"],
        "indirect": [
            "Tether", "USDT", "stablecoin", "exchange",
            "SEC", "regulation", "ETF approval",
            "halving", "mining difficulty", "hash rate",
            "whale", "wallet movement", "exchange outflow",
            "macro liquidity", "risk assets",
        ],
        "inverse": ["ban", "crackdown", "hack", "rug pull"],
    },
}
