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
    
    # Fetch trade data
    response = supabase.table("paper_trade_log").select("created_at").execute()
    data = response.data
    
    if not data:
        print("No records found.")
        exit(0)
        
    df = pd.DataFrame(data)
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['date'] = df['created_at'].dt.date
    
    daily_counts = df.groupby('date').size().reset_index(name='trades')
    print("=== Daily Trade Counts ===")
    print(daily_counts.to_string(index=False))
    
    # Check specifically for the gap days
    print("\nRecent records:")
    print(df.sort_values(by='created_at', ascending=False).head(10).to_string(index=False))

except Exception as e:
    print(f"Error: {e}")
