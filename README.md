# ABS Challenge Decision Engine

This project builds a run-expectancy-based decision engine for optimizing Automated Ball-Strike (ABS) challenges.

The goal is to answer a simple baseball strategy question:

> How much run value does a successful challenge create in each count, out, and base-state situation?

Rather than starting with pitch location or overturn probability, this project begins with the core strategic foundation: the value of the call itself. A borderline pitch in a low-leverage count may not be worth challenging, while a similar call in a full-count, runners-on-base situation can materially change the inning.

## Project Overview

The model evaluates all 288 count/base/out states:

- 12 count states
- 3 out states
- 8 base states

For each situation, the model calculates:

Challenge Value = Run Expectancy if pitch becomes a ball - Run Expectancy if pitch remains a strike

This produces a ranked decision table showing which situations create the most run value from a successful challenge.

Key Features:
- Full 288-state run expectancy framework
- Ball and strike state transition logic
- Walk advancement logic for 3-ball counts
- Ranked challenge value table
- Product-friendly challenge tiers
- Streamlit dashboard for interactive decision support
- Game context multiplier for leverage adjustment
- Heatmap visualization by count, base state, and outs
- Dashboard

The Streamlit dashboard allows users to select:
- Count
- Outs
- Base state
- Game leverage context

The app returns:
- Base run value
- Final decision score
- Sample size
- Final challenge recommendation
- Top challenge situations
- Challenge value heatmap
- High-level strategic takeaways

Project Structure:

ABS_Challenge_Model/
├── processed_data/
│   ├── re_by_count_base_out.csv
│   └── challenge_value_table.csv
├── raw_data/
│   └── statcast_2025_full.csv
├── scripts/
│   ├── re_by_count_base_out.py
│   ├── build_challenge_value_table.py
│   └── streamlit_app.py
├── requirements.txt
└── README.md

Core Scripts
- 08_build_re_by_count_base_out.py : Builds the run expectancy table by count, base state, and outs.
- build_challenge_value_table.py : Creates the final product-ready challenge value table. This is the main model pipeline for the dashboard.
It calculates:
- Run expectancy if the pitch remains a strike
- Run expectancy if the pitch is overturned to a ball
- Challenge value
- Rank
- Tier
- Product-friendly recommendation

- streamlit_app.py - Runs the interactive ABS Challenge Decision Engine dashboard.

How to Run Locally: 

Install dependencies:
- py -m pip install -r requirements.txt

Build the challenge value table:
py scripts/build_challenge_value_table.py

Run the dashboard:
- py -m streamlit run scripts/streamlit_app.py

Product Framing: 
This project is designed as more than a baseball analysis. It is a productized decision-support tool.

It demonstrates:
- Baseball analytics
- Python data modeling
- Run expectancy logic
- Dashboard development
- Product-oriented recommendations
- Validation through baseball intuition
- Communication of model outputs to non-technical users
- Future Enhancements

Potential Enhancements:
- Add true win probability added by inning and score
- Incorporate pitch location and strike-zone proximity
- Modeling umpire-specific miss tendencies
- Adding batter and pitcher profiles
- Tracking team challenge usage
- Building an observability layer to monitor model performance over time