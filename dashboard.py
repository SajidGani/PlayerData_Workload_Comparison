import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Athlete Workload Dashboard", layout="wide")

# Inject External CSS using a relative path for cloud deployment
def local_css(file_name):
    try:
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        pass

local_css("style.css")

# ==========================================
# 1. File Selection Landing Page
# ==========================================
if "selected_file" not in st.session_state:
    st.session_state.selected_file = None

if st.session_state.selected_file is None:
    st.title("🏃‍♂️ Athlete Workload Tracker")
    st.info("Welcome! Please select a dataset to begin.")
    
    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    if not csv_files:
        st.error("No CSV files found in the current folder.")
        st.stop()
        
    choice = st.selectbox("Choose a CSV file:", ["-- Select a file --"] + csv_files)
    
    if choice != "-- Select a file --":
        if st.button("Load Dashboard"):
            st.session_state.selected_file = choice
            st.rerun()
            
    st.stop()

# ==========================================
# 2. Main Dashboard & Data Loading
# ==========================================
st.title("Athlete Workload Tracker")

st.sidebar.header("1. Data Controls")
if st.sidebar.button("📂 Choose a Different File"):
    st.session_state.selected_file = None
    st.rerun()

@st.cache_data
def load_data(file):
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()
    
    text_cols = ["Segment Name", "Session Type", "Athlete Name", "Athlete Position", "Athlete Groups"]
    for text_col in text_cols:
        if text_col in df.columns:
            df[text_col] = df[text_col].astype(str).str.strip()
            
    if "Segment Name" in df.columns:
        allowed_segments = ["whole segment", "whole session"]
        df = df[df["Segment Name"].str.lower().isin(allowed_segments)].copy()

    df['Start Date'] = pd.to_datetime(df['Start Date'])
    return df

df = load_data(st.session_state.selected_file)
st.session_state.df = df

# ==========================================
# 3. Dynamic Time Periods (Sidebar)
# ==========================================
st.sidebar.header("2. Time Periods")

df['Month_Str'] = df['Start Date'].dt.to_period('M').astype(str)
available_months_asc = sorted(df['Month_Str'].unique().tolist())
available_months_desc = sorted(available_months_asc, reverse=True)

# Helper function to display "August 2026" instead of "2026-08"
def format_month(month_str):
    return pd.to_datetime(month_str).strftime('%B %Y')

# 1. Baseline Start
selected_baseline_start = st.sidebar.selectbox(
    "Select Baseline Start:", 
    available_months_asc, 
    index=0,
    format_func=format_month
)

# 2. Baseline End (Defaults to the newest available month)
selected_baseline_end = st.sidebar.selectbox(
    "Select Baseline End:", 
    available_months_asc, 
    index=len(available_months_asc)-1,
    format_func=format_month
)

# 3. Target Month
selected_recent = st.sidebar.selectbox(
    "Select Target Month:", 
    available_months_desc, 
    index=0,
    format_func=format_month
)

baseline_start = pd.to_datetime(selected_baseline_start)
baseline_end = pd.to_datetime(selected_baseline_end)
recent_start = pd.to_datetime(selected_recent)

# Validation Checks
if baseline_start >= baseline_end:
    st.sidebar.error("⚠️ Baseline start must be before Baseline end.")
    st.stop()
if baseline_end > recent_start:
    st.sidebar.error("⚠️ Baseline end cannot be after the Target month.")
    st.stop()

# Save globally for the Drill-Down page
st.session_state.baseline_start = baseline_start
st.session_state.baseline_end = baseline_end
st.session_state.recent_start = recent_start

metrics = [
    "Duration (mins)", "Session Load", "Distance (m)", "Metres per Minute (m)", 
    "High Intensity Running (m)", "No. of High Intensity Events", "Sprint Distance (m)", 
    "No. of Sprints", "Top Speed (m/s)", "Percentage of Max Speed", "Avg Speed (m/s)", 
    "Accelerations", "Decelerations"
]

# ==========================================
# 4. Interactive Athlete Selector
# ==========================================
st.sidebar.header("3. Select Athlete")
athletes = sorted(df['Athlete Name'].unique())
selected_athlete = st.sidebar.selectbox("Choose an athlete to view:", athletes)

