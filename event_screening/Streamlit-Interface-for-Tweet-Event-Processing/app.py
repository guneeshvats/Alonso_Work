import streamlit as st
import json
import pandas as pd
import sqlite3  # Using SQLite to execute generated SQL
from gpt4_api import get_gpt4_response
from sql_utils import generate_sql_from_event, generate_verification_sql

# Load hardcoded database from JSON
with open("db.json", "r") as file:
    game_db = json.load(file)

# Convert JSON data to DataFrame
df = pd.DataFrame(game_db)

# Create an in-memory SQLite database and store the data
@st.cache_resource
def get_db_connection():
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    df.to_sql("game_events", conn, index=False, if_exists="replace")
    return conn

conn = get_db_connection()

# Streamlit UI
st.title("Sports Tweet-Event Screening")

# User Inputs
event_input = st.text_area("Enter Event (JSON format)", '''{
    "winner": "Clemson",
    "team": "Clemson",
    "opponentTeam": "Miami",
    "season": "2024",
    "gameDate": "2024-10-15",
    "points": 41
}''')

tweet_template = st.text_input("Enter Tweet Template", "Florida State has won multiple times against Miami in different seasons")

if st.button("Generate SQL & Verify Tweet"):
    try:
        # Parse JSON input
        event_data = json.loads(event_input)

        # Step 1: Generate SQL to retrieve past games
        sql_query = generate_sql_from_event(event_data)
        st.subheader("Generated SQL to Retrieve Past Games:")
        st.code(sql_query, language="sql")

        # Step 2: Execute SQL on SQLite database
        relevant_data = pd.read_sql_query(sql_query, conn)
        st.subheader("Retrieved Past Games:")
        st.write(relevant_data)

        if relevant_data.empty:
            st.error("No matching historical data found.")
        else:
            # Step 3: Generate verification SQL dynamically
            verification_prompt = generate_verification_sql(tweet_template, relevant_data, event_data)
            verification_sql = get_gpt4_response(verification_prompt).strip().replace("```sql", "").replace("```", "")
            st.subheader("Final Executed SQL Query:")
            st.code(verification_sql, language="sql")

            # Step 4: Execute the generated SQL query
            try:
                verification_result_df = pd.read_sql_query(verification_sql, conn)

                # Ensure the result is processed correctly
                if not verification_result_df.empty:
                    result_value = verification_result_df.iloc[0, 0]

                    # Handle different data types properly
                    if isinstance(result_value, (int, float)):  # If it's a number
                        verification_result = "true" if result_value > 0 else "false"
                    elif isinstance(result_value, str):  # If it's a string
                        verification_result = "true"  # Assuming non-empty results indicate a match
                    else:
                        verification_result = "false"
                else:
                    verification_result = "false"

                st.subheader("Verification Result:")
                st.write(verification_result)

                # Step 5: If verification is True, rewrite the tweet
                if verification_result in ["true", "1", 1]:  # Fix the condition
                    rewrite_prompt = f"""
                    You are a sports analytics writer. Rewrite the given tweet while preserving its intent.
                    - **Original Tweet:** "{tweet_template}"
                    - **Winning Team:** {event_data['winner']}
                    - **Opponent Team:** {event_data['opponentTeam']}
                    - **Verified Trend:** {verification_result}

                    **Rewrite Rules:**
                    1. Maintain the structure and meaning of the original tweet.
                    2. Replace the teams dynamically based on the event data.
                    3. Ensure proper grammar and natural phrasing.
                    4. Output only the rewritten tweet, no explanations.
                    """
                    rewritten_tweet = get_gpt4_response(rewrite_prompt)
                    st.success("Tweet Verified & Rewritten!")
                    st.write(rewritten_tweet)
                else:
                    st.error("Tweet does not match historical data patterns.")

            except Exception as e:
                st.error(f"Error executing verification query: {str(e)}")

    except Exception as e:
        st.error(f"Error: {str(e)}")

