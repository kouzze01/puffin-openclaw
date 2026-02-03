import os
import time
import math
from datetime import datetime, timezone
import pandas as pd
from binance.client import Client
from binance.enums import *
import ta
from dotenv import load_dotenv
from supabase import create_client, Client as SupabaseClient
# Import Snapshot Manager
from snapshot_manager import capture_snapshot
import requests
import json
import threading

# --- Configuration & Safety ---
TRADING_MODE = 'PAPER' # Options: 'LIVE', 'PAPER', 'DRY_RUN'
# ... existing ...
# Load environment variables
load_dotenv(override=True)
N8N_WEBHOOK_URL = os.getenv('N8N_WEBHOOK_URL')

# --- Connections ---
DRY_RUN = True if TRADING_MODE == 'DRY_RUN' else False # Backwards compatibility/Shortcut
SYMBOL = 'BTCUSDT'
GRID_STEP_PRICE = 200.0  # USDT
TP_PROFIT = 200.0       # USDT
TRADE_SIZE_USDT = 20.0  # USDT
MAX_TRADE_QTY = 0.001   # BTC (Hard Limit)
LOOP_INTERVAL = 60      # Seconds
SNAPSHOT_INTERVAL = 3600 # 1 Hour

# RSI SETTINGS
RSI_PERIOD = 14
RSI_LIMIT = 60 # Buy only if RSI < 60
RSI_TIMEFRAME = KLINE_INTERVAL_5MINUTE
TRADE_COOLDOWN = 300 # 5 Minutes

# FEE SETTINGS
# Set to True if you hold BNB and enabled "Use BNB for fees" on Binance (0.075%)
# Set to False for standard USDT fees (0.1%)
USE_BNB_FOR_FEES = True 
TRADING_FEE_RATE = 0.00075 if USE_BNB_FOR_FEES else 0.001

# Global State
LAST_TRADE_TIME = 0
LAST_SNAPSHOT_TIME = 0
SECURED_TRADES = set() # Tracks IDs of trades that have hit > 50% TP

# Load environment variables
load_dotenv(override=True)

# --- Connections ---
binance_api_key = os.getenv('BINANCE_API_KEY')
binance_api_secret = os.getenv('BINANCE_API_SECRET')
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_KEY')

if not all([binance_api_key, binance_api_secret, supabase_url, supabase_key]):
    print("❌ Critical Error: Missing API Keys in .env")
    exit(1)

binance_client = Client(binance_api_key, binance_api_secret)
supabase_client: SupabaseClient = create_client(supabase_url, supabase_key)

# --- Helpers ---

def send_trade_to_analysis(trade_data):
    """
    Sends closed trade data to n8n for AI analysis (Fire-and-forget).
    Using threading to avoid blocking the main bot loop.
    """
    if not N8N_WEBHOOK_URL:
        return

    def _send():
        try:
            payload = {
                "trade_id": trade_data.get('id'),
                "mode": TRADING_MODE, 
                "pair": SYMBOL,
                "entry_price": float(trade_data.get('entry_price', 0)),
                "exit_price": float(trade_data.get('exit_price', 0) or 0),
                "quantity": float(trade_data.get('quantity', 0)),
                "pnl_usdt": float(trade_data.get('pnl_usdt', 0)),
                "rsi_entry": float(trade_data.get('rsi_entry') or 0),
                "rsi_exit": float(trade_data.get('rsi_exit') or 0),
                "duration_minutes": float((datetime.fromisoformat(trade_data['exit_at']) - datetime.fromisoformat(trade_data['created_at'])).total_seconds() / 60) if trade_data.get('created_at') and trade_data.get('exit_at') else 0,
                "market_regime": trade_data.get('market_regime', 'UNKNOWN'), 
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            headers = {"Content-Type": "application/json"}
            requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=5)
        except Exception as e:
            print(f"Failed to send trade to AI: {e}")

    threading.Thread(target=_send).start()

