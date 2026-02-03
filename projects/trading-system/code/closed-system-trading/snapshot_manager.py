
import os
import time
from datetime import datetime, timezone
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client as SupabaseClient

# Load env variables (re-load here to be self-contained or pass client in)
load_dotenv(override=True)

# We can either instantiate client here or pass it from main bot
# To keep it modular, let's accept client as argument, but also support standalone.

def get_supabase_client():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if not url or not key:
        return None
    return create_client(url, key)

def calculate_unrealized_pnl(open_trades, current_price):
    """
    Calculates total Unrealized P&L for all open trades.
    Formula: Sum( (CurrentPrice - EntryPrice) * Quantity )
    """
    total_unrealized = 0.0
    total_position_btc = 0.0
    total_position_value = 0.0
    
    for trade in open_trades:
        try:
            entry = float(trade['entry_price'])
            qty = float(trade['quantity'])
            
            # PnL for this trade
            pnl = (current_price - entry) * qty
            total_unrealized += pnl
            
            total_position_btc += qty
            total_position_value += (current_price * qty)
            
        except Exception as e:
            print(f"⚠️ Error calculating PnL for trade {trade.get('id')}: {e}")
            continue
            
    return total_unrealized, total_position_btc, total_position_value

def fetch_baseline_price(supabase: SupabaseClient, symbol='BTCUSDT'):
    try:
        response = supabase.table("baseline_prices").select("*").eq("symbol", symbol).execute()
        if response.data:
            return float(response.data[0]['baseline_price'])
    except Exception as e:
        print(f"⚠️ Error fetching baseline: {e}")
    return None

def fetch_portfolio_stats(supabase: SupabaseClient, is_paper=True):
    """Fetch realized P&L and fees."""
    table = "paper_trade_log" if is_paper else "trade_log"
    
    realized_pnl = 0.0
    fees_paid = 0.0
    
    try:
        # We need to aggregate stats. 
        # Note: Supabase-js has aggregate, python client is limited.
        # We'll select columns and sum in python for now (assuming not millions of rows yet).
        # For production with large data, use RPC function in Postgres.
        
        # Fetch CLOSED trades for Realized PnL
        res = supabase.table(table).select("pnl_usdt, fee_usdt").eq("status", "CLOSED").execute()
        df_closed = pd.DataFrame(res.data)
        
        if not df_closed.empty:
            if 'pnl_usdt' in df_closed.columns:
                realized_pnl = df_closed['pnl_usdt'].sum()
            if 'fee_usdt' in df_closed.columns:
                fees_paid += df_closed['fee_usdt'].sum()
        
        # Also need fees from OPEN trades (Buy fees are already paid/recorded?)
        # In paper mode, we record buy fee immediately? 
        # The schema has fee_usdt. Let's check open trades for fees too.
        res_open = supabase.table(table).select("fee_usdt").eq("status", "OPEN").execute()
        df_open = pd.DataFrame(res_open.data)
        if not df_open.empty:
             if 'fee_usdt' in df_open.columns:
                fees_paid += df_open['fee_usdt'].sum()

    except Exception as e:
        print(f"⚠️ Error fetching portfolio stats: {e}")
        
    return realized_pnl, fees_paid

