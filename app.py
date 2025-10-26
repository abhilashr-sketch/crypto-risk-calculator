import streamlit as st

# --- Page Setup ---
st.set_page_config(page_title="Pro Crypto Risk-Management Calculator", layout="centered")

st.title("💹 Pro Crypto Risk-Management Calculator")
st.markdown("""
Instant position sizing, liquidation price, margin, and R:R calculations.  
Supports up to 8-decimal precision. Includes DCA logic and account risk tracking.
""")

# --- Custom CSS for input colors ---
st.markdown("""
<style>
    .entry input {background-color: #d4edda !important;}  /* Green */
    .stoploss input {background-color: #f8d7da !important;} /* Red */
    .target input {background-color: #fff3cd !important;}   /* Orange */
</style>
""", unsafe_allow_html=True)

# --- Inputs ---
entry_container = st.container()
with entry_container:
    st.markdown('<div class="entry">', unsafe_allow_html=True)
    entry = st.number_input("Entry Price (USD)", value=0.0000105, format="%.8f", step=0.00000001)
    st.markdown('</div>', unsafe_allow_html=True)

stop_container = st.container()
with stop_container:
    st.markdown('<div class="stoploss">', unsafe_allow_html=True)
    stop = st.number_input("Stop-Loss Price (USD)", value=0.0000095, format="%.8f", step=0.00000001)
    st.markdown('</div>', unsafe_allow_html=True)

target_container = st.container()
with target_container:
    st.markdown('<div class="target">', unsafe_allow_html=True)
    target = st.number_input("Target Price (USD)", value=0.0000115, format="%.8f", step=0.00000001)
    st.markdown('</div>', unsafe_allow_html=True)

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

    # --- Results ---
    st.subheader("📈 Results")
    st.write(f"💰 **Position Size:** {pos_size_units:.8f} units (~${pos_size_units * entry:.2f})")
    st.write(f"⚡ **Liquidation Price:** {liq:.8f}")
    st.write(f"🎯 **Target Price:** {target:.8f}")
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