def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def analyze_market_regime(symbol):
    """
    Analyzes the market regime using EMA 200 and ADX 14 on 1h timeframe.
    Returns: 'SIDEWAY', 'BULL_TREND', or 'BEAR_TREND'
    """
    try:
        klines = binance_client.get_klines(symbol=symbol, interval=Client.KLINE_INTERVAL_1HOUR, limit=300)
        if not klines:
            return 'SIDEWAY'

        # Parse Klines
        closes = [float(k[4]) for k in klines]
        highs = [float(k[2]) for k in klines]
        lows = [float(k[3]) for k in klines]
        
        df = pd.DataFrame({
            'high': highs,
            'low': lows,
            'close': closes
        })

        # Calculate Indicators
        # EMA 200
        df['ema200'] = ta.trend.EMAIndicator(close=df['close'], window=200).ema_indicator()
        
        # ADX 14
        df['ADX_14'] = ta.trend.ADXIndicator(high=df['high'], low=df['low'], close=df['close'], window=14).adx()
        
        # Get latest values
        current_close = df['close'].iloc[-1]
        current_ema200 = df['ema200'].iloc[-1]
        current_adx = df['ADX_14'].iloc[-1]
        
        # Logic
        if current_adx < 25:
            return 'SIDEWAY', current_adx
        elif current_close > current_ema200:
            return 'BULL_TREND', current_adx
        else:
            return 'BEAR_TREND', current_adx
            
    except Exception as e:
        log(f"⚠️ Error analyzing market regime: {e}")
        return 'SIDEWAY', 0 # Default safe fallback

def get_symbol_step_size(symbol):
    try:
        info = binance_client.get_symbol_info(symbol)
        for f in info['filters']:
            if f['filterType'] == 'LOT_SIZE':
                return float(f['stepSize'])
    except Exception as e:
        log(f"⚠️ Error fetching step size: {e}")
    return 0.00001

def execute_mock_order(side, quantity, price):
    """Simulates a Binance order execution for Paper Trading."""
    return {
        'symbol': SYMBOL,
        'orderId': f"paper_{int(time.time()*1000)}",
        'transactTime': int(time.time() * 1000),
        'price': str(price),
        'origQty': str(quantity),
        'executedQty': str(quantity),
        'cummulativeQuoteQty': str(price * quantity),
        'status': 'FILLED',
        'type': 'MARKET',
        'side': side
    }

def round_step_size(quantity, step_size):
    precision = int(round(-math.log(step_size, 10), 0))
    return float(round(quantity, precision))

def get_market_price(symbol):
    try:
        ticker = binance_client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except Exception as e:
        log(f"❌ Error fetching price: {e}")
        return None

def calculate_rsi(symbol, period=14):
    """Calculates the RSI for a given symbol."""
    try:
        klines = binance_client.get_klines(symbol=symbol, interval=RSI_TIMEFRAME, limit=100)
        closes = [float(k[4]) for k in klines]
        df = pd.DataFrame(closes, columns=['close'])
        
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        # Simple RSI calculation (SMA based) - sufficient for bot logic
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Return the last valid RSI value
        return df['rsi'].iloc[-1]
    except Exception as e:
        log(f"⚠️ Error calculating RSI: {e}")
        return 50.0 # Neutral fallback

def get_bot_settings():
    """Fetches dynamic settings from Supabase."""
    try:
        response = supabase_client.table("bot_settings").select("*").eq("id", 1).execute()
        if response.data:
            return response.data[0]
    except Exception as e:
        log(f"⚠️ Error fetching bot settings: {e}")
    return None

# --- Core Logic Functions ---

def fetch_active_zones():
    """Fetches ALL Active Zones from Supabase."""
    try:
        response = supabase_client.table("zones_config")\
            .select("*")\
            .eq("status", "Active")\
            .execute()
        
        return response.data if response.data else []
    except Exception as e:
        log(f"❌ Error fetching active zones: {e}")
        return []

def generate_grid_levels(zone_config):
    """
    Generates a list of grid prices within the zone.
    Range: [price_low, price_high] with step GRID_STEP_PRICE.
    """
    low = float(zone_config['price_low'])
    high = float(zone_config['price_high'])
    
    levels = []
    current_level = low
    while current_level <= high:
        levels.append(current_level)
        current_level += GRID_STEP_PRICE
        
    return levels

