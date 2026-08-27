import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox

# 1. Graphical File Selector (No Terminal Required)
root = tk.Tk()
root.withdraw()  # Hides the blank background window
root.attributes('-topmost', True) # Brings the popup to the front

# Open the Windows file explorer dialog
selected_file = filedialog.askopenfilename(
    title="Select Raw CSV File to Clean",
    filetypes=[("CSV Files", "*.csv")],
    initialdir=os.getcwd()
)

# Exit if the user closes the window without picking a file
if not selected_file:
    exit()

# 2. Cleaning, Filtering Columns & Multi-Level Sorting
df = pd.read_csv(selected_file)
df.columns = df.columns.str.strip()

for text_col in ["Segment Name", "Session Type", "Athlete Name", "Athlete Position", "Athlete Groups"]:
    if text_col in df.columns:
        df[text_col] = df[text_col].astype(str).str.strip()

# Segment Filtering: Whole segment (Matches) & Whole session (Trainings)
allowed_segments = ["Whole segment", "Whole session"]
if "Segment Name" in df.columns:
    df = df[df["Segment Name"].str.lower().isin([s.lower() for s in allowed_segments])].copy()

# Date Filtering from May 1, 2025 onwards
date_column = "Start Date"
if date_column in df.columns:
    df[date_column] = pd.to_datetime(df[date_column])
    df = df[df[date_column] >= pd.Timestamp("2025-05-01")].copy()

# Multi-level Sorting
sort_columns = ["Start Date", "Athlete Groups", "Athlete Position", "Duration (mins)"]
ascending_rules = [True, True, True, False]
valid_sort = [(col, asc) for col, asc in zip(sort_columns, ascending_rules) if col in df.columns]
if valid_sort:
    cols_to_sort, sort_asc = zip(*valid_sort)
    df = df.sort_values(by=list(cols_to_sort), ascending=list(sort_asc))

# Keep defined columns
keep_columns = [
    "Athlete Name", "Athlete Position", "Athlete Groups", "Start Date", 
    "Session Type", "Segment Name", "Duration (mins)", "Session Load", 
    "Distance (m)", "Metres per Minute (m)", "High Intensity Running (m)", 
    "No. of High Intensity Events", "Sprint Distance (m)", "No. of Sprints", 
    "Top Speed (m/s)", "Percentage of Max Speed", "Avg Speed (m/s)", 
    "Accelerations", "Decelerations"
]
valid_columns = [col for col in keep_columns if col in df.columns]
df = df[valid_columns]

# Save output
base_name, _ = os.path.splitext(selected_file)
output_file = f"{base_name}_cleaned.csv"
df.to_csv(output_file, index=False)

# 3. Success Popup
messagebox.showinfo("Success", f"Data cleaned and saved successfully!\n\nFile: {os.path.basename(output_file)}")