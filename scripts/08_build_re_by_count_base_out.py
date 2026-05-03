import pandas as pd
from pathlib import Path

# --------------------------------------------------
# PURPOSE
# --------------------------------------------------
# Build a run expectancy table using the FULL Statcast dataset.
#
# Run Expectancy (RE) answers:
# "From this count, outs, and base state, how many runs is the batting team
# expected to score before the half-inning ends?"
#
# This file creates expected runs by:
# balls, strikes, outs_when_up, base_state
#
# IMPORTANT:
# We use the raw Statcast file, not the cleaned taken-pitches file,
# because run expectancy must include all pitch/play outcomes:
# swings, fouls, balls in play, walks, strikeouts, etc.
# --------------------------------------------------

INPUT_FILE = Path("raw_data/statcast_2025_full.csv")
OUTPUT_FILE = Path("processed_data/re_by_count_base_out.csv")

df = pd.read_csv(INPUT_FILE)

# --------------------------------------------------
# KEEP VALID PRE-PITCH STATES
# --------------------------------------------------
# Statcast rows describe the game state before each pitch.
#
# Valid counts:
# balls: 0, 1, 2, 3
# strikes: 0, 1, 2
# outs: 0, 1, 2
# --------------------------------------------------

df = df[
    df["balls"].isin([0, 1, 2, 3])
    & df["strikes"].isin([0, 1, 2])
    & df["outs_when_up"].isin([0, 1, 2])
].copy()

# --------------------------------------------------
# CREATE BASE STATE
# --------------------------------------------------
# Statcast runner columns contain player IDs when a runner is on base.
# Missing value means the base is empty.
#
# base_state format:
# 000 = bases empty
# 100 = runner on first
# 010 = runner on second
# 001 = runner on third
# 111 = bases loaded
# --------------------------------------------------

df["on_1b_flag"] = df["on_1b"].notna().astype(int)
df["on_2b_flag"] = df["on_2b"].notna().astype(int)
df["on_3b_flag"] = df["on_3b"].notna().astype(int)

df["base_state"] = (
    df["on_1b_flag"].astype(str)
    + df["on_2b_flag"].astype(str)
    + df["on_3b_flag"].astype(str)
)

# --------------------------------------------------
# IDENTIFY HALF-INNINGS
# --------------------------------------------------
# A half-inning is uniquely identified by:
# game_pk, inning, inning_topbot
# --------------------------------------------------

inning_cols = ["game_pk", "inning", "inning_topbot"]

# --------------------------------------------------
# CALCULATE RUNS REMAINING
# --------------------------------------------------
# bat_score = batting team's score before the pitch
# post_bat_score = batting team's score after the pitch/play
#
# inning_final_bat_score is the batting team's final score
# at the end of that half-inning.
#
# runs_remaining = how many more runs scored from this pitch onward
# until the half-inning ended.
# --------------------------------------------------

df["inning_final_bat_score"] = df.groupby(inning_cols)["post_bat_score"].transform("max")
df["runs_remaining"] = df["inning_final_bat_score"] - df["bat_score"]

# --------------------------------------------------
# BUILD RUN EXPECTANCY TABLE
# --------------------------------------------------
# For each count + outs + base state, average the runs remaining.
#
# This gives us the expected future runs from that situation.
# --------------------------------------------------

re_table = (
    df.groupby(["balls", "strikes", "outs_when_up", "base_state"])
    .agg(
        expected_runs=("runs_remaining", "mean"),
        sample_size=("runs_remaining", "size")
    )
    .reset_index()
)

re_table.to_csv(OUTPUT_FILE, index=False)

print("RE table created:", len(re_table))
print("\nSample rows:")
print(re_table.head(20))
print(f"\nSaved to: {OUTPUT_FILE}")