def get_open_trades():
    """Fetches all OPEN trades from Supabase."""
    table_name = "paper_trade_log" if TRADING_MODE == 'PAPER' else "trade_log"
    try:
        # Note: Schema might not have 'symbol', we assume all trades are for this system (BTCUSDT)
        response = supabase_client.table(table_name)\
            .select("*")\
            .eq("status", "OPEN")\
            .execute()
        return response.data
    except Exception as e:
        log(f"❌ Error fetching open trades: {e}")
        return []

def execute_buy(zone, grid_price, market_price, step_size, current_rsi):
    """
    Executes a BUY order (Limit or Market).
    """
    global LAST_TRADE_TIME
    
    # Check Cooldown
    if time.time() - LAST_TRADE_TIME < TRADE_COOLDOWN:
        log(f"⏳ Trade Cooldown Active. Skipping BUY. ({int(TRADE_COOLDOWN - (time.time() - LAST_TRADE_TIME))}s left)")
        return

    trade_size_usdt = TRADE_SIZE_USDT
    qty = round_step_size(trade_size_usdt / market_price, step_size)
    
    if qty > MAX_TRADE_QTY:
        qty = MAX_TRADE_QTY
        
    log(f"[BUY SIGNAL] Grid: {grid_price} | Price: {market_price} | Qty: {qty} | RSI: {current_rsi:.2f}")

    if TRADING_MODE == 'DRY_RUN':
        log(f"💊 [DRY RUN] Would BUY {qty} BTC @ {market_price}")
        LAST_TRADE_TIME = time.time() # Update cooldown even in Dry Run
        return

    try:
        order = None
        if TRADING_MODE == 'LIVE':
            # Execute Real Order
            order = binance_client.create_order(
                symbol=SYMBOL,
                side=SIDE_BUY,
                type=ORDER_TYPE_MARKET,
                quantity=qty
            )
        elif TRADING_MODE == 'PAPER':
            # Execute Mock Order
            order = execute_mock_order(SIDE_BUY, qty, market_price)
        
        # Update Global State
        LAST_TRADE_TIME = time.time()
        
        # Log to Supabase
        cummulative_quote_qty = float(order['cummulativeQuoteQty'])
        executed_qty = float(order['executedQty'])
        avg_price = cummulative_quote_qty / executed_qty if executed_qty > 0 else market_price

        # Specific Logic for Paper vs Live Table
        table_name = "paper_trade_log" if TRADING_MODE == 'PAPER' else "trade_log"
        
        data = {
            "order_type": "BUY",
            "zone_name": zone['zone_name'],
            "entry_price": avg_price,
            "quantity": executed_qty,
            "status": "OPEN",
            "rsi_entry": float(current_rsi), # NEW: Save RSI
            "notes": f"Grid Level {grid_price}. OrderID: {order['orderId']}" 
        }

        if TRADING_MODE == 'PAPER':
            # Add fields specific to paper_trade_log
            data["total_usdt"] = cummulative_quote_qty
            data["fee_usdt"] = cummulative_quote_qty * TRADING_FEE_RATE

        supabase_client.table(table_name).insert(data).execute()
        log(f"[OK] {TRADING_MODE} BUY Executed & Logged: {executed_qty} BTC @ {avg_price}")

    except Exception as e:
        log(f"❌ {TRADING_MODE} BUY Failure: {e}")

