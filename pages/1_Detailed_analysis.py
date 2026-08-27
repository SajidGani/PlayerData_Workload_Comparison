import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="Metric Drill-Down", layout="wide")

# Inject UNCG CSS using relative path
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass
local_css("style.css")

if "df" not in st.session_state or st.session_state.df is None:
    st.warning("Please go back to the main page and load a dataset first.")
    st.stop()

df = st.session_state.df

st.title("📊 Detailed Metric History")

# Dropdown Layout
col1, col2, col3 = st.columns(3)
with col1:
    athletes = sorted(df['Athlete Name'].unique())
    selected_athlete = st.selectbox("Select Athlete:", athletes)
with col2:
    metrics = [
        "Duration (mins)", "Session Load", "Distance (m)", "Metres per Minute (m)", 
        "High Intensity Running (m)", "No. of High Intensity Events", "Sprint Distance (m)", 
        "No. of Sprints", "Top Speed (m/s)", "Percentage of Max Speed", "Avg Speed (m/s)", 
        "Accelerations", "Decelerations"
    ]
    valid_metrics = [m for m in metrics if m in df.columns]
    selected_metric = st.selectbox("Select Metric:", valid_metrics)
with col3:
    session_type = st.selectbox("Session Type:", ["Training Session", "Match session"])

# Filter and Sort Data Chronologically
athlete_df = df[(df['Athlete Name'] == selected_athlete) & (df['Session Type'].str.lower() == session_type.lower())].copy()
athlete_df = athlete_df.sort_values(by="Start Date")

if athlete_df.empty:
    st.info(f"No {session_type} data found for {selected_athlete}.")
    st.stop()

# Pull exact baseline dates from session state to match the main dashboard
baseline_start = st.session_state.get('baseline_start', pd.to_datetime('2025-05-01'))
baseline_end = st.session_state.get('baseline_end', pd.to_datetime('2026-08-01'))
recent_start = st.session_state.get('recent_start', pd.to_datetime('2026-08-01'))

baseline_df = athlete_df[(athlete_df['Start Date'] >= baseline_start) & (athlete_df['Start Date'] < baseline_end)]
baseline_avg = baseline_df[selected_metric].mean() if not baseline_df.empty else 0

# Build Bar Chart
fig = go.Figure()

# Daily Bars in UNCG Gold
fig.add_trace(go.Bar(
    x=athlete_df['Start Date'].dt.strftime('%b %d, %Y'),
    y=athlete_df[selected_metric],
    name="Daily Value",
    marker_color='#FFB71B' 
))

# Baseline Horizontal Line in UNCG Navy
fig.add_hline(
    y=baseline_avg,
    line_dash="dash",
    line_color="#0F2044", 
    annotation_text=f"Baseline Avg: {baseline_avg:.2f}",
    annotation_position="top left",
    annotation_font=dict(color="#0F2044", size=14)
)

fig.update_layout(
    title=f"{selected_metric} History",
    xaxis_title="Date",
    yaxis_title=selected_metric,
    template="plotly_white",
    hovermode="x unified",
    height=500
)

st.plotly_chart(fig, use_container_width=True)