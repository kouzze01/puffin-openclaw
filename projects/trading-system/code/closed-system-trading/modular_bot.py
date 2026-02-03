import os
import time
import math
from datetime import datetime, timezone
from binance.client import Client
from dotenv import load_dotenv
from supabase import create_client, Client as SupabaseClient

# Load environment variables
load_dotenv()

class ModularBot:
    def __init__(self):
        # 1. Setup Binance Client
        self.api_key = os.getenv('BINANCE_API_KEY')
        self.api_secret = os.getenv('BINANCE_API_SECRET')
        if not self.api_key or not self.api_secret:
            raise ValueError("Binance keys not found in .env")
        self.binance_client = Client(self.api_key, self.api_secret)

        # 2. Setup Supabase Client
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase keys not found in .env")
        self.supabase_client: SupabaseClient = create_client(self.supabase_url, self.supabase_key)

        self.symbol = 'BTCUSDT'

    def get_current_price(self):
        """Fetches current price from Binance."""
        try:
            ticker = self.binance_client.get_symbol_ticker(symbol=self.symbol)
            return float(ticker['price'])
        except Exception as e:
            print(f"❌ Error fetching price: {e}")
            return None

    def get_active_zones(self):
        """Fetches rows from zones_config where status = 'Active'."""
        try:
            response = self.supabase_client.table("zones_config") \
                .select("*") \
                .eq("status", "Active") \
                .execute()
            return response.data
        except Exception as e:
            print(f"❌ Error fetching active zones: {e}")
            return []

    def check_zone_integrity(self, current_price, active_zones):
        """
        Checks if the current price is within any active zone.
        Returns:
            - in_zone (bool): True if price is inside an active zone.
            - current_zone (dict): The specific zone dict if found, else None.
        """
        if not active_zones:
            return False, None

        for zone in active_zones:
            low = float(zone['price_low'])
            high = float(zone['price_high'])
            
            if low <= current_price <= high:
                return True, zone
        
        return False, None

    def alert_out_of_zone(self, current_price):
        """Sends an alert (currently print) that price is out of active zones."""
        # In a real scenario, this might send a Line/Telegram notification
        msg = (
            f"\n🚨 [URGENT] PRICE OUT OF ACTIVE ZONES! 🚨\n"
            f"Current Price: {current_price}\n"
            f"Action Required: Check Dashboard, Update Status, or Add Funds.\n"
        )
        print(msg)

    def run_check(self):
        """Single iteration check (for cron or loop)."""
        print(f"\n--- Checking System State at {datetime.now().strftime('%H:%M:%S')} ---")
        
        # 1. Get Price
        price = self.get_current_price()
        if not price:
            return

        print(f"💰 Current {self.symbol} Price: ${price:,.2f}")

        # 2. Get Active Zones
        active_zones = self.get_active_zones()
        if not active_zones:
            print("⚠️ No ACTIVE zones found in database. System is Idle.")
            # Depending on logic, might want to alert here too if we expect to always be active
            return

        print(f"ℹ️ Found {len(active_zones)} Active Zone(s).")
        for z in active_zones:
            print(f"   - [{z['zone_name']}] Range: {z['price_low']} - {z['price_high']} | Cap: ${z['capital_allocated']}")

        # 3. Check Integrity
        in_zone, current_zone = self.check_zone_integrity(price, active_zones)

        if in_zone:
            print(f"✅ System Healthy. Price is inside active zone: {current_zone['zone_name']}")
            # TODO: Here we would proceed to Trading Logic (check for entry opportunities)
            # For now, we just confirm we have the capital budget available
            print(f"   Using Allocated Capital: ${current_zone['capital_allocated']} for MM calculations.")
        else:
            self.alert_out_of_zone(price)

if __name__ == "__main__":
    bot = ModularBot()
    # Simple loop for demonstration
    try:
        while True:
            bot.run_check()
            time.sleep(10) # Check every 10 seconds
    except KeyboardInterrupt:
        print("\nStopping Bot...")
