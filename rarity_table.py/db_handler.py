import pandas as pd
from sqlalchemy import inspect
from config import engine

def find_matching_tables(event_data):
    """Find tables that contain the relevant columns matching the event JSON keys"""
    inspector = inspect(engine)
    matched_tables = []

    # Extract event keys
    event_keys = set(event_data.keys())

    # Get all table names
    for table_name in inspector.get_table_names():
        # Get column names for this table
        columns = {col['name'].lower() for col in inspector.get_columns(table_name)}

        # Find common columns
        common_columns = event_keys.intersection(columns)

        # If stat column exists and at least one other key matches
        if 'stat' in columns and common_columns:
            matched_tables.append(table_name)

    return matched_tables
