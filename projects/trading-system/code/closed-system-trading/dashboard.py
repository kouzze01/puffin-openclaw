import streamlit as st
import pandas as pd
import os
import time
from binance.client import Client
from dotenv import load_dotenv
from supabase import create_client, Client as SupabaseClient
from snapshot_manager import calculate_unrealized_pnl # Import shard logic

# --- Configuration & Setup ---
st.set_page_config(
    page_title="Modular Grid Manager",
    page_icon="🤖",
    layout="wide",
)

# Load env
load_dotenv(override=True)

# Initialize Clients
@st.cache_resource
def init_clients():
    try:
        # Binance
        b_key = os.getenv('BINANCE_API_KEY')
        b_secret = os.getenv('BINANCE_API_SECRET')
        binance_client = Client(b_key, b_secret)

        # Supabase
        s_url = os.getenv('SUPABASE_URL')
        s_key = os.getenv('SUPABASE_KEY')
        supabase_client = create_client(s_url, s_key)
        
        return binance_client, supabase_client
    except Exception as e:
        st.error(f"Failed to initialize clients: {e}")
        return None, None

binance_client, supabase_client = init_clients()

# --- Data Fetching ---
def get_btc_price():
    try:
        ticker = binance_client.get_symbol_ticker(symbol='BTCUSDT')
        return float(ticker['price'])
    except:
        return 0.0

def get_thb_rate():
    try:
        # Try fetching USDTTHB
        ticker = binance_client.get_symbol_ticker(symbol='USDTTHB')
        return float(ticker['price'])
    except:
        # Fallback to ~34.0 if unavailable
        return 34.0

def fetch_zones():
    response = supabase_client.table("zones_config").select("*").order("price_low", desc=False).execute()
    df = pd.DataFrame(response.data)
    if not df.empty:
        # Ensure correct types
        df['price_low'] = df['price_low'].astype(float)
        df['price_high'] = df['price_high'].astype(float)
        df['capital_allocated'] = df['capital_allocated'].astype(float)
    return df

def fetch_baseline(symbol='BTCUSDT'):
    try:
        response = supabase_client.table("baseline_prices").select("*").eq("symbol", symbol).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        # Table might not exist yet if migration hasn't run
        return None

def set_baseline(symbol, price, capital):
    try:
        from datetime import datetime
        data = {
            "symbol": symbol,
            "baseline_price": price,
            "initial_capital": capital,
            # baseline_date will auto-update or default
        }
        # Upsert based on symbol unique constraint
        supabase_client.table("baseline_prices").upsert(data, on_conflict="symbol").execute()
        st.success("✅ Baseline Set Successfully!")
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to set baseline: {e}")

def upsert_zones(df_to_save):
    try:
        # Convert df back to list of dicts for supabase
        records = df_to_save.to_dict('records')
        # We need to remove 'created_at' if it exists and we don't want to mess with it, 
        # but upsert usually handles it. 
        # Ideally, we only send back the columns that can change: status, capital_allocated, id.
        # But for 'new' rows (if we supported adding rows in table directly), we need all cols.
        # Here we rely on ID for updates.
        
        for record in records:
            # Minimal update payload to avoid overwriting other things if possible, 
            # though usually safe to send all.
            payload = {
                "id": record['id'],
                "status": record['status'],
                "capital_allocated": record['capital_allocated']
            }
            supabase_client.table("zones_config").update(payload).eq("id", record['id']).execute()
            
        st.success("✅ Changes saved to Supabase!")
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to save: {e}")

def create_next_zone(based_on_price, direction="UP"):
    """
    Creates a new zone.
    UP: [based_on_price, based_on_price + 2000]
    DOWN: [based_on_price - 2000, based_on_price]
    """
    width = 2000
    if direction == "UP":
        low = based_on_price
        high = low + width
        name = f"Module {int(low/1000)}k-{int(high/1000)}k"
    else: # DOWN
        high = based_on_price
        low = high - width
        name = f"Module {int(low/1000)}k-{int(high/1000)}k"

    try:
        new_zone = {
            "zone_name": name,
            "price_low": low,
            "price_high": high,
            # "zone_width": width, # Removed: Generated column in DB
            "capital_allocated": 0, # Default 0, user sets it
            "status": "Inactive"
        }
        supabase_client.table("zones_config").insert(new_zone).execute()
        st.success(f"✅ Created Zone: {name}")
        st.rerun()
    except Exception as e:
        st.error(f"Failed to create zone: {e}")

