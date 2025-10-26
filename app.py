import streamlit as st

st.set_page_config(page_title="Pro Crypto Risk-Management Calculator", layout="centered")

st.title("💹 Pro Crypto Risk-Management Calculator")
st.markdown("""
Instant position sizing, liquidation price, margin, and R:R calculations.  
Supports up to 8-decimal precision. Includes DCA logic and account risk tracking.
""")

# === Inputs ===
entry = st.number_input("Entry Price (USD)", value=0.0000105, format="%.8f", step=0.00000001)
stop = st.number_input("Stop-Loss Price (USD)", value=0.0000095, format="%.8f", step=0.00000001)
leverage = st.number_input("Leverage (×)", value=20, min_value=1)
risk = st.number_input("Dollar Risk ($)", value=100.0, step=10.0)
account_balance = st.number_input("Account Balance ($)", value=5000.0, step=100.0)
side = st.selectbox("Position Side", ["Long", "Short"])
rr = st.number_input("Desired Risk : Reward (optional)", value=3.0, step=0.5)
dca_option = st.selectbox("Use DCA (Default 50%)", ["Yes", "No"], index=0)

# === Core Calculations ===
try:
    # Base position calculations
    pos_size_usd = risk / abs(entry - stop)
    pos_size_units = pos_size_usd / entry

    # Apply DCA scaling
    if dca_option == "Yes":
        pos_size_usd *= 0.5
        pos_size_units *= 0.5
        dca_note = "🟢 DCA active: Using 50% of calculated position size."
    else:
        dca_note = "⚪ DCA disabled: Using full position size."

    # Liquidation price & target
    if side == "Long":
        liq = entry * (1 - (1 / leverage))
        target = entry + (rr * (entry - stop))
    else:
        liq = entry * (1 + (1 / leverage))
        target = entry - (rr * (stop - entry))

    # Distances
    entry_stop_pct = (abs(entry - stop) / entry) * 100
    entry_liq_pct = (abs(entry - liq) / entry) * 100
    stop_liq_pct = (abs(stop - liq) / stop) * 100

    # Margin calculation
    margin_required = pos_size_usd / leverage

    # Risk percentage of account
    account_risk_pct = (risk / account_balance) * 100

    # === Outputs ===
    st.subheader("📈 Results")
    st.write(f"💰 **Position Size:** ${pos_size_usd:,.2f} (≈ {pos_size_units:,.8f} units)")
    st.write(f"⚡ **Liquidation Price:** {liq:.8f}")
    st.write(f"🎯 **Target Price (1:{rr:g}):** {target:.8f}")
    st.write(f"📉 **Risk : Reward Ratio:** 1 : {rr:g}")
    st.write(f"💵 **Actual Margin Required:** ${margin_required:,.2f}")
    st.write(f"📊 **Account Risked:** {account_risk_pct:.2f}%")
    st.write(f"🔹 Entry → Stop-Loss: {entry_stop_pct:.2f}%")
    st.write(f"🔹 Entry → Liquidation: {entry_liq_pct:.2f}%")
    st.write(f"🔹 Stop-Loss → Liquidation: {stop_liq_pct:.2f}%")
    st.info(dca_note)

    # === Warnings ===
    if stop_liq_pct < 1:
        st.warning("⚠️ Liquidation is dangerously close to Stop-Loss — consider lowering leverage.")
    elif rr < 2:
        st.info("ℹ️ R:R below 1:2 — may not justify risk.")
    elif account_risk_pct > 2:
        st.warning("⚠️ Risk exceeds 2% of account — high exposure.")
    else:
        st.success("✅ Setup looks balanced. Manage risk responsibly.")

except ZeroDivisionError:
    st.error("Entry and Stop-Loss cannot be identical.")
except Exception as e:
    st.error(f"Error: {e}")
