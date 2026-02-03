# System Architecture & Logic

## 1. Core Workflow (`trade_and_log.py`)

The bot operates on a continuous loop (defined by `LOOP_INTERVAL`, default 60s).

### The Loop Cycle:
1.  **Fetch Data**:
    *   Retrieves all **Active Zones** from Supabase (`zones_config`).
    *   Fetches current **BTCUSDT price** from Binance.
    *   **Market Regime Analysis**:
        *   Calculates EMA 200 and ADX 14 (1h timeframe).
        *   Determines regime: `SIDEWAY` (ADX < 25), `BULL_TREND` (Price > EMA), or `BEAR_TREND` (Price < EMA).
2.  **Zone Selection**:
    *   The bot iterates through active zones to find one that contains the current market price (`price_low <= current_price <= price_high`).
    *   **Safety**: If the price is outside any active zone, the bot pauses and logs a warning.
3.  **State Synchronization**:
    *   Generates **Grid Levels** for the active zone based on `GRID_STEP_PRICE` (e.g., every $200).
    *   Fetches **Open Trades** from the database to know which grid levels are already occupied.
4.  **Signal Generation**:
    *   **BUY Signal**:
        *   Checks if price is within a specific "bucket" below a grid level.
        *   Checks if the level is empty (no open trade).
        *   **RSI Filter**: Checks if RSI (14-period, 5m candle) is below `RSI_LIMIT` (default 60).
        *   **Regime Check**: In `BEAR_TREND`, only buys if RSI < 30 (oversold).
    *   **SELL Signal (Take Profit & Smart Exit)**:
        *   Iterates through open trades.
        *   **Standard TP**: Checks if `current_price >= entry_price + TP_PROFIT`.
        *   **Smart Exit (Breakeven)**:
            *   If price hits > 50% of TP target, the trade is marked as `SECURED`.
            *   If a `SECURED` trade drops back to `entry + $10` (Breakeven), it closes immediately to prevent loss.
5.  **Execution and Logging**:
    *   Executes the order (Mock or Real).
    *   Logs the result to Supabase (`trade_log` or `paper_trade_log`).

## 2. Database Schema

The system uses Supabase (PostgreSQL) with the following key tables:

### `zones_config`
Configuration for trading modules.
*   `zone_name`: Identifier (e.g., "Module 90k-92k").
*   `price_low` / `price_high`: The price range this module covers.
*   `status`: `Active`, `Inactive`, or `Reserve`. Bot only looks at `Active`.
*   `capital_allocated`: How much USDT is assigned to this module.

### `trade_log` (Live) & `paper_trade_log` (Paper)
Stores individual trade records. Live and Paper modes use identical schemas but separate tables to keep data clean.
*   `entry_price`: The average price the asset was bought at.
*   `quantity`: Amount of BTC.
*   `status`: `OPEN` (holding) or `CLOSED` (sold).
*   `pnl_usdt`: Realized profit/loss (only populated on close).
*   `fee_usdt`: Transaction fees (estimated or real).

## 3. Trading Modes

You can switch modes in `trade_and_log.py` via the `TRADING_MODE` variable.

| Mode | Real Money? | Execution | Database Table |
| :--- | :--- | :--- | :--- |
| **LIVE** | ✅ YES | Binance API (Real Orders) | `trade_log` |
| **PAPER** | ❌ NO | Mock (Simulated Fills) | `paper_trade_log` |
| **DRY_RUN**| ❌ NO | Print to Console Only | None (No DB write) |

### Paper Trading Details
*   Simulates instantaneous fills at the current market price.
*   Calculates fees using the `TRADING_FEE_RATE` config (default 0.075% for BNB users, 0.1% standard).
*   Useful for testing strategy performance without risk.

## 4. Dashboard (`dashboard.py`)
A wrapper around the database and Binance API.
*   **Zone Editor**: Allows you to flip switches on zones (Active/Inactive) and managing capital.
*   **Metrics**: Shows Real-time PnL, Open Trades count, and Capital usage.
*   **Paper Mode**: Toggle the sidebar to view simulation data instead of live data.
