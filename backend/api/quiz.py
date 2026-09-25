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

@router.post("/quiz/generate")
def generate_quiz(request: QuizRequest):
    try:
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

        # Call Ollama with format="json"
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "format": "json",
                "stream": False
            }
        )
        response.raise_for_status()
        data = response.json()
        answer = data.get("response", "")

        # Parse the JSON response
        quiz_data = json.loads(answer)
        
        # Verify the structure has "questions"
        if "questions" not in quiz_data:
            # Fallback or wrap in structure
            if isinstance(quiz_data, list):
                quiz_data = {"questions": quiz_data}
            else:
                raise HTTPException(status_code=500, detail="Invalid quiz format returned from model")

        return quiz_data

    except Exception as e:
        print(f"Quiz generation failed: {e}")
        # Return a fallback quiz so the UI doesn't completely break
        fallback = {
            "questions": [
                {
                    "question": f"What is a key concept in {request.topic}?",
                    "options": [
                        f"Core concept A of {request.topic}",
                        f"Core concept B of {request.topic}",
                        f"Core concept C of {request.topic}",
                        f"Core concept D of {request.topic}"
                    ],
                    "answer": f"Core concept A of {request.topic}",
                    "explanation": f"This is a fallback question for {request.topic} because the AI generation failed or timed out."
                }
            ]
        }
        return fallback
