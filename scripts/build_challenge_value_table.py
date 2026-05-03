import pandas as pd
import numpy as np

# ==================================================
# PURPOSE
# ==================================================
# This script builds the final product-ready ABS Challenge Value table.
#
# Each row represents one game situation:
# - Count: balls / strikes
# - Outs
# - Base state
#
# For each situation, the script calculates:
#
# Challenge Value =
#   Run Expectancy if the pitch is changed to a BALL
#   minus
#   Run Expectancy if the pitch remains a STRIKE
#
# This answers:
# "How many runs is a successful ABS challenge worth in this situation?"
#
# The output feeds directly into the Streamlit dashboard.
# ==================================================


# ==================================================
# LOAD RUN EXPECTANCY TABLE
# ==================================================
# This file should contain all count/base/out states with:
# balls, strikes, outs_when_up, base_state, expected_runs, sample_size
# ==================================================

re = pd.read_csv(
    "processed_data/re_by_count_base_out.csv",
    dtype={"base_state": str}
)

# Ensure base states remain formatted as 3-character strings:
# 1st/2nd/3rd represented as 100, 010, 001, etc.
re["base_state"] = re["base_state"].str.zfill(3)

# Rename outs column for cleaner downstream use
re = re.rename(columns={"outs_when_up": "outs"})


# ==================================================
# CREATE RUN EXPECTANCY LOOKUP
# ==================================================
# This lets us quickly ask:
# "What is the expected run value for this count/out/base state?"
# ==================================================

re_lookup = re.set_index(
    ["balls", "strikes", "outs", "base_state"]
)["expected_runs"].to_dict()


# ==================================================
# WALK ADVANCEMENT LOGIC
# ==================================================
# When ball four occurs, runners advance only when forced.
#
# Examples:
# 000 -> 100
# 100 -> 110
# 110 -> 111
# 111 -> 111 plus 1 run scores
# ==================================================

walk_state_map = {
    "000": ("100", 0),
    "100": ("110", 0),
    "010": ("110", 0),
    "001": ("101", 0),
    "110": ("111", 0),
    "101": ("111", 0),
    "011": ("111", 0),
    "111": ("111", 1),
}


# ==================================================
# BUILD CHALLENGE VALUE TABLE
# ==================================================

rows = []

for _, row in re.iterrows():
    balls = int(row["balls"])
    strikes = int(row["strikes"])
    outs = int(row["outs"])
    base_state = row["base_state"]

    current_expected_runs = row["expected_runs"]
    sample_size = row["sample_size"]

    # ----------------------------------------------
    # STRIKE RESULT
    # ----------------------------------------------
    # If the pitch remains a strike:
    #
    # - With fewer than 2 strikes:
    #     Count simply moves to the next strike count.
    #
    # - With 2 strikes:
    #     Batter strikes out, outs increase by 1,
    #     count resets to 0-0 for the next batter.
    #
    # - If outs become 3:
    #     The inning ends, so run expectancy is 0.
    # ----------------------------------------------

    if strikes < 2:
        re_if_strike = re_lookup.get(
            (balls, strikes + 1, outs, base_state),
            np.nan
        )
    else:
        new_outs = outs + 1

        if new_outs >= 3:
            re_if_strike = 0.0
        else:
            re_if_strike = re_lookup.get(
                (0, 0, new_outs, base_state),
                np.nan
            )

    # ----------------------------------------------
    # BALL RESULT
    # ----------------------------------------------
    # If the pitch is overturned to a ball:
    #
    # - With fewer than 3 balls:
    #     Count simply moves to the next ball count.
    #
    # - With 3 balls:
    #     Ball four creates a walk.
    #     Runners advance if forced.
    #     If bases are loaded, one run scores.
    # ----------------------------------------------

    if balls < 3:
        re_if_ball = re_lookup.get(
            (balls + 1, strikes, outs, base_state),
            np.nan
        )
    else:
        new_base_state, runs_scored = walk_state_map[base_state]

        re_after_walk = re_lookup.get(
            (0, 0, outs, new_base_state),
            np.nan
        )

        re_if_ball = runs_scored + re_after_walk

    # ----------------------------------------------
    # CHALLENGE VALUE
    # ----------------------------------------------
    # Positive values mean a successful challenge creates run value.
    # Higher values mean the situation is more important to challenge.
    # ----------------------------------------------

    if pd.notna(re_if_ball) and pd.notna(re_if_strike):
        challenge_value = re_if_ball - re_if_strike
    else:
        challenge_value = np.nan

    rows.append({
        "balls": balls,
        "strikes": strikes,
        "outs": outs,
        "base_state": base_state,
        "current_expected_runs": current_expected_runs,
        "re_if_strike": re_if_strike,
        "re_if_ball": re_if_ball,
        "challenge_value": challenge_value,
        "sample_size": sample_size
    })


