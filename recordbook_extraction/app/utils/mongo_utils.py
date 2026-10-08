#############################################################################################################################  
#                                      MONGODB UTILITIES FOR TABLE MATCHING                                                                                                                                            #############################################################################################
#############################################################################################################################
'''
Purpose:
    - Provides helper functions to interact with MongoDB.
    - Cleans and standardizes table headers for accurate matching.
    - Retrieves matching records from MongoDB based on processed headers.

Key Features:
    - Establishes MongoDB connection using environment variables.
    - Cleans headers to ensure consistent comparison.
    - Performs case-insensitive matching using MongoDB queries.

Created by:
    Guneesh Vats
    ML Engineer, Alonzo

Dated:
    23rd Jan, 2024
    Thursday
'''

#############################################################################################################################
#                                               IMPORTS                                                                                                                                               #############################################################################################
#############################################################################################################################

from pymongo import MongoClient
import os
import re

#############################################################################################################################
''' 
MongoDB Connection:
    - Reads MongoDB URI, database, and collection from environment variables.
    - Defaults to 'mongodb://mongodb:27017/' if no URI is provided.
'''
#############################################################################################################################
MONGO_URI = os.getenv("MONGO_URI", "mongodb://mongodb:27017/")  
MONGO_DB = os.getenv("MONGO_DB", "stage_database")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "StageRecords")



#####################################################################################################
''' 
get_mongo_client():
    - Creates and returns a new MongoDB client instance.
    - Ensures a fresh connection for each function call (Celery fork-safe).
'''
#####################################################################################################
def get_mongo_client():
    return MongoClient(MONGO_URI)



#####################################################################################################
''' 
clean_header():
    - Standardizes headers for accurate matching:
        1. Removes ':PageNo|X' patterns.
        2. Splits into individual words.
        3. Converts all words to lowercase.
    - Ensures headers from master JSON and MongoDB are formatted identically.
'''
#####################################################################################################
def clean_header(header: str) -> list:
    # Removing the ":PageNo|X" from the header field of master_json.json file for proper comparison with mongodb tables
    header = re.split(r":PageNo\|\d+", header)[0]  
    return [word.strip().lower() for word in header.split(",")]



#####################################################################################################
''' 
get_matching_table():
    - Searches MongoDB for a record where the 'headers' field contains all words from the cleaned header.
    - Uses case-insensitive comparison to improve matching accuracy.
    - Returns the first matched document or None if no match is found.
'''
#####################################################################################################
def get_matching_table(header: str):
    client = get_mongo_client()  
    db = client[MONGO_DB]
    collection = db[MONGO_COLLECTION]
    cleaned_header = clean_header(header)

    print(f"🔍 Searching MongoDB for: {cleaned_header}")

    # Check MongoDB records
    mongo_records = list(collection.find({}, {"headers": 1, "_id": 0}))
    print(f"🔍 Available MongoDB Headers: {mongo_records}")

    # Match Query
    query = {"headers": {"$all": cleaned_header}}
    result = collection.find_one(query)

    if not result:
        print(f"❌ No match found for {cleaned_header}")

    return result
