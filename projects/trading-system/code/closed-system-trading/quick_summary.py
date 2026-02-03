import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

try:
    supabase: Client = create_client(url, key)
    
    # Fetch all data from paper_trade_log
    response = supabase.table("paper_trade_log").select("*").execute()
    data = response.data
    
    if not data:
        print("No records found in paper_trade_log.")
        exit(0)
        
    df = pd.DataFrame(data)
    
    # Pre-process columns
    for col in ['pnl_usdt', 'fee_usdt', 'entry_price', 'exit_price', 'quantity']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
    # Statistics
    closed_trades = df[df['status'] == 'CLOSED']
    open_trades = df[df['status'] == 'OPEN']
    
    total_realized_pnl = closed_trades['pnl_usdt'].sum()
    total_fees = df['fee_usdt'].sum()
    num_closed = len(closed_trades)
    num_open = len(open_trades)
    
    win_trades = closed_trades[closed_trades['pnl_usdt'] > 0]
    win_rate = (len(win_trades) / num_closed * 100) if num_closed > 0 else 0
    
    avg_pnl = closed_trades['pnl_usdt'].mean() if num_closed > 0 else 0
    
    print("=== Paper Trading Summary ===")
    print(f"Total Records: {len(df)}")
    print(f"Closed Trades: {num_closed}")
    print(f"Open Trades:   {num_open}")
    print("-" * 30)
    print(f"Total Realized PnL: {total_realized_pnl:.2f} USDT")
    print(f"Total Fees Paid:    {total_fees:.2f} USDT")
    print(f"Net Realized PnL:   {total_realized_pnl:.2f} USDT (Fees already deducted in pnl_usdt in trade_and_log.py)")
    print("-" * 30)
    print(f"Win Rate:    {win_rate:.1f}%")
    print(f"Avg PnL/Trade: {avg_pnl:.2f} USDT")
    
    if num_closed > 0:
        print("\nLatest 5 Closed Trades:")
        latest_closed = closed_trades.sort_values(by='exit_at', ascending=False).head(5)
        for _, row in latest_closed.iterrows():
            print(f"- {row['exit_at'][:19]} | Entry: {row['entry_price']:.2f} | Exit: {row['exit_price']:.2f} | PnL: {row['pnl_usdt']:.2f} USDT")

except Exception as e:
    print(f"Error: {e}")
