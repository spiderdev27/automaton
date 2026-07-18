"""
Exchange Factory

Creates exchange connectors based on configuration.
"""

from enum import Enum
from pathlib import Path
from typing import Optional

from gemtrade.exchanges.base import ExchangeConnector
from gemtrade.exchanges.paper import PaperExchange


class ExchangeType(Enum):
    """Supported exchange types."""
    PAPER = "paper"
    MT5 = "mt5"
    DELTA = "delta"
    FYERS = "fyers"
    GROWW = "groww"


def get_exchange(
    exchange_type: ExchangeType = ExchangeType.PAPER,
    project_root: Optional[Path] = None,
    **kwargs,
) -> ExchangeConnector:
    """
    Create an exchange connector.
    
    Args:
        exchange_type: Type of exchange
        project_root: Project root for state storage
        **kwargs: Exchange-specific arguments
        
    Returns:
        ExchangeConnector instance
    """
    if exchange_type == ExchangeType.PAPER:
        return PaperExchange(
            project_root=project_root,
            initial_balance_paise=kwargs.get("initial_balance_paise", 500_000),
            spread_pips=kwargs.get("spread_pips", 2.0),
            slippage_pips=kwargs.get("slippage_pips", 0.5),
        )
    
    elif exchange_type == ExchangeType.MT5:
        # MT5 connector (to be implemented)
        raise NotImplementedError(
            "MT5 connector not yet implemented. "
            "Use PAPER for testing."
        )
    
    elif exchange_type == ExchangeType.DELTA:
        # Delta Exchange connector (to be implemented)
        raise NotImplementedError(
            "Delta Exchange connector not yet implemented. "
            "Use PAPER for testing."
        )
    
    elif exchange_type == ExchangeType.FYERS:
        raise NotImplementedError(
            "Fyers connector not yet implemented. "
            "Use PAPER for testing."
        )
    
    elif exchange_type == ExchangeType.GROWW:
        raise NotImplementedError(
            "Groww connector not yet implemented. "
            "Use PAPER for testing."
        )
    
    else:
        raise ValueError(f"Unknown exchange type: {exchange_type}")
