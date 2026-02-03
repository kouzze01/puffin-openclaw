# Troubleshooting

Common issues and how to resolve them.

## 1. "Critical Error: Missing API Keys"
**Symptom**: The bot starts and immediately exits with this error.
**Fix**:
*   Ensure the `.env` file exists in the root directory.
*   Ensure it contains valid `BINANCE_API_KEY`, `BINANCE_API_SECRET`, `SUPABASE_URL`, and `SUPABASE_KEY`.
*   Make sure there are no spaces around the `=` sign in the `.env` file.

## 2. "Price is OUTSIDE all Active Zones"
**Symptom**: The bot runs but keeps saying "Trading Paused".
**Fix**:
*   Open the Dashboard (`streamlit run dashboard.py`).
*   Check the "Active Capital" or "Current Zone" metric.
*   If the Current Zone says "None", look at the **Zone Config** table.
*   Find a zone that covers the current price (e.g., if BTC is 95k, you need a 94k-96k zone).
*   Change its Status to `Active` and click **Save Changes**.
*   If no such zone exists, use the **Quick Actions** to generate new zones up or down until you cover the current price.

## 3. "ModuleNotFoundError"
**Symptom**: Python errors about missing modules (e.g., `ModuleNotFoundError: No module named 'supabase'`).
**Fix**:
Rerunning the installation command usually fixes this:
```bash
pip install -r requirements.txt
```

## 4. Connection Failures
**Symptom**: `Expected 200 after ...` or connection timeouts.
**Fix**:
*   **Binance**: Check your internet connection. API bans are rare unless you are spamming requests (bot interval is 60s, which is safe).
*   **Supabase**: Check if the Supabase project is paused (free tier projects pause after inactivity). Log in to Supabase dashboard to wake it up.

## 5. Dashboard Changes Not Saving
**Symptom**: You edit the table in the dashboard, click Save, but the values revert.
**Fix**:
*   Ensure you are clicking the **"Save Changes"** button after editing.
*   Check the terminal where `streamlit` is running for any error logs.
*   Ensure your `SUPABASE_KEY` has write permissions (Service Role key or properly configured RLS policies).
