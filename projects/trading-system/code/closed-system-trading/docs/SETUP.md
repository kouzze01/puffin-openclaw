# Setup Guide

This guide covers the installation and configuration of the Modular Closed System.

## Prerequisites

*   **Python**: Version 3.9 or higher.
*   **Binance Account**: For market data and trading (Spot API enabled).
*   **Supabase Project**: For database hosting.

## 1. Installation

1.  Clone the repository or download the source code.
2.  Open a terminal in the project directory.
3.  Create a virtual environment (recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
4.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## 2. Environment Configuration

Create a file named `.env` in the root directory. You can copy the example:
```bash
cp .env.example .env
```

Fill in the following variables:

```ini
# Binance API (Required for Price Data & Trading)
BINANCE_API_KEY=your_binance_api_key
BINANCE_API_SECRET=your_binance_api_secret

# Supabase (Required for Database)
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key
```

## 3. Database Setup

You need to set up the tables in your Supabase project.

1.  Log in to your Supabase Dashboard.
2.  Go to the **SQL Editor**.
3.  Open the `schema.sql` file from this project.
4.  Copy the contents and paste them into the SQL Editor.
5.  Click **Run** to create the necessary tables:
    *   `zones_config`
    *   `trade_log`
    *   `paper_trade_log`
    *   `portfolio_summary`

## 4. Running the System

### Start the Dashboard
The dashboard is used to create and activate zones. **You must set up at least one active zone for the bot to trade.**

```bash
streamlit run dashboard.py
```

*   Go to "Quick Actions" and generate a Zone (UP or DOWN).
*   In the "Zone Config" table, change a zone's status to `Active` and allocate capital.
*   Click **Save Changes**.
*   **Paper Trading View**: Use the sidebar to toggle between 'Live Portfolio' and 'Paper Trading' to see simulated results.
*   **TP Calculator**: Switch to the "TP Calculator" tab to plan your profit targets and fee calculations.

### Start the Bot
Run the main trading logic script.

```bash
python trade_and_log.py
```

**Note on Modes:**
By default, the bot might be in `PAPER` or `DRY_RUN` mode. Open `trade_and_log.py` and modify the `TRADING_MODE` variable at the top of the file to change modes:

```python
# trade_and_log.py
TRADING_MODE = 'LIVE' # Options: 'LIVE', 'PAPER', 'DRY_RUN'
```
