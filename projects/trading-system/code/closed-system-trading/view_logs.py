import os
from dotenv import load_dotenv
from supabase import create_client, Client
import json

load_dotenv()

url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

if not url or not key:
    print("Error: Supabase keys not found.")
    exit(1)

supabase: Client = create_client(url, key)

try:
    print("Fetching 'trade_log'...")
    response = supabase.table("trade_log").select("*").order("id", desc=True).execute()
    data = response.data
    
    if not data:
        print("No records found in trade_log.")
    else:
        print(f"Found {len(data)} records:\n")
        for record in data:
            print("--------------------------------------------------")
            print(f"ID: {record['id']}")
            print(f"Time: {record['created_at']}")
            print(f"Type: {record['order_type']}")
            print(f"Entry Price: {record['entry_price']}")
            print(f"Qty: {record['quantity']}")
            print(f"Status: {record['status']}")
            print(f"Notes: {record['notes']}")
            if record.get('matched_pair_id'):
                print(f"Matched with ID: {record['matched_pair_id']}")
            print("--------------------------------------------------")

except Exception as e:
    print(f"Error fetching logs: {e}")
