def extract_metadata_and_records(table_text):
    rows = table_text.split("\n")
    metadata = {}
    records = []

    # Example heuristic-based metadata extraction
    if "rushing yards" in table_text.lower():
        metadata = {"entity": "Player", "statistic": "Rushing Yards", "statPeriod": "Game"}

    # Extract rows into structured records
    for row in rows:
        columns = row.split()
        if len(columns) > 3:
            records.append({
                "playerName": columns[0],
                "opponentName": columns[-2],
                "statValue": columns[-1]
            })

    return metadata, records