def fetch_snapshots(limit=100):
    try:
        response = supabase_client.table("portfolio_snapshots")\
            .select("*")\
            .order("snapshot_time", desc=True)\
            .limit(limit)\
            .execute()
        return pd.DataFrame(response.data)
    except Exception as e:
        return pd.DataFrame()

def fetch_ai_trades(is_paper_mode, limit=50):
    """Fetch closed trades that have AI analysis."""
    table = "paper_trade_log" if is_paper_mode else "trade_log"
    try:
        response = supabase_client.table(table)\
            .select("id, created_at, exit_at, zone_name, entry_price, exit_price, quantity, pnl_usdt, pnl_percent, ai_analysis, ai_score")\
            .eq("status", "CLOSED")\
            .order("exit_at", desc=True)\
            .limit(limit)\
            .execute()
        df = pd.DataFrame(response.data)
        return df
    except Exception as e:
        return pd.DataFrame()

# --- Bot Settings Helpers ---
def fetch_bot_settings():
    try:
        # Assuming ID=1 is the singleton settings row
        response = supabase_client.table("bot_settings").select("*").eq("id", 1).execute()
        if response.data:
            return response.data[0]
        return {} # Empty if not found
    except Exception:
        # If table missing or error, return empty (UI will use defaults)
        return {}

def update_bot_settings(settings_dict):
    try:
        supabase_client.table("bot_settings").update(settings_dict).eq("id", 1).execute()
        st.success("✅ Bot Settings Updated!")
        time.sleep(1) # Give a moment to see the success message
        st.rerun()
    except Exception as e:
        st.error(f"❌ Failed to update settings: {e}")

# --- Main UI ---
st.title("🤖 Modular Closed System Manager")

# Sidebar - View Mode
view_mode = st.sidebar.radio(
    "View Mode",
    ['Live Portfolio', 'Paper Trading'],
    index=0
)

is_paper = (view_mode == 'Paper Trading')

if is_paper:
    st.warning("⚠️ SIMULATION MODE: Displaying Paper Trading Data")
    st.markdown("""
    <style>
    .paper-badge {
        background-color: #ffcc00;
        color: black;
        padding: 5px 10px;
        border-radius: 5px;
        font-weight: bold;
        text-align: center;
        margin-bottom: 10px;
    }
    </style>
    <div class="paper-badge">SIMULATION / PAPER TRADING ACTIVE</div>
    """, unsafe_allow_html=True)

# Main Tabs
main_tab1, main_tab2, main_tab3, main_tab4 = st.tabs(["Control & Monitor", "Performance Analysis", "TP Calculator", "AI Analytics"])

