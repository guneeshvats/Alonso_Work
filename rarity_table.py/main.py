import streamlit as st
import pandas as pd
from db_handler import find_matching_tables
from probability import process_probability

st.title("Event Probability Calculator")

st.markdown("### Enter JSON Event Data")
event_json = st.text_area("Paste JSON here", height=250)

if st.button("Calculate Probability"):
    try:
        # Parse user input
        event_data = eval(event_json)

        # Get matched tables
        matched_tables = find_matching_tables(event_data)

        if not matched_tables:
            st.error("No matching tables found.")
        else:
            # Compute probability
            result_df = process_probability(event_data, matched_tables)
            if result_df.empty:
                st.error("No statistical data found for the given event.")
            else:
                st.success("Probability Computed!")
                st.dataframe(result_df)
    except Exception as e:
        st.error(f"Error: {e}")
