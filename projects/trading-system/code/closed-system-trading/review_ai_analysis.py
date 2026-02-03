"""Review AI Analysis Results for Closed Trades"""
import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# Fetch all CLOSED trades with AI data
response = supabase.table("paper_trade_log")\
    .select("id, zone_name, entry_price, exit_price, pnl_usdt, ai_score, ai_analysis")\
    .eq("status", "CLOSED")\
    .order("id", desc=False)\
    .execute()

df = pd.DataFrame(response.data)

print("=" * 70)
print("   AI ANALYSIS REVIEW - CLOSED TRADES")
print("=" * 70)
print()

if df.empty:
    print("No closed trades found.")
else:
    # Summary Stats
    avg_score = df['ai_score'].mean()
    all_same_score = df['ai_score'].nunique() == 1
    
    print(f"Total Closed Trades: {len(df)}")
    print(f"Average AI Score: {avg_score:.1f}/10")
    print(f"Score Range: {df['ai_score'].min()} - {df['ai_score'].max()}")
    print()
    
    if all_same_score:
        print("[WARNING] All trades have the SAME score! Possible issue with AI prompt or data.")
        print()
    
    # Check for potential issues
    issues = []
    
    # Issue 1: All scores are the same
    if all_same_score:
        issues.append("All trades got the same score - AI might not be differentiating well")
    
    # Issue 2: Very low scores for profitable trades
    profitable_low_score = df[(df['pnl_usdt'] > 0) & (df['ai_score'] < 5)]
    if len(profitable_low_score) > 0:
        issues.append(f"{len(profitable_low_score)} profitable trades got low scores (< 5)")
    
    # Issue 3: Analysis too short or generic
    short_analysis = df[df['ai_analysis'].str.len() < 50]
    if len(short_analysis) > 0:
        issues.append(f"{len(short_analysis)} trades have very short analysis (< 50 chars)")
    
    print("-" * 70)
    print("POTENTIAL ISSUES:")
    if issues:
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
    else:
        print("  No obvious issues detected!")
    print("-" * 70)
    print()
    
    # Detailed Trade Analysis
    print("DETAILED ANALYSIS BY TRADE:")
    print("-" * 70)
    
    for idx, row in df.iterrows():
        trade_id = row['id']
        pnl = row['pnl_usdt']
        score = row['ai_score']
        analysis = row['ai_analysis'] or "N/A"
        zone = row['zone_name'] or "N/A"
        entry = row['entry_price']
        exit_p = row['exit_price']
        
        pnl_status = "PROFIT" if pnl > 0 else "LOSS"
        
        print(f"Trade #{trade_id} | {zone}")
        print(f"  Entry: ${entry:,.2f} -> Exit: ${exit_p:,.2f}")
        print(f"  P&L: ${pnl:.4f} ({pnl_status}) | AI Score: {score}/10")
        print(f"  AI Analysis:")
        print(f"    {analysis[:200]}{'...' if len(analysis) > 200 else ''}")
        print()