# ==========================================
# TAB 1: Control & Monitor
# ==========================================
with main_tab1:
    # --- Configuration Section (Expander) ---
    with st.expander("⚙️ Bot Configuration", expanded=False):
        current_settings = fetch_bot_settings()
        
        # Defaults if DB is empty or table missing
        s_rsi = current_settings.get('rsi_limit', 45)
        s_tp = float(current_settings.get('tp_usdt', 200.0))
        s_step = float(current_settings.get('grid_step_usdt', 200.0))
        s_cool = current_settings.get('trade_cooldown', 300)
        s_active = current_settings.get('is_active', True)
        
        # New Trade Size Setting
        s_size = float(current_settings.get('trade_size_usdt', 20.0))

        with st.form("settings_form"):
            col_s1, col_s2, col_s3, col_s4, col_s5 = st.columns(5)
            with col_s1:
                new_rsi = st.number_input("RSI Limit", min_value=10, max_value=90, value=s_rsi)
            with col_s2:
                new_tp = st.number_input("TP Target (USDT)", min_value=10.0, value=s_tp, step=10.0)
            with col_s3:
                new_step = st.number_input("Grid Step (USDT)", min_value=50.0, value=s_step, step=10.0)
            with col_s4:
                new_cool = st.number_input("Cooldown (Sec)", min_value=60, value=s_cool, step=60)
            with col_s5:
                new_size = st.number_input("Trade Size (USDT)", min_value=10.0, value=s_size, step=5.0)

            # Conversion Display
            thb_rate = get_thb_rate()
            btc_price_live = get_btc_price()
            
            size_thb = new_size * thb_rate
            size_btc = new_size / btc_price_live if btc_price_live > 0 else 0
            
            st.info(f"💵 **Value in THB:** ~{size_thb:,.2f} THB (Rate: {thb_rate:.2f})  |  BTC: {size_btc:.6f}")
            
            new_active = st.checkbox("✅ Master Switch (Active)", value=s_active)
            
            if st.form_submit_button("💾 Save Settings"):
                payload = {
                    "rsi_limit": new_rsi,
                    "tp_usdt": new_tp,
                    "grid_step_usdt": new_step,
                    "trade_cooldown": new_cool,
                    "is_active": new_active,
                    "trade_size_usdt": new_size
                }
                update_bot_settings(payload)

    # --- Dashboard Overview ---
    col1, col2, col3, col4, col5 = st.columns(5)
    
    btc_price = get_btc_price()
    df_zones = fetch_zones()
    df_snapshots = fetch_snapshots(limit=1) # Get latest snapshot for drawdown
    
    # Data Fetching for Metrics
    def fetch_trades_data(is_paper_mode):
        table = "paper_trade_log" if is_paper_mode else "trade_log"
        try:
            res = supabase_client.table(table).select("*").execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                for col in ['entry_price', 'quantity', 'total_usdt', 'pnl_usdt', 'fee_usdt']:
                    if col in df.columns:
                        df[col] = df[col].astype(float)
            return df
        except Exception as e:
            st.error(f"Error fetching trades: {e}")
            return pd.DataFrame()
    
    df_trades = fetch_trades_data(is_paper)
    
    # Calc Metrics
    realized_profit = 0.0
    unrealized_profit = 0.0
    open_trades_count = 0
    paper_fees = 0.0
    
    if not df_trades.empty:
        # Realized PnL (Closed Trades)
        if 'pnl_usdt' in df_trades.columns:
            realized_profit = df_trades[df_trades['status'] == 'CLOSED']['pnl_usdt'].sum()
        
        # Unrealized PnL (Open Trades)
        # Using shared logic for consistency
        open_trades_df = df_trades[df_trades['status'] == 'OPEN']
        if not open_trades_df.empty:
            open_trades_list = open_trades_df.to_dict('records')
            unrealized_profit, _, _ = calculate_unrealized_pnl(open_trades_list, btc_price)
            open_trades_count = len(open_trades_df)
            
        if is_paper and 'fee_usdt' in df_trades.columns:
            paper_fees = df_trades['fee_usdt'].sum()
            
    # Get Drawdown from latest snapshot if available
    current_dd = 0.0
    if not df_snapshots.empty and 'current_drawdown_pct' in df_snapshots.columns:
        current_dd = df_snapshots.iloc[0]['current_drawdown_pct']
    
    # Zone metrics
    if not df_zones.empty:
        active_zones = df_zones[df_zones['status'] == 'Active']
        total_active_capital = active_zones['capital_allocated'].sum() or 0.0
        
        current_active_zone = active_zones[
            (active_zones['price_low'] <= btc_price) & 
            (active_zones['price_high'] >= btc_price)
        ]
        
        current_zone_display = current_active_zone.iloc[0]['zone_name'] if not current_active_zone.empty else "None (⚠️ OUT OF ZONE)"
        is_price_safe = not current_active_zone.empty
    else:
        total_active_capital = 0.0
        current_zone_display = "No Data"
        is_price_safe = False
    
    with col1:
        st.metric("BTC Price", f"${btc_price:,.2f}")
    with col2:
        st.metric("Active Capital", f"${total_active_capital:,.2f}")
    with col3:
        # Split PnL Display
        st.metric("Realized PnL", f"${realized_profit:,.2f}", delta=f"${unrealized_profit:.2f} (Unrealized)")
    with col4:
        st.metric("Open Trades", f"{open_trades_count}")
    with col5:
         st.metric("Drawdown", f"{current_dd:.2f}%", delta_color="inverse")
    
    # Alert Banner
    if not is_price_safe and not df_zones.empty:
        st.error(f"🚨 ALERT: Current Price ${btc_price:,.2f} is NOT in any Active Module! Please Activate a zone.")
    
    st.divider()
    
    # 2. Zone Management
    st.subheader("🛠️ Zone Config & Status")
    
    if not df_zones.empty:
        # Filter only necessary columns to avoid PyArrow/Streamlit rendering issues with null columns
        cols_to_show = ["id", "zone_name", "price_low", "price_high", "capital_allocated", "status"]
        # Ensure these columns exist
        available_cols = [c for c in cols_to_show if c in df_zones.columns]
        
        df_display = df_zones[available_cols].sort_values(by='price_low', ascending=False).reset_index(drop=True)
    
        edited_df = st.data_editor(
            df_display,
            column_config={
                "id": st.column_config.NumberColumn(disabled=True),
                "zone_name": st.column_config.TextColumn("Zone Name", disabled=True),
                "price_low": st.column_config.NumberColumn("Low ($)", format="$%d", disabled=True),
                "price_high": st.column_config.NumberColumn("High ($)", format="$%d", disabled=True),
                "capital_allocated": st.column_config.NumberColumn("Allocated Capital ($)", format="$%d", min_value=0),
                "status": st.column_config.SelectboxColumn(
                    "Status",
                    options=['Active', 'Inactive', 'Reserve'],
                    help="Select Zone Status",
                    width="medium"
                ),
            },
            use_container_width=True,
            hide_index=True,
            key="zone_editor"
        )
    
        if st.button("💾 Save Changes", type="primary"):
            upsert_zones(edited_df)

    # 3. Zone Performance Analysis
    st.divider()
    with st.expander("📊 Zone Performance Analysis", expanded=True):
        if not df_zones.empty:
            # Prepare aggregation
            # We need: Zone Name | Budget | Invested | Remaining | Realized PnL | % Utilized
            
            # Create a base frame from df_zones
            perf_df = df_zones[['zone_name', 'capital_allocated']].copy()
            perf_df.columns = ['Zone Name', 'Budget (USDT)']
            perf_df['Invested (USDT)'] = 0.0
            perf_df['Realized PnL (USDT)'] = 0.0
            perf_df['Trade Count'] = 0
            
            if not df_trades.empty:
                # Group metrics
                # Invested: Sum total_usdt where status=OPEN
                open_trades_agg = df_trades[df_trades['status'] == 'OPEN'].groupby('zone_name')['total_usdt'].sum().reset_index()
                
                # Realized PnL: Sum pnl_usdt (all closed trades)
                pnl_agg = df_trades.groupby('zone_name')['pnl_usdt'].sum().reset_index() if 'pnl_usdt' in df_trades.columns else pd.DataFrame(columns=['zone_name', 'pnl_usdt'])
                
                # Count
                count_agg = df_trades[df_trades['status'] == 'OPEN'].groupby('zone_name').size().reset_index(name='count')
                
                pass # Aggregations ready
                
                # Map to perf_df
                for index, row in perf_df.iterrows():
                    z_name = row['Zone Name']
                    
                    # Fill Invested
                    if not open_trades_agg.empty:
                        item = open_trades_agg[open_trades_agg['zone_name'] == z_name]
                        if not item.empty:
                            perf_df.at[index, 'Invested (USDT)'] = item.iloc[0]['total_usdt']
                            
                    # Fill PnL
                    if not pnl_agg.empty:
                        item = pnl_agg[pnl_agg['zone_name'] == z_name]
                        if not item.empty:
                            perf_df.at[index, 'Realized PnL (USDT)'] = item.iloc[0]['pnl_usdt']
                            
                    # Fill Count
                    if not count_agg.empty:
                        item = count_agg[count_agg['zone_name'] == z_name]
                        if not item.empty:
                            perf_df.at[index, 'Trade Count'] = item.iloc[0]['count']
            
            # Calc Derivatives
            perf_df['Remaining (USDT)'] = perf_df['Budget (USDT)'] - perf_df['Invested (USDT)']
            perf_df['% Utilized'] = (perf_df['Invested (USDT)'] / perf_df['Budget (USDT)'].replace(0, 1)) * 100
            
            # Formatting for display
            st.dataframe(
                perf_df.style.format({
                    'Budget (USDT)': "${:,.2f}",
                    'Invested (USDT)': "${:,.2f}",
                    'Remaining (USDT)': "${:,.2f}",
                    'Realized PnL (USDT)': "${:,.2f}",
                    '% Utilized': "{:.1f}%",
                    'Trade Count': "{:.0f}"
                }).map(lambda x: 'color: green' if x > 0 else ('color: red' if x < 0 else ''), subset=['Realized PnL (USDT)']),
                use_container_width=True,
                hide_index=True
            )
            
            # Summary Footer with THB
            thb_rate_disp = get_thb_rate()
            total_invested = perf_df['Invested (USDT)'].sum()
            total_pnl = perf_df['Realized PnL (USDT)'].sum()
            
            sum_c1, sum_c2 = st.columns(2)
            with sum_c1:
                st.markdown(f"**Total Invested:** `${total_invested:,.2f}` (~฿{total_invested*thb_rate_disp:,.0f})")
            with sum_c2:
                color = "green" if total_pnl >= 0 else "red"
                st.markdown(f"**Total Realized PnL:** :{color}[`${total_pnl:,.2f}`] (~฿{total_pnl*thb_rate_disp:,.0f})")

        else:
            st.info("No zones configured.")

    
    c_act1, c_act2, c_act3 = st.columns(3)
    
    with c_act1:
        if st.button("⬆️ Generate Next UPPER Zone"):
            if not df_zones.empty:
                max_high = df_zones['price_high'].max()
                create_next_zone(max_high, "UP")
            else:
                base = round(btc_price / 1000) * 1000
                create_next_zone(base, "UP")
    
    with c_act2:
        if st.button("⬇️ Generate Next LOWER Zone"):
            if not df_zones.empty:
                min_low = df_zones['price_low'].min()
                create_next_zone(min_low, "DOWN")
            else:
                base = round(btc_price / 1000) * 1000
                create_next_zone(base, "DOWN")
    
    with c_act3:
        if st.button("🛑 Emergency Mode (Toggle)"):
            st.toast("Entered Emergency Mode: Bot will stop new entries (Mock Action).")

    # 4. Export Section
    st.divider()
    st.subheader("📥 Data Export")
    col_ex1, col_ex2 = st.columns(2)
    
    with col_ex1:
        if not df_zones.empty:
            csv_zones = df_zones.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📊 Export Zone Config (CSV)",
                data=csv_zones,
                file_name=f"zones_config_{'paper' if is_paper else 'live'}_{int(time.time())}.csv",
                mime="text/csv",
            )
            
    with col_ex2:
        if not df_trades.empty:
            csv_trades = df_trades.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📜 Export Trade History (CSV)",
                data=csv_trades,
                file_name=f"trade_history_{'paper' if is_paper else 'live'}_{int(time.time())}.csv",
                mime="text/csv",
            )

