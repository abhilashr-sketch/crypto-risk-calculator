import streamlit as st

# --- Page Setup ---
st.set_page_config(page_title="Pro Crypto Risk-Management Calculator", layout="wide")

st.title("💹 Pro Crypto Risk-Management Calculator")
st.markdown("""
Instant position sizing, liquidation price, margin, and R:R calculations.  
Supports up to 8-decimal precision. Includes DCA logic and account risk tracking.
""")

# --- Columns for layout ---
col1, col2 = st.columns(2)

# --- Custom CSS for input colors ---
st.markdown("""
<style>
    .green-bg {background-color: #d4edda !important; padding:2px; border-radius:3px;}
    .red-bg {background-color: #f8d7da !important; padding:2px; border-radius:3px;}
    .orange-bg {background-color: #fff3cd !important; padding:2px; border-radius:3px;}
</style>
""", unsafe_allow_html=True)

with col1:
    # Use text_input to allow background color for small decimals
    entry = st.text_input("Entry Price (USD)", value="0.0000105")
    stop = st.text_input("Stop-Loss Price (USD)", value="0.0000095")
    target = st.text_input("Target Price (USD)", value="0.0000115")
    
    # Convert inputs to float safely
    try:
        entry = float(entry)
        stop = float(stop)
        target = float(target)
    except:
        st.error("Entry, Stop-Loss, and Target must be valid decimal numbers.")
        st.stop()

    leverage = st.number_input("Leverage (×)", value=20, min_value=1)
    risk = st.number_input("Dollar Risk ($)", value=100.0, step=10.0)
    account_balance = st.number_input("Account Balance ($)", value=5000.0, step=100.0)
    side = st.selectbox("Position Side", ["Long", "Short"])
    
    use_dca = st.checkbox("Use DCA (Default 50%)", value=True)
    dca_pct = 50
    if use_dca:
        dca_pct = st.slider("DCA Percentage (%)", min_value=0, max_value=100, value=50)

# === Core Calculations ===
try:
    # Risk per unit
    risk_per_unit = abs(entry - stop)
    if risk_per_unit == 0:
        st.error("Entry and Stop-Loss cannot be identical.")
        st.stop()

    # Adjust risk for DCA
    adjusted_risk = risk * (dca_pct / 100)

    # Position size in units
    pos_size_units = adjusted_risk / risk_per_unit

    # Margin required in USD
    margin_required = (pos_size_units * entry) / leverage

    # Risk:Reward ratio
    reward = abs(target - entry)
    if reward == 0:
        risk_reward_ratio = None
    else:
        risk_reward_ratio = reward / risk_per_unit

    # Account risk %
    account_risk_pct = (adjusted_risk / account_balance) * 100

    # Liquidation price (approximation)
    if side == "Long":
        liq = entry * (1 - (1 / leverage))
    else:
        liq = entry * (1 + (1 / leverage))

    # Percent distances
    entry_stop_pct = (risk_per_unit / entry) * 100
    entry_liq_pct = (abs(entry - liq) / entry) * 100
    stop_liq_pct = (abs(stop - liq) / stop) * 100

    # --- Results in right column ---
    with col2:
        st.subheader("📈 Results")
        st.markdown(f'<div class="green-bg">💚 Entry Price: {entry:.8f}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="red-bg">❤️ Stop-Loss Price: {stop:.8f}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="orange-bg">🟠 Target Price: {target:.8f}</div>', unsafe_allow_html=True)
        
        st.write(f"💰 **Position Size:** {pos_size_units:.8f} units (~${pos_size_units * entry:.2f})")
        st.write(f"⚡ **Liquidation Price:** {liq:.8f}")
        if risk_reward_ratio:
            st.write(f"📉 **Risk : Reward Ratio:** 1 : {risk_reward_ratio:.2f}")
        st.write(f"💵 **Actual Margin Required:** ${margin_required:.2f}")
        st.write(f"📊 **Account Risked:** {account_risk_pct:.2f}%")
        st.write(f"🔹 Entry → Stop-Loss: {entry_stop_pct:.2f}%")
        st.write(f"🔹 Entry → Liquidation: {entry_liq_pct:.2f}%")
        st.write(f"🔹 Stop-Loss → Liquidation: {stop_liq_pct:.2f}%")
        st.write(f"🔹 DCA % applied: {dca_pct}%")

        # DCA note
        if use_dca:
            st.info("🟢 DCA active: Using selected percentage of calculated position size.")
        else:
            st.info("⚪ DCA disabled: Using full position size.")

        # --- Warnings ---
        if stop_liq_pct < 1:
            st.warning("⚠️ Liquidation is dangerously close to Stop-Loss — consider lowering leverage.")
        elif account_risk_pct > 2:
            st.warning("⚠️ Risk exceeds 2% of account — high exposure.")
        elif risk_reward_ratio and risk_reward_ratio < 2:
            st.info("ℹ️ R:R below 1:2 — may not justify risk.")
        else:
            st.success("✅ Setup looks balanced. Manage risk responsibly.")

except Exception as e:
    st.error(f"Error: {e}")
