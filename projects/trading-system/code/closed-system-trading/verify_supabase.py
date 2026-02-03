import os
import time
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env")
    exit(1)

try:
    print(f"Connecting to Supabase at {url}...")
    supabase: Client = create_client(url, key)
    
    # 1. Verify Authentication (simple health check or getting user - might fail if no user logic, so we skip to table check)
    print("Client initialized.")

    # 2. Check Tables
    tables_to_check = ['zones_config', 'portfolio_summary', 'trade_log']
    missing_tables = []
    
    for table in tables_to_check:
        try:
            # Try to select 0 rows just to see if table exists
            response = supabase.table(table).select("*").limit(1).execute()
            print(f"✅ Table '{table}' found.")
        except Exception as e:
            # Currently Supabase-py might raise error or return error in response depending on version
            # If table doesn't exist, it usually throws a 404 or specific error code
            print(f"❌ Table '{table}' NOT found or not accessible. (Error: {e})")
            missing_tables.append(table)
            
    if missing_tables:
        print("\nWarning: Some tables are missing. Please run the SQL commands in 'schema.sql' in your Supabase Dashboard SQL Editor.")
    else:
        print("\nSuccess! All tables exist and are accessible.")
        
except Exception as e:
    print(f"\nConnection Failed: {e}")