challenge = pd.DataFrame(rows)

# Remove rows where challenge value could not be calculated
challenge = challenge.dropna(subset=["challenge_value"])


# ==================================================
# RANK SITUATIONS
# ==================================================
# Rank the highest-value challenge situations first.
# ==================================================

challenge = challenge.sort_values("challenge_value", ascending=False)
challenge["rank"] = range(1, len(challenge) + 1)


# ==================================================
# ASSIGN DECISION TIERS
# ==================================================
# These tiers turn raw run values into product-friendly decisions.
# Thresholds can be adjusted later based on product strategy.
# ==================================================

def assign_tier(value):
    if value >= 1.25:
        return "Must Challenge"
    elif value >= 0.75:
        return "Strong Challenge"
    elif value >= 0.40:
        return "Situational"
    else:
        return "Low Value"


challenge["tier"] = challenge["challenge_value"].apply(assign_tier)


# ==================================================
# ADD PRODUCT-FRIENDLY DISPLAY COLUMNS
# ==================================================

challenge["count"] = (
    challenge["balls"].astype(str)
    + "-"
    + challenge["strikes"].astype(str)
)


def base_state_label(base_state):
    labels = {
        "000": "Bases Empty",
        "100": "Runner on 1st",
        "010": "Runner on 2nd",
        "001": "Runner on 3rd",
        "110": "Runners on 1st & 2nd",
        "101": "Runners on 1st & 3rd",
        "011": "Runners on 2nd & 3rd",
        "111": "Bases Loaded",
    }

    return labels.get(base_state, base_state)


challenge["base_state_label"] = challenge["base_state"].apply(base_state_label)


def outs_label(outs):
    if outs == 0:
        return "0 Outs"
    elif outs == 1:
        return "1 Out"
    else:
        return "2 Outs"


challenge["outs_label"] = challenge["outs"].apply(outs_label)


def recommendation(tier):
    if tier == "Must Challenge":
        return "Challenge if the call is remotely uncertain"
    elif tier == "Strong Challenge":
        return "Strong challenge opportunity"
    elif tier == "Situational":
        return "Consider game context before challenging"
    else:
        return "Generally save the challenge"


challenge["recommendation"] = challenge["tier"].apply(recommendation)


# ==================================================
# FINAL COLUMN ORDER
# ==================================================

final_columns = [
    "rank",
    "count",
    "balls",
    "strikes",
    "outs",
    "outs_label",
    "base_state",
    "base_state_label",
    "current_expected_runs",
    "re_if_strike",
    "re_if_ball",
    "challenge_value",
    "tier",
    "recommendation",
    "sample_size"
]

challenge = challenge[final_columns]


# ==================================================
# EXPORT PRODUCT TABLE
# ==================================================

output_file = "processed_data/challenge_value_table.csv"
challenge.to_csv(output_file, index=False)


# ==================================================
# VALIDATION OUTPUTS
# ==================================================
# These printed summaries help confirm the model behaves logically.
# They are useful for debugging and for writing the project summary.
# ==================================================

print(f"\nSaved product table to: {output_file}")

print("\nTop 10 challenge situations:")
print(challenge.head(10)[[
    "rank",
    "count",
    "outs_label",
    "base_state_label",
    "challenge_value",
    "tier",
    "sample_size"
]])

print("\nAverage challenge value by count:")
print(
    challenge.groupby("count")["challenge_value"]
    .mean()
    .sort_values(ascending=False)
)

print("\nAverage challenge value by base state:")
print(
    challenge.groupby("base_state_label")["challenge_value"]
    .mean()
    .sort_values(ascending=False)
)

print("\nAverage challenge value by outs:")
print(
    challenge.groupby("outs_label")["challenge_value"]
    .mean()
    .sort_values(ascending=False)
)