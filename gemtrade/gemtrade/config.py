"""
GemTrade Configuration

Trading-specific configuration that extends GemCode's config system.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import json
import os


@dataclass
class ExchangeConfig:
    """Configuration for an exchange connector."""
    name: str
    type: str  # "paper", "oanda", "alpaca", "binance"
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    account_id: Optional[str] = None
    sandbox: bool = True  # Use sandbox/demo account
    
    @classmethod
    def paper(cls) -> "ExchangeConfig":
        """Create paper trading config."""
        return cls(name="paper", type="paper", sandbox=True)


@dataclass
class RiskConfig:
    """Risk management configuration."""
    # Position limits (can be stricter than constitution, not looser)
    max_position_pct: float = 5.0
    max_concurrent_positions: int = 3
    min_reserve_pct: float = 50.0
    
    # Loss limits
    max_daily_loss_pct: float = 3.0
    max_weekly_loss_pct: float = 10.0
    max_drawdown_pct: float = 20.0
    
    # Stop loss
    default_stop_loss_pct: float = 2.0  # 2% of entry price
    max_stop_loss_pct: float = 5.0
    
    # Circuit breaker
    consecutive_losses_pause: int = 5
    pause_duration_hours: int = 4


@dataclass
class StrategyConfig:
    """Configuration for trading strategies."""
    name: str
    enabled: bool = True
    symbols: List[str] = field(default_factory=lambda: ["XAU/USD"])
    timeframe: str = "H1"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradingConfig:
    """
    Complete trading configuration.
    
    This extends GemCode's config with trading-specific settings.
    """
    
    # Identity
    name: str = "gemtrade"
    
    # Symbols
    default_symbol: str = "XAU/USD"
    allowed_symbols: List[str] = field(default_factory=lambda: ["XAU/USD"])
    
    # Exchange
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig.paper)
    
    # Risk
    risk: RiskConfig = field(default_factory=RiskConfig)
    
    # Strategies
    strategies: List[StrategyConfig] = field(default_factory=list)
    
    # Initial capital (for paper trading)
    initial_balance_cents: int = 1000000  # $10,000
    
    # Paths
    state_path: Optional[Path] = None
    journal_path: Optional[Path] = None
    memory_path: Optional[Path] = None
    
    # Features
    enable_habits: bool = True
    enable_triggers: bool = True
    enable_learning: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_trades: bool = True
    
    def __post_init__(self):
        """Set default paths if not provided."""
        if self.state_path is None:
            self.state_path = Path(".gemcode/trading/state.json")
        if self.journal_path is None:
            self.journal_path = Path(".gemcode/trading/journal.jsonl")
        if self.memory_path is None:
            self.memory_path = Path(".gemcode/trading/memory/")
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "default_symbol": self.default_symbol,
            "allowed_symbols": self.allowed_symbols,
            "exchange": {
                "name": self.exchange.name,
                "type": self.exchange.type,
                "sandbox": self.exchange.sandbox,
            },
            "risk": {
                "max_position_pct": self.risk.max_position_pct,
                "max_concurrent_positions": self.risk.max_concurrent_positions,
                "min_reserve_pct": self.risk.min_reserve_pct,
                "max_daily_loss_pct": self.risk.max_daily_loss_pct,
                "max_weekly_loss_pct": self.risk.max_weekly_loss_pct,
                "max_drawdown_pct": self.risk.max_drawdown_pct,
            },
            "strategies": [
                {"name": s.name, "enabled": s.enabled, "symbols": s.symbols}
                for s in self.strategies
            ],
            "initial_balance_cents": self.initial_balance_cents,
            "enable_habits": self.enable_habits,
            "enable_triggers": self.enable_triggers,
            "enable_learning": self.enable_learning,
        }
    
    def save(self, path: Path) -> None:
        """Save config to disk."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.to_dict(), f, indent=2)
    
    @classmethod
    def from_dict(cls, data: dict) -> "TradingConfig":
        """Create from dictionary."""
        config = cls()
        
        if "name" in data:
            config.name = data["name"]
        if "default_symbol" in data:
            config.default_symbol = data["default_symbol"]
        if "allowed_symbols" in data:
            config.allowed_symbols = data["allowed_symbols"]
        
        if "exchange" in data:
            config.exchange = ExchangeConfig(**data["exchange"])
        
        if "risk" in data:
            config.risk = RiskConfig(**data["risk"])
        
        if "strategies" in data:
            config.strategies = [StrategyConfig(**s) for s in data["strategies"]]
        
        if "initial_balance_cents" in data:
            config.initial_balance_cents = data["initial_balance_cents"]
        
        return config
    
    @classmethod
    def load(cls, path: Path) -> "TradingConfig":
        """Load config from disk."""
        if not path.exists():
            return cls()
        with open(path) as f:
            data = json.load(f)
        return cls.from_dict(data)


def load_trading_config(project_root: Path) -> TradingConfig:
    """
    Load trading configuration from a project directory.
    
    Looks for config in:
    1. .gemcode/trading/config.json
    2. Environment variables (GEMTRADE_*)
    3. Defaults
    """
    config_path = project_root / ".gemcode" / "trading" / "config.json"
    
    if config_path.exists():
        config = TradingConfig.load(config_path)
    else:
        config = TradingConfig()
    
    # Override from environment variables
    if os.environ.get("GEMTRADE_SYMBOL"):
        config.default_symbol = os.environ["GEMTRADE_SYMBOL"]
    
    if os.environ.get("GEMTRADE_EXCHANGE"):
        config.exchange.type = os.environ["GEMTRADE_EXCHANGE"]
    
    if os.environ.get("GEMTRADE_SANDBOX"):
        config.exchange.sandbox = os.environ["GEMTRADE_SANDBOX"].lower() in ("true", "1", "yes")
    
    if os.environ.get("OANDA_API_KEY"):
        config.exchange.api_key = os.environ["OANDA_API_KEY"]
    
    if os.environ.get("OANDA_ACCOUNT_ID"):
        config.exchange.account_id = os.environ["OANDA_ACCOUNT_ID"]
    
    # Set paths relative to project root
    config.state_path = project_root / ".gemcode" / "trading" / "state.json"
    config.journal_path = project_root / ".gemcode" / "trading" / "journal.jsonl"
    config.memory_path = project_root / ".gemcode" / "trading" / "memory"
    
    return config


def create_default_config(project_root: Path) -> TradingConfig:
    """Create and save default configuration."""
    config = TradingConfig(
        strategies=[
            StrategyConfig(
                name="ema_crossover",
                enabled=True,
                symbols=["XAU/USD"],
                timeframe="H1",
                parameters={
                    "fast_period": 12,
                    "slow_period": 26,
                    "atr_period": 14,
                    "atr_multiplier_sl": 2.0,
                    "atr_multiplier_tp": 3.0,
                }
            )
        ]
    )
    
    config_path = project_root / ".gemcode" / "trading" / "config.json"
    config.save(config_path)
    
    return config
