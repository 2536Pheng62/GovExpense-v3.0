import sqlite3
import json
from datetime import datetime

class GovExpenseDB:
    def __init__(self, db_path="govexpense.db"):
        self.db_path = db_path
        self._create_tables()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _create_tables(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for Traveler Profiles
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    full_name TEXT UNIQUE,
                    position TEXT,
                    c_level TEXT,
                    department TEXT,
                    last_used DATETIME
                )
            """)
            # Table for Saved Trip Drafts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drafts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    draft_name TEXT,
                    session_data TEXT,
                    created_at DATETIME
                )
            """)
            conn.commit()

    # --- Profile Methods ---
    def save_profile(self, full_name, position, c_level, department):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO profiles (full_name, position, c_level, department, last_used)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(full_name) DO UPDATE SET
                    position=excluded.position,
                    c_level=excluded.c_level,
                    department=excluded.department,
                    last_used=excluded.last_used
            """, (full_name, position, c_level, department, datetime.now()))
            conn.commit()

    def get_all_profiles(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT full_name, position, c_level, department FROM profiles ORDER BY last_used DESC")
            return cursor.fetchall()

    def delete_profile(self, full_name):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM profiles WHERE full_name = ?", (full_name,))
            conn.commit()

    # --- Draft Methods ---
    def save_draft(self, name, data_dict):
        # Convert date/time objects to string for JSON serialization
        def serializable(obj):
            if hasattr(obj, 'isoformat'):
                return obj.isoformat()
            return str(obj)

        json_data = json.dumps(data_dict, default=serializable)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO drafts (draft_name, session_data, created_at) VALUES (?, ?, ?)",
                           (name, json_data, datetime.now()))
            conn.commit()

    def get_all_drafts(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, draft_name, created_at FROM drafts ORDER BY created_at DESC")
            return cursor.fetchall()

    def load_draft(self, draft_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT session_data FROM drafts WHERE id = ?", (draft_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else None
