"""
GemTrade CLI

Extends GemCode's CLI with trading-specific commands.
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from gemtrade import __version__
from gemtrade.config import load_trading_config, create_default_config
from gemtrade.core.survival import SurvivalManager, format_tier_status, get_survival_tier
from gemtrade.core.state import TradingState
from gemtrade.core.constitution import format_constitution


def main(args: Optional[list] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="gemtrade",
        description="GemTrade - Autonomous AI Trading Agent"
    )
    
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"gemtrade {__version__}"
    )
    
    parser.add_argument(
        "-C", "--project",
        type=Path,
        default=Path.cwd(),
        help="Project directory (default: current directory)"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Status command
    status_parser = subparsers.add_parser("status", help="Show trading status")
    
    # Constitution command
    const_parser = subparsers.add_parser("constitution", help="Show trading constitution")
    
    # Init command
    init_parser = subparsers.add_parser("init", help="Initialize trading configuration")
    
    # Journal command
    journal_parser = subparsers.add_parser("journal", help="Show trade journal")
    journal_parser.add_argument("-n", "--limit", type=int, default=20, help="Number of trades")
    
    # Run command (main trading mode)
    run_parser = subparsers.add_parser("run", help="Run trading mode")
    run_parser.add_argument("--super", action="store_true", help="Enable super mode")
    run_parser.add_argument("--paper", action="store_true", help="Paper trading only")
    
    parsed = parser.parse_args(args)
    
    if parsed.command == "status":
        return cmd_status(parsed.project)
    elif parsed.command == "constitution":
        return cmd_constitution()
    elif parsed.command == "init":
        return cmd_init(parsed.project)
    elif parsed.command == "journal":
        return cmd_journal(parsed.project, parsed.limit)
    elif parsed.command == "run":
        return cmd_run(parsed.project, getattr(parsed, "super", False), parsed.paper)
    else:
        parser.print_help()
        return 0


def cmd_status(project: Path) -> int:
    """Show trading status."""
    print(f"GemTrade v{__version__}")
    print("=" * 50)
    
    # Load config
    config = load_trading_config(project)
    print(f"\nProject: {project}")
    print(f"Symbol: {config.default_symbol}")
    print(f"Exchange: {config.exchange.type} ({'sandbox' if config.exchange.sandbox else 'live'})")
    
    # Load state
    state = TradingState.load(config.state_path)
    
    # Survival tier
    tier = get_survival_tier(state.balance_cents)
    print(f"\n{format_tier_status(tier, state.balance_cents)}")
    
    # Positions
    print(f"\nOpen Positions: {len(state.open_positions)}")
    for pos in state.open_positions:
        pnl_sign = "+" if pos.unrealized_pnl >= 0 else ""
        print(f"  {pos.symbol} {pos.direction.upper()} @ {pos.entry_price:.2f}")
        print(f"    P&L: {pnl_sign}{pos.unrealized_pnl:.2f} ({pnl_sign}{pos.unrealized_pnl_pct:.2f}%)")
    
    # Today's stats
    print(f"\nToday:")
    print(f"  Trades: {state.trades_today}")
    print(f"  P&L: ${state.daily_pnl_cents / 100:.2f} ({state.daily_loss_pct:+.2f}%)")
    
    # Circuit breakers
    if state.circuit_breaker_active:
        print(f"\n⚠️  Circuit Breaker: {state.circuit_breaker_active}")
        if state.circuit_breaker_until:
            print(f"    Until: {state.circuit_breaker_until}")
    
    if state.trading_halted:
        print(f"\n🛑 TRADING HALTED: {state.halt_reason}")
    
    return 0


def cmd_constitution() -> int:
    """Show trading constitution."""
    print(format_constitution())
    return 0


def cmd_init(project: Path) -> int:
    """Initialize trading configuration."""
    config_path = project / ".gemcode" / "trading" / "config.json"
    
    if config_path.exists():
        print(f"Configuration already exists: {config_path}")
        return 1
    
    config = create_default_config(project)
    print(f"Created trading configuration: {config_path}")
    print(f"\nDefault settings:")
    print(f"  Symbol: {config.default_symbol}")
    print(f"  Exchange: {config.exchange.type}")
    print(f"  Initial Balance: ${config.initial_balance_cents / 100:.2f}")
    print(f"\nStrategies:")
    for strat in config.strategies:
        print(f"  - {strat.name} ({'enabled' if strat.enabled else 'disabled'})")
    
    return 0


def cmd_journal(project: Path, limit: int) -> int:
    """Show trade journal."""
    config = load_trading_config(project)
    
    if not config.journal_path.exists():
        print("No trades recorded yet.")
        return 0
    
    import json
    trades = []
    with open(config.journal_path) as f:
        for line in f:
            trades.append(json.loads(line))
    
    trades = trades[-limit:]
    
    print(f"Last {len(trades)} trades:")
    print("-" * 60)
    
    for trade in trades:
        pnl = trade.get("profit_loss", 0)
        pnl_pct = trade.get("profit_loss_pct", 0)
        symbol = trade.get("symbol", "???")
        direction = trade.get("direction", "???").upper()
        strategy = trade.get("strategy", "???")
        
        result = "✅" if pnl >= 0 else "❌"
        pnl_sign = "+" if pnl >= 0 else ""
        
        print(f"{result} {symbol} {direction} | {strategy}")
        print(f"   P&L: {pnl_sign}${pnl:.2f} ({pnl_sign}{pnl_pct:.2f}%)")
        print()
    
    return 0


def cmd_run(project: Path, super_mode: bool, paper: bool) -> int:
    """Run trading mode."""
    print(f"GemTrade v{__version__}")
    print("=" * 50)
    
    # This would integrate with GemCode's runtime
    print("\n⚠️  Trading mode not yet implemented.")
    print("   This will integrate with GemCode's agent mesh.")
    print("\nPlanned features:")
    print("  - Register trading agents as GemCode org members")
    print("  - Start trading habits (market scan, position check)")
    print("  - Enable trading triggers (signal validation, trade learning)")
    print("  - Begin trading loop with constitutional enforcement")
    
    if super_mode:
        print("\n🚀 Super mode: Would enable all trading capabilities")
    if paper:
        print("📝 Paper trading: Would use simulated execution")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