def capture_snapshot(supabase: SupabaseClient, binance_client, mode='PAPER'):
    """
    Main function to capture and save portfolio snapshot.
    """
    try:
        # 1. Get Market Data
        ticker = binance_client.get_symbol_ticker(symbol='BTCUSDT')
        current_price = float(ticker['price'])
        
        # 2. Get Open Trades
        table_name = "paper_trade_log" if mode == 'PAPER' else "trade_log"
        open_trades_res = supabase.table(table_name).select("*").eq("status", "OPEN").execute()
        open_trades = open_trades_res.data
        
        # 3. Calculate Unrealized Metrics
        unrealized_pnl, total_pos_btc, total_pos_value = calculate_unrealized_pnl(open_trades, current_price)
        
        # 4. Get Realized Stats
        realized_pnl, total_fees = fetch_portfolio_stats(supabase, is_paper=(mode=='PAPER'))
        
        # 5. Get Cash Balance (Simulated or Real)
        # For Paper, we might calculate cash based on Initial - NetInvested + Realized?
        # Or just track "Equity" = Initial + Realized + Unrealized.
        
        # Let's fetch Baseline info first
        baseline_price = fetch_baseline_price(supabase, 'BTCUSDT')
        
        # Try to find Initial Capital
        initial_capital = 0.0
        try:
             res = supabase.table("baseline_prices").select("initial_capital").eq("symbol", "BTCUSDT").execute()
             if res.data and res.data[0]['initial_capital']:
                 initial_capital = float(res.data[0]['initial_capital'])
        except:
            pass
            
        # Total Equity Calculation
        # Equity = Initial Capital + Realized PnL + Unrealized PnL - Fees (if not already deducted from realized)
        # Note: My realized_pnl logic usually is "Net PnL" (after fees).
        # Let's assume realized_pnl is NET.
        # Then Equity = Initial + Realized_Net + Unrealized_Gross - (Unrealized Fees? No, unrealized PnL is usually gross until close)
        # Let's keep it simple: Equity = Initial + Realized + Unrealized.
        
        if initial_capital == 0:
            # Fallback if not set, maybe assume start from 0 profit
            total_equity = realized_pnl + unrealized_pnl 
        else:
            total_equity = initial_capital + realized_pnl + unrealized_pnl

        # 6. Calculate Drawdown
        # Need Peak Equity
        peak_equity = total_equity # Default to current if no history
        
        # Fetch max equity from history
        try:
            # Perform a query to get max(total_equity_usdt)
            # direct ordering
            res_max = supabase.table("portfolio_snapshots")\
                .select("total_equity_usdt")\
                .order("total_equity_usdt", desc=True)\
                .limit(1)\
                .execute()
            if res_max.data:
                hist_peak = float(res_max.data[0]['total_equity_usdt'])
                peak_equity = max(peak_equity, hist_peak)
        except Exception as e:
            print(f"⚠️ Error fetching peak equity: {e}")
            
        # Drawdown %
        drawdown_pct = 0.0
        if peak_equity > 0:
            drawdown_pct = (peak_equity - total_equity) / peak_equity * 100
            
        # Baseline Return
        baseline_return = 0.0
        if baseline_price and baseline_price > 0:
            baseline_return = (current_price - baseline_price) / baseline_price * 100
            
        # 7. Insert Snapshot
        snapshot_data = {
            "symbol": "BTCUSDT",
            "btc_price": current_price,
            "total_equity_usdt": total_equity,
            "realized_pnl": realized_pnl,
            "unrealized_pnl": unrealized_pnl,
            "total_fees_paid": total_fees,
            "open_trade_count": len(open_trades),
            "total_position_btc": total_pos_btc,
            "total_position_usdt": total_pos_value,
            "peak_equity": peak_equity,
            "current_drawdown_pct": drawdown_pct,
            "max_drawdown_pct": 0, # To be calculated or updated? Let's just store current DD, and max is derived
            "baseline_price": baseline_price,
            "baseline_return_pct": baseline_return,
            "snapshot_time": datetime.now(timezone.utc).isoformat()
        }
        
        supabase.table("portfolio_snapshots").insert(snapshot_data).execute()
        print(f"📸 Portfolio Snapshot Captured. Equity: ${total_equity:,.2f} | DD: {drawdown_pct:.2f}%")
        
    except Exception as e:
        print(f"❌ Snapshot Capture Failed: {e}")

if __name__ == "__main__":
    # Test Run
    print("Testing Snapshot...")
    s = get_supabase_client()
    # Need binance client too, we can create one
    from binance.client import Client
    b_key = os.getenv('BINANCE_API_KEY')
    b_sec = os.getenv('BINANCE_API_SECRET')
    b = Client(b_key, b_sec)
    
    capture_snapshot(s, b, mode='PAPER')
