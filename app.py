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

    /* Color specific input fields by their label */
    input[aria-label="Entry Price (USD)"] {
        background-color: #d4edda !important;   /* Entry - green */
    }
    input[aria-label="Stop-Loss Price (USD)"] {
        background-color: #f8d7da !important;   /* Stop - red */
    }
    input[aria-label="Target Price (USD)"] {
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
    val = st.session_state.dca_pct_input
    # Clamp between 0 and 100
    if val < 0:
        val = 0
    if val > 100:
        val = 100
    st.session_state.dca_pct_input = val
    st.session_state.dca_pct_slider = val


with col1:
    # --- Price inputs ---
    entry_str = st.text_input("Entry Price (USD)", value="0.0000105")
    stop_str = st.text_input("Stop-Loss Price (USD)", value="0.0000095")
    target_str = st.text_input("Target Price (USD)", value="0.0000115")

    # Convert inputs to float safely
    try:
        entry = float(entry_str)
        stop = float(stop_str)
        target = float(target_str)
    except Exception:
        st.error("Entry, Stop-Loss, and Target must be valid decimal numbers.")
        st.stop()

    leverage = st.number_input("Leverage (×)", value=20, min_value=1)
    account_balance = st.number_input("Account Balance ($)", value=5000.0, step=100.0, min_value=0.0)

    # --- Risk mode: manual $ or % of account ---
    use_risk_pct = st.checkbox("Use % of account as risk", value=False)

    if use_risk_pct:
        risk_pct = st.number_input(
            "Risk % of account",
            value=1.0,
            min_value=0.0,
            max_value=100.0,
            step=0.25
        )
        risk = account_balance * risk_pct / 100.0
        st.markdown(f"**Dollar Risk ($):** {risk:.2f}")
    else:
        risk = st.number_input("Dollar Risk ($)", value=100.0, step=10.0, min_value=0.0)
        risk_pct = (risk / account_balance * 100.0) if account_balance > 0 else 0.0

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
        dca_pct = 0.0  # 0% reserved for DCA -> 100% at entry

# === Core Calculations ===
try:
    # Basic sanity checks
    risk_per_unit = abs(entry - stop)
    if risk_per_unit == 0:
        st.error("Entry and Stop-Loss cannot be identical.")
        st.stop()

    if risk <= 0:
        st.error("Dollar Risk must be greater than 0.")
        st.stop()

    # --- TOTAL position size (full idea, if all orders fill) ---
    total_pos_units = risk / risk_per_unit            # units (coins/contracts)
    total_notional = total_pos_units * entry          # approx position value at entry price

    # --- Split between Entry and DCA ---
    entry_fraction = 1.0 - (dca_pct / 100.0)          # % of size opened at entry
    dca_fraction = dca_pct / 100.0                    # % reserved for DCA

    entry_units = total_pos_units * entry_fraction
    dca_units = total_pos_units * dca_fraction

    entry_notional = entry_units * entry
    dca_notional = dca_units * entry  # approx; real value uses DCA price on exchange

    # Margin required (for full plan and for entry leg only)
    margin_full = total_notional / leverage if leverage > 0 else 0.0
    margin_entry = entry_notional / leverage if leverage > 0 else 0.0
    margin_dca = dca_notional / leverage if leverage > 0 else 0.0

    # Risk:Reward ratio (per unit)
    reward_per_unit = abs(target - entry)
    risk_reward_ratio = reward_per_unit / risk_per_unit if risk_per_unit != 0 else None

    # Account risk %
    account_risk_pct = (risk / account_balance) * 100 if account_balance > 0 else None

    # Simple liquidation approximation
    if side == "Long":
        liq = entry * (1 - (1 / leverage))
        move_to_target = target - entry
    else:
        liq = entry * (1 + (1 / leverage))
        move_to_target = entry - target

    # % distances
    entry_stop_pct = (risk_per_unit / entry) * 100
    entry_liq_pct = (abs(entry - liq) / entry) * 100
    stop_liq_pct = (abs(stop - liq) / stop) * 100 if stop != 0 else None

    # PnL at target for full planned size
    pnl_target_full = move_to_target * total_pos_units

    # Risk now (only entry leg filled)
    risk_entry_only = entry_units * risk_per_unit

    # --- Results ---
    with col2:
        st.subheader("📈 Results ↔")

        # Quick summary banner
        summary = (
            f"{side} **{total_pos_units:.6f} units** "
            f"(full size ≈ ${total_notional:.2f}) • "
            f"Max loss at SL: **${risk:.2f}** "
            f"({account_risk_pct:.2f}% of account) • "
            f"Est. PnL at TP (full size): **${pnl_target_full:.2f}** • "
            f"Full margin @ {leverage}×: **${margin_full:.2f}**"
        )
        st.info(summary)

        st.markdown("### 📐 Position Breakdown")

        # Current entry leg
        st.write(
            f"📥 **Current Entry Size:** {entry_units:.8f} units "
            f"(~${entry_notional:.2f}) | Margin now: ${margin_entry:.2f} | "
            f"Max loss now (if only entry filled): ${risk_entry_only:.2f}"
        )

        # DCA leg (if any)
        if use_dca and dca_pct > 0:
            st.write(
                f"📥 **Planned DCA Size:** {dca_units:.8f} units "
                f"(~${dca_notional:.2f} approx) | Margin later: ${margin_dca:.2f} | "
                f"Additional risk when DCA fills: ${risk - risk_entry_only:.2f}"
            )
        else:
            st.write("📥 **DCA:** Not used (100% of size opens at Entry).")

        st.markdown("### 💸 Risk & Margin")

        st.write(f"💵 **Planned Dollar Risk (full idea):** ${risk:.2f}")
        st.write(f"📊 **Risk as % of account:** {risk_pct:.2f}%")
        st.write(f"💵 **Full Position Margin Required:** ${margin_full:.2f}")
        st.write(f"⚡ **Estimated Liquidation Price:** {liq:.8f}")

        st.markdown("### 📊 Price Distances")
        st.write(f"🔹 Entry → Stop-Loss: {entry_stop_pct:.2f}%")
        st.write(f"🔹 Entry → Liquidation: {entry_liq_pct:.2f}%")
        if stop_liq_pct is not None:
            st.write(f"🔹 Stop-Loss → Liquidation: {stop_liq_pct:.2f}%")
        st.write(f"🔹 DCA % of position reserved: {dca_pct:.0f}%")

        # --- DCA note ---
        if use_dca and dca_pct > 0:
            st.info(
                "🟢 DCA active: Total position size is based on full risk. "
                "Part is opened at Entry, remaining is reserved for DCA."
            )
        else:
            st.info("⚪ DCA disabled: 100% of planned size opens at Entry.")

        # --- R:R color-coded message ---
        if risk_reward_ratio is not None:
            if risk_reward_ratio >= 3:
                st.success(f"✅ Strong setup: R:R is 1:{risk_reward_ratio:.2f} (≥ 1:3).")
            elif risk_reward_ratio >= 2:
                st.warning(f"🟠 Decent setup: R:R is 1:{risk_reward_ratio:.2f} (around 1:2).")
            else:
                st.error(f"🔴 Weak setup: R:R is 1:{risk_reward_ratio:.2f} (< 1:2).")

        # --- Other safety warnings ---
        if stop_liq_pct is not None and stop_liq_pct < 1:
            st.warning("⚠️ Liquidation is dangerously close to Stop-Loss — consider lowering leverage.")
        if account_risk_pct is not None and account_risk_pct > 2:
            st.warning("⚠️ Risk exceeds 2% of account — high exposure.")

except Exception as e:
    st.error(f"Error: {e}")
