# MongoDB connection helper
# All database operations go through this module

import pymongo
from django.conf import settings

def get_db():
    """Return the MongoDB database instance."""
    client = pymongo.MongoClient(settings.MONGO_URI)
    return client[settings.MONGO_DB_NAME]

def get_collection(name):
    """Return a specific MongoDB collection by name."""
    return get_db()[name]