def execute_sell(trade, market_price, step_size, current_rsi, market_regime='UNKNOWN'):
    """Executes a SELL (Take Profit) order."""
    log(f"[SELL SIGNAL] Entry: {trade['entry_price']} | Price: {market_price} | Target: {float(trade['entry_price']) + TP_PROFIT}")
    
    if TRADING_MODE == 'DRY_RUN':
        log(f"💊 [DRY RUN] Would SELL {trade['quantity']} BTC @ {market_price}. PnL: ~{(market_price - float(trade['entry_price'])) * float(trade['quantity']):.2f} USDT")
        return

    try:
        qty = float(trade['quantity'])
        order = None

        if TRADING_MODE == 'LIVE':
            # Execute Real Order
            order = binance_client.create_order(
                symbol=SYMBOL,
                side=SIDE_SELL,
                type=ORDER_TYPE_MARKET,
                quantity=qty
            )
        elif TRADING_MODE == 'PAPER':
             # Execute Mock Order
            order = execute_mock_order(SIDE_SELL, qty, market_price)
        
        # Log update to Supabase
        cummulative_quote_qty = float(order['cummulativeQuoteQty'])
        executed_qty = float(order['executedQty'])
        exit_price = cummulative_quote_qty / executed_qty if executed_qty > 0 else market_price
        
        # Calculate Trade Economics
        entry_price_val = float(trade['entry_price'])
        buy_value = entry_price_val * executed_qty
        sell_value = exit_price * executed_qty
        
        # Estimate Fees (Roundtrip: Buy + Sell)
        estimated_total_fee = (buy_value + sell_value) * TRADING_FEE_RATE
        
        # Net Profit
        net_pnl = sell_value - buy_value - estimated_total_fee
        
        pnl_percent = ((exit_price - entry_price_val) / entry_price_val) * 100

        update_data = {
            "exit_price": exit_price,
            "exit_at": datetime.now(timezone.utc).isoformat(),
            "pnl_usdt": net_pnl,  # Storing Net PnL
            "pnl_percent": pnl_percent,
            "status": "CLOSED",
            "rsi_exit": float(current_rsi), # NEW: Save RSI Exit
            "notes": f"{trade.get('notes', '')} | Closed at {exit_price} | Net PnL: {net_pnl:.2f}"
        }

        table_name = "paper_trade_log" if TRADING_MODE == 'PAPER' else "trade_log"
        
        if TRADING_MODE == 'PAPER':
            # Update fee_usdt for paper trade
            # In Buy order we only stored Buy Fee. Now we need to update it to Total Fee (Buy + Sell).
            # But wait, the schema says: "Update fee_usdt (accumulate Buy Fee + Sell Fee)."
            # So if we stored buy fee, we should add sell fee? Or just overwrite with total estimated fee?
            # Re-reading: "Values: ... fee_usdt".
            # If I overwrite it with `estimated_total_fee` (which is Buy+Sell), that is correct.
            update_data["fee_usdt"] = estimated_total_fee

        supabase_client.table(table_name).update(update_data).eq("id", trade['id']).execute()
        
        log(f"[SUCCESS] {TRADING_MODE} Trade Closed! Gross: {sell_value - buy_value:.2f} | Net PnL: {net_pnl:.2f} | Fee: {estimated_total_fee:.2f}")

        # Trigger AI Analysis
        try:
            completed_trade_data = trade.copy()
            completed_trade_data.update(update_data)
            completed_trade_data['market_regime'] = market_regime
            send_trade_to_analysis(completed_trade_data)
        except Exception:
            pass # Creating payload failed, ignore

    except Exception as e:
        log(f"❌ {TRADING_MODE} SELL Failure: {e}")

    except Exception as e:
        log(f"❌ {TRADING_MODE} SELL Failure: {e}")

# --- Main Loop ---

