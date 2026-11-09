"""
SQLite Database module for SkillBridge.
Provides session storage and privacy-focused 'Delete My Data' operations.
Simple, beginner-friendly SQLite implementation without heavy ORM overhead.
"""

import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any

# Locate root directory for the database file
DB_FILE = Path(__file__).resolve().parent.parent.parent / "skillbridge.db"

def get_connection():
    """
    Creates and returns a connection to the SQLite database.
    Sets row_factory to sqlite3.Row so columns can be accessed by name.
    """
    conn = sqlite3.connect(str(DB_FILE))
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """
    Initializes the database schema if tables do not already exist.
    Called on FastAPI startup.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        # Table to store analysis sessions
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                session_id TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                company_type TEXT NOT NULL,
                overall_score REAL NOT NULL,
                data_json TEXT NOT NULL
            )
        """)
        conn.commit()

def save_analysis(session_id: str, company_type: str, overall_score: float, data: Dict[str, Any]) -> None:
    """
    Saves an analysis record to the database as a JSON string.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO analyses (session_id, created_at, company_type, overall_score, data_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                session_id,
                datetime.now(timezone.utc).isoformat(),
                company_type,
                round(overall_score, 2),
                json.dumps(data)
            )
        )
        conn.commit()

def get_analysis(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a saved analysis session by ID.
    Returns None if not found.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT data_json FROM analyses WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        if row:
            return json.loads(row["data_json"])
        return None

def delete_analysis(session_id: str) -> bool:
    """
    Deletes a specific user analysis session for privacy compliance.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses WHERE session_id = ?", (session_id,))
        conn.commit()
        return cursor.rowcount > 0

def delete_all_user_data() -> int:
    """
    Wipes all saved analysis records to fulfill user 'Delete My Data' requests.
    Returns the count of deleted records.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM analyses")
        conn.commit()
        return cursor.rowcount
