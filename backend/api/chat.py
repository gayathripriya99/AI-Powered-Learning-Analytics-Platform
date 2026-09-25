from fastapi import APIRouter
from pydantic import BaseModel
import requests
import os

from database.db import get_connection, is_sqlite_db

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

def fallback_answer(message: str, history: str = "", doc_context: str = "") -> str:
    text = (message or "").strip()
    if not text:
        return "Please ask me a question and I will help you study."

    lower = text.lower()
    question = text.strip()

    if "quiz" in lower and ("resume" in lower or "cv" in lower or "uploaded" in lower or doc_context):
        return "Yes — I can create a quiz based on your uploaded resume or document. I would first extract the key skills, experience, and education points, then turn them into short MCQ questions with answers and explanations."

    if "resume" in lower or "cv" in lower:
        return "I can help review your resume by highlighting strengths, spotting skill gaps, and suggesting better phrasing. If you want, I can also turn it into interview questions or a quiz based on the content."

    if "document" in lower or "pdf" in lower or "upload" in lower or "file" in lower:
        return "I can use your uploaded document as context. I would extract the main ideas, summarize important points, and then answer questions or generate quizzes based on the file content."

    if "python" in lower:
        return "Python is a beginner-friendly language used for automation, data analysis, AI, and backend development. A strong way to learn it is to practice small exercises, review syntax regularly, and build one mini project at a time."

    if "math" in lower or "algebra" in lower or "calculus" in lower:
        return "For math, start by identifying the goal, recall the formula or concept, solve one small step at a time, and check the result before moving on. This helps reduce mistakes and build confidence."

    if "react" in lower:
        return "React works by breaking your UI into reusable components. Think of each component as a small building block: one handles the layout, another handles user actions, and together they create the page."

    if "study" in lower or "learning" in lower or "learn" in lower:
        return "A strong study routine is to review a topic, practice 5–10 questions, explain it in your own words, and revisit the weak areas the next day. That repetition makes learning stick."

    if "hello" in lower or "hi" in lower or "how are you" in lower:
        return "Hello! I’m here to help with learning, study planning, document review, and quiz creation. Ask me anything and I’ll guide you step by step."

    if history:
        return f"Based on our earlier conversation, I can help with that. For your question: '{question}', the best approach is to focus on the main idea, identify the key facts, and then apply them in a small example or practice task."

    if doc_context:
        return f"Using the uploaded document as context, I would answer your question by focusing on the main themes in the file, the important details, and the practical takeaway for {question.lower()}."

    return f"Here is a simple way to think about it for '{question}': break the topic into the main idea, key facts, and one example, then practice explaining it out loud in your own words."

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


def build_ollama_messages(request_message: str, chat_history: str, doc_context: str) -> list:
    system_message = (
        "You are Priya Mentor AI, a helpful learning assistant. "
        "Answer clearly, use the conversation context when available, and use uploaded document content when relevant. "
        "Keep answers concise but useful."
    )

    messages = [{"role": "system", "content": system_message}]

    if doc_context:
        messages.append({"role": "user", "content": f"Relevant document context:\n{doc_context}"})

    if chat_history:
        messages.append({"role": "user", "content": chat_history})

    messages.append({"role": "user", "content": request_message})
    return messages


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        doc_context = search_documents(request.message)
        chat_history = get_recent_chat_history(request.session_id)

        answer = fallback_answer(request.message, chat_history, doc_context)

        if OLLAMA_BASE_URL and OLLAMA_MODEL:
            try:
                payload = {
                    "model": OLLAMA_MODEL,
                    "messages": build_ollama_messages(request.message, chat_history, doc_context),
                    "stream": False,
                }
                response = requests.post(
                    f"{OLLAMA_BASE_URL}/api/chat",
                    json=payload,
                    timeout=30,
                )
                if response.ok:
                    data = response.json()
                    message_content = data.get("message", {}).get("content")
                    if message_content:
                        answer = message_content.strip()
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