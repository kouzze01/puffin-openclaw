import os
from binance.client import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

if not api_key or not api_secret:
    print("Error: BINANCE_API_KEY or BINANCE_API_SECRET not found in .env file.")
    exit(1)

try:
    client = Client(api_key, api_secret)
    
    # Get account information
    account_info = client.get_account()
    
    print("\n=== Binance Account Asset Overview ===")
    
    balances = account_info['balances']
    has_assets = False
    
    for balance in balances:
        free = float(balance['free'])
        locked = float(balance['locked'])
        
        if free > 0 or locked > 0:
            has_assets = True
            print(f"Asset: {balance['asset']}, Free: {free}, Locked: {locked}")
            
    if not has_assets:
        print("No assets with positive balance found.")
        
except Exception as e:
    print(f"An error occurred: {e}")
