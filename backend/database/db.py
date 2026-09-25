import psycopg2
from psycopg2.extras import RealDictCursor
import os
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv

load_dotenv(override=True)
DATABASE_URL = os.getenv("DATABASE_URL")

def get_connection():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def test_connection():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        result = cursor.fetchone()
        conn.close()
        print("Database connected:", result["version"])
        return True
    except Exception as e:
        print("Database error:", e)
        return False