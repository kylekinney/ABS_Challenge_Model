from pybaseball import statcast
from pathlib import Path
import pandas as pd
import time

OUTPUT_FILE = Path("raw_data/statcast_2025_full.csv")

date_ranges = [
    ("2025-03-27", "2025-03-31"),
    ("2025-04-01", "2025-04-30"),
    ("2025-05-01", "2025-05-31"),
    ("2025-06-01", "2025-06-30"),
    ("2025-07-01", "2025-07-31"),
    ("2025-08-01", "2025-08-31"),
    ("2025-09-01", "2025-09-30"),
    ("2025-10-01", "2025-10-05"),
]

all_data = []

for start, end in date_ranges:
    print(f"Pulling {start} to {end}...")
    data = statcast(start_dt=start, end_dt=end)
    all_data.append(data)

    print(f"Rows pulled: {len(data)}")
    time.sleep(5)  # be gentle with Baseball Savant

full_df = pd.concat(all_data, ignore_index=True)

full_df.to_csv(OUTPUT_FILE, index=False)

print("Full 2025 Statcast saved.")
print("Total rows:", len(full_df))
print(f"Saved to: {OUTPUT_FILE}")