import os
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(override=True)

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

try:
    client = create_client(url, key)
    
    print("Fetching zones_config...")
    response = client.table("zones_config").select("*").order("price_low", desc=False).execute()
    df = pd.DataFrame(response.data)
    
    if df.empty:
        print("DataFrame is empty.")
    else:
        # Mimic dashboard transformation
        try:
            df['price_low'] = df['price_low'].astype(float)
            df['price_high'] = df['price_high'].astype(float)
            df['capital_allocated'] = df['capital_allocated'].astype(float)
        except Exception as e:
            print(f"Error converting types: {e}")

        print("\nDataFrame Info:")
        print(df.info())
        print("\nDataFrame Head:")
        print(df.head())
        
        # Check specific columns used in config
        required_cols = ["id", "zone_name", "price_low", "price_high", "capital_allocated", "status"]
        missing = [c for c in required_cols if c not in df.columns]
        if missing:
            print(f"\n❌ Missing columns: {missing}")
        else:
            print("\n✅ All required columns present.")

except Exception as e:
    print("Error:", e)
