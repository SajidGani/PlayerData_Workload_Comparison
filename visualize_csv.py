import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

# ==========================================
# 1. Dynamic File Selector
# ==========================================
# Look for CSV files (you can easily change this to .xlsx if needed)
csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]

if not csv_files:
    print("No CSV files found in the current folder.")
    exit()

print("Available CSV files:")
for idx, file in enumerate(csv_files, 1):
    print(f"[{idx}] {file}")

while True:
    try:
        choice = int(input("\nEnter the number of the file to process: "))
        if 1 <= choice <= len(csv_files):
            selected_file = csv_files[choice - 1]
            break
        print("Invalid number. Please try again.")
    except ValueError:
        print("Please enter a valid number.")

print(f"\nLoading {selected_file}...")

# ==========================================
# 2. Cleaning, Filtering & Data Prep
# ==========================================
# Load the data
df = pd.read_csv(selected_file)

# Strip whitespace from column names
df.columns = df.columns.str.strip()

# Clean text columns
text_cols = ["Segment Name", "Session Type", "Athlete Name", "Athlete Position", "Athlete Groups"]
for text_col in text_cols:
    if text_col in df.columns:
        df[text_col] = df[text_col].astype(str).str.strip()

# Segment Filtering: Whole segment (Matches) & Whole session (Trainings)
allowed_segments = ["Whole segment", "Whole session"]
if "Segment Name" in df.columns:
    df = df[df["Segment Name"].str.lower().isin([s.lower() for s in allowed_segments])].copy()

# Convert 'Start Date' to a datetime object so we can filter by time periods
df['Start Date'] = pd.to_datetime(df['Start Date'])

# ==========================================
# 3. Define Time Periods (Baseline vs Recent)
# ==========================================
# Baseline: May 2025 to July 2026
baseline_start = pd.to_datetime('2025-05-01')
recent_start = pd.to_datetime('2026-08-01') # Current month (August 2026)

# ==========================================
# 4. Visualization Function
# ==========================================
def generate_workload_plot(df, metric, session_type):
    # Filter by Session Type (e.g., "Training Session" or "Matchday Session")
    df_session = df[df['Session Type'].str.lower() == session_type.lower()].copy()
    
    if df_session.empty:
        print(f"No data found for {session_type}. Skipping plot.")
        return

    # Split into Baseline and Recent
    baseline_df = df_session[(df_session['Start Date'] >= baseline_start) & (df_session['Start Date'] < recent_start)]
    recent_df = df_session[df_session['Start Date'] >= recent_start]
    
    # Calculate Max and Avg for Baseline
    baseline_stats = baseline_df.groupby('Athlete Name')[metric].agg(['max', 'mean']).rename(
        columns={'max': 'Baseline Max', 'mean': 'Baseline Avg'}
    )
    
    # Calculate Max and Avg for Recent
    recent_stats = recent_df.groupby('Athlete Name')[metric].agg(['max', 'mean']).rename(
        columns={'max': 'Recent Max', 'mean': 'Recent Avg'}
    )
    
    # Merge the stats together
    combined_stats = pd.concat([baseline_stats, recent_stats], axis=1).fillna(0)
    
    # Plotting
    athletes = combined_stats.index
    x = np.arange(len(athletes))  # the label locations
    width = 0.2  # the width of the bars
    
    fig, ax = plt.subplots(figsize=(14, 7))
    
    # Create the grouped bars
    ax.bar(x - 1.5*width, combined_stats['Baseline Avg'], width, label='Baseline Avg', color='#1f77b4')
    ax.bar(x - 0.5*width, combined_stats['Baseline Max'], width, label='Baseline Max', color='#aec7e8')
    ax.bar(x + 0.5*width, combined_stats['Recent Avg'], width, label='Recent Avg', color='#ff7f0e')
    ax.bar(x + 1.5*width, combined_stats['Recent Max'], width, label='Recent Max', color='#ffbb78')
    
    # Add labels, title, and formatting
    ax.set_ylabel(metric)
    ax.set_title(f'{metric} - {session_type} (Baseline vs Recent)')
    ax.set_xticks(x)
    ax.set_xticklabels(athletes, rotation=45, ha='right')
    ax.legend()
    
    # Add a grid for easier reading
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    
    plt.tight_layout()
    plt.show()

# ==========================================
# 5. Execute Plots
# ==========================================
# Define the metric you want to graph
target_metric = 'Session Load' 

if target_metric not in df.columns:
    print(f"Error: '{target_metric}' is not a valid column in your data.")
else:
    # Plot 1: Trainings
    generate_workload_plot(df, target_metric, 'Training Session')

    # Plot 2: Matchdays
    generate_workload_plot(df, target_metric, 'Matchday Session')