from fastapi import APIRouter
from pydantic import BaseModel
import requests
import os
from database.db import get_connection

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

def search_documents(query: str) -> str:
    """Search uploaded documents for relevant content"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        # Simple search - find documents containing words from the query
        cursor.execute(
            "SELECT filename, content FROM documents WHERE content ILIKE %s LIMIT 2",
            (f'%{query[:50]}%',)
        )
        docs = cursor.fetchall()
        conn.close()

        if docs:
            context = "\n\n".join([f"From {d['filename']}:\n{d['content'][:500]}" for d in docs])
            return context
        return ""
    except:
        return ""

@router.post("/chat")
def chat(request: ChatRequest):
    try:
        # Search documents for context
        doc_context = search_documents(request.message)

        # Build prompt with or without document context
        if doc_context:
            prompt = f"""You are Priya Mentor AI, a helpful learning assistant.

The user has uploaded documents. Here is relevant content:
{doc_context}

Based on the above context, answer this question:
{request.message}"""
        else:
            prompt = f"""You are Priya Mentor AI, a helpful learning assistant.
Answer this question: {request.message}"""

        # Call Ollama
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "stream": False
            }
        )
        data = response.json()
        answer = data.get("response", "No response")

        # Save to database
        conn = get_connection()
        cursor = conn.cursor()
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
            "used_documents": bool(doc_context)
        }
    except Exception as e:
        return {"error": str(e)}