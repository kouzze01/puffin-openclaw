import os
from dotenv import load_dotenv
from supabase import create_client
import sys

# Force load to ensure we get new credentials
load_dotenv(override=True)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

try:
    client = create_client(url, key)
    
    print("--- Inspecting 'zones_config' ---")
    response = client.table("zones_config").select("*").execute()
    data = response.data
    
    if not data:
        print("No zones found in database! The table is empty.")
    else:
        print(f"Found {len(data)} zones:")
        print(f"{'ID':<4} | {'Name':<20} | {'Status':<10} | {'Range':<20} | {'Capital':<10}")
        print("-" * 80)
        for z in data:
            print(f"{z.get('id'):<4} | {z.get('zone_name'):<20} | {z.get('status'):<10} | {z.get('price_low')}-{z.get('price_high'):<20} | {z.get('capital_allocated')}")

except Exception as e:
    print("Error:", e)
