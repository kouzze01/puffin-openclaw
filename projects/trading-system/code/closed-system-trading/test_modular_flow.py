import time
from modular_bot import ModularBot
from supabase import create_client
import os

# Subclass to isolate testing
class TestModularBot(ModularBot):
    def __init__(self, target_test_zone_name):
        super().__init__()
        self.target_test_zone_name = target_test_zone_name

    def get_active_zones(self):
        # Fetch real zones but filter in memory to pretend only our test zone exists
        # This prevents the test from inadvertently passing due to other real active zones
        real_zones = super().get_active_zones()
        return [z for z in real_zones if z['zone_name'] == self.target_test_zone_name]

def run_verification():
    print("=== Starting SOLITARY Verification of Modular Bot Logic ===")
    
    test_zone_name = "TEST_VERIFICATION_ZONE"
    bot = TestModularBot(test_zone_name)
    supabase = bot.supabase_client
    
    # 1. Get real price
    price = bot.get_current_price()
    print(f"Current Price: {price}")
    
    # Cleanup any existing test zone
    supabase.table("zones_config").delete().eq("zone_name", test_zone_name).execute()
    
    try:
        # 2. Test HEALTHY State
        print("\n[Test 1] Creating Active Zone covering current price...")
        data = {
            "zone_name": test_zone_name,
            "price_low": price - 100,
            "price_high": price + 100,
            "capital_allocated": 500,
            "status": "Active"
        }
        supabase.table("zones_config").insert(data).execute()
        
        # Run Check
        print(">>> Running Bot Check:")
        bot.run_check()
        
        # 3. Test ALERT State
        print("\n[Test 2] Moving Active Zone away from price...")
        update_data = {
            "price_low": price - 2000,
            "price_high": price - 1000
        }
        supabase.table("zones_config").update(update_data).eq("zone_name", test_zone_name).execute()
        
        # Run Check
        print(">>> Running Bot Check (Expect ALERT):")
        bot.run_check()
        
    finally:
        # 4. Cleanup
        print("\n[Cleanup] Removing test zone...")
        supabase.table("zones_config").delete().eq("zone_name", test_zone_name).execute()
        print("Done.")

if __name__ == "__main__":
    run_verification()
