
import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(override=True)
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    print("❌ Critical Error: Supabase credentials missing!")
    exit()

supabase = create_client(supabase_url, supabase_key)

print("[SEARCH] STARTING SYSTEM DATA AUDIT...\n")

# 1. Check Portfolio Snapshots
print("[STATS] 1. Checking Portfolio Snapshots...")
try:
    res = supabase.table("portfolio_snapshots").select("*").order("snapshot_time", desc=True).limit(20).execute()
    data = res.data
    if data:
        df = pd.DataFrame(data)
        print(f"   [OK] Found {len(data)} recent snapshots.")
        # Select key columns
        display_cols = ['snapshot_time', 'btc_price', 'total_equity_usdt', 'realized_pnl', 'current_drawdown_pct']
        print(df[display_cols].to_string())
        
        # Check Interval (Roughly)
        last_time = pd.to_datetime(df['snapshot_time'].iloc[0])
        prev_time = pd.to_datetime(df['snapshot_time'].iloc[1]) if len(df) > 1 else last_time
        print(f"\n   [TIME] Last Snapshot: {last_time}")
        print(f"   [TIME] Interval check: {(last_time - prev_time).total_seconds()/3600:.2f} hours diff (approx)")
    else:
        print("   [WARN] No Snapshot Data found!")
except Exception as e:
    print(f"   [ERROR] Error fetching snapshots: {e}")

print("-" * 50)

# 2. Check AI Analysis in Paper Trade Log
print("[AI] 2. Checking AI Integration (paper_trade_log)...")
try:
    # Fetch recent CLOSED trades
    res = supabase.table("paper_trade_log")\
        .select("id, exit_at, pnl_usdt, ai_analysis, ai_score")\
        .eq("status", "CLOSED")\
        .order("exit_at", desc=True)\
        .limit(5)\
        .execute()
    
    data = res.data
    if data:
        print(f"   [OK] Found {len(data)} recent CLOSED trades.")
        for trade in data:
            has_ai = "[YES]" if trade.get('ai_analysis') else "[NO]"
            print(f"   - Trade ID {trade['id']}: PnL ${trade['pnl_usdt']} | AI Data: {has_ai}")
            if trade.get('ai_analysis'):
                print(f"     [OPINION] AI Says: {trade['ai_analysis'][:100]}...")
                print(f"     [SCORE] Score: {trade['ai_score']}")
    else:
        print("   [INFO] No CLOSED trades found recently (Maybe only OPEN trades?)")
        
except Exception as e:
    print(f"   [ERROR] Error fetching trade log: {e}")

print("-" * 50)

# 3. Check Baseline
print("[BASE] 3. Checking Baseline Prices...")
try:
    res = supabase.table("baseline_prices").select("*").execute()
    if res.data:
        for row in res.data:
            print(f"   [OK] Symbol: {row['symbol']} | Baseline: ${row['baseline_price']} | Date: {row['baseline_date']}")
    else:
        print("   [WARN] No Baseline data found!")
except Exception as e:
    print(f"   [ERROR] Error checking baseline: {e}")

print("\n[DONE] AUDIT COMPLETE")
