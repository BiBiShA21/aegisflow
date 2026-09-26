"""
AegisFlow - MongoDB Database Configuration
Phase 1: Complete database setup with all collections
"""
import os
from datetime import datetime
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/aegisflow")
DB_NAME = os.getenv("DB_NAME", "aegisflow")

# Global client
_client = None
_db = None


def get_client():
    global _client
    if _client is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    return _client


def get_db():
    global _db
    if _db is None:
        _db = get_client()[DB_NAME]
    return _db


def init_db():
    """Initialize all collections and indexes"""
    try:
        db = get_db()
        db.command("ping")
        print("[OK] MongoDB Connected Successfully")

        # Create indexes
        db.users.create_index("username", unique=True)
        db.users.create_index("email", unique=True)
        db.scans.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])
        db.vulnerabilities.create_index("scan_id")
        db.fixes.create_index("scan_id")
        db.audit_logs.create_index([("user_id", ASCENDING), ("timestamp", DESCENDING)])
        db.repo_scans.create_index([("user_id", ASCENDING), ("created_at", DESCENDING)])

        print("[OK] All collections and indexes ready")
        return True
    except ConnectionFailure as e:
        print(f"[ERROR] MongoDB connection failed: {e}")
        return False


# ─── COLLECTION HELPERS ────────────────────────────────────────────

def users_col():
    return get_db().users

def scans_col():
    return get_db().scans

def vulnerabilities_col():
    return get_db().vulnerabilities

def fixes_col():
    return get_db().fixes

def scan_history_col():
    return get_db().scan_history

def audit_logs_col():
    return get_db().audit_logs

def confidence_scores_col():
    return get_db().confidence_scores

def repo_scans_col():
    return get_db().repo_scans

def workspaces_col():
    return get_db().workspaces

def scheduled_scans_col():
    return get_db().scheduled_scans

