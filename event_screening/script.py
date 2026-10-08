import psycopg2

# Connect to database
conn = psycopg2.connect(
    dbname="your_db",
    user="your_user",
    password="your_password",
    host="your_host"
)
cursor = conn.cursor()

# Run SQL query to check if the pattern matches
cursor.execute("""
    WITH team_victories AS (
        SELECT 
            winner,
            opponentTeam AS opponent,
            COUNT(DISTINCT season) AS unique_seasons,
            ARRAY_AGG(DISTINCT season ORDER BY season) AS seasons
        FROM game_events
        WHERE winner IS NOT NULL AND opponentTeam IS NOT NULL
        GROUP BY winner, opponentTeam
    )
    SELECT 
        winner,
        opponent,
        seasons
    FROM team_victories
    WHERE unique_seasons > 1;
""")

results = cursor.fetchall()

# Close connection
cursor.close()
conn.close()

# If results exist, generate a new tweet dynamically
if results:
    for winner, opponent, seasons in results:
        seasons_str = ", ".join(map(str, seasons))
        new_tweet = f"{winner} has won multiple times against {opponent} in different seasons: {seasons_str}."
        print(new_tweet)
else:
    print("No matching events found.")
