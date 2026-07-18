"""
GemTrade Configuration

Trading-specific configuration for Indian markets with:
- INR 5,000 starting capital
- High leverage support (1:100 to 1:2000)
- Delta Exchange (crypto) and MT5 (forex/gold) connectors
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
    type: str  # "paper", "delta", "mt5"
    
    # API credentials (loaded from env or secrets)
    api_key: Optional[str] = None
    api_secret: Optional[str] = None
    
    # MT5 specific
    mt5_login: Optional[int] = None
    mt5_password: Optional[str] = None
    mt5_server: Optional[str] = None
    mt5_path: Optional[str] = None  # Path to MT5 terminal
    
    # Delta Exchange specific
    delta_account_id: Optional[str] = None
    
    # Environment
    sandbox: bool = True  # Use testnet/demo account
    
    @classmethod
    def paper(cls, currency: str = "INR") -> "ExchangeConfig":
        """Create paper trading config."""
        return cls(name="paper", type="paper", sandbox=True)
    
    @classmethod
    def delta_testnet(cls) -> "ExchangeConfig":
        """Create Delta Exchange testnet config."""
        return cls(
            name="delta-testnet",
            type="delta",
            sandbox=True,
            api_key=os.environ.get("DELTA_API_KEY"),
            api_secret=os.environ.get("DELTA_API_SECRET"),
        )
    
    @classmethod
    def delta_live(cls) -> "ExchangeConfig":
        """Create Delta Exchange live config."""
        return cls(
            name="delta-live",
            type="delta",
            sandbox=False,
            api_key=os.environ.get("DELTA_API_KEY"),
            api_secret=os.environ.get("DELTA_API_SECRET"),
        )
    
    @classmethod
    def mt5_demo(cls) -> "ExchangeConfig":
        """Create MT5 demo config."""
        return cls(
            name="mt5-demo",
            type="mt5",
            sandbox=True,
            mt5_login=int(os.environ.get("MT5_LOGIN", 0)),
            mt5_password=os.environ.get("MT5_PASSWORD"),
            mt5_server=os.environ.get("MT5_SERVER"),
            mt5_path=os.environ.get("MT5_PATH"),
        )


@dataclass
class LeverageConfig:
    """
    Leverage management configuration.
    
    With ₹5,000 and broker offering 1:2000, USE IT AGGRESSIVELY:
    - High leverage = small margin required = more trades possible
    - Risk is controlled by STOP LOSS, not by leverage
    - Leverage just determines margin, stop loss determines risk
    """
    
    # Broker maximum (what's available)
    broker_max_leverage: int = 2000
    
    # Our limits per tier - AGGRESSIVE
    starting_max_leverage: int = 500    # NORMAL tier - use good leverage from start
    earned_max_leverage: int = 1000     # HIGH tier - near max after proving profits
    reduced_leverage: int = 200         # LOW tier - still decent
    critical_leverage: int = 100        # CRITICAL tier - reduced but usable
    
    # Leverage scaling rules
    consecutive_wins_to_increase: int = 3   # Faster scaling up
    consecutive_losses_to_decrease: int = 2  # Quick to protect
    leverage_increase_step: int = 100   # Increase by 100x per step
    leverage_decrease_step: int = 100   # Decrease by 100x per step


@dataclass
class RiskConfig:
    """
    Risk management configuration for small capital (₹5,000) + high leverage.
    
    AGGRESSIVE BUT SMART:
    - Higher per-trade risk (5-10%) to make meaningful gains
    - Circuit breakers to prevent account wipeout
    - Stop losses are MANDATORY - risk is controlled by stop distance
    """
    
    # Position limits
    max_position_pct: float = 20.0      # Can use up to 20% per position with leverage
    max_concurrent_positions: int = 2   # Max 2 positions with INR 5,000
    min_reserve_pct: float = 30.0       # Keep 30% cash (more aggressive)
    
    # Loss limits (circuit breakers)
    max_daily_loss_pct: float = 15.0    # 15% daily = ₹750, then STOP for day
    max_weekly_loss_pct: float = 25.0   # 25% weekly = ₹1,250, then STOP for week  
    max_drawdown_pct: float = 40.0      # 40% drawdown = ₹2,000, emergency halt
    
    # Per-trade risk (AGGRESSIVE for small capital growth)
    max_risk_per_trade_pct: float = 10.0  # Risk up to 10% = ₹500 per trade
    default_risk_per_trade_pct: float = 5.0  # Default 5% = ₹250 per trade
    min_risk_per_trade_pct: float = 2.0   # Minimum 2% = ₹100 per trade
    
    # Stop loss (MANDATORY - this controls actual risk)
    default_stop_loss_pct: float = 1.0   # 1% of entry price
    min_stop_loss_pct: float = 0.3       # Minimum 0.3% (tight stops with leverage)
    max_stop_loss_pct: float = 3.0       # Maximum 3%
    
    # Circuit breakers
    consecutive_losses_pause: int = 4    # Pause after 4 losses
    pause_duration_hours: int = 2        # 2 hour cooldown
    
    # Leverage config
    leverage: LeverageConfig = field(default_factory=LeverageConfig)


@dataclass
class StrategyConfig:
    """Configuration for trading strategies."""
    name: str
    enabled: bool = True
    symbols: List[str] = field(default_factory=lambda: ["XAUUSD"])  # MT5 format
    timeframe: str = "H1"
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TradingConfig:
    """
    Complete trading configuration for Indian markets.
    
    Defaults:
    - Currency: INR
    - Starting capital: INR 5,000
    - Primary symbol: XAU/USD (gold)
    - Exchange: Paper trading (demo)
    """
    
    # Identity
    name: str = "gemtrade"
    
    # Currency (affects survival tier thresholds)
    currency: str = "INR"
    
    # Symbols
    default_symbol: str = "XAUUSD"  # Gold on MT5
    allowed_symbols: List[str] = field(default_factory=lambda: [
        "XAUUSD",    # Gold/USD (primary focus)
        "BTCUSD",    # Bitcoin/USD (Delta Exchange)
        "ETHUSD",    # Ethereum/USD (Delta Exchange)
    ])
    
    # Exchange configurations
    primary_exchange: ExchangeConfig = field(default_factory=ExchangeConfig.paper)
    exchanges: Dict[str, ExchangeConfig] = field(default_factory=dict)
    
    # Risk
    risk: RiskConfig = field(default_factory=RiskConfig)
    
    # Strategies
    strategies: List[StrategyConfig] = field(default_factory=list)
    
    # Initial capital (INR 5,000 = 500000 paise)
    initial_balance_paise: int = 500000  # INR 5,000
    
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
        """Set default paths and strategies if not provided."""
        if self.state_path is None:
            self.state_path = Path(".gemcode/trading/state.json")
        if self.journal_path is None:
            self.journal_path = Path(".gemcode/trading/journal.jsonl")
        if self.memory_path is None:
            self.memory_path = Path(".gemcode/trading/memory/")
            
        # Default strategy if none provided
        if not self.strategies:
            self.strategies = [
                StrategyConfig(
                    name="ema_crossover",
                    enabled=True,
                    symbols=["XAUUSD"],
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
    
    @property
    def initial_balance_display(self) -> str:
        """Display initial balance in human readable format."""
        if self.currency == "INR":
            return f"₹{self.initial_balance_paise / 100:,.2f}"
        return f"${self.initial_balance_paise / 100:.2f}"
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "currency": self.currency,
            "default_symbol": self.default_symbol,
            "allowed_symbols": self.allowed_symbols,
            "primary_exchange": {
                "name": self.primary_exchange.name,
                "type": self.primary_exchange.type,
                "sandbox": self.primary_exchange.sandbox,
            },
            "risk": {
                "max_position_pct": self.risk.max_position_pct,
                "max_concurrent_positions": self.risk.max_concurrent_positions,
                "min_reserve_pct": self.risk.min_reserve_pct,
                "max_daily_loss_pct": self.risk.max_daily_loss_pct,
                "max_weekly_loss_pct": self.risk.max_weekly_loss_pct,
                "max_drawdown_pct": self.risk.max_drawdown_pct,
                "max_risk_per_trade_pct": self.risk.max_risk_per_trade_pct,
                "leverage": {
                    "broker_max": self.risk.leverage.broker_max_leverage,
                    "starting_max": self.risk.leverage.starting_max_leverage,
                    "earned_max": self.risk.leverage.earned_max_leverage,
                }
            },
            "strategies": [
                {"name": s.name, "enabled": s.enabled, "symbols": s.symbols}
                for s in self.strategies
            ],
            "initial_balance_paise": self.initial_balance_paise,
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
        if "currency" in data:
            config.currency = data["currency"]
        if "default_symbol" in data:
            config.default_symbol = data["default_symbol"]
        if "allowed_symbols" in data:
            config.allowed_symbols = data["allowed_symbols"]
        
        if "primary_exchange" in data:
            config.primary_exchange = ExchangeConfig(**data["primary_exchange"])
        
        if "risk" in data:
            risk_data = data["risk"]
            if "leverage" in risk_data:
                leverage = LeverageConfig(**risk_data.pop("leverage"))
                risk_data["leverage"] = leverage
            config.risk = RiskConfig(**risk_data)
        
        if "strategies" in data:
            config.strategies = [StrategyConfig(**s) for s in data["strategies"]]
        
        if "initial_balance_paise" in data:
            config.initial_balance_paise = data["initial_balance_paise"]
        
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
    if os.environ.get("GEMTRADE_CURRENCY"):
        config.currency = os.environ["GEMTRADE_CURRENCY"]
    
    if os.environ.get("GEMTRADE_SYMBOL"):
        config.default_symbol = os.environ["GEMTRADE_SYMBOL"]
    
    if os.environ.get("GEMTRADE_EXCHANGE"):
        config.primary_exchange.type = os.environ["GEMTRADE_EXCHANGE"]
    
    if os.environ.get("GEMTRADE_SANDBOX"):
        config.primary_exchange.sandbox = os.environ["GEMTRADE_SANDBOX"].lower() in ("true", "1", "yes")
    
    if os.environ.get("GEMTRADE_INITIAL_BALANCE"):
        config.initial_balance_paise = int(os.environ["GEMTRADE_INITIAL_BALANCE"])
    
    # Delta Exchange credentials
    if os.environ.get("DELTA_API_KEY"):
        config.primary_exchange.api_key = os.environ["DELTA_API_KEY"]
    if os.environ.get("DELTA_API_SECRET"):
        config.primary_exchange.api_secret = os.environ["DELTA_API_SECRET"]
    
    # MT5 credentials
    if os.environ.get("MT5_LOGIN"):
        config.primary_exchange.mt5_login = int(os.environ["MT5_LOGIN"])
    if os.environ.get("MT5_PASSWORD"):
        config.primary_exchange.mt5_password = os.environ["MT5_PASSWORD"]
    if os.environ.get("MT5_SERVER"):
        config.primary_exchange.mt5_server = os.environ["MT5_SERVER"]
    
    # Set paths relative to project root
    config.state_path = project_root / ".gemcode" / "trading" / "state.json"
    config.journal_path = project_root / ".gemcode" / "trading" / "journal.jsonl"
    config.memory_path = project_root / ".gemcode" / "trading" / "memory"
    
    return config


def create_default_config(project_root: Path, 
                          currency: str = "INR",
                          initial_balance_paise: int = 500000) -> TradingConfig:
    """
    Create and save default configuration.
    
    Args:
        project_root: Project directory
        currency: "INR" or "USD"
        initial_balance_paise: Starting balance (default INR 5,000)
    """
    config = TradingConfig(
        currency=currency,
        initial_balance_paise=initial_balance_paise,
        strategies=[
            StrategyConfig(
                name="ema_crossover",
                enabled=True,
                symbols=["XAUUSD"],
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


# ═══════════════════════════════════════════════════════════════════════════════
# Exchange URL Constants
# ═══════════════════════════════════════════════════════════════════════════════

DELTA_EXCHANGE_URLS = {
    "production_india": "https://api.india.delta.exchange",
    "testnet_india": "https://cdn-ind.testnet.deltaex.org",
    "production_global": "https://api.delta.exchange",
    "testnet_global": "https://testnet-api.delta.exchange",
}

MT5_DEFAULT_PATHS = {
    "windows": r"C:\Program Files\MetaTrader 5\terminal64.exe",
    "wine": "~/.wine/drive_c/Program Files/MetaTrader 5/terminal64.exe",
}
