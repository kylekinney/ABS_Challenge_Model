import streamlit as st
import pandas as pd

# ------------------------------------------------------
# Page configuration
# ------------------------------------------------------
# Sets the browser tab title and uses the full page width.
# "wide" gives the dashboard more horizontal space for tables and heatmaps.
st.set_page_config(page_title="ABS Challenge Engine", layout="wide")

# ------------------------------------------------------
# Load model output data
# ------------------------------------------------------
# This CSV is the final processed table created by the analysis pipeline.
# Each row represents a count / outs / base-state situation and its estimated
# run value from a successful ABS challenge.
df = pd.read_csv("processed_data/challenge_value_table.csv")

# Main dashboard title
st.title("ABS Challenge Decision Engine")

# ------------------------------------------------------
# Sidebar: user inputs
# ------------------------------------------------------
# These filters allow the user to select the exact game situation they want
# to evaluate. Streamlit automatically reruns the app whenever a selection changes.
st.sidebar.header("Game Situation")

count = st.sidebar.selectbox("Count", sorted(df["count"].unique()))
outs = st.sidebar.selectbox("Outs", sorted(df["outs_label"].unique()))
base = st.sidebar.selectbox("Base State", sorted(df["base_state_label"].unique()))

# This is a product-layer adjustment.
# The base model only values the count/base/out state.
# This dropdown lets the user adjust for game urgency, such as inning and score.
game_context = st.sidebar.selectbox(
    "Game Context (Inning + Score Differential)",
    ["Low Leverage", "Medium Leverage", "High Leverage", "Critical"]
)

# Maps the selected game context to a multiplier.
# Higher leverage situations increase the final decision score.
leverage_map = {
    "Low Leverage": 0.75,
    "Medium Leverage": 1.00,
    "High Leverage": 1.25,
    "Critical": 1.50
}

leverage_multiplier = leverage_map[game_context]

# ------------------------------------------------------
# Filter data to selected game situation
# ------------------------------------------------------
# This pulls the one row from the challenge value table that matches
# the selected count, outs, and base state.
filtered = df[
    (df["count"] == count) &
    (df["outs_label"] == outs) &
    (df["base_state_label"] == base)
]

# ------------------------------------------------------
# Recommendation logic
# ------------------------------------------------------
# Converts the adjusted run value into a readable recommendation.
# These thresholds create simple decision tiers for the user.
def adjusted_recommendation(value):
    if value >= 1.25:
        return "Challenge aggressively"
    elif value >= 0.75:
        return "Strong challenge opportunity"
    elif value >= 0.40:
        return "Consider challenging if uncertain"
    else:
        return "Do not challenge unless highly confident"


st.divider()

# ------------------------------------------------------
# Main Decision Panel
# ------------------------------------------------------
st.header("Decision Recommendation")

# If the selected situation exists in the data, calculate the adjusted score.
if not filtered.empty:
    row = filtered.iloc[0]

    # Base challenge value is multiplied by the selected game leverage.
    # Example: a 0.80 run value in a Critical context becomes 1.20.
    adjusted_value = row["challenge_value"] * leverage_multiplier

    # Convert numeric decision score into a readable recommendation.
    final_reco = adjusted_recommendation(adjusted_value)

    # Display the three main dashboard metrics.
    col1, col2, col3 = st.columns(3)

    col1.metric("Base Run Value", f"{row['challenge_value']:.3f} runs")
    col2.metric("Final Decision Score", f"{adjusted_value:.3f}")
    col3.metric("Sample Size", int(row["sample_size"]))

    st.subheader("Final Decision")

    # Use different Streamlit message styles depending on recommendation strength.
    if adjusted_value >= 1.25:
        st.success(final_reco)
    elif adjusted_value >= 0.75:
        st.info(final_reco)
    elif adjusted_value >= 0.40:
        st.warning(final_reco)
    else:
        st.error(final_reco)

    # Explain how the final score was adjusted.
    st.caption(
        f"Leverage: {game_context} ({leverage_multiplier}x) • "
        "Score reflects game context (Inning + Score Differential)"
    )

