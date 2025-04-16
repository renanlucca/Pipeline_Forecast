
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Pipeline Forecast Tool", layout="wide")
st.title("📊 Pipeline Forecast Tool")

# --- Stage Probabilities ---
stage_probability_map = {
    "S1 - Introductory Call Completed": 0.30,
    "S2 - Sales Qualified Opportunity": 0.42,
    "S3 - Initial Deep-dive Completed": 0.61,
    "S4 - Solution Fit Confirmed": 0.81,
    "S5 - Pricing and Negotiation": 0.95,
    "S6 - Closed Won": 1.00
}

# --- Upload File ---
uploaded_file = st.file_uploader("📤 Upload your deals CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)

    required_cols = ["Deal Name", "Deal Value", "Current Stage", "Expected Close Date"]
    if not all(col in df.columns for col in required_cols):
        st.error("❌ CSV must include: Deal Name, Deal Value, Current Stage, Expected Close Date")
    else:
        df["Deal Value"] = pd.to_numeric(df["Deal Value"], errors="coerce").fillna(0)
        df["Expected Close Date"] = pd.to_datetime(df["Expected Close Date"], errors="coerce")

        # Allow user to set Forecast Action for each deal
        forecast_actions = []
        st.subheader("🔧 Set Forecast Action for Each Deal")
        for i, row in df.iterrows():
            action = st.selectbox(
                f"Deal: {row['Deal Name']} | Stage: {row['Current Stage']} | Value: ${row['Deal Value']:,.0f}",
                options=["Win", "Advance", "Bin"],
                key=f"action_{i}"
            )
            forecast_actions.append(action)

        df["Forecast Action"] = forecast_actions

        # Calculate forecast
        def calculate_forecast(row):
            action = row["Forecast Action"].strip().lower()
            stage = row["Current Stage"]
            value = row["Deal Value"]
            if action == "win":
                return value
            elif action == "advance":
                return value * stage_probability_map.get(stage, 0)
            else:
                return 0

        df["Forecast Value"] = df.apply(calculate_forecast, axis=1)

        # --- Period Selector ---
        df["Quarter"] = df["Expected Close Date"].dt.to_period("Q")
        current_year = pd.Timestamp.now().year
        fiscal_quarters = [f"{current_year}Q2", f"{current_year}Q3", f"{current_year}Q4", f"{current_year}FY"]
        selected_period = st.selectbox("📅 Select Period", options=fiscal_quarters)

        # --- Period Filter ---
        if selected_period.endswith("FY"):
            filtered_df = df[df["Expected Close Date"].dt.year == current_year]
        else:
            filtered_df = df[df["Quarter"].astype(str) == selected_period]

        # --- Display ---
        st.subheader("📋 Deals in Selected Period")
        st.dataframe(filtered_df[["Deal Name", "Deal Value", "Forecast Action", "Current Stage", "Expected Close Date", "Forecast Value"]])

        # --- Chart ---
        total_forecast = filtered_df["Forecast Value"].sum()
        baseline = df["Deal Value"].sum()

        chart_df = pd.DataFrame({
            "Type": ["Baseline (Total Pipeline)", "Forecast (Selected Period)"],
            "Value": [baseline, total_forecast]
        })

        fig, ax = plt.subplots()
        ax.bar(chart_df["Type"], chart_df["Value"])
        ax.set_ylabel("USD")
        ax.set_title("📊 Forecast Comparison")
        st.pyplot(fig)
