"""
Database Configuration Module
Provides connection helpers for MongoDB and Neo4j.
"""

import os
import sys
from dotenv import load_dotenv
from pymongo import MongoClient
from neo4j import GraphDatabase

# Load environment variables from .env file
load_dotenv()

# ─── MongoDB ────────────────────────────────────────────────────────────────

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "online_learning_portal")

_mongo_client = None


def get_mongo_client():
    """Return a singleton MongoClient instance."""
    global _mongo_client
    if _mongo_client is None:
        try:
            _mongo_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # Force a connection to verify it works
            _mongo_client.admin.command("ping")
            print("[MongoDB] Connected successfully.")
        except Exception as e:
            print(f"[MongoDB] Connection failed: {e}")
            sys.exit(1)
    return _mongo_client


def get_mongo_db():
    """Return the project database handle."""
    client = get_mongo_client()
    return client[MONGO_DB_NAME]


# ─── Neo4j ──────────────────────────────────────────────────────────────────

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

_neo4j_driver = None


def get_neo4j_driver():
    """Return a singleton Neo4j Driver instance."""
    global _neo4j_driver
    if _neo4j_driver is None:
        try:
            _neo4j_driver = GraphDatabase.driver(
                NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            _neo4j_driver.verify_connectivity()
            print("[Neo4j] Connected successfully.")
        except Exception as e:
            print(f"[Neo4j] Connection failed: {e}")
            sys.exit(1)
    return _neo4j_driver


def close_connections():
    """Gracefully close all database connections."""
    global _mongo_client, _neo4j_driver
    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        print("[MongoDB] Connection closed.")
    if _neo4j_driver:
        _neo4j_driver.close()
        _neo4j_driver = None
        print("[Neo4j] Connection closed.")
