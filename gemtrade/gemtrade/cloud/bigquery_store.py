"""
BigQuery Data Store for GemTrade

Leverages Google Cloud's free tier:
- 1 TB of queries per month
- 10 GB of storage per month

Stores:
- Trade records and performance metrics
- Intelligence signals and their outcomes
- Market data snapshots
- Learning data for pattern recognition
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import json
import os

try:
    from google.cloud import bigquery
    from google.cloud.exceptions import NotFound
    HAS_BIGQUERY = True
except ImportError:
    HAS_BIGQUERY = False


@dataclass
class TradeRecord:
    """A trade record for storage and analysis."""
    trade_id: str
    symbol: str
    side: str  # "long" or "short"
    
    # Entry
    entry_time: datetime
    entry_price: float
    entry_reason: str
    entry_signals: List[str] = field(default_factory=list)
    
    # Exit
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    
    # Position
    quantity: float = 0.0
    leverage: float = 1.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    
    # Performance
    pnl_paise: int = 0  # In paise (1/100 INR)
    pnl_percent: float = 0.0
    max_drawdown_percent: float = 0.0
    
    # Risk metrics
    risk_per_trade_percent: float = 0.0
    survival_tier: str = "NORMAL"
    
    # Metadata
    strategy: str = ""
    market_regime: str = ""
    news_context: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for BigQuery."""
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "side": self.side,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "entry_price": self.entry_price,
            "entry_reason": self.entry_reason,
            "entry_signals": json.dumps(self.entry_signals),
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "quantity": self.quantity,
            "leverage": self.leverage,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "pnl_paise": self.pnl_paise,
            "pnl_percent": self.pnl_percent,
            "max_drawdown_percent": self.max_drawdown_percent,
            "risk_per_trade_percent": self.risk_per_trade_percent,
            "survival_tier": self.survival_tier,
            "strategy": self.strategy,
            "market_regime": self.market_regime,
            "news_context": self.news_context,
        }


