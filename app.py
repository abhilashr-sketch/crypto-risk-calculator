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

    /* Color the first three text inputs (Entry, Stop, Target) */
    div[data-testid="stTextInput"]:nth-of-type(1) input {
        background-color: #d4edda !important;   /* Entry - green */
    }
    div[data-testid="stTextInput"]:nth-of-type(2) input {
        background-color: #f8d7da !important;   /* Stop - red */
    }
    div[data-testid="stTextInput"]:nth-of-type(3) input {
        background-color: #fff3cd !important;   /* Target - orange */
    }
</style>
""", unsafe_allow_html=True)

# --- Session state for DCA slider + input sync ---
if "dca_pct_slider" not in st.session_state:
    st.session_state.dca_pct_slider = 50
if "dca_pct_input" not in st.session_state:
    st.session_state.dca_pct_input = 50

def sync_dca_from_slider():
    st.session_state.dca_pct_input = st.session_state.dca_pct_slider

def sync_dca_from_input():
    # clamp between 0 and 100 just in case
    val = st.session_state.dca_pct_input
    if val < 0:
        val = 0
    if val > 100:
        val = 100
    st.session_state.dca_pct_input = val
    st.session_state.dca_pct_slider = val

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

    # Read-only style for position side: use radio instead of selectbox
    side = st.radio("Position Side", ["Long", "Short"], horizontal=True)

    # --- DCA controls ---
    use_dca = st.checkbox("Use DCA (Default 50%)", value=True)

    if use_dca:
        st.write("Adjust DCA either with slider or by typing exact %:")
        st.slider(
            "DCA Percentage (%) - Slider",
            min_value=0,
            max_value=100,
            key="dca_pct_slider",
            on_change=sync_dca_from_slider
        )
        st.number_input(
            "DCA Percentage (%) - Type Value",
            min_value=0,
            max_value=100,
            key="dca_pct_input",
            on_change=sync_dca_from_input
        )
        dca_pct = float(st.session_state.dca_pct_slider)
    else:
        dca_pct = 100.0  # if DCA disabled, use full risk/size

# === Core Calculations ===
try:
    # Risk per unit
    risk_per_unit = abs(entry - stop)
    if risk_per_unit == 0:
        st.error("Entry and Stop-Loss cannot be identical.")
        st.stop()

    # Adjust risk for DCA (this is the actual risk being used to size position)
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
    account_risk_pct = (adjusted_risk / account_balance) * 100 if account_balance > 0 else None

    # Liquidation price (approximation)
    if side == "Long":
        liq = entry * (1 - (1 / leverage))
    else:
        liq = entry * (1 + (1 / leverage))

    # Percent distances
    entry_stop_pct = (risk_per_unit / entry) * 100
    entry_liq_pct = (abs(entry - liq) / entry) * 100
    stop_liq_pct = (abs(stop - liq) / stop) * 100 if stop != 0 else None

    # --- Results in right column ---
    with col2:
        st.subheader("📈 Results")
        st.markdown(f'<div class="green-bg">💚 Entry Price: {entry:.8f}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="red-bg">❤️ Stop-Loss Price: {stop:.8f}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="orange-bg">🟠 Target Price: {target:.8f}</div>', unsafe_allow_html=True)
        
        st.write(f"💰 **Position Size:** {pos_size_units:.8f} units (~${pos_size_units * entry:.2f})")
        st.write(f"💵 **Planned Dollar Risk:** ${risk:.2f}")
        st.write(f"💵 **Effective Risk Used (after DCA):** ${adjusted_risk:.2f}")
        st.write(f"💵 **Actual Margin Required:** ${margin_required:.2f}")
        st.write(f"⚡ **Liquidation Price:** {liq:.8f}")

        if risk_reward_ratio:
            st.write(f"📉 **Risk : Reward Ratio:** 1 : {risk_reward_ratio:.2f}")

        if account_risk_pct is not None:
            st.write(f"📊 **Account Risked (with DCA):** {account_risk_pct:.2f}%")

        st.write(f"🔹 Entry → Stop-Loss: {entry_stop_pct:.2f}%")
        st.write(f"🔹 Entry → Liquidation: {entry_liq_pct:.2f}%")
        if stop_liq_pct is not None:
            st.write(f"🔹 Stop-Loss → Liquidation: {stop_liq_pct:.2f}%")
        st.write(f"🔹 DCA % applied: {dca_pct:.0f}%")

        # DCA note
        if use_dca:
            st.info("🟢 DCA active: Using selected percentage of calculated position size.")
        else:
            st.info("⚪ DCA disabled: Using full position size.")

        # --- R:R color-coded message ---
        if risk_reward_ratio:
            if risk_reward_ratio >= 3:
                st.success(f"✅ Strong setup: R:R is 1:{risk_reward_ratio:.2f} (≥ 1:3).")
            elif risk_reward_ratio >= 2:
                st.warning(f"🟠 Decent setup: R:R is 1:{risk_reward_ratio:.2f} (around 1:2).")
            else:
                st.error(f"🔴 Weak setup: R:R is 1:{risk_reward_ratio:.2f} (< 1:2).")

        # --- Other warnings ---
        if stop_liq_pct is not None and stop_liq_pct < 1:
            st.warning("⚠️ Liquidation is dangerously close to Stop-Loss — consider lowering leverage.")
        if account_risk_pct is not None and account_risk_pct > 2:
            st.warning("⚠️ Risk exceeds 2% of account — high exposure.")

except Exception as e:
    st.error(f"Error: {e}")
