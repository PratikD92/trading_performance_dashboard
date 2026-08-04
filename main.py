import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from read_data import load_and_clean_data

# Set Page Config to Wide Mode
st.set_page_config(page_title="Trading Performance Dashboard", layout="wide")

st.title("📈 Trading Performance Dashboard")


# --- DATA PREPARATION ---
# @st.cache_data
def get_data():
    return load_and_clean_data()


df_og = get_data()
df = df_og.copy(deep=True)

# --- TOP METRICS ROW ---
# --- METRIC CALCULATIONS ---
initial_cap = df["Capital"].iloc[0] - df["PnL"].iloc[0]  # Or df['Capital'].iloc[0]
final_cap = df["Capital"].iloc[-1]
total_pnl = df["PnL"].sum()
max_loss = abs(df["Entry"] - df["SL"]).mean()
max_profit = abs(df["Target"] - df["Entry"]).mean()

# Calculate duration in months based on Exit Date range
start_date = df["Entry Date"].min()
end_date = df["Exit Date"].max()
duration_days = (end_date - start_date).days
duration_months = max(1, round(duration_days / 30.44))  # Rough average days per month
average_monthly_return = total_pnl / duration_months
win_rate = (df["P or L"] == "P").mean() * 100
avg_rr = (
    ((df["Target"] - df["Entry"]).abs() / (df["Entry"] - df["SL"]).abs())
    .replace([np.inf, -np.inf], np.nan)
    .mean()
)

# 1. Calculate holding time per trade in days
df["Holding_Days"] = (df["Exit Date"] - df["Entry Date"]).dt.days

# 2. Calculate the average holding period
average_holding_period = df["Holding_Days"].mean()


# --- ROW 1: CAPITAL METRICS ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Initial Capital", f"₹{initial_cap:,.2f}")
col2.metric("Final Capital", f"₹{final_cap:,.2f}")
col3.metric(
    "Total PnL", f"₹{total_pnl:,.2f}", delta=f"{(total_pnl / initial_cap) * 100:.2f}%"
)
col4.metric(
    "Total Trades",
    f"{len(df)}",
    delta=f"Avg {average_holding_period:.2f} days positions held",
)

st.write("")  # Small spacing line

# --- ROW 2: PERFORMANCE METRICS ---
col5, col6, col7, col8 = st.columns(4)
col5.metric("Duration", f"{duration_months} Months")
col6.metric(
    "Avg Return per Month",
    f"₹{average_monthly_return:,.2f}",
    delta=f"{(average_monthly_return / initial_cap) * 100:.2f}%",
)
col7.metric(
    "Avg Risk:Reward",
    f"1 : {avg_rr:.2f}",
    delta=f"Avg SL: {max_loss:,.2f} | Avg Target: {max_profit:,.2f}",
)
col8.metric("Win Rate", f"{win_rate:.1f}%")

st.divider()

# --- ROW 1: CAPITAL GROWTH & MONTHLY PNL ---
left_col, right_col = st.columns(2)

with left_col:
    st.subheader("Capital Growth Curve")
    fig_cap = px.line(
        df, x="Entry Date", y="Capital", custom_data=["Capital", "Return on Cap"]
    )
    fig_cap.update_traces(
        hovertemplate="<b>Date:</b> %{x|%Y-%m-%d}<br><b>Capital:</b> ₹%{customdata[0]:,.2f}<br><b>Return:</b> %{customdata[1]:.2f}%<extra></extra>",
        line_color="#2962ff",
        line_width=2.5,
    )
    st.plotly_chart(fig_cap, use_container_width=True)

with right_col:
    st.subheader("Monthly Profit / Loss")
    # 1. Group by Month and aggregate both PnL and Return on Cap
    monthly_pnl = (
        df.groupby(df["Entry Date"].dt.to_period("M").astype(str))
        .agg({"PnL": "sum", "Return on Cap": "sum"})  # Sum return % for the month
        .reset_index()
    )

    monthly_pnl["Return on Cap"] = monthly_pnl["Return on Cap"] * 100

    # 2. Determine Profit or Loss status for color mapping
    monthly_pnl["Status"] = monthly_pnl["PnL"].apply(
        lambda x: "Profit" if x >= 0 else "Loss"
    )

    # 3. Create Bar Chart with hover_data
    fig_monthly = px.bar(
        monthly_pnl,
        x="Entry Date",
        y="PnL",
        color="Status",
        color_discrete_map={"Profit": "#26a69a", "Loss": "#ef5350"},
        hover_data={"Return on Cap": ":.2f%"},  # Formats return as percentage
    )

    # 4. Customize the hover template layout
    fig_monthly.update_traces(
        hovertemplate="<b>Month:</b> %{x}<br><b>PnL:</b> ₹%{y:,.2f}<br><b>Return:</b> %{customdata[0]:.2f}%<extra></extra>"
    )

    st.plotly_chart(fig_monthly, use_container_width=True)

