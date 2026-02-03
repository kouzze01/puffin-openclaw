import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

try:
    supabase: Client = create_client(url, key)
    
    # Fetch all CLOSED trades (Profit realized)
    response = supabase.table("paper_trade_log").select("*").eq("status", "CLOSED").execute()
    
    trades = response.data
    
    if not trades:
        print("No CLOSED trades found.")
    else:
        print(f"Found {len(trades)} CLOSED trades.")
        
        total_pnl = 0.0
        total_fee = 0.0
        
        print("\n--- Profitable Trades ---")
        for trade in trades:
            pnl = float(trade.get('pnl_usdt') or 0.0)
            fee = float(trade.get('fee_usdt') or 0.0)
            total_pnl += pnl
            total_fee += fee
            
            print(f"Time: {trade['created_at']} | PnL: {pnl:.4f} USDT | Fee: {fee:.4f} USDT | Price: {trade['entry_price']}")

        net_profit = total_pnl - total_fee
        print("\n" + "="*30)
        print(f"Total Gross PnL: {total_pnl:.4f} USDT")
        print(f"Total Fees:      {total_fee:.4f} USDT")
        print(f"Net Profit:      {net_profit:.4f} USDT")
        print("="*30)

except Exception as e:
    print(f"Error analyzing profits: {e}")
