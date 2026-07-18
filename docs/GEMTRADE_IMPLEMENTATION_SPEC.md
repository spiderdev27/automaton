# GemTrade: Technical Implementation Specification

**Version**: 0.1.0  
**Status**: Design Document  
**Based on**: Automaton v0.2.1 Architecture

---

## 1. Architecture Overview

### 1.1 Integration with Automaton

GemTrade extends Automaton rather than replacing it. Key integration points:

```
automaton/
├── src/
│   ├── agent/
│   │   ├── loop.ts              # Extended with trading hooks
│   │   └── policy-engine.ts     # Add trading-specific policies
│   ├── memory/
│   │   ├── trading/             # NEW: Trading-specific memory
│   │   │   ├── trade-journal.ts
│   │   │   ├── regime-memory.ts
│   │   │   └── procedural-trading.ts
│   │   └── ingestion.ts         # Extend with trade processing
│   ├── trading/                 # NEW: Trading subsystem
│   │   ├── overseer.ts
│   │   ├── analyst.ts
│   │   ├── strategist.ts
│   │   ├── executor.ts
│   │   ├── learner.ts
│   │   ├── exchange/
│   │   │   ├── connector.ts
│   │   │   ├── oanda.ts
│   │   │   └── paper.ts
│   │   ├── strategies/
│   │   │   ├── base.ts
│   │   │   ├── ema-crossover.ts
│   │   │   └── regime-adaptive.ts
│   │   ├── indicators/
│   │   │   ├── ema.ts
│   │   │   ├── rsi.ts
│   │   │   └── atr.ts
│   │   └── risk/
│   │       ├── position-sizer.ts
│   │       ├── circuit-breakers.ts
│   │       └── limits.ts
│   └── types.ts                 # Extended with trading types
```

### 1.2 New Database Schema

Extending `src/state/schema.ts`:

