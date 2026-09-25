from fastapi import APIRouter
from pydantic import BaseModel
import requests
import os

from database.db import get_connection, is_sqlite_db

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

def fallback_answer(message: str) -> str:
    text = (message or "").strip()
    if not text:
        return "Please ask me a question and I will help you study."

    lower = text.lower()
    if "python" in lower:
        return "Python is a beginner-friendly language used for automation, data analysis, and AI. A good way to learn it is to practice small projects, read code examples, and repeat key syntax daily."
    if "math" in lower or "algebra" in lower:
        return "Math becomes easier when you break it into steps: identify the goal, recall the formula, solve one step at a time, and check your answer."
    if "react" in lower:
        return "React helps you build user interfaces using reusable components. Think of each component as a small building block that manages one part of the page."
    if "study" in lower or "learning" in lower:
        return "A strong study routine is to review a topic, practice a few questions, explain it in your own words, and revisit the weak areas the next day."
    return f"Here is a simple way to think about it: break the topic into the main idea, key facts, and one example, then practice explaining it out loud in your own words."

def search_documents(query: str) -> str:
    """Search uploaded documents for relevant content."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        search_term = f"%{query[:50]}%"
        if is_sqlite_db():
            cursor.execute(
                "SELECT filename, content FROM documents WHERE lower(content) LIKE lower(?) LIMIT 2",
                (search_term,)
            )
        else:
            cursor.execute(
                "SELECT filename, content FROM documents WHERE content ILIKE %s LIMIT 2",
                (search_term,)
            )
        docs = cursor.fetchall()
        conn.close()

        if docs:
            context = "\n\n".join([f"From {d['filename']}:\n{d['content'][:500]}" for d in docs])
            return context
        return ""
    except Exception:
        return ""


def get_recent_chat_history(session_id: str, limit: int = 8) -> str:
    """Return the most recent conversation for this session in plain text."""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if is_sqlite_db():
            cursor.execute(
                "SELECT role, content FROM chat_history WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                (session_id, limit)
            )
        else:
            cursor.execute(
                "SELECT role, content FROM chat_history WHERE session_id = %s ORDER BY id DESC LIMIT %s",
                (session_id, limit)
            )
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return ""

        history = "\n".join(
            f"{entry['role'].capitalize()}: {entry['content']}" for entry in reversed(rows)
        )
        return f"Conversation history:\n{history}\n"
    except Exception:
        return ""

@router.post("/chat")
def chat(request: ChatRequest):
    try:
        doc_context = search_documents(request.message)
        chat_history = get_recent_chat_history(request.session_id)

        if doc_context:
            prompt = f"""You are Priya Mentor AI, a helpful learning assistant.

{chat_history}The user has uploaded documents. Here is relevant content:
{doc_context}

Based on the above context, answer this question:
{request.message}"""
        elif chat_history:
            prompt = f"""You are Priya Mentor AI, a helpful learning assistant.

{chat_history}Answer this question while using the conversation history above as context:
{request.message}"""
        else:
            prompt = f"""You are Priya Mentor AI, a helpful learning assistant.
Answer this question: {request.message}"""

        answer = fallback_answer(request.message)
        if OLLAMA_BASE_URL and OLLAMA_MODEL:
            try:
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/generate",
                    json={
                        "model": OLLAMA_MODEL,
                        "prompt": prompt,
                        "stream": False,
                    },
                    timeout=20,
                )
                if response.ok:
                    data = response.json()
                    answer = data.get("response", answer)
            except Exception as exc:
                print(f"Ollama fallback triggered: {exc}")

        conn = get_connection()
        cursor = conn.cursor()
        if is_sqlite_db():
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
                (request.session_id, "user", request.message)
            )
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)",
                (request.session_id, "ai", answer)
            )
        else:
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, content) VALUES (%s, %s, %s)",
                (request.session_id, "user", request.message)
            )
            cursor.execute(
                "INSERT INTO chat_history (session_id, role, content) VALUES (%s, %s, %s)",
                (request.session_id, "ai", answer)
            )
        conn.commit()
        conn.close()

        return {
            "message": request.message,
            "response": answer,
            "used_documents": bool(doc_context),
        }
    except Exception as e:
        return {"error": str(e)}