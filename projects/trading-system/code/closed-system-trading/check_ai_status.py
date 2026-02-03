"""Quick check of paper_trade_log status"""
import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Fetch ALL trades
response = supabase.table("paper_trade_log").select("id, status, ai_analysis, ai_score").execute()
df = pd.DataFrame(response.data)

print("=== PAPER TRADE LOG SUMMARY ===")
print(f"Total Rows: {len(df)}")
print()

# Status breakdown
print("Status Breakdown:")
print(df['status'].value_counts())
print()

# AI Analysis breakdown for CLOSED trades
closed = df[df['status'] == 'CLOSED']
print(f"Total CLOSED Trades: {len(closed)}")

# Check ai_analysis values
has_ai = closed[closed['ai_analysis'].notna() & (closed['ai_analysis'] != '')]
no_ai = closed[closed['ai_analysis'].isna() | (closed['ai_analysis'] == '')]

print(f"  - With AI Analysis: {len(has_ai)}")
print(f"  - Without AI Analysis: {len(no_ai)}")

if not no_ai.empty:
    print()
    print("Trade IDs without AI:")
    print(no_ai['id'].tolist())
