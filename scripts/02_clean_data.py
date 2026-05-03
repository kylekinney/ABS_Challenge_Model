import pandas as pd
from pathlib import Path

# File paths
RAW_FILE = Path("raw_data/statcast_april_2023.csv")
OUTPUT_FILE = Path("processed_data/cleaned_taken_pitches.csv")

# Load data
df = pd.read_csv(RAW_FILE)

# Keep only taken pitches where the umpire made a ball/strike call
df = df[df["description"].isin(["called_strike", "ball"])].copy()

# Define an approximate rulebook strike zone using Statcast location data
df["true_strike"] = (
    (df["plate_x"] >= -0.83) &
    (df["plate_x"] <= 0.83) &
    (df["plate_z"] >= df["sz_bot"]) &
    (df["plate_z"] <= df["sz_top"])
)

# What the umpire actually called
df["called_strike"] = df["description"] == "called_strike"

# Did the umpire call disagree with the estimated true zone?
df["missed_call"] = df["true_strike"] != df["called_strike"]

# Save cleaned file
df.to_csv(OUTPUT_FILE, index=False)

print("Cleaned taken pitches:", len(df))
print("Missed calls:", df["missed_call"].sum())
print("Missed call rate:", round(df["missed_call"].mean() * 100, 2), "%")
print(f"Saved to: {OUTPUT_FILE}")