"""
Backfill AI Analysis Script
============================
This script fetches all closed trades without AI analysis
and sends them to the n8n webhook for processing.

Usage: python backfill_ai_analysis.py
"""

import os
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv(override=True)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
DELAY_SECONDS = 15  # Wait time between each request

# Validate environment
if not all([SUPABASE_URL, SUPABASE_KEY, N8N_WEBHOOK_URL]):
    print("[ERROR] Missing environment variables. Check .env file.")
    exit(1)

# Initialize Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_trades_without_ai(table_name):
    """Fetch all closed trades that don't have AI analysis yet."""
    try:
        response = supabase.table(table_name)\
            .select("*")\
            .eq("status", "CLOSED")\
            .is_("ai_analysis", "null")\
            .order("exit_at", desc=False)\
            .execute()
        return response.data
    except Exception as e:
        print(f"[ERROR] Failed to fetch trades: {e}")
        return []

def send_to_webhook(trade, mode):
    """Send trade data to n8n webhook for AI analysis."""
    try:
        payload = {
            "trade_id": trade.get('id'),
            "mode": mode,
            "pair": "BTCUSDT",
            "entry_price": float(trade.get('entry_price', 0)),
            "exit_price": float(trade.get('exit_price', 0) or 0),
            "quantity": float(trade.get('quantity', 0)),
            "pnl_usdt": float(trade.get('pnl_usdt', 0)),
            "zone_name": trade.get('zone_name', 'Unknown'),
            "market_regime": "UNKNOWN",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        headers = {"Content-Type": "application/json"}
        response = requests.post(N8N_WEBHOOK_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            print(f"   [WARN] Webhook returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   [ERROR] Failed to send: {e}")
        return False

def main():
    print("=" * 50)
    print("   BACKFILL AI ANALYSIS SCRIPT")
    print("=" * 50)
    print(f"[INFO] Webhook URL: {N8N_WEBHOOK_URL[:50]}...")
    print(f"[INFO] Delay between requests: {DELAY_SECONDS} seconds")
    print()
    
    # Fetch trades from paper_trade_log (change to trade_log for live)
    table = "paper_trade_log"
    mode = "PAPER"
    
    print(f"[STEP 1] Fetching closed trades without AI analysis from '{table}'...")
    trades = fetch_trades_without_ai(table)
    
    if not trades:
        print("[INFO] No trades found that need AI analysis. All done!")
        return
    
    print(f"[INFO] Found {len(trades)} trades to process.")
    print()
    
    # Process each trade
    success_count = 0
    fail_count = 0
    
    for i, trade in enumerate(trades, 1):
        trade_id = trade.get('id')
        pnl = trade.get('pnl_usdt', 0)
        zone = trade.get('zone_name', 'N/A')
        
        print(f"[{i}/{len(trades)}] Processing Trade #{trade_id} | Zone: {zone} | PnL: ${pnl:.4f}")
        
        if send_to_webhook(trade, mode):
            print(f"   [OK] Sent to AI successfully!")
            success_count += 1
        else:
            fail_count += 1
        
        # Wait before next request (except for the last one)
        if i < len(trades):
            print(f"   [WAIT] Waiting {DELAY_SECONDS} seconds before next request...")
            time.sleep(DELAY_SECONDS)
        
        print()
    
    # Summary
    print("=" * 50)
    print("   BACKFILL COMPLETE!")
    print("=" * 50)
    print(f"   Total Processed: {len(trades)}")
    print(f"   Success: {success_count}")
    print(f"   Failed: {fail_count}")
    print()
    print("[TIP] Run 'python audit_system.py' to verify AI data was saved.")

if __name__ == "__main__":
    main()