# ==========================================
# TAB 2: Performance Analysis (NEW)
# ==========================================
with main_tab2:
    st.header("📈 Performance vs Baseline")
    
    # 1. Baseline Configuration
    st.subheader("1. Day 1 Baseline Configuration")
    
    # Needs to fetch baseline for BTCUSDT
    baseline_data = fetch_baseline("BTCUSDT")
    current_baseline_price = float(baseline_data['baseline_price']) if baseline_data else 0.0
    current_initial_capital = float(baseline_data['initial_capital']) if baseline_data and baseline_data.get('initial_capital') else 0.0
    
    with st.expander("📝 Set/Update Baseline", expanded=not bool(baseline_data)):
        with st.form("baseline_form"):
            b_symbol = st.text_input("Symbol", value="BTCUSDT", disabled=True)
            b_price = st.number_input("Day 1 Price ($)", value=current_baseline_price if current_baseline_price > 0 else btc_price, min_value=0.0)
            b_capital = st.number_input("Initial Capital ($)", value=current_initial_capital, min_value=0.0)
            
            if st.form_submit_button("Save Baseline"):
                set_baseline(b_symbol, b_price, b_capital)

    # 2. Performance Metrics
    st.divider()
    st.subheader("2. Market Comparison")
    
    if current_baseline_price > 0:
        btc_price_now = get_btc_price()
        
        # Calculate BTC Return
        btc_change_pct = ((btc_price_now - current_baseline_price) / current_baseline_price) * 100
        
        col_pm1, col_pm2, col_pm3 = st.columns(3)
        
        with col_pm1:
            st.metric("Day 1 Price", f"${current_baseline_price:,.2f}")
        with col_pm2:
            st.metric("Current Price", f"${btc_price_now:,.2f}")
        with col_pm3:
            st.metric("Market Change", f"{btc_change_pct:.2f}%", delta=f"{btc_change_pct:.2f}%")
            
        st.info(f"💡 Explanation: If you held BTC since Day 1 (${current_baseline_price:,.0f}), your asset value would have changed by {btc_change_pct:.2f}%.")
        
        # 3. Portfolio Health
        st.divider()
        st.subheader("3. Portfolio Health")
        
        # specific fetch for history
        df_history = fetch_snapshots(limit=500)
        
        if not df_history.empty:
            # Sort chronologically for charting
            df_history['snapshot_time'] = pd.to_datetime(df_history['snapshot_time'])
            df_chart = df_history.sort_values('snapshot_time')
            
            chart_col1, chart_col2 = st.columns(2)
            
            with chart_col1:
                st.markdown("**Equity Curve (USDT)**")
                st.line_chart(df_chart, x='snapshot_time', y='total_equity_usdt')
                
            with chart_col2:
                st.markdown("**Drawdown History (%)**")
                # Invert DD to look like underwater chart if possible, or just line
                st.area_chart(df_chart, x='snapshot_time', y='current_drawdown_pct', color="#ff4b4b")
                
            # Additional Breakdown
            with st.expander("🔎 Detailed History Data"):
                st.dataframe(df_chart.sort_values('snapshot_time', ascending=False), use_container_width=True)
                
        else:
            st.info("📉 Charts will appear here once data is collected (Runs hourly).")
            
        st.caption("Advanced metrics tracking is Active.")
        
    else:
        st.warning("Please set a Baseline Price above to see performance metrics.")