# --- ROW 2: WIN/LOSS DONUT & TIMEFRAME ANALYTICS ---
col_a, col_b, col_c = st.columns([1, 1, 1])

with col_a:
    st.subheader("Win / Loss Ratio")
    win_loss = df["P or L"].value_counts().reset_index()
    win_loss.columns = ["Result", "Count"]
    fig_wl = px.pie(
        win_loss,
        names="Result",
        values="Count",
        hole=0.5,
        color="Result",
        color_discrete_map={"P": "#26a69a", "L": "#ef5350"},
    )
    fig_wl.update_traces(textinfo="percent+value", insidetextfont=dict(color="white"))
    fig_wl.add_annotation(
        text=f"<b>Avg R:R</b><br>1:{avg_rr:.2f}",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(size=14),
    )
    st.plotly_chart(fig_wl, use_container_width=True)

with col_b:
    st.subheader("Entry TF Distribution")
    tf_counts = df["Entry TF"].value_counts().reset_index()
    tf_counts.columns = ["Entry TF", "Count"]
    fig_tf = px.pie(
        tf_counts,
        names="Entry TF",
        values="Count",
        hole=0.4,
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_tf.update_traces(textinfo="percent+label", insidetextfont=dict(color="white"))
    st.plotly_chart(fig_tf, use_container_width=True)

with col_c:
    st.subheader("Win/Loss by TF")
    tf_pl = df.groupby(["Entry TF", "P or L"]).size().unstack(fill_value=0)
    fig_tf_pl = go.Figure()
    if "P" in tf_pl.columns:
        fig_tf_pl.add_trace(
            go.Bar(x=tf_pl.index, y=tf_pl["P"], name="Wins (P)", marker_color="#26a69a")
        )
    if "L" in tf_pl.columns:
        fig_tf_pl.add_trace(
            go.Bar(
                x=tf_pl.index, y=tf_pl["L"], name="Losses (L)", marker_color="#ef5350"
            )
        )
    fig_tf_pl.update_layout(barmode="group")
    st.plotly_chart(fig_tf_pl, use_container_width=True)


# ==============================================================================
# SECTION: HOURLY ENTRIES & SPOT-OPTION RATIO DECAY
# ==============================================================================

st.header("⏱️ Trade Timing & Option Decay Analytics")

# --- DATA PREPARATION FOR GRAPH 1 (Hourly Bins) ---
# Ensure Entry Time is parsed to extract the hour
df["Entry_Hour"] = pd.to_datetime(
    df["Entry Time"].astype(str), format="%H:%M:%S", errors="coerce"
).dt.hour

# Map hours to market-session intervals
time_bins = {
    9: "09:15 - 10:15",
    10: "10:15 - 11:15",
    11: "11:15 - 12:15",
    12: "12:15 - 13:15",
    13: "13:15 - 14:15",
    14: "14:15 - 15:15",
    15: "15:15 - 15:30",
}
df["Time_Range"] = df["Entry_Hour"].map(time_bins).fillna("Other")

# Count entries per range and order chronologically
time_range_counts = df["Time_Range"].value_counts().reset_index()
time_range_counts.columns = ["Time_Range", "Entry_Count"]

ordered_ranges = [
    "09:15 - 10:15",
    "10:15 - 11:15",
    "11:15 - 12:15",
    "12:15 - 13:15",
    "13:15 - 14:15",
    "14:15 - 15:15",
    "15:15 - 15:30",
]
time_range_counts["Time_Range"] = pd.Categorical(
    time_range_counts["Time_Range"], categories=ordered_ranges, ordered=True
)
time_range_counts = time_range_counts.sort_values("Time_Range")


# --- RENDER SIDE-BY-SIDE IN STREAMLIT ---
g_col1, g_col2 = st.columns(2)

# --- GRAPH 1: HOURLY ENTRIES ---
with g_col1:
    st.subheader("Max Entries by 1-Hour Time Window")

    fig_entries = px.bar(
        time_range_counts,
        x="Time_Range",
        y="Entry_Count",
        text="Entry_Count",
        color_discrete_sequence=["#2962ff"],
    )

    fig_entries.update_traces(textposition="outside")
    fig_entries.update_layout(
        xaxis_title="Time Window",
        yaxis_title="Total Entries",
        xaxis_tickangle=-30,
        height=450,
    )

    st.plotly_chart(fig_entries, use_container_width=True)


# --- GRAPH 2: SPOT-OPTION RATIO & ABSOLUTE MONEYNESS DISTANCE (JUNE & JULY) ---
with g_col2:
    st.subheader("Spot-Option Ratio & Absolute Moneyness Distance (June & July)")

    # 1. Ensure Entry Date is datetime
    df["Entry Date"] = pd.to_datetime(df["Entry Date"])

    # 2. Filter dataset strictly for June and July based on Entry Date
    df_june_july = df[df["Entry Date"].dt.month.isin([6, 7])].copy()
    df_june_july = df_june_july.sort_values("Entry Date")

    # 3. Format Entry Date as string for discrete X-axis
    df_june_july["Trade_Date_Str"] = df_june_july["Entry Date"].dt.strftime("%d-%b")

    # 4. Calculate Absolute Moneyness Distance: |Strike - Spot Entry|
    df_june_july["Abs_Strike_Distance"] = (
        df_june_july["Option"] - df_june_july["Entry"]
    ).abs()

    # 5. Define Bar Colors based on Option Type (CE = Green, PE = Red)
    # Adjust column name 'Option_Type' if named differently (e.g. 'Type' or 'CE/PE')
    df_june_july["Bar_Color"] = df_june_july["Type"].apply(
        lambda x: "#26a69a" if str(x).strip().upper() == "CE" else "#ef5350"
    )

    # 6. Create Dual Y-Axis Figure
    fig_decay = make_subplots(specs=[[{"secondary_y": True}]])

    # --- Secondary Axis (Y2): Absolute Moneyness Distance Bars ---
    # Plotted first so the lines stay on top
    fig_decay.add_trace(
        go.Bar(
            x=df_june_july["Trade_Date_Str"],
            y=df_june_july["Abs_Strike_Distance"],
            name="Moneyness Distance",
            marker_color=df_june_july["Bar_Color"],
            opacity=0.6,
            text=df_june_july["Type"],
            hovertemplate="<b>Date:</b> %{x}<br><b>Type:</b> %{text}<br><b>Abs Distance:</b> %{y:.1f} pts<extra></extra>",
        ),
        secondary_y=True,
    )

    # --- Primary Axis (Y1): Spot-Option Ratio lines per Expiry ---
    expiries = df_june_july["Expiry"].unique()
    colors = ["#ff9800", "#9c27b0", "#2962ff"]

    for idx, exp in enumerate(expiries):
        exp_df = df_june_july[df_june_july["Expiry"] == exp]
        fig_decay.add_trace(
            go.Scatter(
                x=exp_df["Trade_Date_Str"],
                y=(exp_df["Spot-option ratio"] * 100).round(2),
                name=f"Ratio ({exp})",
                mode="lines+markers",
                line=dict(width=2.5, color=colors[idx % len(colors)]),
                marker=dict(size=7),
            ),
            secondary_y=False,
        )

    # 7. Axis and Layout Setup
    fig_decay.update_xaxes(type="category", title_text="Entry Date")
    fig_decay.update_yaxes(title_text="Spot-Option Ratio", secondary_y=False)
    fig_decay.update_yaxes(
        title_text="Abs Moneyness Distance (pts)", secondary_y=True, showgrid=False
    )

    fig_decay.update_layout(
        height=450,
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig_decay, use_container_width=True)


# ==============================================================================
# SECTION: SPOT PTS VS OPTION PTS OVER TIME (WITH SPOT-OPTION RATIO HOVER)
# ==============================================================================

st.header("📊 Spot Points vs. Option Points Movement")

# 1. Prepare Data
df["Entry Date"] = pd.to_datetime(df["Entry Date"])
df_pts = df.sort_values("Entry Date").copy()
df_pts["Trade_Date_Str"] = df_pts["Entry Date"].dt.strftime("%d-%b")

# 2. Build Figure with Single Y-Axis
fig_pts = go.Figure()

# --- Trace 1: Spot Points ---
fig_pts.add_trace(
    go.Scatter(
        x=df_pts["Trade_Date_Str"],
        y=df_pts["Spot points"],
        customdata=df_pts["Spot-option ratio"],
        name="Spot Points",
        mode="lines+markers",
        line=dict(color="#2962ff", width=3),
        marker=dict(size=7, symbol="circle"),
        hovertemplate="<b>Spot Pts:</b> %{y:,.2f}<br><b>Ratio:</b> %{customdata:.3f}<extra></extra>",
    )
)

# --- Trace 2: Option Points ---
fig_pts.add_trace(
    go.Scatter(
        x=df_pts["Trade_Date_Str"],
        y=df_pts["Option pts"],
        customdata=df_pts["Spot-option ratio"] * 100,
        name="Option Points",
        mode="lines+markers",
        line=dict(color="#ff9800", width=2.5),
        marker=dict(size=7, symbol="diamond"),
        hovertemplate="<b>Option Pts:</b> %{y:,.2f}<br><b>Ratio:</b> %{customdata:.3f}<extra></extra>",
    )
)

# 3. Layout & Hover Settings
fig_pts.update_xaxes(type="category", title_text="Entry Date")

fig_pts.update_yaxes(title_text="Points")

fig_pts.update_layout(
    height=500,
    hovermode="x unified",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
)

st.plotly_chart(fig_pts, use_container_width=True)

# st.header("📊 Spot Points vs. Option Points Movement")

# # 1. Prepare Data
# df["Entry Date"] = pd.to_datetime(df["Entry Date"])
# df_pts = df.sort_values("Entry Date").copy()
# df_pts["Trade_Date_Str"] = df_pts["Entry Date"].dt.strftime("%d-%b")

# # 2. Calculate Combined Min and Max for Uniform Scale
# min_val = min(df_pts["Spot points"].min(), df_pts["Option pts"].min())
# max_val = max(df_pts["Spot points"].max(), df_pts["Option pts"].max())

# padding = (max_val - min_val) * 0.05
# unified_range = [min_val - padding, max_val + padding]

# # 3. Build Dual Y-Axis Figure
# fig_pts = make_subplots(specs=[[{"secondary_y": True}]])

# # --- Primary Axis (Y1): Spot Points ---
# fig_pts.add_trace(
#     go.Scatter(
#         x=df_pts["Trade_Date_Str"],
#         y=df_pts["Spot points"],
#         customdata=df_pts["Spot-option ratio"],  # Pass ratio for hover display
#         name="Spot Points",
#         mode="lines+markers",
#         line=dict(color="#2962ff", width=3),
#         marker=dict(size=7, symbol="circle"),
#         hovertemplate="<b>Spot Pts:</b> %{y:,.2f}<extra></extra>",
#     ),
#     secondary_y=False,
# )

# # --- Secondary Axis (Y2): Option Points ---
# fig_pts.add_trace(
#     go.Scatter(
#         x=df_pts["Trade_Date_Str"],
#         y=df_pts["Option pts"],
#         customdata=df_pts["Spot-option ratio"],  # Pass ratio for hover display
#         name="Option Points",
#         mode="lines+markers",
#         line=dict(color="#ff9800", width=2.5),
#         marker=dict(size=7, symbol="diamond"),
#         hovertemplate="<b>Option Pts:</b> %{y:,.2f}<br><b>Ratio:</b> %{customdata:.2f}%<extra></extra>",
#     ),
#     secondary_y=True,
# )

# # 4. Apply Same Range to Both Axes & Set Unified Hover
# fig_pts.update_xaxes(type="category", title_text="Entry Date")

# fig_pts.update_yaxes(
#     title_text="<b>Spot Points</b>",
#     title_font=dict(color="#2962ff"),
#     tickfont=dict(color="#2962ff"),
#     range=unified_range,
#     secondary_y=False,
# )

# fig_pts.update_yaxes(
#     title_text="<b>Option Points</b>",
#     title_font=dict(color="#ff9800"),
#     tickfont=dict(color="#ff9800"),
#     range=unified_range,
#     showgrid=False,
#     secondary_y=True,
# )

# fig_pts.update_layout(
#     height=500,
#     hovermode="x unified",  # Displays both traces + ratio in a single tooltip
#     legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
# )

# st.plotly_chart(fig_pts, use_container_width=True)