@dataclass
class SignalRecord:
    """An intelligence signal record."""
    signal_id: str
    symbol: str
    timestamp: datetime
    
    # Signal properties
    signal_type: str  # "news", "sentiment", "indirect", "contrarian"
    direction: str  # "buy", "sell", "neutral"
    confidence: float
    timeframe: str
    
    # Content
    headline: str
    content: str
    source: str
    source_url: Optional[str] = None
    
    # Outcome tracking
    was_traded: bool = False
    trade_id: Optional[str] = None
    outcome_correct: Optional[bool] = None
    price_at_signal: Optional[float] = None
    price_after_1h: Optional[float] = None
    price_after_24h: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for BigQuery."""
        return {
            "signal_id": self.signal_id,
            "symbol": self.symbol,
            "timestamp": self.timestamp.isoformat(),
            "signal_type": self.signal_type,
            "direction": self.direction,
            "confidence": self.confidence,
            "timeframe": self.timeframe,
            "headline": self.headline,
            "content": self.content[:1000] if self.content else None,  # Truncate for storage
            "source": self.source,
            "source_url": self.source_url,
            "was_traded": self.was_traded,
            "trade_id": self.trade_id,
            "outcome_correct": self.outcome_correct,
            "price_at_signal": self.price_at_signal,
            "price_after_1h": self.price_after_1h,
            "price_after_24h": self.price_after_24h,
        }


@dataclass
class PerformanceMetrics:
    """Aggregated performance metrics."""
    period_start: datetime
    period_end: datetime
    
    # Trade counts
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    
    # P&L
    total_pnl_paise: int = 0
    gross_profit_paise: int = 0
    gross_loss_paise: int = 0
    
    # Ratios
    win_rate: float = 0.0
    profit_factor: float = 0.0
    average_win_paise: int = 0
    average_loss_paise: int = 0
    
    # Risk
    max_drawdown_paise: int = 0
    max_drawdown_percent: float = 0.0
    sharpe_ratio: float = 0.0
    
    # By strategy
    strategy_breakdown: Dict[str, Dict] = field(default_factory=dict)
    
    # By signal type
    signal_accuracy: Dict[str, float] = field(default_factory=dict)


class BigQueryStore:
    """
    BigQuery-backed data store for GemTrade.
    
    Tables:
    - trades: All trade records
    - signals: Intelligence signals
    - daily_metrics: Daily performance snapshots
    - learned_patterns: Patterns from signal-outcome correlation
    """
    
    # Schema definitions
    TRADES_SCHEMA = [
        bigquery.SchemaField("trade_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("side", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("entry_time", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("entry_price", "FLOAT64", mode="REQUIRED"),
        bigquery.SchemaField("entry_reason", "STRING"),
        bigquery.SchemaField("entry_signals", "STRING"),  # JSON array
        bigquery.SchemaField("exit_time", "TIMESTAMP"),
        bigquery.SchemaField("exit_price", "FLOAT64"),
        bigquery.SchemaField("exit_reason", "STRING"),
        bigquery.SchemaField("quantity", "FLOAT64"),
        bigquery.SchemaField("leverage", "FLOAT64"),
        bigquery.SchemaField("stop_loss", "FLOAT64"),
        bigquery.SchemaField("take_profit", "FLOAT64"),
        bigquery.SchemaField("pnl_paise", "INT64"),
        bigquery.SchemaField("pnl_percent", "FLOAT64"),
        bigquery.SchemaField("max_drawdown_percent", "FLOAT64"),
        bigquery.SchemaField("risk_per_trade_percent", "FLOAT64"),
        bigquery.SchemaField("survival_tier", "STRING"),
        bigquery.SchemaField("strategy", "STRING"),
        bigquery.SchemaField("market_regime", "STRING"),
        bigquery.SchemaField("news_context", "STRING"),
    ] if HAS_BIGQUERY else []
    
    SIGNALS_SCHEMA = [
        bigquery.SchemaField("signal_id", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("symbol", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        bigquery.SchemaField("signal_type", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("direction", "STRING", mode="REQUIRED"),
        bigquery.SchemaField("confidence", "FLOAT64"),
        bigquery.SchemaField("timeframe", "STRING"),
        bigquery.SchemaField("headline", "STRING"),
        bigquery.SchemaField("content", "STRING"),
        bigquery.SchemaField("source", "STRING"),
        bigquery.SchemaField("source_url", "STRING"),
        bigquery.SchemaField("was_traded", "BOOL"),
        bigquery.SchemaField("trade_id", "STRING"),
        bigquery.SchemaField("outcome_correct", "BOOL"),
        bigquery.SchemaField("price_at_signal", "FLOAT64"),
        bigquery.SchemaField("price_after_1h", "FLOAT64"),
        bigquery.SchemaField("price_after_24h", "FLOAT64"),
    ] if HAS_BIGQUERY else []
    
    def __init__(
        self,
        project_id: Optional[str] = None,
        dataset_id: str = "gemtrade",
        location: str = "US",  # Free tier is US-only
    ):
        if not HAS_BIGQUERY:
            raise ImportError(
                "google-cloud-bigquery not installed. "
                "Run: pip install google-cloud-bigquery"
            )
        
        self.project_id = project_id or os.getenv("GOOGLE_CLOUD_PROJECT")
        if not self.project_id:
            raise ValueError(
                "Project ID required. Set GOOGLE_CLOUD_PROJECT or pass project_id"
            )
        
        self.dataset_id = dataset_id
        self.location = location
        
        self.client = bigquery.Client(project=self.project_id)
        self.dataset_ref = f"{self.project_id}.{self.dataset_id}"
        
        # Ensure dataset and tables exist
        self._ensure_dataset()
        self._ensure_tables()
    
    def _ensure_dataset(self):
        """Create dataset if it doesn't exist."""
        dataset = bigquery.Dataset(self.dataset_ref)
        dataset.location = self.location
        
        try:
            self.client.get_dataset(self.dataset_ref)
        except NotFound:
            self.client.create_dataset(dataset)
    
    def _ensure_tables(self):
        """Create tables if they don't exist."""
        tables = {
            "trades": self.TRADES_SCHEMA,
            "signals": self.SIGNALS_SCHEMA,
        }
        
        for table_name, schema in tables.items():
            table_ref = f"{self.dataset_ref}.{table_name}"
            table = bigquery.Table(table_ref, schema=schema)
            
            try:
                self.client.get_table(table_ref)
            except NotFound:
                self.client.create_table(table)
    
    def insert_trade(self, trade: TradeRecord):
        """Insert a trade record."""
        table_ref = f"{self.dataset_ref}.trades"
        rows = [trade.to_dict()]
        
        errors = self.client.insert_rows_json(table_ref, rows)
        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")
    
    def insert_signal(self, signal: SignalRecord):
        """Insert a signal record."""
        table_ref = f"{self.dataset_ref}.signals"
        rows = [signal.to_dict()]
        
        errors = self.client.insert_rows_json(table_ref, rows)
        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")
    
    def insert_signals_batch(self, signals: List[SignalRecord]):
        """Insert multiple signals efficiently."""
        if not signals:
            return
        
        table_ref = f"{self.dataset_ref}.signals"
        rows = [s.to_dict() for s in signals]
        
        errors = self.client.insert_rows_json(table_ref, rows)
        if errors:
            raise Exception(f"BigQuery insert errors: {errors}")
    
    def update_signal_outcome(
        self,
        signal_id: str,
        outcome_correct: bool,
        price_after_1h: Optional[float] = None,
        price_after_24h: Optional[float] = None,
    ):
        """Update signal with outcome data."""
        query = f"""
        UPDATE `{self.dataset_ref}.signals`
        SET 
            outcome_correct = @outcome_correct,
            price_after_1h = @price_after_1h,
            price_after_24h = @price_after_24h
        WHERE signal_id = @signal_id
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("signal_id", "STRING", signal_id),
                bigquery.ScalarQueryParameter("outcome_correct", "BOOL", outcome_correct),
                bigquery.ScalarQueryParameter("price_after_1h", "FLOAT64", price_after_1h),
                bigquery.ScalarQueryParameter("price_after_24h", "FLOAT64", price_after_24h),
            ]
        )
        
        self.client.query(query, job_config=job_config).result()
    
    def get_performance_metrics(
        self,
        start_date: datetime,
        end_date: datetime,
        symbol: Optional[str] = None,
    ) -> PerformanceMetrics:
        """Calculate performance metrics for a period."""
        symbol_filter = f"AND symbol = '{symbol}'" if symbol else ""
        
        query = f"""
        SELECT
            COUNT(*) as total_trades,
            COUNTIF(pnl_paise > 0) as winning_trades,
            COUNTIF(pnl_paise < 0) as losing_trades,
            SUM(pnl_paise) as total_pnl_paise,
            SUM(IF(pnl_paise > 0, pnl_paise, 0)) as gross_profit_paise,
            SUM(IF(pnl_paise < 0, ABS(pnl_paise), 0)) as gross_loss_paise,
            AVG(IF(pnl_paise > 0, pnl_paise, NULL)) as avg_win_paise,
            AVG(IF(pnl_paise < 0, ABS(pnl_paise), NULL)) as avg_loss_paise,
            MAX(max_drawdown_percent) as max_drawdown_percent
        FROM `{self.dataset_ref}.trades`
        WHERE entry_time BETWEEN @start_date AND @end_date
            AND exit_time IS NOT NULL
            {symbol_filter}
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("start_date", "TIMESTAMP", start_date),
                bigquery.ScalarQueryParameter("end_date", "TIMESTAMP", end_date),
            ]
        )
        
        result = self.client.query(query, job_config=job_config).result()
        row = list(result)[0]
        
        total_trades = row.total_trades or 0
        winning_trades = row.winning_trades or 0
        gross_profit = row.gross_profit_paise or 0
        gross_loss = row.gross_loss_paise or 0
        
        metrics = PerformanceMetrics(
            period_start=start_date,
            period_end=end_date,
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=row.losing_trades or 0,
            total_pnl_paise=row.total_pnl_paise or 0,
            gross_profit_paise=gross_profit,
            gross_loss_paise=gross_loss,
            win_rate=winning_trades / total_trades if total_trades > 0 else 0,
            profit_factor=gross_profit / gross_loss if gross_loss > 0 else float('inf'),
            average_win_paise=int(row.avg_win_paise or 0),
            average_loss_paise=int(row.avg_loss_paise or 0),
            max_drawdown_percent=row.max_drawdown_percent or 0,
        )
        
        return metrics
    
    def get_signal_accuracy(
        self,
        days: int = 30,
        symbol: Optional[str] = None,
    ) -> Dict[str, float]:
        """Get accuracy by signal type."""
        symbol_filter = f"AND symbol = '{symbol}'" if symbol else ""
        
        query = f"""
        SELECT
            signal_type,
            COUNTIF(outcome_correct = TRUE) as correct,
            COUNTIF(outcome_correct = FALSE) as incorrect,
            COUNT(*) as total
        FROM `{self.dataset_ref}.signals`
        WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            AND outcome_correct IS NOT NULL
            {symbol_filter}
        GROUP BY signal_type
        """
        
        result = self.client.query(query).result()
        
        accuracy = {}
        for row in result:
            if row.total > 0:
                accuracy[row.signal_type] = row.correct / row.total
        
        return accuracy
    
    def get_best_performing_patterns(
        self,
        min_occurrences: int = 5,
        min_win_rate: float = 0.6,
    ) -> List[Dict]:
        """Find patterns that lead to successful trades."""
        query = f"""
        WITH signal_trades AS (
            SELECT
                s.signal_type,
                s.direction,
                s.confidence,
                s.source,
                t.pnl_paise > 0 as profitable
            FROM `{self.dataset_ref}.signals` s
            JOIN `{self.dataset_ref}.trades` t
                ON s.trade_id = t.trade_id
            WHERE s.was_traded = TRUE
                AND t.exit_time IS NOT NULL
        )
        SELECT
            signal_type,
            direction,
            ROUND(AVG(confidence), 2) as avg_confidence,
            source,
            COUNT(*) as occurrences,
            COUNTIF(profitable) as wins,
            ROUND(COUNTIF(profitable) / COUNT(*), 3) as win_rate
        FROM signal_trades
        GROUP BY signal_type, direction, source
        HAVING occurrences >= {min_occurrences}
            AND win_rate >= {min_win_rate}
        ORDER BY win_rate DESC, occurrences DESC
        LIMIT 20
        """
        
        result = self.client.query(query).result()
        
        patterns = []
        for row in result:
            patterns.append({
                "signal_type": row.signal_type,
                "direction": row.direction,
                "avg_confidence": row.avg_confidence,
                "source": row.source,
                "occurrences": row.occurrences,
                "wins": row.wins,
                "win_rate": row.win_rate,
            })
        
        return patterns
    
    def get_recent_trades(
        self,
        limit: int = 20,
        symbol: Optional[str] = None,
    ) -> List[Dict]:
        """Get recent trades."""
        symbol_filter = f"WHERE symbol = '{symbol}'" if symbol else ""
        
        query = f"""
        SELECT *
        FROM `{self.dataset_ref}.trades`
        {symbol_filter}
        ORDER BY entry_time DESC
        LIMIT {limit}
        """
        
        result = self.client.query(query).result()
        return [dict(row) for row in result]
    
    def get_daily_pnl(
        self,
        days: int = 30,
        symbol: Optional[str] = None,
    ) -> List[Dict]:
        """Get daily P&L for charting."""
        symbol_filter = f"AND symbol = '{symbol}'" if symbol else ""
        
        query = f"""
        SELECT
            DATE(exit_time) as date,
            SUM(pnl_paise) as pnl_paise,
            COUNT(*) as trades,
            COUNTIF(pnl_paise > 0) as wins
        FROM `{self.dataset_ref}.trades`
        WHERE exit_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            AND exit_time IS NOT NULL
            {symbol_filter}
        GROUP BY date
        ORDER BY date
        """
        
        result = self.client.query(query).result()
        return [dict(row) for row in result]


# Fallback for local development without BigQuery
class LocalStore:
    """Local JSON-based store for development/testing."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.trades_file = os.path.join(data_dir, "trades.json")
        self.signals_file = os.path.join(data_dir, "signals.json")
        
        self._trades = self._load_file(self.trades_file)
        self._signals = self._load_file(self.signals_file)
    
    def _load_file(self, path: str) -> List[Dict]:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
        return []
    
    def _save_file(self, path: str, data: List[Dict]):
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
    
    def insert_trade(self, trade: TradeRecord):
        self._trades.append(trade.to_dict())
        self._save_file(self.trades_file, self._trades)
    
    def insert_signal(self, signal: SignalRecord):
        self._signals.append(signal.to_dict())
        self._save_file(self.signals_file, self._signals)
    
    def insert_signals_batch(self, signals: List[SignalRecord]):
        for signal in signals:
            self._signals.append(signal.to_dict())
        self._save_file(self.signals_file, self._signals)


def get_store(use_bigquery: bool = True, **kwargs) -> Any:
    """Get appropriate store based on configuration."""
    if use_bigquery and HAS_BIGQUERY:
        try:
            return BigQueryStore(**kwargs)
        except Exception:
            pass
    
    return LocalStore(**kwargs)
