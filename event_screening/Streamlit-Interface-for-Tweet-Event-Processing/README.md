# Sports Tweet-Event Screening Process

##  Overview
This Streamlit app verifies sports tweets by checking if the pattern described in a tweet matches historical data. It dynamically generates SQL queries using GPT-4o, executes them on a dataset, and rewrites the tweet with updated information if verified.

##  Features
- **User Inputs:** Accepts event data (JSON) and a tweet template.
- **Dynamic SQL Generation:** GPT-4o generates SQL queries to retrieve and verify historical patterns.
- **In-Memory SQLite Execution:** Queries are executed dynamically rather than using hardcoded Pandas filters.
- **Automated Tweet Rewriting:** If verified, GPT-4o rewrites the tweet with new event details.

##  Project Structure
```
/ sports_tweet_verifier
│── app.py                    # Main Streamlit UI & logic
│── gpt4_api.py                # Handles OpenAI GPT-4o API calls
│── sql_utils.py               # Generates dynamic SQL queries
│── db.json                    # Mock database (hardcoded sports data)
│── requirements.txt           # Python dependencies
│── README.md                  # Project documentation
```

## ⚙️ Installation & Setup
### **1️ Clone the Repository**
```sh
git clone https://github.com/your-repo/sports-tweet-verifier.git
cd sports-tweet-verifier
```

### **2️ Install Dependencies**
```sh
pip install -r requirements.txt
```

### **3️ Run the Application**
```sh
streamlit run app.py
```

##  How It Works
### **1️ User Inputs Event & Tweet**
Users enter:
- **Event JSON:** `{ "winner": "Clemson", "team": "Clemson", "opponentTeam": "Miami", "season": "2024" }`
- **Tweet Template:** `"Florida State has won multiple times against Miami in different seasons"`

These are stored as:
```python
event_input = st.text_area("Enter Event (JSON format)", "...")
tweet_template = st.text_input("Enter Tweet Template", "...")
```

### **2️ Generate SQL Query (Retrieving Past Games)**
The function `generate_sql_from_event(event_data)` creates an SQL query:
```sql
SELECT * FROM game_events
WHERE (team = 'Clemson' AND opponentTeam = 'Miami')
   OR (team = 'Miami' AND opponentTeam = 'Clemson');
```
This fetches relevant past games from `db.json` and executes dynamically on SQLite.

### **3️ Execute SQL Query on SQLite Database**
Instead of Pandas filtering, the dataset is loaded into an **in-memory SQLite database**:
```python
df = pd.DataFrame(game_db)
conn = sqlite3.connect(":memory:")
df.to_sql("game_events", conn, index=False, if_exists="replace")
```
Query execution:
```python
relevant_data = pd.read_sql_query(sql_query, conn)
```

### **4️ Generate Verification SQL Query Dynamically**
GPT-4o generates a second SQL query to validate the event against the tweet pattern:
```sql
SELECT 
    CASE 
        WHEN COUNT(DISTINCT season) > 1 THEN 'True'
        ELSE 'False' 
    END AS match_result
FROM game_events
WHERE winner = 'Clemson'
AND opponentTeam = 'Miami';
```
This ensures the response is **directly `True` or `False`**.

### **5️ Execute Verification Query**
```python
verification_result_df = pd.read_sql_query(verification_sql, conn)
if not verification_result_df.empty:
    result_value = str(verification_result_df.iloc[0, 0]).strip().lower()
    verification_result = "true" if result_value == "true" else "false"
```

### **6️ Rewrite Tweet if Verified**
If `verification_result == "true"`, GPT-4o dynamically rewrites the tweet:
```python
rewrite_prompt = f"""
You are a sports analytics writer. Rewrite the tweet based on the event details.
- **Original Tweet:** "{tweet_template}"
- **Winning Team:** {event_data['winner']}
- **Opponent Team:** {event_data['opponentTeam']}
- **Verified Trend:** {verification_result}
"""
rewritten_tweet = get_gpt4_response(rewrite_prompt)
st.success("Tweet Verified & Rewritten!")
st.write(rewritten_tweet)
```

##  Future Improvements
1. Optimize GPT-4o prompt engineering for better SQL accuracy.
2. Expand dataset for real-time sports event integration.
3. Implement more robust SQL execution error handling.

 **Now, the system ensures accurate SQL query generation, execution, and tweet validation dynamically!** 🚀