# ==========================================
# TAB 3: TP Calculator
# ==========================================
with main_tab3:
    st.header("🧮 Percentage & Fee Calculator")
    st.markdown("Calculate Target Profit levels ensuring you cover fees.")
    
    # Two Columns: Inputs | Results
    calc_col1, calc_col2 = st.columns([1, 1])
    
    with calc_col1:
        st.subheader("Input Parameters")
        
        # Fee Selection
        fee_choice = st.radio("Fee Tier", ("0.1% (Standard)", "0.075% (BNB)", "Custom"), horizontal=True)
        if fee_choice == "0.1% (Standard)":
            fee_rate = 0.001
        elif fee_choice == "0.075% (BNB)":
            fee_rate = 0.00075
        else:
            fee_pct = st.number_input("Custom Fee (%)", 0.0, 1.0, 0.1, step=0.01)
            fee_rate = fee_pct / 100.0
            
        # Default to current price if available, else 60000
        default_price = btc_price if btc_price > 0 else 60000.0
        c_buy_price = st.number_input("Entry Price (USDT)", value=default_price, step=100.0)
        c_qty = st.number_input("Quantity (BTC)", value=0.001, step=0.0001, format="%.4f")
        c_target_percent = st.number_input("Desired Net Profit %", value=1.0, step=0.1)

    with calc_col2:
        st.subheader("Results")
        if c_buy_price > 0 and c_qty > 0:
            buy_val = c_buy_price * c_qty
            buy_fee = buy_val * fee_rate
            
            # Formula for Target Price to get Net % Profit:
            # Net = SellVal - BuyVal - BuyFee - SellFee
            # Net = SellVal - BuyVal - BuyFee - (SellVal * Fee)
            # Net = SellVal(1 - Fee) - BuyVal - BuyFee
            # We want Net = BuyVal * (Target% / 100)
            # BuyVal * Pct = SellVal(1 - Fee) - BuyVal - BuyFee
            # SellVal(1 - Fee) = BuyVal * Pct + BuyVal + BuyFee
            # SellVal = (BuyVal * (1 + Pct) + BuyFee) / (1 - Fee)
            # SellPrice = SellVal / Qty
            
            target_ratio = c_target_percent / 100.0
            numerator = buy_val * (1 + target_ratio) + buy_fee # Approximation? No, let's be precise.
            # wait, buy_fee is sunk cost.
            # Let's use the formula from the other file:
            # target_price = buy_price * (ratio + 1 + fee_rate) / (1 - fee_rate)
            # Let's double check that formula.
            # P_sell = P_buy * ( (Target%/100) + 1 + fee_rate ) / (1 - fee_rate) is what was there.
            
            calculated_tp_price = c_buy_price * (target_ratio + 1 + fee_rate) / (1 - fee_rate)
            
            sell_val = calculated_tp_price * c_qty
            sell_fee = sell_val * fee_rate
            total_fees = buy_fee + sell_fee
            
            gross_pnl = sell_val - buy_val
            net_pnl = gross_pnl - total_fees
            real_pct = (net_pnl / buy_val) * 100
            
            st.markdown(f"**Target Sell Price:**")
            st.title(f"${calculated_tp_price:,.2f}")
            
            st.metric("Net Profit (USDT)", f"${net_pnl:.2f}", delta=f"{real_pct:.2f}%")
            
            st.divider()
            st.write(f"**Breakdown:**")
            st.write(f"- Buy Cost: `${buy_val:.2f}` (Fee: `${buy_fee:.3f}`)")
            st.write(f"- Sell Value: `${sell_val:.2f}` (Fee: `${sell_fee:.3f}`)")
            st.write(f"- Total Fees: `${total_fees:.3f}`")

