import pymongo
from decouple import config

# Load MongoDB credentials from .env
MONGO_URI = config("DB_URI")
DB_NAME = config("DB_NAME")

# Initialize MongoDB connection
client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]  # Access the database

__all__ = ["db"]  # Explicitly define exports
