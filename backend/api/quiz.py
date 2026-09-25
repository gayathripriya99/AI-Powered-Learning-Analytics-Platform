from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import requests
import os
import json

router = APIRouter()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL")

class QuizRequest(BaseModel):
    topic: str
    num_questions: int = 3
    difficulty: str = "beginner"


def build_fallback_quiz(request: QuizRequest):
    topic = request.topic.strip() or "the topic"
    questions = []
    for index in range(max(1, request.num_questions)):
        label = f"Concept {index + 1}"
        questions.append(
            {
                "question": f"What is the most important idea to remember about {topic}?",
                "options": [
                    f"{label}: Understand the main idea and apply it in practice",
                    f"{label}: Skip the basics and memorize only the final answer",
                    f"{label}: Ignore examples and focus only on the title",
                    f"{label}: Avoid reviewing the topic after a first attempt"
                ],
                "answer": f"{label}: Understand the main idea and apply it in practice",
                "explanation": f"Strong learning starts with understanding the key concept, then applying it through examples and practice.",
            }
        )
    return {"questions": questions}


@router.post("/quiz/generate")
def generate_quiz(request: QuizRequest):
    try:
        if not OLLAMA_BASE_URL or not OLLAMA_MODEL:
            return build_fallback_quiz(request)

        prompt = f"""You are Priya Mentor AI, a helpful learning assistant.
Generate a multiple-choice quiz about "{request.topic}" at a "{request.difficulty}" difficulty level.
Generate exactly {request.num_questions} multiple-choice questions.

Output MUST be a JSON object containing a "questions" key, which is a list of objects.
Each object must have the following keys:
- "question": string, the text of the question
- "options": list of 4 strings, the possible answers
- "answer": string, the correct answer (MUST match one of the strings in the "options" list exactly)
- "explanation": string, a brief explanation of why the answer is correct

Return only the raw JSON.
"""

        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "")

        quiz_data = json.loads(answer)

        if "questions" not in quiz_data:
            if isinstance(quiz_data, list):
                quiz_data = {"questions": quiz_data}
            else:
                raise HTTPException(status_code=500, detail="Invalid quiz format returned from model")

        return quiz_data

    except Exception as e:
        print(f"Quiz generation failed: {e}")
        return build_fallback_quiz(request)
