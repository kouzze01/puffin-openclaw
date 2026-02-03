
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv(override=True)
webhook_url = os.getenv("N8N_WEBHOOK_URL")

print(f"[TEST] Testing Webhook URL: {webhook_url}")

if not webhook_url:
    print("[ERROR] Error: N8N_WEBHOOK_URL not found in .env")
    exit()

payload = {
    "trade_id": 999,
    "mode": "PAPER",
    "pair": "BTCUSDT",
    "entry_price": 90000.0,
    "exit_price": 90500.0,
    "quantity": 0.001,
    "pnl_usdt": 0.5,
    "market_regime": "DEBUG_TEST",
    "timestamp": "2026-01-21T12:00:00Z"
}

try:
    headers = {"Content-Type": "application/json"}
    print("[SEND] Sending payload...")
    response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
    
    print(f"[STATUS] Response Status: {response.status_code}")
    print(f"[BODY] Response Body: {response.text}")
    
    if response.status_code == 200:
        print("[SUCCESS] Webhook Test PASSED! Check n8n executions.")
    else:
        print("[WARN] Webhook reached but returned error.")
        
except Exception as e:
    print(f"[FAIL] Failed to reach Webhook: {e}")
