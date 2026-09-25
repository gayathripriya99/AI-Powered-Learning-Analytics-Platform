import os
import sqlite3

import psycopg2
from psycopg2.extras import RealDictCursor
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = os.getenv("DATABASE_URL")
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "priya_mentor.db")

def is_sqlite_db() -> bool:
    return not DATABASE_URL or DATABASE_URL.startswith("sqlite")

def ensure_sqlite_schema(conn: sqlite3.Connection):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK (role IN ('user', 'ai')),
            content TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_chat_history_session_id ON chat_history(session_id)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC)"
    )
    conn.commit()

def get_connection():
    if is_sqlite_db():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        ensure_sqlite_schema(conn)
        return conn

    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if is_sqlite_db():
            cursor.execute("SELECT sqlite_version();")
            result = cursor.fetchone()
            print("Database connected:", result[0])
        else:
            cursor.execute("SELECT version();")
            result = cursor.fetchone()
            print("Database connected:", result["version"])
        conn.close()
        return True
    except Exception as e:
        print("Database error:", e)
        return False