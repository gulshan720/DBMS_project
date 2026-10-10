"""
MongoDB Service Helper
Provides serialization, collection operations, and transactional helpers.
"""

from datetime import datetime, date
from bson import ObjectId
from config.db_config import get_mongo_db, get_mongo_client

def serialize_doc(doc):
    """Recursively convert MongoDB document objects (ObjectId, datetime) to JSON serializable formats."""
    if doc is None:
        return None
    if isinstance(doc, list):
        return [serialize_doc(item) for item in doc]
    if isinstance(doc, dict):
        result = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            elif isinstance(value, ObjectId):
                result[key] = str(value)
            elif isinstance(value, (datetime, date)):
                result[key] = value.isoformat()
            elif isinstance(value, (dict, list)):
                result[key] = serialize_doc(value)
            else:
                result[key] = value
        return result
    return doc

def get_collection(name: str):
    """Retrieve collection handle."""
    db = get_mongo_db()
    return db[name]
