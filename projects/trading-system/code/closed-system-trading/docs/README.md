# Modular Closed System (BTCUSDT)

A modular grid trading system/bot for BTCUSDT on Binance, designed with privacy and control in mind. This system allows you to manage trading "Zones" or "Modules" (specific price ranges), allocating capital dynamically to where the price action is.

## 🌟 Key Features

*   **Modular Zone Management**: Divide the market into price distinct zones (e.g., 88k-90k, 90k-92k). Activate/Deactivate zones and allocate capital via a GUI.
*   **Market Regime Detection**: Automatically classifies market as SIDEWAY, BULL_TREND, or BEAR_TREND using EMA 200 & ADX 14 to adapt trading logic.
*   **Smart Exit**: Protects profits by triggering a 'Safe Mode' when a trade hits >50% of TP, setting a Breakeven stop-loss.
*   **Grid Trading Strategy**: Executes Buy/Sell orders within active zones based on grid levels.
*   **RSI Filter**: Incorporates RSI (Relative Strength Index) to filter entries during overbought conditions.
*   **Multiple Modes**:
    *   **LIVE**: Real money trading on Binance.
    *   **PAPER**: Simulation mode using live market data but mock execution, tracking PnL in a separate ledger.
    *   **DRY_RUN**: Print-only mode for logic verification.
*   **Dashboard**: A Streamlit-based UI to monitor the portfolio, manage zones, view trade history, and calculate TP targets (new **TP Calculator** tab).
*   **Supabase Backend**: Uses Supabase for persistent storage of configuration and trade logs.

## 📂 Project Structure

*   `trade_and_log.py`: **The Core Bot**. Runs the main trading loop, handles signals, and executes orders.
*   `dashboard.py`: **The Control Center**. Streamlit web app for monitoring and configuration.
*   `schema.sql`: Database schema definitions for Supabase.
*   `docs/`: Documentation folder.

## 🚀 Quick Start

1.  **Setup Environment**: Ensure you have Python 3.9+ and a Supabase project.
2.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Configure**: Create a `.env` file with your keys (see [Setup Guide](SETUP.md)).
4.  **Run Dashboard**:
    ```bash
    streamlit run dashboard.py
    ```
5.  **Run Bot**:
    ```bash
    python trade_and_log.py
    ```

## 📚 Documentation

*   [**Setup Guide**](SETUP.md): Detailed installation and configuration instructions.
*   [**Architecture & Logic**](ARCHITECTURE.md): Deep dive into how the bot works, database schema, and decision logic.
