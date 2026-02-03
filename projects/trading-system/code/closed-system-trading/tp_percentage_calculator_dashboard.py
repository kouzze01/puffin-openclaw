import streamlit as st
import pandas as pd

# Set Page Config
st.set_page_config(page_title="TP % Calculator", page_icon="💰", layout="centered")

st.title("💰 TP Percentage & Fee Calculator")
st.markdown("Calculate your Take Profit levels, ensuring meaningful net profit after fees.")

# --- Sidebar: Settings ---
st.sidebar.header("⚙️ Settings")

# Fee Selection
fee_option = st.sidebar.radio(
    "Fee Tier",
    ("0.075% (BNB Deduction)", "0.1% (Standard)", "Custom")
)

if fee_option == "0.1% (Standard)":
    fee_rate = 0.001
elif fee_option == "0.075% (BNB Deduction)":
    fee_rate = 0.00075
else:
    fee_rate_percent = st.sidebar.number_input("Custom Fee (%)", value=0.1, step=0.01, format="%.3f")
    fee_rate = fee_rate_percent / 100

st.sidebar.markdown(f"**Applied Fee Rate:** `{fee_rate*100:.3f}%` (per side)")
st.sidebar.markdown("---")
st.sidebar.info("This calculator assumes fees are applied to the total transaction value on both BUY and SELL (Roundtrip).")

# --- Main Inputs ---
col1, col2 = st.columns(2)

with col1:
    buy_price = st.number_input("🔵 Buy Price (USDT)", min_value=0.0, value=60000.0, step=100.0, format="%.2f")

with col2:
    quantity = st.number_input("📦 Quantity (BTC/Asset)", min_value=0.0, value=0.001, step=0.0001, format="%.5f")

# Helper Calculation for Entry
buy_value = buy_price * quantity
buy_fee = buy_value * fee_rate
breakeven_price = buy_price * (1 + fee_rate) / (1 - fee_rate) # Price where Net PnL is 0

st.success(f"**Initial Investment:** `{buy_value:,.2f} USDT`  \n**Buy Fee:** `-{buy_fee:,.4f} USDT`")

st.markdown("---")

# --- Calculation Tabs ---
tab1, tab2 = st.tabs(["🎯 Target Price Finder (From %)", "📊 Profit Calculator (From Price)"])

# TAB 1: Find Price from Desired %
with tab1:
    st.subheader("🎯 Find TP Price by Desired Net %")
    st.markdown("Enter how much **Net Profit %** you want to make.")
    
    target_percent = st.number_input("Desired Net Profit (%)", value=1.0, step=0.1, key="target_pct_input")
    
    # Formula:
    # Net Profit = Sell_Val - Buy_Val - (Buy_Fee + Sell_Fee)
    # Net Profit % = (Net Profit / Buy_Value) * 100
    # ...
    # P_sell = P_buy * ( (Target%/100) + 1 + fee_rate ) / (1 - fee_rate)
    
    if buy_price > 0:
        ratio = target_percent / 100.0
        target_price = buy_price * (ratio + 1 + fee_rate) / (1 - fee_rate)
        
        # Breakdown
        sell_value = target_price * quantity
        sell_fee = sell_value * fee_rate
        total_fee = buy_fee + sell_fee
        gross_profit = sell_value - buy_value
        net_profit = gross_profit - total_fee
        
        # Display Result
        st.markdown(f"### 🏷️ Target Price: `{target_price:,.2f} USDT`")
        
        # Detailed Table
        res_data = {
            "Metric": ["Sell Price", "Gross Profit (No Fees)", "Total Fees", "Net Profit (Realized)"],
            "Value (USDT)": [
                f"{target_price:,.2f}", 
                f"{gross_profit:,.2f}", 
                f"-{total_fee:,.4f}", 
                f"{net_profit:,.2f}",
            ]
        }
        st.table(pd.DataFrame(res_data))
        
        if target_price < breakeven_price:
             st.warning(f"⚠️ Note: This target is below the breakeven price of {breakeven_price:,.2f}")

# TAB 2: Calculate % from Specific Price
with tab2:
    st.subheader("📊 Calculate Profit at Sell Price")
    st.markdown("Enter a **Sell Price** to see your potential returns.")
    
    sell_price_input = st.number_input("Sell Price (USDT)", value=buy_price * 1.01, step=100.0, format="%.2f", key="sell_price_input")
    
    if buy_price > 0:
        # Calculations
        sell_value_2 = sell_price_input * quantity
        sell_fee_2 = sell_value_2 * fee_rate
        total_fee_2 = buy_fee + sell_fee_2
        gross_profit_2 = sell_value_2 - buy_value
        net_profit_2 = gross_profit_2 - total_fee_2
        net_percent_2 = (net_profit_2 / buy_value) * 100 if buy_value > 0 else 0
        
        # Display large metric
        if net_profit_2 > 0:
            st.metric(label="Net Profit %", value=f"{net_percent_2:.2f}%", delta=f"{net_profit_2:.2f} USDT")
        else:
            st.metric(label="Net Profit %", value=f"{net_percent_2:.2f}%", delta=f"{net_profit_2:.2f} USDT", delta_color="inverse")

        # Detailed Breakdown
        st.write("#### 🧾 Breakdown")
        
        col_res1, col_res2 = st.columns(2)
        with col_res1:
            st.write(f"**Gross Profit:** `{gross_profit_2:,.2f} USDT`")
            st.write(f"**Total Fees:** `{total_fee_2:,.4f} USDT`")
        with col_res2:
            st.write(f"**Breakeven Price:** `{breakeven_price:,.2f} USDT`")
            st.write(f"**Sell Value:** `{sell_value_2:,.2f} USDT`")