def start_bot():
    global RSI_LIMIT, TP_PROFIT, GRID_STEP_PRICE, TRADE_COOLDOWN, TRADE_SIZE_USDT, SECURED_TRADES, LAST_SNAPSHOT_TIME
    
    # Pre-fetch settings for accurate startup log
    initial_settings = get_bot_settings()
    if initial_settings:
        RSI_LIMIT = int(initial_settings.get('rsi_limit', RSI_LIMIT))
        TP_PROFIT = float(initial_settings.get('tp_usdt', TP_PROFIT))
        GRID_STEP_PRICE = float(initial_settings.get('grid_step_usdt', GRID_STEP_PRICE))
        TRADE_COOLDOWN = int(initial_settings.get('trade_cooldown', TRADE_COOLDOWN))
        TRADE_SIZE_USDT = float(initial_settings.get('trade_size_usdt', TRADE_SIZE_USDT))

    log(f"[START] Bot Starting... MODE={TRADING_MODE} | Step=${GRID_STEP_PRICE} | TP=${TP_PROFIT} | RSI Limit: {RSI_LIMIT} | Size=${TRADE_SIZE_USDT}")
    step_size = get_symbol_step_size(SYMBOL)
    
    while True:
        try:
            # 0. Dynamic Configuration & Master Switch
            settings = get_bot_settings()
            if settings:
                # Update Globals - Keep updating in loop for dynamic changes
                RSI_LIMIT = int(settings.get('rsi_limit', RSI_LIMIT))
                TP_PROFIT = float(settings.get('tp_usdt', TP_PROFIT))
                GRID_STEP_PRICE = float(settings.get('grid_step_usdt', GRID_STEP_PRICE))
                TRADE_COOLDOWN = int(settings.get('trade_cooldown', TRADE_COOLDOWN))
                TRADE_SIZE_USDT = float(settings.get('trade_size_usdt', TRADE_SIZE_USDT))
                
                is_active = settings.get('is_active', True)
                if not is_active:
                    log("[PAUSE] Bot Paused via Dashboard (Master Switch OFF). Sleeping...")
                    time.sleep(LOOP_INTERVAL)
                    continue

            # 0.5 Snapshot Check (For Portfolio Tracking)
            if time.time() - LAST_SNAPSHOT_TIME > SNAPSHOT_INTERVAL:
                # Capture snapshot
                # Note: Capture runs in main thread here, might delay 1-2s. Acceptable.
                log(f"[SNAPSHOT] Running Hourly Portfolio Snapshot...")
                capture_snapshot(supabase_client, binance_client, mode=TRADING_MODE)
                LAST_SNAPSHOT_TIME = time.time()

            # 1. Fetch Active Zones & Price
            active_zones = fetch_active_zones()
            if not active_zones:
                log("⚠️ No Active Zones found. Sleeping...")
                time.sleep(LOOP_INTERVAL)
                continue

            current_price = get_market_price(SYMBOL)
            if not current_price:
                time.sleep(10)
                continue
            
            # --- MARKET REGIME ANALYSIS ---
            market_regime, current_adx = analyze_market_regime(SYMBOL)
            log(f"[ANALYSIS] Regime: {market_regime} | ADX: {current_adx:.2f}")

            # 2. Select Correct Zone based on Price
            active_zone = None
            for zone in active_zones:
                z_low = float(zone['price_low'])
                z_high = float(zone['price_high'])
                
                if z_low <= current_price <= z_high:
                    active_zone = zone
                    log(f"[OK] Active Zone Selected: {zone['zone_name']} ({z_low}-{z_high})")
                    break
            
            if not active_zone:
                # Fallback: Price is outside ALL active zones
                log(f"⚠️ Price {current_price} is OUTSIDE all Active Zones. Trading Paused.")
                time.sleep(LOOP_INTERVAL)
                continue
            
            # Fetch RSI
            current_rsi = calculate_rsi(SYMBOL)
            log(f"[STATS] Market Data | Price: {current_price:.2f} | RSI: {current_rsi:.2f}")

            # 3. Get State
            grid_levels = generate_grid_levels(active_zone)
            open_trades = get_open_trades()
            
            # Map open trades to grid levels and calculate zone usage
            occupied_levels = []
            current_zone_invested = 0.0
            
            for t in open_trades:
                # Track occupied levels
                entry = float(t['entry_price'])
                occupied_levels.append(entry)
                
                # Calculate invested capital for this zone
                # Check if trade belongs to current active zone (by name or ID if available)
                # Note: t['zone_name'] is available from fetch
                if t.get('zone_name') == active_zone['zone_name']:
                    # Use total_usdt if available, else calc
                    trade_val = float(t.get('total_usdt') or 0)
                    if trade_val == 0:
                        trade_val = float(t['entry_price']) * float(t['quantity'])
                    current_zone_invested += trade_val

            log(f"[STATUS] Status: {len(open_trades)} Open Trades | Zone Usage: ${current_zone_invested:,.2f} / ${float(active_zone['capital_allocated']):,.2f}")

            # 4. Check BUY Conditions (Entry)
            # --- Permission Check (Pre-Loop) ---
            can_buy = True
            buy_block_reason = None
            
            # A. Budget Check
            allocated_cap = float(active_zone['capital_allocated'])
            if current_zone_invested + TRADE_SIZE_USDT > allocated_cap:
                can_buy = False
                buy_block_reason = f"💰 Zone Budget Exceeded (${current_zone_invested:,.2f} + ${TRADE_SIZE_USDT} > ${allocated_cap:,.2f})"

            # B. Regime & RSI Check (Only check if budget allows)
            if can_buy:
                is_rsi_safe = current_rsi < RSI_LIMIT
                
                if market_regime == 'BEAR_TREND':
                    if current_rsi < 30:
                        is_rsi_safe = True
                    else:
                        is_rsi_safe = False
                        buy_block_reason = f"🐻 Market is BEARISH & RSI High ({current_rsi:.2f} >= 30)"
                elif not is_rsi_safe:
                     buy_block_reason = f"⚠️ RSI High ({current_rsi:.2f} >= {RSI_LIMIT})"
                
                if not is_rsi_safe:
                    can_buy = False
            
            # Log Permission Status ONCE
            if not can_buy:
                log(f"[STOP] Trading Paused: {buy_block_reason}")
            
            # Execute Grid Checks ONLY if allowed
            if can_buy:
                for level in grid_levels:
                    # Optimized Bucket Logic: Only buy if price is within the bucket BELOW the level
                    # and ABOVE the previous level (approximately)
                    # Effectively: (Grid - Step) < Price <= Grid
                    
                    lower_bound = level - GRID_STEP_PRICE
                    
                    # Condition A: Price is inside the immediate bucket of this specific grid level
                    is_in_bucket = lower_bound < current_price <= level
                    
                    # Condition B: Level is empty
                    is_occupied = False
                    for occ_price in occupied_levels:
                        if abs(occ_price - level) < 10.0: # $10 Tolerance
                            is_occupied = True
                            break
                    
                    if is_in_bucket and not is_occupied:
                        # We already checked RSI/Regime globally, so we are safe to buy
                        execute_buy(active_zone, level, current_price, step_size, current_rsi)
                        # Break after one trade attempt to wait for next loop (and cooldown)
                        break 
                    # No else logging here to prevent spam


            # 5. Check SELL Conditions (Take Profit & Smart Exit)
            for trade in open_trades:
                entry = float(trade['entry_price'])
                target_price = entry + TP_PROFIT
                trade_id = trade['id']
                
                # --- Smart Exit Logic ---
                # Check if we should mark as SECURED
                # 50% to Target
                secure_trigger_price = entry + (TP_PROFIT * 0.5)
                
                if current_price >= secure_trigger_price:
                    if trade_id not in SECURED_TRADES:
                        log(f"[SECURED] Trade {trade_id} SECURED! (Price hit > 50% to TP)")
                        SECURED_TRADES.add(trade_id)
                
                # If Secured, Check for Breakeven Stop
                if trade_id in SECURED_TRADES:
                    breakeven_price = entry + 10.0 # Buffer to cover fees
                    if current_price <= breakeven_price:
                        log(f"[SECURED] [SMART EXIT] Trade {trade_id} hit Breakeven Trigger! Closing to protect funds.")
                        execute_sell(trade, current_price, step_size, current_rsi, market_regime)
                        SECURED_TRADES.remove(trade_id) # Clean up
                        continue # Trade closed, move to next

                # Normal TP Check
                if current_price >= target_price:
                    execute_sell(trade, current_price, step_size, current_rsi, market_regime)
                    if trade_id in SECURED_TRADES:
                        SECURED_TRADES.remove(trade_id)

            log("💤 Waiting for price action...")
            time.sleep(LOOP_INTERVAL)

        except Exception as e:
            log(f"[CRITICAL] Error in main loop: {e}")
            time.sleep(LOOP_INTERVAL)

if __name__ == "__main__":
    try:
        start_bot()
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user.")
