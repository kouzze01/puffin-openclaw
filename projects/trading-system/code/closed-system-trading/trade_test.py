import os
import time
import math
from binance.client import Client
from binance.enums import *
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
api_secret = os.getenv('BINANCE_API_SECRET')

if not api_key or not api_secret:
    print("Error: BINANCE_API_KEY or BINANCE_API_SECRET not found.")
    exit(1)

client = Client(api_key, api_secret)

def get_symbol_info(symbol):
    info = client.get_symbol_info(symbol)
    if not info:
        raise Exception(f"Symbol {symbol} not found")
    
    # Extract filters
    filters = {f['filterType']: f for f in info['filters']}
    min_qty = float(filters['LOT_SIZE']['minQty'])
    max_qty = float(filters['LOT_SIZE']['maxQty'])
    step_size = float(filters['LOT_SIZE']['stepSize'])
    min_notional = float(filters['NOTIONAL']['minNotional']) if 'NOTIONAL' in filters else 0
    
    # Some symbols use MIN_NOTIONAL filter instead
    if min_notional == 0 and 'MIN_NOTIONAL' in filters:
         min_notional = float(filters['MIN_NOTIONAL']['minNotional'])

    return min_qty, step_size, min_notional

def round_step_size(quantity, step_size):
    precision = int(round(-math.log(step_size, 10), 0))
    return float(round(quantity, precision))

def main():
    symbol = 'BTCUSDT'
    print(f"\n=== Trading Test: {symbol} ===")
    
    try:
        # 1. Check Limits
        min_qty, step_size, min_notional = get_symbol_info(symbol)
        ticker = client.get_symbol_ticker(symbol=symbol)
        current_price = float(ticker['price'])
        
        print(f"Current Price: {current_price} USDT")
        print(f"Limits: Min Qty={min_qty}, Min Notional={min_notional} USDT")
        
        # Calculate safe trade amount (~15 USDT)
        target_usd_value = 15.0 
        required_qty = target_usd_value / current_price
        
        # Ensure quantity is valid
        if required_qty < min_qty:
            required_qty = min_qty
        
        # Round to step size
        # We use floor logic effectively for sell to avoid over-balance if we were checking balance tightly, 
        # but here we just need a valid quantum.
        quantity = round(required_qty // step_size * step_size, 8) # simplistic round down to step
        
        # Double check notional
        trade_value = quantity * current_price
        if trade_value < min_notional:
            print(f"Calculated value {trade_value:.2f} is below min notional {min_notional}. Adjusting...")
            quantity = round((min_notional * 1.1) / current_price // step_size * step_size, 8)
            trade_value = quantity * current_price

        print(f"Planned Trade: {quantity} BTC (~{trade_value:.2f} USDT)")
        
        # Confirmation (Optional in auto-script, but good for safety)
        # response = input("Proceed with REAL TRADE? (y/n): ")
        # if response.lower() != 'y':
        #     return

        # 2. Execute SELL (BTC -> USDT)
        print("\n>>> Executing SELL Order...")
        order_sell = client.create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_MARKET,
            quantity=quantity
        )
        print(f"SELL Order Created: ID={order_sell['orderId']}, Status={order_sell['status']}")
        
        # Wait a bit
        time.sleep(2)
        
        # 3. Execute BUY (USDT -> BTC)
        # We try to buy back roughly the same amount or slightly less to cover fees.
        # Actually safer to use quoteOrderQty if available, but for symmetry let's use quantity.
        # If we use quoteOrderQty on BUY MARKET, it's easier: "Buy 14 USD worth".
        
        print("\n>>> Executing BUY Order (Buying back)...")
        # Buying back ~99% of the USD we just got (or the target value) to ensure we have enough USDT
        buy_value = trade_value * 0.99 
        
        # Use quoteOrderQty for market buy is often easier
        order_buy = client.create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type=ORDER_TYPE_MARKET,
            quoteOrderQty=round(buy_value, 2)
        )
        print(f"BUY Order Created: ID={order_buy['orderId']}, Status={order_buy['status']}")
        
        print("\nTest Complete!")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