# ==========================================
# TAB 4: AI Analytics
# ==========================================
with main_tab4:
    st.header("AI Trade Analysis")
    st.caption("Automated insights from AI for every closed trade")
    
    # Fetch AI-analyzed trades
    df_ai_trades = fetch_ai_trades(is_paper)
    
    if df_ai_trades.empty:
        st.info("No closed trades found yet. AI insights will appear here once trades are closed.")
    else:
        # --- Summary Stats ---
        st.subheader("Performance Summary")
        
        # Filter trades WITH AI data
        df_with_ai = df_ai_trades[df_ai_trades['ai_score'].notna()]
        
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        
        total_trades = len(df_ai_trades)
        trades_with_ai = len(df_with_ai)
        avg_score = df_with_ai['ai_score'].mean() if not df_with_ai.empty else 0
        
        # Win/Loss Stats
        winning_trades = len(df_ai_trades[df_ai_trades['pnl_usdt'] > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        total_pnl = df_ai_trades['pnl_usdt'].sum()
        
        with col_s1:
            st.metric("Total Closed Trades", total_trades)
        with col_s2:
            st.metric("Win Rate", f"{win_rate:.1f}%")
        with col_s3:
            st.metric("Total P&L", f"${total_pnl:.2f}")
        with col_s4:
            st.metric("Avg AI Score", f"{avg_score:.1f}/10", help="Average score from AI analysis")
        
        st.divider()
        
        # --- Charts Section (2 columns) ---
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            st.subheader("AI Score Distribution")
            if not df_with_ai.empty:
                score_counts = df_with_ai['ai_score'].value_counts().sort_index()
                st.bar_chart(score_counts, use_container_width=True)
            else:
                st.caption("No AI scores yet")
        
        with chart_col2:
            st.subheader("P&L by Zone")
            if 'zone_name' in df_ai_trades.columns:
                zone_pnl = df_ai_trades.groupby('zone_name')['pnl_usdt'].sum().sort_values(ascending=False)
                st.bar_chart(zone_pnl, use_container_width=True)
            else:
                st.caption("No zone data available")
        
        st.divider()
        
        # --- Best & Worst Trades ---
        if not df_with_ai.empty:
            st.subheader("Highlights")
            highlight_col1, highlight_col2 = st.columns(2)
            
            best_trade = df_with_ai.loc[df_with_ai['ai_score'].idxmax()]
            worst_trade = df_with_ai.loc[df_with_ai['ai_score'].idxmin()]
            
            with highlight_col1:
                st.markdown("##### Best Trade (by AI Score)")
                st.success(f"""
                **Trade #{int(best_trade['id'])}** | Zone: {best_trade.get('zone_name', 'N/A')}
                - Score: **{int(best_trade['ai_score'])}/10**
                - P&L: ${best_trade['pnl_usdt']:.4f}
                """)
                if best_trade.get('ai_analysis'):
                    with st.expander("View AI Analysis"):
                        st.write(best_trade['ai_analysis'])
            
            with highlight_col2:
                st.markdown("##### Worst Trade (by AI Score)")
                st.error(f"""
                **Trade #{int(worst_trade['id'])}** | Zone: {worst_trade.get('zone_name', 'N/A')}
                - Score: **{int(worst_trade['ai_score'])}/10**
                - P&L: ${worst_trade['pnl_usdt']:.4f}
                """)
                if worst_trade.get('ai_analysis'):
                    with st.expander("View AI Analysis"):
                        st.write(worst_trade['ai_analysis'])
            
            st.divider()
        
        
        # --- Trade History with AI Analysis ---
        st.subheader("Trade History with AI Insights")
        
        # Display each trade with AI analysis
        for idx, row in df_ai_trades.iterrows():
            pnl = row.get('pnl_usdt', 0)
            pnl_color = "green" if pnl > 0 else "red"
            ai_score = row.get('ai_score')
            ai_analysis = row.get('ai_analysis')
            
            # Score badge
            if ai_score is not None:
                if ai_score >= 7:
                    score_badge = f":green[Score: {ai_score}/10]"
                elif ai_score >= 4:
                    score_badge = f":orange[Score: {ai_score}/10]"
                else:
                    score_badge = f":red[Score: {ai_score}/10]"
            else:
                score_badge = ":gray[Pending AI...]"
            
            with st.expander(f"Trade #{row['id']} | Zone: {row.get('zone_name', 'N/A')} | P&L: :{pnl_color}[${pnl:.4f}] | {score_badge}"):
                col_t1, col_t2 = st.columns(2)
                with col_t1:
                    st.write(f"**Entry:** ${row.get('entry_price', 0):,.2f}")
                    st.write(f"**Exit:** ${row.get('exit_price', 0):,.2f}")
                    st.write(f"**Quantity:** {row.get('quantity', 0):.6f} BTC")
                with col_t2:
                    st.write(f"**Closed At:** {row.get('exit_at', 'N/A')}")
                    st.write(f"**P&L %:** {row.get('pnl_percent', 0):.2f}%")
                
                st.divider()
                st.markdown("**AI Analysis:**")
                if ai_analysis:
                    st.info(ai_analysis)
                else:
                    st.caption("Awaiting AI analysis...")

