from fuzzywuzzy import fuzz

def is_relevant_table(table_text):
    keywords = ["rushing yards", "touchdowns", "passing completions"]
    for keyword in keywords:
        if fuzz.partial_ratio(keyword.lower(), table_text.lower()) > 70:
            return True
    return False