```typescript
// ─── Trading Schema (V10) ────────────────────────────────────────

export const SCHEMA_V10_TRADING = `
-- Market Data Cache
CREATE TABLE IF NOT EXISTS market_data (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  timeframe TEXT NOT NULL,
  timestamp TEXT NOT NULL,
  open REAL NOT NULL,
  high REAL NOT NULL,
  low REAL NOT NULL,
  close REAL NOT NULL,
  volume REAL,
  created_at TEXT DEFAULT (datetime('now')),
  UNIQUE(symbol, timeframe, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_market_data_symbol_time 
  ON market_data(symbol, timeframe, timestamp DESC);

-- Trade Journal (Episodic Memory for Trading)
CREATE TABLE IF NOT EXISTS trade_journal (
  id TEXT PRIMARY KEY,
  session_id TEXT NOT NULL,
  symbol TEXT NOT NULL,
  direction TEXT NOT NULL CHECK (direction IN ('long', 'short')),
  strategy_name TEXT NOT NULL,
  
  -- Entry
  entry_timestamp TEXT NOT NULL,
  entry_price REAL NOT NULL,
  entry_reason_code TEXT NOT NULL,
  market_regime_at_entry TEXT,
  
  -- Exit
  exit_timestamp TEXT,
  exit_price REAL,
  exit_reason_code TEXT,
  
  -- Position management
  position_size REAL NOT NULL,
  position_value REAL NOT NULL,
  initial_stop_loss REAL NOT NULL,
  initial_take_profit REAL,
  stop_loss_moved INTEGER DEFAULT 0,
  take_profit_moved INTEGER DEFAULT 0,
  
  -- Outcome
  profit_loss REAL,
  profit_loss_percent REAL,
  max_adverse_excursion REAL,
  max_favorable_excursion REAL,
  hold_duration_seconds INTEGER,
  
  -- Process evaluation
  followed_rules INTEGER NOT NULL DEFAULT 1,
  entry_quality_score REAL CHECK (entry_quality_score BETWEEN 0 AND 1),
  exit_quality_score REAL CHECK (exit_quality_score BETWEEN 0 AND 1),
  behavioral_flags TEXT DEFAULT '[]',
  
  -- Learning
  lesson_learned TEXT,
  pattern_identified TEXT,
  should_have_done TEXT,
  
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_trade_journal_symbol ON trade_journal(symbol);
CREATE INDEX IF NOT EXISTS idx_trade_journal_strategy ON trade_journal(strategy_name);
CREATE INDEX IF NOT EXISTS idx_trade_journal_time ON trade_journal(entry_timestamp DESC);

-- Market Regime Memory
CREATE TABLE IF NOT EXISTS market_regime_memory (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  regime_type TEXT NOT NULL,
  volatility_percentile REAL,
  trend_strength REAL,
  strategy_performance TEXT DEFAULT '{}',
  trades_in_regime INTEGER DEFAULT 0,
  win_rate_in_regime REAL,
  avg_profit_in_regime REAL,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  duration_hours REAL,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_regime_symbol_time 
  ON market_regime_memory(symbol, started_at DESC);

-- Procedural Trading Memory (The "Feeling" System)
CREATE TABLE IF NOT EXISTS procedural_trading_memory (
  id TEXT PRIMARY KEY,
  condition_type TEXT NOT NULL,
  condition_params TEXT DEFAULT '{}',
  adjustment_type TEXT NOT NULL,
  adjustment_magnitude REAL,
  supporting_trades INTEGER DEFAULT 0,
  outcome_when_applied REAL,
  outcome_when_ignored REAL,
  confidence REAL DEFAULT 0.5,
  last_validated_at TEXT,
  enabled INTEGER DEFAULT 1,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_procedural_condition 
  ON procedural_trading_memory(condition_type, enabled);

-- Trading Error Patterns
CREATE TABLE IF NOT EXISTS trading_error_patterns (
  id TEXT PRIMARY KEY,
  error_type TEXT NOT NULL,
  error_context TEXT DEFAULT '{}',
  occurrence_count INTEGER DEFAULT 1,
  total_loss_from_error REAL DEFAULT 0,
  early_warning_signs TEXT DEFAULT '[]',
  prevention_rule TEXT,
  prevention_effective INTEGER DEFAULT 0,
  first_occurred_at TEXT NOT NULL,
  last_occurred_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_error_type ON trading_error_patterns(error_type);

-- Trading State
CREATE TABLE IF NOT EXISTS trading_state (
  id TEXT PRIMARY KEY DEFAULT 'singleton',
  is_trading_enabled INTEGER DEFAULT 0,
  current_regime TEXT,
  daily_pnl_cents INTEGER DEFAULT 0,
  weekly_pnl_cents INTEGER DEFAULT 0,
  current_drawdown_percent REAL DEFAULT 0,
  trades_today INTEGER DEFAULT 0,
  consecutive_losses INTEGER DEFAULT 0,
  last_trade_at TEXT,
  circuit_breaker_active TEXT,
  circuit_breaker_until TEXT,
  updated_at TEXT DEFAULT (datetime('now'))
);

-- Open Positions
CREATE TABLE IF NOT EXISTS open_positions (
  id TEXT PRIMARY KEY,
  symbol TEXT NOT NULL,
  direction TEXT NOT NULL,
  entry_price REAL NOT NULL,
  current_price REAL,
  position_size REAL NOT NULL,
  unrealized_pnl REAL DEFAULT 0,
  stop_loss REAL NOT NULL,
  take_profit REAL,
  opened_at TEXT NOT NULL,
  updated_at TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_open_positions_symbol ON open_positions(symbol);
`;
```

---

## 2. Type Definitions

Adding to `src/types.ts`:

```typescript
// ─── Trading Types ───────────────────────────────────────────────

export type MarketRegime = 
  | 'trending_up' 
  | 'trending_down' 
  | 'ranging' 
  | 'volatile' 
  | 'quiet'
  | 'unknown';

export type TradeDirection = 'long' | 'short';

export type TradeStatus = 'pending' | 'open' | 'closed' | 'cancelled';

export type ExitReason = 
  | 'stop_loss'
  | 'take_profit'
  | 'trailing_stop'
  | 'strategy_signal'
  | 'time_stop'
  | 'manual'
  | 'circuit_breaker'
  | 'overseer_halt';

export type BehavioralFlag =
  | 'moved_stop'
  | 'removed_stop'
  | 'overleveraged'
  | 'revenge_trade'
  | 'fomo_entry'
  | 'early_exit'
  | 'late_exit'
  | 'ignored_signal'
  | 'traded_against_regime';

export interface OHLCV {
  timestamp: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface TradeSignal {
  symbol: string;
  direction: TradeDirection;
  entryPrice: number;
  stopLoss: number;
  takeProfit?: number;
  positionSize: number;
  strategy: string;
  confidence: number;
  reason: string;
  marketRegime: MarketRegime;
  timestamp: Date;
}

export interface Trade {
  id: string;
  symbol: string;
  direction: TradeDirection;
  status: TradeStatus;
  strategy: string;
  
  // Entry
  entryPrice: number;
  entryTime: Date;
  entryReason: string;
  
  // Position
  positionSize: number;
  positionValue: number;
  stopLoss: number;
  takeProfit?: number;
  
  // Exit
  exitPrice?: number;
  exitTime?: Date;
  exitReason?: ExitReason;
  
  // Outcome
  profitLoss?: number;
  profitLossPercent?: number;
  maxAdverseExcursion?: number;
  maxFavorableExcursion?: number;
  
  // Process Evaluation
  followedRules: boolean;
  entryQualityScore?: number;
  exitQualityScore?: number;
  behavioralFlags: BehavioralFlag[];
}

export interface TradingConfig {
  // Symbols
  allowedSymbols: string[];
  defaultSymbol: string;
  
  // Risk Management (Constitutional - cannot be modified by agents)
  maxPositionSizePercent: number;
  maxDailyLossPercent: number;
  maxWeeklyLossPercent: number;
  maxDrawdownPercent: number;
  maxLeverageMultiple: number;
  maxConcurrentPositions: number;
  requiredMinimumReserve: number;
  
  // Dynamic (can be adjusted by Strategist within bounds)
  positionSizeRange: [number, number];
  stopLossRange: [number, number];
  takeProfitRange: [number, number];
  
  // Circuit Breakers
  consecutiveLossesForPause: number;
  pauseDurationMinutes: number;
  drawdownForSizeReduction: number;
  
  // Exchange
  exchangeType: 'paper' | 'oanda' | 'alpaca';
  exchangeCredentials?: Record<string, string>;
}

export const DEFAULT_TRADING_CONFIG: TradingConfig = {
  allowedSymbols: ['XAU/USD'],
  defaultSymbol: 'XAU/USD',
  
  maxPositionSizePercent: 5,
  maxDailyLossPercent: 3,
  maxWeeklyLossPercent: 10,
  maxDrawdownPercent: 20,
  maxLeverageMultiple: 10,
  maxConcurrentPositions: 3,
  requiredMinimumReserve: 0.5,
  
  positionSizeRange: [0.5, 5],
  stopLossRange: [10, 100],
  takeProfitRange: [20, 500],
  
  consecutiveLossesForPause: 5,
  pauseDurationMinutes: 240,
  drawdownForSizeReduction: 10,
  
  exchangeType: 'paper',
};

// Procedural Memory for "Feeling"
export interface TradingProceduralMemory {
  id: string;
  conditionType: string;
  conditionParams: Record<string, unknown>;
  adjustmentType: string;
  adjustmentMagnitude: number;
  supportingTrades: number;
  outcomeWhenApplied: number;
  outcomeWhenIgnored: number;
  confidence: number;
  enabled: boolean;
}

// Trading State (singleton)
export interface TradingState {
  isTradingEnabled: boolean;
  currentRegime: MarketRegime;
  dailyPnlCents: number;
  weeklyPnlCents: number;
  currentDrawdownPercent: number;
  tradesToday: number;
  consecutiveLosses: number;
  lastTradeAt: Date | null;
  circuitBreakerActive: string | null;
  circuitBreakerUntil: Date | null;
}
```

---

## 3. Core Components

### 3.1 Overseer Agent

The Overseer enforces constitutional limits and cannot be overridden.

```typescript
// src/trading/overseer.ts

import type { TradingConfig, TradingState, TradeSignal, Trade } from '../types.js';
import { createLogger } from '../observability/logger.js';

const logger = createLogger('trading.overseer');

export class TradingOverseer {
  private config: TradingConfig;
  
  constructor(config: TradingConfig) {
    this.config = Object.freeze({ ...config }); // Immutable
  }
  
  /**
   * Validate a trade signal against constitutional limits.
   * Returns null if approved, or an error message if rejected.
   */
  validateSignal(
    signal: TradeSignal,
    state: TradingState,
    accountBalance: number,
    openPositions: Trade[]
  ): string | null {
    // Check if trading is enabled
    if (!state.isTradingEnabled) {
      return 'OVERSEER: Trading is disabled';
    }
    
    // Check circuit breakers
    if (state.circuitBreakerActive && state.circuitBreakerUntil) {
      if (new Date() < state.circuitBreakerUntil) {
        return `OVERSEER: Circuit breaker active until ${state.circuitBreakerUntil}`;
      }
    }
    
    // Check daily loss limit
    const dailyLossPercent = Math.abs(state.dailyPnlCents) / (accountBalance * 100);
    if (state.dailyPnlCents < 0 && dailyLossPercent >= this.config.maxDailyLossPercent) {
      return `OVERSEER: Daily loss limit reached (${dailyLossPercent.toFixed(2)}%)`;
    }
    
    // Check weekly loss limit
    const weeklyLossPercent = Math.abs(state.weeklyPnlCents) / (accountBalance * 100);
    if (state.weeklyPnlCents < 0 && weeklyLossPercent >= this.config.maxWeeklyLossPercent) {
      return `OVERSEER: Weekly loss limit reached (${weeklyLossPercent.toFixed(2)}%)`;
    }
    
    // Check drawdown
    if (state.currentDrawdownPercent >= this.config.maxDrawdownPercent) {
      return `OVERSEER: Maximum drawdown reached (${state.currentDrawdownPercent.toFixed(2)}%)`;
    }
    
    // Check position size
    const positionSizePercent = (signal.positionSize * signal.entryPrice) / accountBalance * 100;
    if (positionSizePercent > this.config.maxPositionSizePercent) {
      return `OVERSEER: Position size ${positionSizePercent.toFixed(2)}% exceeds max ${this.config.maxPositionSizePercent}%`;
    }
    
    // Check concurrent positions
    if (openPositions.length >= this.config.maxConcurrentPositions) {
      return `OVERSEER: Maximum concurrent positions (${this.config.maxConcurrentPositions}) reached`;
    }
    
    // Check minimum reserve
    const totalExposure = openPositions.reduce((sum, p) => sum + p.positionValue, 0);
    const proposedExposure = totalExposure + (signal.positionSize * signal.entryPrice);
    const reserveRatio = (accountBalance - proposedExposure) / accountBalance;
    if (reserveRatio < this.config.requiredMinimumReserve) {
      return `OVERSEER: Trade would violate minimum reserve requirement (${(reserveRatio * 100).toFixed(2)}% < ${this.config.requiredMinimumReserve * 100}%)`;
    }
    
    // Check symbol is allowed
    if (!this.config.allowedSymbols.includes(signal.symbol)) {
      return `OVERSEER: Symbol ${signal.symbol} is not in allowed list`;
    }
    
    // Check stop loss is set
    if (!signal.stopLoss || signal.stopLoss <= 0) {
      return 'OVERSEER: Stop loss is required for all trades';
    }
    
    logger.info('Trade signal approved by Overseer', {
      symbol: signal.symbol,
      direction: signal.direction,
      positionSize: signal.positionSize,
    });
    
    return null; // Approved
  }
  
  /**
   * Check if circuit breaker should be activated.
   */
  checkCircuitBreakers(state: TradingState): {
    shouldActivate: boolean;
    breakerType: string | null;
    duration: number;
  } {
    // Consecutive losses
    if (state.consecutiveLosses >= this.config.consecutiveLossesForPause) {
      return {
        shouldActivate: true,
        breakerType: 'consecutive_losses',
        duration: this.config.pauseDurationMinutes * 60 * 1000,
      };
    }
    
    // Drawdown threshold for size reduction (not full stop)
    if (state.currentDrawdownPercent >= this.config.drawdownForSizeReduction) {
      return {
        shouldActivate: true,
        breakerType: 'drawdown_warning',
        duration: 60 * 60 * 1000, // 1 hour
      };
    }
    
    return { shouldActivate: false, breakerType: null, duration: 0 };
  }
  
  /**
   * EMERGENCY: Halt all trading immediately.
   * This can be triggered by any agent but cannot be undone without human intervention.
   */
  emergencyHalt(reason: string): void {
    logger.error('EMERGENCY HALT ACTIVATED', { reason });
    // This would update the database and potentially alert humans
    throw new Error(`TRADING HALTED: ${reason}`);
  }
}
```

### 3.2 Exchange Connector Interface

```typescript
// src/trading/exchange/connector.ts

import type { OHLCV, Trade, TradeSignal, TradeDirection } from '../../types.js';

export interface OrderResult {
  orderId: string;
  status: 'filled' | 'partial' | 'pending' | 'rejected';
  filledPrice?: number;
  filledQuantity?: number;
  commission?: number;
  message?: string;
}

export interface AccountInfo {
  balance: number;
  equity: number;
  margin: number;
  freeMargin: number;
  currency: string;
}

export interface ExchangeConnector {
  // Connection
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  isConnected(): boolean;
  
  // Account
  getAccountInfo(): Promise<AccountInfo>;
  
  // Market Data
  getLatestPrice(symbol: string): Promise<number>;
  getOHLCV(symbol: string, timeframe: string, limit: number): Promise<OHLCV[]>;
  subscribeToPrice(symbol: string, callback: (price: number) => void): void;
  unsubscribeFromPrice(symbol: string): void;
  
  // Orders
  placeMarketOrder(
    symbol: string,
    direction: TradeDirection,
    quantity: number,
    stopLoss: number,
    takeProfit?: number
  ): Promise<OrderResult>;
  
  placeLimitOrder(
    symbol: string,
    direction: TradeDirection,
    quantity: number,
    price: number,
    stopLoss: number,
    takeProfit?: number
  ): Promise<OrderResult>;
  
  modifyOrder(
    orderId: string,
    stopLoss?: number,
    takeProfit?: number
  ): Promise<OrderResult>;
  
  cancelOrder(orderId: string): Promise<boolean>;
  
  closePosition(positionId: string): Promise<OrderResult>;
  
  // Positions
  getOpenPositions(): Promise<Trade[]>;
  getPosition(positionId: string): Promise<Trade | null>;
}
```

### 3.3 Paper Trading Connector

```typescript
// src/trading/exchange/paper.ts

import type { 
  ExchangeConnector, 
  OrderResult, 
  AccountInfo 
} from './connector.js';
import type { OHLCV, Trade, TradeDirection } from '../../types.js';
import { ulid } from 'ulid';
import { createLogger } from '../../observability/logger.js';

const logger = createLogger('trading.paper');

interface PaperPosition {
  id: string;
  symbol: string;
  direction: TradeDirection;
  entryPrice: number;
  quantity: number;
  stopLoss: number;
  takeProfit?: number;
  openedAt: Date;
}

export class PaperTradingConnector implements ExchangeConnector {
  private connected = false;
  private balance: number;
  private positions: Map<string, PaperPosition> = new Map();
  private priceSubscriptions: Map<string, (price: number) => void> = new Map();
  private currentPrices: Map<string, number> = new Map();
  private historicalData: Map<string, OHLCV[]> = new Map();
  
  constructor(initialBalance: number = 10000) {
    this.balance = initialBalance;
  }
  
  async connect(): Promise<void> {
    this.connected = true;
    logger.info('Paper trading connected', { balance: this.balance });
  }
  
  async disconnect(): Promise<void> {
    this.connected = false;
    this.priceSubscriptions.clear();
  }
  
  isConnected(): boolean {
    return this.connected;
  }
  
  async getAccountInfo(): Promise<AccountInfo> {
    const equity = this.calculateEquity();
    return {
      balance: this.balance,
      equity,
      margin: equity * 0.1, // Simplified
      freeMargin: equity * 0.9,
      currency: 'USD',
    };
  }
  
  async getLatestPrice(symbol: string): Promise<number> {
    // In production, this would fetch from a real data source
    // For paper trading, we simulate or use cached data
    const price = this.currentPrices.get(symbol);
    if (!price) {
      throw new Error(`No price data for ${symbol}`);
    }
    return price;
  }
  
  async getOHLCV(symbol: string, timeframe: string, limit: number): Promise<OHLCV[]> {
    // Would fetch from data provider
    const data = this.historicalData.get(`${symbol}-${timeframe}`) || [];
    return data.slice(-limit);
  }
  
  subscribeToPrice(symbol: string, callback: (price: number) => void): void {
    this.priceSubscriptions.set(symbol, callback);
  }
  
  unsubscribeFromPrice(symbol: string): void {
    this.priceSubscriptions.delete(symbol);
  }
  
  // Method to feed price data (for testing/simulation)
  feedPrice(symbol: string, price: number): void {
    this.currentPrices.set(symbol, price);
    
    // Check stops and limits for open positions
    for (const [id, pos] of this.positions) {
      if (pos.symbol !== symbol) continue;
      
      if (pos.direction === 'long') {
        if (price <= pos.stopLoss) {
          this.closePositionInternal(id, pos.stopLoss, 'stop_loss');
        } else if (pos.takeProfit && price >= pos.takeProfit) {
          this.closePositionInternal(id, pos.takeProfit, 'take_profit');
        }
      } else {
        if (price >= pos.stopLoss) {
          this.closePositionInternal(id, pos.stopLoss, 'stop_loss');
        } else if (pos.takeProfit && price <= pos.takeProfit) {
          this.closePositionInternal(id, pos.takeProfit, 'take_profit');
        }
      }
    }
    
    // Notify subscribers
    const callback = this.priceSubscriptions.get(symbol);
    if (callback) {
      callback(price);
    }
  }
  
  async placeMarketOrder(
    symbol: string,
    direction: TradeDirection,
    quantity: number,
    stopLoss: number,
    takeProfit?: number
  ): Promise<OrderResult> {
    const price = await this.getLatestPrice(symbol);
    
    // Simulate slippage (0-2 pips)
    const slippage = (Math.random() * 0.0002) * (direction === 'long' ? 1 : -1);
    const filledPrice = price * (1 + slippage);
    
    const positionId = ulid();
    this.positions.set(positionId, {
      id: positionId,
      symbol,
      direction,
      entryPrice: filledPrice,
      quantity,
      stopLoss,
      takeProfit,
      openedAt: new Date(),
    });
    
    logger.info('Paper order filled', {
      positionId,
      symbol,
      direction,
      quantity,
      price: filledPrice,
    });
    
    return {
      orderId: positionId,
      status: 'filled',
      filledPrice,
      filledQuantity: quantity,
      commission: quantity * filledPrice * 0.0001, // 1 pip commission
    };
  }
  
  async placeLimitOrder(
    symbol: string,
    direction: TradeDirection,
    quantity: number,
    price: number,
    stopLoss: number,
    takeProfit?: number
  ): Promise<OrderResult> {
    // For simplicity, treat limit orders as market orders in paper trading
    // A real implementation would queue them
    return this.placeMarketOrder(symbol, direction, quantity, stopLoss, takeProfit);
  }
  
  async modifyOrder(
    orderId: string,
    stopLoss?: number,
    takeProfit?: number
  ): Promise<OrderResult> {
    const position = this.positions.get(orderId);
    if (!position) {
      return { orderId, status: 'rejected', message: 'Position not found' };
    }
    
    if (stopLoss !== undefined) position.stopLoss = stopLoss;
    if (takeProfit !== undefined) position.takeProfit = takeProfit;
    
    return { orderId, status: 'filled' };
  }
  
  async cancelOrder(orderId: string): Promise<boolean> {
    return this.positions.delete(orderId);
  }
  
  async closePosition(positionId: string): Promise<OrderResult> {
    const position = this.positions.get(positionId);
    if (!position) {
      return { orderId: positionId, status: 'rejected', message: 'Position not found' };
    }
    
    const price = await this.getLatestPrice(position.symbol);
    return this.closePositionInternal(positionId, price, 'manual');
  }
  
  async getOpenPositions(): Promise<Trade[]> {
    const trades: Trade[] = [];
    for (const pos of this.positions.values()) {
      const currentPrice = this.currentPrices.get(pos.symbol) || pos.entryPrice;
      const pnl = pos.direction === 'long'
        ? (currentPrice - pos.entryPrice) * pos.quantity
        : (pos.entryPrice - currentPrice) * pos.quantity;
      
      trades.push({
        id: pos.id,
        symbol: pos.symbol,
        direction: pos.direction,
        status: 'open',
        strategy: 'unknown',
        entryPrice: pos.entryPrice,
        entryTime: pos.openedAt,
        entryReason: 'paper_trade',
        positionSize: pos.quantity,
        positionValue: pos.quantity * currentPrice,
        stopLoss: pos.stopLoss,
        takeProfit: pos.takeProfit,
        profitLoss: pnl,
        profitLossPercent: (pnl / (pos.quantity * pos.entryPrice)) * 100,
        followedRules: true,
        behavioralFlags: [],
      });
    }
    return trades;
  }
  
  async getPosition(positionId: string): Promise<Trade | null> {
    const positions = await this.getOpenPositions();
    return positions.find(p => p.id === positionId) || null;
  }
  
  private closePositionInternal(
    positionId: string,
    exitPrice: number,
    reason: string
  ): OrderResult {
    const position = this.positions.get(positionId);
    if (!position) {
      return { orderId: positionId, status: 'rejected' };
    }
    
    const pnl = position.direction === 'long'
      ? (exitPrice - position.entryPrice) * position.quantity
      : (position.entryPrice - exitPrice) * position.quantity;
    
    this.balance += pnl;
    this.positions.delete(positionId);
    
    logger.info('Paper position closed', {
      positionId,
      exitPrice,
      reason,
      pnl,
      newBalance: this.balance,
    });
    
    return {
      orderId: positionId,
      status: 'filled',
      filledPrice: exitPrice,
      filledQuantity: position.quantity,
    };
  }
  
  private calculateEquity(): number {
    let equity = this.balance;
    for (const pos of this.positions.values()) {
      const currentPrice = this.currentPrices.get(pos.symbol) || pos.entryPrice;
      const pnl = pos.direction === 'long'
        ? (currentPrice - pos.entryPrice) * pos.quantity
        : (pos.entryPrice - currentPrice) * pos.quantity;
      equity += pnl;
    }
    return equity;
  }
}
```

### 3.4 Strategy Interface

```typescript
// src/trading/strategies/base.ts

import type { OHLCV, TradeSignal, MarketRegime, TradingProceduralMemory } from '../../types.js';

export interface StrategyContext {
  symbol: string;
  accountBalance: number;
  currentRegime: MarketRegime;
  proceduralMemories: TradingProceduralMemory[];
  recentTrades: { direction: 'long' | 'short'; profitLoss: number }[];
}

export interface StrategyResult {
  signal: TradeSignal | null;
  analysis: {
    trend: 'up' | 'down' | 'sideways';
    strength: number;
    volatility: number;
    regime: MarketRegime;
  };
  reason: string;
}

export interface TradingStrategy {
  name: string;
  description: string;
  
  // Supported regimes (empty = all)
  supportedRegimes: MarketRegime[];
  
  // Analysis method
  analyze(candles: OHLCV[], context: StrategyContext): Promise<StrategyResult>;
  
  // Get current parameters
  getParameters(): Record<string, number>;
  
  // Update parameters (within bounds)
  updateParameters(params: Partial<Record<string, number>>): void;
}
```

### 3.5 EMA Crossover Strategy (Simple Starting Strategy)

```typescript
// src/trading/strategies/ema-crossover.ts

import type { TradingStrategy, StrategyContext, StrategyResult } from './base.js';
import type { OHLCV, TradeSignal, MarketRegime } from '../../types.js';
import { calculateEMA } from '../indicators/ema.js';
import { calculateATR } from '../indicators/atr.js';

interface EMAParams {
  fastPeriod: number;
  slowPeriod: number;
  atrPeriod: number;
  atrMultiplierSL: number;
  atrMultiplierTP: number;
  minTrendStrength: number;
}

const DEFAULT_PARAMS: EMAParams = {
  fastPeriod: 12,
  slowPeriod: 26,
  atrPeriod: 14,
  atrMultiplierSL: 2.0,
  atrMultiplierTP: 3.0,
  minTrendStrength: 0.3,
};

export class EMACrossoverStrategy implements TradingStrategy {
  name = 'ema_crossover';
  description = 'Simple EMA crossover with ATR-based stops';
  supportedRegimes: MarketRegime[] = ['trending_up', 'trending_down'];
  
  private params: EMAParams;
  
  constructor(params: Partial<EMAParams> = {}) {
    this.params = { ...DEFAULT_PARAMS, ...params };
  }
  
  async analyze(candles: OHLCV[], context: StrategyContext): Promise<StrategyResult> {
    if (candles.length < this.params.slowPeriod + 2) {
      return {
        signal: null,
        analysis: { trend: 'sideways', strength: 0, volatility: 0, regime: 'unknown' },
        reason: 'Insufficient data',
      };
    }
    
    // Calculate EMAs
    const closes = candles.map(c => c.close);
    const fastEMA = calculateEMA(closes, this.params.fastPeriod);
    const slowEMA = calculateEMA(closes, this.params.slowPeriod);
    const atr = calculateATR(candles, this.params.atrPeriod);
    
    const currentFast = fastEMA[fastEMA.length - 1];
    const currentSlow = slowEMA[slowEMA.length - 1];
    const prevFast = fastEMA[fastEMA.length - 2];
    const prevSlow = slowEMA[slowEMA.length - 2];
    const currentATR = atr[atr.length - 1];
    const currentPrice = candles[candles.length - 1].close;
    
    // Determine trend
    const trendStrength = Math.abs(currentFast - currentSlow) / currentSlow;
    const trend = currentFast > currentSlow ? 'up' : currentFast < currentSlow ? 'down' : 'sideways';
    
    // Detect regime
    const avgATR = atr.slice(-20).reduce((a, b) => a + b, 0) / 20;
    const volatilityRatio = currentATR / avgATR;
    let regime: MarketRegime;
    if (volatilityRatio > 1.5) {
      regime = 'volatile';
    } else if (trendStrength > this.params.minTrendStrength) {
      regime = trend === 'up' ? 'trending_up' : 'trending_down';
    } else {
      regime = 'ranging';
    }
    
    // Check if regime is supported
    if (!this.supportedRegimes.includes(regime)) {
      return {
        signal: null,
        analysis: { trend, strength: trendStrength, volatility: volatilityRatio, regime },
        reason: `Current regime (${regime}) not supported by this strategy`,
      };
    }
    
    // Look for crossover
    const bullishCross = prevFast <= prevSlow && currentFast > currentSlow;
    const bearishCross = prevFast >= prevSlow && currentFast < currentSlow;
    
    // Apply procedural memory adjustments
    let positionSizeMultiplier = 1.0;
    let shouldSkip = false;
    
    for (const memory of context.proceduralMemories) {
      if (!memory.enabled || memory.confidence < 0.6) continue;
      
      if (memory.conditionType === 'high_volatility' && volatilityRatio > 1.3) {
        if (memory.adjustmentType === 'reduce_size') {
          positionSizeMultiplier *= memory.adjustmentMagnitude;
        } else if (memory.adjustmentType === 'skip_trade') {
          shouldSkip = true;
        }
      }
      
      if (memory.conditionType === 'losing_streak' && 
          context.recentTrades.filter(t => t.profitLoss < 0).length >= 3) {
        if (memory.adjustmentType === 'reduce_size') {
          positionSizeMultiplier *= memory.adjustmentMagnitude;
        }
      }
    }
    
    if (shouldSkip) {
      return {
        signal: null,
        analysis: { trend, strength: trendStrength, volatility: volatilityRatio, regime },
        reason: 'Procedural memory: skip trade in current conditions',
      };
    }
    
    if (!bullishCross && !bearishCross) {
      return {
        signal: null,
        analysis: { trend, strength: trendStrength, volatility: volatilityRatio, regime },
        reason: 'No crossover signal',
      };
    }
    
    // Calculate position size (simplified - in reality would consider account balance)
    const baseSize = context.accountBalance * 0.02 / currentPrice; // 2% risk per trade
    const adjustedSize = baseSize * positionSizeMultiplier;
    
    // Build signal
    const direction = bullishCross ? 'long' : 'short';
    const stopDistance = currentATR * this.params.atrMultiplierSL;
    const tpDistance = currentATR * this.params.atrMultiplierTP;
    
    const signal: TradeSignal = {
      symbol: context.symbol,
      direction,
      entryPrice: currentPrice,
      stopLoss: direction === 'long' 
        ? currentPrice - stopDistance 
        : currentPrice + stopDistance,
      takeProfit: direction === 'long'
        ? currentPrice + tpDistance
        : currentPrice - tpDistance,
      positionSize: adjustedSize,
      strategy: this.name,
      confidence: Math.min(trendStrength * 2, 1),
      reason: `${direction === 'long' ? 'Bullish' : 'Bearish'} EMA crossover`,
      marketRegime: regime,
      timestamp: new Date(),
    };
    
    return {
      signal,
      analysis: { trend, strength: trendStrength, volatility: volatilityRatio, regime },
      reason: signal.reason,
    };
  }
  
  getParameters(): Record<string, number> {
    return { ...this.params };
  }
  
  updateParameters(params: Partial<EMAParams>): void {
    // Validate bounds
    if (params.fastPeriod !== undefined) {
      this.params.fastPeriod = Math.max(5, Math.min(50, params.fastPeriod));
    }
    if (params.slowPeriod !== undefined) {
      this.params.slowPeriod = Math.max(10, Math.min(200, params.slowPeriod));
    }
    // Ensure fast < slow
    if (this.params.fastPeriod >= this.params.slowPeriod) {
      this.params.fastPeriod = this.params.slowPeriod - 1;
    }
  }
}
```

---

## 4. Learner Agent: The "Feeling" System

The Learner analyzes completed trades and updates procedural memory.

```typescript
// src/trading/learner.ts

import type BetterSqlite3 from 'better-sqlite3';
import type { Trade, TradingProceduralMemory, BehavioralFlag } from '../types.js';
import { ulid } from 'ulid';
import { createLogger } from '../observability/logger.js';

const logger = createLogger('trading.learner');

type Database = BetterSqlite3.Database;

export class TradingLearner {
  constructor(private db: Database) {}
  
  /**
   * Analyze a completed trade and extract lessons.
   * This is the core "learning from mistakes" function.
   */
  analyzeTrade(trade: Trade): {
    processScore: number;
    lessonsLearned: string[];
    behavioralIssues: BehavioralFlag[];
    proceduralUpdates: Partial<TradingProceduralMemory>[];
  } {
    const lessonsLearned: string[] = [];
    const behavioralIssues: BehavioralFlag[] = [];
    const proceduralUpdates: Partial<TradingProceduralMemory>[] = [];
    
    // Process evaluation (not outcome!)
    let processScore = 1.0;
    
    // Did we follow the rules?
    if (!trade.followedRules) {
      processScore -= 0.3;
      lessonsLearned.push('Trade deviated from strategy rules');
    }
    
    // Did we move the stop loss?
    if (trade.behavioralFlags.includes('moved_stop')) {
      processScore -= 0.2;
      behavioralIssues.push('moved_stop');
      lessonsLearned.push('Moving stop loss to avoid loss is a mistake');
      
      // Update procedural memory: when tempted to move stop, don't
      proceduralUpdates.push({
        conditionType: 'tempted_to_move_stop',
        adjustmentType: 'reminder',
        adjustmentMagnitude: 1.0,
      });
    }
    
    // Was this a revenge trade?
    if (trade.behavioralFlags.includes('revenge_trade')) {
      processScore -= 0.3;
      behavioralIssues.push('revenge_trade');
      lessonsLearned.push('Revenge trading after loss leads to more losses');
      
      // Update procedural memory: after loss, reduce size
      proceduralUpdates.push({
        conditionType: 'after_loss',
        adjustmentType: 'reduce_size',
        adjustmentMagnitude: 0.5,
      });
    }
    
    // Check if trade was taken against the regime
    // This would compare trade direction vs market regime at entry
    
    // Analyze exit quality
    if (trade.exitQualityScore !== undefined && trade.exitQualityScore < 0.5) {
      if (trade.behavioralFlags.includes('early_exit')) {
        processScore -= 0.1;
        lessonsLearned.push('Early exit missed profitable continuation');
      }
      if (trade.behavioralFlags.includes('late_exit')) {
        processScore -= 0.1;
        lessonsLearned.push('Late exit gave back profits');
      }
    }
    
    // MAE/MFE analysis
    if (trade.maxAdverseExcursion && trade.maxFavorableExcursion && trade.profitLoss !== undefined) {
      const mae = Math.abs(trade.maxAdverseExcursion);
      const mfe = trade.maxFavorableExcursion;
      
      if (trade.profitLoss < 0 && mfe > mae * 2) {
        lessonsLearned.push('Trade was in profit but ended as loss - improve exit management');
      }
    }
    
    return {
      processScore: Math.max(0, processScore),
      lessonsLearned,
      behavioralIssues,
      proceduralUpdates,
    };
  }
  
  /**
   * Update procedural memory with a new learned pattern.
   * This creates the "feeling" that influences future behavior.
   */
  updateProceduralMemory(
    conditionType: string,
    adjustmentType: string,
    outcome: number,
    wasAdjustmentApplied: boolean
  ): void {
    // Find existing entry
    const existing = this.db.prepare(
      `SELECT * FROM procedural_trading_memory 
       WHERE condition_type = ? AND adjustment_type = ?`
    ).get(conditionType, adjustmentType) as any;
    
    if (existing) {
      // Update with new evidence
      const field = wasAdjustmentApplied ? 'outcome_when_applied' : 'outcome_when_ignored';
      const currentOutcome = existing[field] || 0;
      const count = existing.supporting_trades + 1;
      
      // Running average
      const newOutcome = ((currentOutcome * existing.supporting_trades) + outcome) / count;
      
      // Confidence increases with more evidence
      let confidence = existing.confidence;
      if (wasAdjustmentApplied && outcome > 0) {
        confidence = Math.min(1, confidence + 0.05);
      } else if (!wasAdjustmentApplied && outcome < 0) {
        confidence = Math.min(1, confidence + 0.05);
      }
      
      this.db.prepare(
        `UPDATE procedural_trading_memory 
         SET ${field} = ?, supporting_trades = ?, confidence = ?, 
             last_validated_at = datetime('now'), updated_at = datetime('now')
         WHERE id = ?`
      ).run(newOutcome, count, confidence, existing.id);
      
      logger.info('Procedural memory updated', {
        conditionType,
        adjustmentType,
        confidence,
        supportingTrades: count,
      });
    } else {
      // Create new entry
      const id = ulid();
      this.db.prepare(
        `INSERT INTO procedural_trading_memory 
         (id, condition_type, adjustment_type, outcome_when_applied, outcome_when_ignored,
          supporting_trades, confidence, enabled)
         VALUES (?, ?, ?, ?, ?, 1, 0.5, 1)`
      ).run(
        id,
        conditionType,
        adjustmentType,
        wasAdjustmentApplied ? outcome : null,
        wasAdjustmentApplied ? null : outcome
      );
      
      logger.info('Procedural memory created', { id, conditionType, adjustmentType });
    }
  }
  
  /**
   * Record a trading error pattern.
   * This is specifically for mistakes we should not repeat.
   */
  recordErrorPattern(
    errorType: string,
    context: Record<string, unknown>,
    lossAmount: number
  ): void {
    const existing = this.db.prepare(
      `SELECT * FROM trading_error_patterns WHERE error_type = ?`
    ).get(errorType) as any;
    
    if (existing) {
      this.db.prepare(
        `UPDATE trading_error_patterns 
         SET occurrence_count = occurrence_count + 1,
             total_loss_from_error = total_loss_from_error + ?,
             error_context = ?,
             last_occurred_at = datetime('now')
         WHERE id = ?`
      ).run(lossAmount, JSON.stringify(context), existing.id);
      
      logger.warn('Error pattern recurring', {
        errorType,
        occurrences: existing.occurrence_count + 1,
        totalLoss: existing.total_loss_from_error + lossAmount,
      });
    } else {
      const id = ulid();
      this.db.prepare(
        `INSERT INTO trading_error_patterns 
         (id, error_type, error_context, total_loss_from_error, 
          first_occurred_at, last_occurred_at)
         VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))`
      ).run(id, errorType, JSON.stringify(context), lossAmount);
      
      logger.warn('New error pattern recorded', { id, errorType, loss: lossAmount });
    }
  }
  
  /**
   * Get all active procedural memories.
   * These influence trading decisions (the "feeling").
   */
  getActiveProceduralMemories(): TradingProceduralMemory[] {
    const rows = this.db.prepare(
      `SELECT * FROM procedural_trading_memory WHERE enabled = 1`
    ).all() as any[];
    
    return rows.map(row => ({
      id: row.id,
      conditionType: row.condition_type,
      conditionParams: JSON.parse(row.condition_params || '{}'),
      adjustmentType: row.adjustment_type,
      adjustmentMagnitude: row.adjustment_magnitude || 1.0,
      supportingTrades: row.supporting_trades,
      outcomeWhenApplied: row.outcome_when_applied,
      outcomeWhenIgnored: row.outcome_when_ignored,
      confidence: row.confidence,
      enabled: row.enabled === 1,
    }));
  }
  
  /**
   * Check for error patterns that should prevent a trade.
   */
  checkErrorPatterns(context: Record<string, unknown>): {
    shouldBlock: boolean;
    reason: string | null;
  } {
    const patterns = this.db.prepare(
      `SELECT * FROM trading_error_patterns 
       WHERE occurrence_count >= 3 AND prevention_effective = 0`
    ).all() as any[];
    
    // Check if current context matches any recurring error pattern
    for (const pattern of patterns) {
      const errorContext = JSON.parse(pattern.error_context);
      
      // Simple context matching (could be more sophisticated)
      if (this.contextsMatch(errorContext, context)) {
        return {
          shouldBlock: true,
          reason: `Error pattern "${pattern.error_type}" has occurred ${pattern.occurrence_count} times with total loss of $${pattern.total_loss_from_error.toFixed(2)}`,
        };
      }
    }
    
    return { shouldBlock: false, reason: null };
  }
  
  private contextsMatch(
    pattern: Record<string, unknown>,
    current: Record<string, unknown>
  ): boolean {
    // Check if key pattern attributes match
    const keysToCheck = ['marketRegime', 'timeOfDay', 'afterLoss', 'volatilityLevel'];
    
    for (const key of keysToCheck) {
      if (key in pattern && key in current && pattern[key] === current[key]) {
        return true;
      }
    }
    
    return false;
  }
}
```

---

## 5. Integration with Automaton Loop

The trading subsystem integrates with Automaton's heartbeat daemon:

```typescript
// Addition to src/heartbeat/tasks/trading.ts

import type { HeartbeatTaskFn, TickContext, HeartbeatLegacyContext } from '../../types.js';
import { TradingOverseer } from '../../trading/overseer.js';
import { TradingLearner } from '../../trading/learner.js';
import { EMACrossoverStrategy } from '../../trading/strategies/ema-crossover.js';
import { PaperTradingConnector } from '../../trading/exchange/paper.js';
import { createLogger } from '../../observability/logger.js';

const logger = createLogger('heartbeat.trading');

export const tradingTickTask: HeartbeatTaskFn = async (
  ctx: TickContext,
  taskCtx: HeartbeatLegacyContext
): Promise<{ shouldWake: boolean; message?: string }> => {
  const config = taskCtx.config;
  
  // Skip if trading not enabled
  if (!config.tradingConfig?.enabled) {
    return { shouldWake: false };
  }
  
  try {
    const overseer = new TradingOverseer(config.tradingConfig);
    const learner = new TradingLearner(ctx.db);
    const strategy = new EMACrossoverStrategy();
    const exchange = new PaperTradingConnector();
    
    await exchange.connect();
    
    // Get current state
    const tradingState = getTradingState(ctx.db);
    const accountInfo = await exchange.getAccountInfo();
    const openPositions = await exchange.getOpenPositions();
    
    // Check circuit breakers
    const breakerCheck = overseer.checkCircuitBreakers(tradingState);
    if (breakerCheck.shouldActivate) {
      activateCircuitBreaker(ctx.db, breakerCheck.breakerType!, breakerCheck.duration);
      return { 
        shouldWake: false, 
        message: `Circuit breaker activated: ${breakerCheck.breakerType}` 
      };
    }
    
    // Get market data
    const candles = await exchange.getOHLCV(
      config.tradingConfig.defaultSymbol,
      'H1',
      100
    );
    
    // Get procedural memories for "feeling"
    const proceduralMemories = learner.getActiveProceduralMemories();
    
    // Run strategy
    const strategyContext = {
      symbol: config.tradingConfig.defaultSymbol,
      accountBalance: accountInfo.balance,
      currentRegime: tradingState.currentRegime,
      proceduralMemories,
      recentTrades: getRecentTrades(ctx.db, 5),
    };
    
    const result = await strategy.analyze(candles, strategyContext);
    
    if (!result.signal) {
      return { shouldWake: false, message: result.reason };
    }
    
    // Validate with Overseer
    const validationError = overseer.validateSignal(
      result.signal,
      tradingState,
      accountInfo.balance,
      openPositions.map(p => p as any)
    );
    
    if (validationError) {
      logger.warn('Trade signal rejected by Overseer', { reason: validationError });
      return { shouldWake: true, message: validationError };
    }
    
    // Check error patterns
    const errorCheck = learner.checkErrorPatterns({
      marketRegime: tradingState.currentRegime,
      signal: result.signal,
    });
    
    if (errorCheck.shouldBlock) {
      logger.warn('Trade blocked by error pattern', { reason: errorCheck.reason });
      return { shouldWake: true, message: `Error pattern: ${errorCheck.reason}` };
    }
    
    // Execute trade
    const orderResult = await exchange.placeMarketOrder(
      result.signal.symbol,
      result.signal.direction,
      result.signal.positionSize,
      result.signal.stopLoss,
      result.signal.takeProfit
    );
    
    if (orderResult.status === 'filled') {
      recordTradeEntry(ctx.db, result.signal, orderResult);
      return { shouldWake: true, message: `Trade executed: ${result.signal.direction} ${result.signal.symbol}` };
    }
    
    return { shouldWake: false };
  } catch (error) {
    logger.error('Trading tick failed', error instanceof Error ? error : undefined);
    return { shouldWake: true, message: `Trading error: ${error}` };
  }
};

// Helper functions would be implemented separately
function getTradingState(db: any): any { /* ... */ }
function activateCircuitBreaker(db: any, type: string, duration: number): void { /* ... */ }
function getRecentTrades(db: any, limit: number): any[] { return []; }
function recordTradeEntry(db: any, signal: any, order: any): void { /* ... */ }
```

---

## 6. Deployment Checklist

### Phase 0: Infrastructure
- [ ] Create schema migration V10 for trading tables
- [ ] Implement `ExchangeConnector` interface
- [ ] Implement `PaperTradingConnector`
- [ ] Create `TradingOverseer` with all constitutional limits
- [ ] Create `TradingLearner` with procedural memory
- [ ] Implement EMA indicator
- [ ] Implement ATR indicator
- [ ] Create `EMACrossoverStrategy`
- [ ] Integration tests for all components

### Phase 1: Paper Trading
- [ ] Connect data feed for XAU/USD (can use free APIs initially)
- [ ] Implement heartbeat task for trading tick
- [ ] Add trading state management
- [ ] Implement trade journal recording
- [ ] Create dashboard for monitoring (can be CLI-based)
- [ ] Run 100 paper trades
- [ ] Analyze results and tune parameters

### Phase 2: Live Trading
- [ ] Implement OANDA connector (or Alpaca for US equities)
- [ ] Add proper API key management
- [ ] Implement slippage tracking
- [ ] Add alerting for circuit breakers
- [ ] Human-in-the-loop approval for first 10 trades
- [ ] Gradual position size increase

---

This specification provides a complete technical blueprint for implementing GemTrade on top of Automaton. The key insight is that we're not building a trading bot—we're extending an autonomous agent with trading capabilities while maintaining all the safety, memory, and learning systems that make Automaton robust.
