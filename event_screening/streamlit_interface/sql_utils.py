def generate_sql_from_event(event):
    """
    Generates an SQL query to retrieve relevant past games based on the given event (teamName, opponentName).
    """
    return f"""
    SELECT * FROM game_events
    WHERE (team = '{event["team"]}' AND opponentTeam = '{event["opponentTeam"]}')
       OR (team = '{event["opponentTeam"]}' AND opponentTeam = '{event["team"]}');
    """


"""
    Generates a prompt to make GPT-4o analyze the tweet's intent and write 
    the correct SQL query dynamically.
"""
def generate_verification_sql(tweet, past_data, event_data):
    """
    Generates a GPT-4o prompt to analyze a tweet, determine its pattern, 
    and create a valid SQL query dynamically.
    """
    past_games = past_data[['winner', 'team', 'opponentTeam', 'season', 'gameDate', 'points']].to_string(index=False)

    return f"""
    You are a sports data analyst generating an SQL query to verify a pattern in game history.

    **Task:** Analyze the given tweet and determine the statistical trend it describes (e.g., multiple wins, undefeated streak, point dominance).  
    **Goal:** Generate a valid SQL query that checks if this pattern exists in the `game_events` table.  

    ### Tweet Template:
    "{tweet}"

    ### Event Details:
    - Winning Team: {event_data["winner"]}
    - Team: {event_data["team"]}
    - Opponent Team: {event_data["opponentTeam"]}
    - Season: {event_data["season"]}

    ### Past Relevant Games:
    {past_games}

    ### Instructions:
    1. **Understand the tweet’s intent** (e.g., multiple wins, streaks, point differences) and determine the correct pattern.
    2. **Identify the statistical pattern that should be checked in `game_events`**.
    3. **Generate a complete SQL query** that returns "True" or "False". Based on if the patterns exist in the given data. 
    4. **Ensure the SQL references `game_events` table correctly**.
    5. **Return only the SQL query, with no explanations.**
    """
