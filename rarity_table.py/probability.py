import pandas as pd
import scipy.stats as stats
from sqlalchemy import inspect
from config import engine

def process_probability(event_data, matched_tables):
    """Calculate probability based on mean and standard deviation"""

    inspector = inspect(engine)
    results = []

    for table in matched_tables:
        # Get available columns in this table
        columns = {col['name'].lower() for col in inspector.get_columns(table)}

        if 'avg' in columns and 'std' in columns:
            query = f"""
            SELECT "avg", "std" FROM {table} 
            WHERE "stat" = '{event_data['stat']}'
            LIMIT 1
            """
            df = pd.read_sql(query, engine)

            if not df.empty:
                mean = df.iloc[0]['avg']
                std_dev = df.iloc[0]['std']

                # Handle None (NULL) values and prevent division by zero
                if mean is None or std_dev is None or std_dev == 0:
                    probability = None  # Invalid probability
                else:
                    value = event_data['value']
                    z_score = abs(value - mean) / std_dev
                    probability = 2 * (1 - stats.norm.cdf(z_score))

                results.append({'table': table, 'probability': probability})
    
    # Convert to DataFrame and sort the values in ascending order
    result_df = pd.DataFrame(results)
    if not result_df.empty:
        result_df = result_df.sort_values(by='probability', ascending=True)  # Sorting

    return result_df
