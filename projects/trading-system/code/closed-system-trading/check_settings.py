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
    
    # Fetch bot settings
    response = supabase.table("bot_settings").select("*").eq("id", 1).execute()
    data = response.data
    
    if not data:
        print("No bot settings found.")
    else:
        print("=== Bot Settings (Current) ===")
        for k, v in data[0].items():
            print(f"{k}: {v}")

except Exception as e:
    print(f"Error: {e}")
