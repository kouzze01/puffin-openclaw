import os
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
    
    # Check paper_trade_log
    response = supabase.table("paper_trade_log").select("id", count="exact").execute()
    count = response.count if hasattr(response, 'count') else len(response.data)
    print(f"Total records in paper_trade_log: {count}")
    
    if count > 0:
        # Get last 5 trades
        recent = supabase.table("paper_trade_log").select("*").order("created_at", desc=True).limit(5).execute()
        print("\nLast 5 Paper Trades:")
        for trade in recent.data:
            print(f"- {trade['created_at']} | {trade['order_type']} | qty: {trade['quantity']} | price: {trade['entry_price']} | status: {trade['status']}")
            if trade['order_type'] == 'SELL':
                print(f"  PnL: {trade.get('pnl_usdt', 'N/A')} | Fee: {trade.get('fee_usdt', 'N/A')}")
    
    # Check if there are any OPEN paper trades
    open_trades = supabase.table("paper_trade_log").select("*").eq("status", "OPEN").execute()
    print(f"\nTotal OPEN paper trades: {len(open_trades.data)}")

except Exception as e:
    print(f"Error checking paper trades: {e}")