athlete_df = df[df['Athlete Name'] == selected_athlete]

# ==========================================
# 5. Spider Chart Visualization Layout
# ==========================================
st.subheader(f"Workload Spider Chart for: {selected_athlete}")

tab_train, tab_match = st.tabs(["Training Sessions", "Matchday Sessions"])

def render_spider_chart(df_filtered, session_type):
    df_session = df_filtered[df_filtered['Session Type'].str.lower() == session_type.lower()]
    
    if df_session.empty:
        st.warning(f"No {session_type} data found for {selected_athlete}.")
        return

    baseline_df = df_session[(df_session['Start Date'] >= baseline_start) & (df_session['Start Date'] < baseline_end)]
    recent_df = df_session[df_session['Start Date'] >= recent_start]

    valid_metrics = [m for m in metrics if m in df.columns]
    
    raw_b_avg, raw_b_max, raw_r_avg, raw_r_max = [], [], [], []
    norm_b_avg, norm_b_max, norm_r_avg, norm_r_max = [], [], [], []

    for m in valid_metrics:
        b_a = baseline_df[m].mean() if not baseline_df.empty else 0
        b_m = baseline_df[m].max() if not baseline_df.empty else 0
        r_a = recent_df[m].mean() if not recent_df.empty else 0
        r_m = recent_df[m].max() if not recent_df.empty else 0
        
        max_val = max(b_m, r_m)
        if pd.isna(max_val) or max_val == 0:
            max_val = 1 
            
        raw_b_avg.append(b_a if pd.notna(b_a) else 0)
        raw_b_max.append(b_m if pd.notna(b_m) else 0)
        raw_r_avg.append(r_a if pd.notna(r_a) else 0)
        raw_r_max.append(r_m if pd.notna(r_m) else 0)
        
        norm_b_avg.append((b_a / max_val) if pd.notna(b_a) else 0)
        norm_b_max.append((b_m / max_val) if pd.notna(b_m) else 0)
        norm_r_avg.append((r_a / max_val) if pd.notna(r_a) else 0)
        norm_r_max.append((r_m / max_val) if pd.notna(r_m) else 0)

    categories = valid_metrics + [valid_metrics[0]]
    for lst in [raw_b_avg, raw_b_max, raw_r_avg, raw_r_max, norm_b_avg, norm_b_max, norm_r_avg, norm_r_max]:
        if lst:
            lst.append(lst[0])

    fig = go.Figure()

    hover_b_avg = [f"{m}: {v:.2f}" for m, v in zip(categories, raw_b_avg)]
    hover_b_max = [f"{m}: {v:.2f}" for m, v in zip(categories, raw_b_max)]
    hover_r_avg = [f"{m}: {v:.2f}" for m, v in zip(categories, raw_r_avg)]
    hover_r_max = [f"{m}: {v:.2f}" for m, v in zip(categories, raw_r_max)]

    fig.add_trace(go.Scatterpolar(
        r=norm_b_avg, theta=categories, mode='lines+markers',
        line=dict(color='blue', dash='solid'), name='Baseline Average',
        hoverinfo="text", hovertext=hover_b_avg
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=norm_b_max, theta=categories, mode='lines+markers',
        line=dict(color='blue', dash='dot'), name='Baseline Peak',
        hoverinfo="text", hovertext=hover_b_max
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=norm_r_avg, theta=categories, mode='lines+markers',
        line=dict(color='red', dash='solid'), name='Recent Average',
        hoverinfo="text", hovertext=hover_r_avg
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=norm_r_max, theta=categories, mode='lines+markers',
        line=dict(color='red', dash='dot'), name='Recent Peak',
        hoverinfo="text", hovertext=hover_r_max
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=False, range=[0, 1]) 
        ),
        showlegend=True,
        height=700,
        margin=dict(t=60, b=60, l=60, r=60)
    )
    
    st.plotly_chart(fig, use_container_width=True)

with tab_train:
    render_spider_chart(athlete_df, "training session")

with tab_match:
    render_spider_chart(athlete_df, "match session")