else:
    # Fallback message if the selected combination does not exist in the data.
    st.warning("No data available for this situation")


st.divider()

# ------------------------------------------------------
# Strategy Insights Section
# ------------------------------------------------------
st.header("Strategy Insights")

# ------------------------------------------------------
# Top Challenge Situations Table
# ------------------------------------------------------
st.subheader("Top Challenge Situations")

# Selects the most important columns for a clean display table.
# Assumes the CSV is already sorted by challenge value.
table = df[[
    "count",
    "outs_label",
    "base_state_label",
    "challenge_value",
    "tier"
]].head(15).copy()

# Format the table for easier reading.
# challenge_value is rounded to three decimals.
styled_table = table.style.set_properties(**{
    "text-align": "left"
}).format({
    "challenge_value": "{:.3f}"
})

st.dataframe(styled_table, use_container_width=True)

# ------------------------------------------------------
# Challenge Value Heatmap
# ------------------------------------------------------
st.subheader("Challenge Value Heatmap")

# Lets the user choose which out state to visualize.
# Defaults to the same outs value selected in the sidebar.
heatmap_outs = st.selectbox(
    "Select outs for heatmap",
    sorted(df["outs_label"].unique()),
    index=sorted(df["outs_label"].unique()).index(outs)
)

# Manually defined baseball-friendly order for base states.
# This prevents the table from appearing in random alphabetical order.
base_state_order = [
    "Bases Empty",
    "Runner on 1st",
    "Runner on 2nd",
    "Runner on 3rd",
    "Runners on 1st & 2nd",
    "Runners on 1st & 3rd",
    "Runners on 2nd & 3rd",
    "Bases Loaded"
]

# Manually defined count order.
# This keeps counts displayed in normal baseball progression.
count_order = [
    "0-0", "0-1", "0-2",
    "1-0", "1-1", "1-2",
    "2-0", "2-1", "2-2",
    "3-0", "3-1", "3-2"
]

# Build a matrix where:
# rows = count
# columns = base state
# values = average challenge value
heatmap_df = df[df["outs_label"] == heatmap_outs].pivot_table(
    index="count",
    columns="base_state_label",
    values="challenge_value",
    aggfunc="mean"
)

# Reorder rows and columns into baseball-friendly order.
heatmap_df = heatmap_df.reindex(index=count_order, columns=base_state_order)

# Apply background color gradient.
# Higher challenge values appear darker.
# NOTE: This requires matplotlib in requirements.txt on Streamlit Cloud.
styled_heatmap = heatmap_df.style.background_gradient(
    axis=None
).format("{:.3f}")

st.dataframe(styled_heatmap, use_container_width=True)

st.caption(
    "Darker cells represent higher run value from a successful challenge "
    "in that count, out, and base-state situation."
)

# ------------------------------------------------------
# Written interpretation
# ------------------------------------------------------
# This section explains the model output in plain English so the dashboard
# is not just a table of numbers. This is useful for non-technical viewers.
st.subheader("High-Level Takeaways")

st.markdown("""
1. Full counts consistently produce the highest challenge value. These situations carry outsized importance because the difference between a ball and a strike often determines whether the plate appearance continues, ends, or results in a walk.

2. Run expectancy increases significantly when runners are on base, making challenges more valuable in traffic than with the bases empty.

3. Bases loaded situations represent the highest-leverage opportunities because a successful challenge can directly force in a run while extending the inning.

4. Lower-leverage situations, particularly early counts with the bases empty, usually provide minimal expected value and should generally be avoided unless the team is highly confident the call will be overturned.

5. The game context multiplier adds a product-layer adjustment for urgency. For example, an 0-2 pitch with the bases empty is usually a poor challenge candidate, but a critical late-game situation may justify challenging if the team has strong conviction.

6. Situations with zero outs often carry higher challenge value than two-out situations because preserving an early-inning opportunity allows for multiple subsequent scoring events, increasing total run expectancy despite the absence of immediate inning-ending risk.
""")