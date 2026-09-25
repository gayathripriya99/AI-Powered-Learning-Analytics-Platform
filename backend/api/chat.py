from fastapi import APIRouter
from pydantic import BaseModel
import requests
import os
import re

from database.db import get_connection, is_sqlite_db

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:1b")

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

def normalize_topic_name(value: str) -> str:
    cleaned = re.sub(r"\s+", " ", (value or "")).strip()
    if not cleaned:
        return "Interview Preparation"
    return cleaned.strip(". ")


def infer_quiz_topic(doc_context: str, message: str) -> str:
    text = (doc_context or message or "").strip()
    if not text:
        return "Interview Preparation"

    lower = text.lower()
    if "python" in lower:
        return "Python Interview Questions"
    if "react" in lower:
        return "React Interview Questions"
    if "sql" in lower:
        return "SQL Interview Questions"
    if "java" in lower:
        return "Java Interview Questions"
    if "aws" in lower:
        return "AWS Interview Questions"
    if "resume" in lower or "cv" in lower or "experience" in lower or "skills" in lower:
        return "Resume and Interview Preparation"
    if "machine learning" in lower or "ml" in lower:
        return "Machine Learning Concepts"
    if "data analysis" in lower or "analytics" in lower:
        return "Data Analysis Fundamentals"

    sentence = " ".join(text.split())
    if len(sentence) > 180:
        sentence = sentence[:180]
    topic = re.sub(r"[^a-zA-Z0-9\s-]", " ", sentence)
    parts = [p for p in topic.split() if len(p) > 3]
    if len(parts) >= 5:
        return normalize_topic_name(" ".join(parts[:6]))
    return normalize_topic_name(sentence[:60])


def technology_prompt_for_quiz() -> str:
    return "Which technology should I quiz you on? Python, React, SQL, Java, AWS, Machine Learning, or Resume/Interview Preparation."


def fallback_answer(message: str, history: str = "", doc_context: str = "") -> str:
    text = (message or "").strip()
    if not text:
        return "Please ask me a question and I will help you study."

    lower = text.lower()
    question = text.strip()

    if "quiz" in lower and ("resume" in lower or "cv" in lower or "uploaded" in lower or doc_context):
        topic = infer_quiz_topic(doc_context, text)
        return f"Yes — I reviewed your uploaded document and the best quiz topic is '{topic}'. I can open a quiz for that topic immediately and fill it in automatically."

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
        topic = infer_quiz_topic(doc_context, question)
        return f"Using the uploaded document as context, I would answer your question by focusing on the main themes in the file, the important details, and the practical takeaway for {question.lower()}. A good quiz topic from this document is '{topic}'."

    return f"Here is a simple way to think about it for '{question}': break the topic into the main idea, key facts, and one example, then practice explaining it out loud in your own words."

def get_recent_document_context(limit: int = 3) -> str:
    try:
        conn = get_connection()
        cursor = conn.cursor()
        if is_sqlite_db():
            cursor.execute(
                "SELECT filename, content FROM documents ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        else:
            cursor.execute(
                "SELECT filename, content FROM documents ORDER BY created_at DESC LIMIT %s",
                (limit,)
            )
        docs = cursor.fetchall()
        conn.close()
        if not docs:
            return ""
        return "\n\n".join(f"From {d['filename']}:\n{d['content'][:1500]}" for d in docs)
    except Exception:
        return ""


def search_documents(query: str) -> str:
    """Return the most relevant uploaded document context for the current question."""
    query_text = (query or "").strip()
    lower_query = query_text.lower()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        if query_text:
            search_term = f"%{query_text[:50]}%"
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
            if docs:
                conn.close()
                return "\n\n".join([f"From {d['filename']}:\n{d['content'][:1500]}" for d in docs])

        if any(word in lower_query for word in ["document", "resume", "cv", "uploaded", "quiz", "topic", "interview", "file", "generate"]):
            conn.close()
            return get_recent_document_context()

        conn.close()
        return get_recent_document_context()
    except Exception:
        return get_recent_document_context()


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


def is_ollama_available() -> bool:
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.ok
    except Exception:
        return False


@router.post("/chat")
def chat(request: ChatRequest):
    try:
        doc_context = search_documents(request.message)
        chat_history = get_recent_chat_history(request.session_id)

        suggested_topic = ""
        redirect_to_quiz = False
        needs_technology = False
        lower_msg = request.message.lower()

        if doc_context and any(word in lower_msg for word in ["quiz", "interview", "topic", "generate", "document", "resume", "cv", "file", "uploaded"]):
            suggested_topic = infer_quiz_topic(doc_context, request.message)
            redirect_to_quiz = True

        if not doc_context and any(word in lower_msg for word in ["quiz", "interview", "topic", "generate", "practice"]):
            needs_technology = True

        answer = fallback_answer(request.message, chat_history, doc_context)
        if suggested_topic:
            answer = (
                f"I reviewed your uploaded document and the best quiz topic is '{suggested_topic}'. "
                "I’ve prepared it for quiz generation so you can continue with the topic already filled in."
            )
        elif needs_technology:
            answer = technology_prompt_for_quiz()

        if "doubt" in lower_msg or "confused" in lower_msg or "not sure" in lower_msg or "explain" in lower_msg or "understand" in lower_msg:
            answer = (
                "Here is the core idea: start with the main concept, connect it to a practical example, and then test yourself with a short section-wise quiz. "
                "If you want, I can generate a quiz for Python, React, SQL, Java, AWS, Machine Learning, or Resume topics next."
            )

        if OLLAMA_BASE_URL and OLLAMA_MODEL and is_ollama_available():
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
                else:
                    answer = "I’m running in offline mode right now because the free local model is not reachable. Please make sure Ollama is running and the model is installed."
            except Exception as exc:
                print(f"Ollama fallback triggered: {exc}")
                answer = "I’m in offline mode right now because the free local model is not available. Start Ollama and install a model like llama3.2:1b for full chatbot behavior."

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
            "redirect_to_quiz": redirect_to_quiz,
            "suggested_topic": suggested_topic,
            "needs_technology": needs_technology,
        }
    except Exception as e:
        return {"error": str(e)}