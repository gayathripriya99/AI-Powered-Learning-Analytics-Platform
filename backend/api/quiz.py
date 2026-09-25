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


TECHNOLOGY_SECTIONS = {
    "python": [
        "Python Basics",
        "Data Structures",
        "OOP Concepts",
        "Error Handling",
        "Modules and Libraries",
        "Project Thinking"
    ],
    "react": [
        "Components",
        "State and Props",
        "Hooks",
        "Routing",
        "API Integration",
        "Performance"
    ],
    "sql": [
        "Joins",
        "Normalization",
        "Indexes",
        "Queries",
        "Transactions",
        "Optimization"
    ],
    "java": [
        "Java Basics",
        "OOP",
        "Collections",
        "Exception Handling",
        "Multithreading",
        "Spring Concepts"
    ],
    "aws": [
        "Compute",
        "Storage",
        "Networking",
        "Security",
        "Databases",
        "Cost Optimization"
    ],
    "machine learning": [
        "Model Basics",
        "Preprocessing",
        "Evaluation",
        "Feature Engineering",
        "Training",
        "Deployment"
    ],
    "resume": [
        "Skills",
        "Experience",
        "Projects",
        "Communication",
        "Achievements",
        "Interview Readiness"
    ],
}


def detect_technology(topic: str):
    value = (topic or "").lower()
    for tech, sections in TECHNOLOGY_SECTIONS.items():
        if tech in value:
            return tech, sections
    return "general interview", [
        "Core Concepts",
        "Application",
        "Problem Solving",
        "Communication",
        "Practical Examples",
        "Review"
    ]


def build_fallback_quiz(request: QuizRequest):
    topic = (request.topic or "").strip() or "the topic"
    technology, sections = detect_technology(topic)
    question_count = max(1, min(request.num_questions, len(sections)))
    questions = []
    selected_sections = sections[:question_count]

    for index, section in enumerate(selected_sections):
        question_text = f"What is the most important thing to know about {section} in {technology.title()}?"
        options = [
            f"Understand the core idea and apply it using a practical example",
            "Memorize the answer without understanding the concept",
            "Skip examples and only focus on the final result",
            "Avoid reviewing the topic after a first attempt"
        ]
        questions.append(
            {
                "section": section,
                "question": question_text,
                "options": options,
                "answer": "Understand the core idea and apply it using a practical example",
                "explanation": f"Strong performance in {technology.title()} comes from understanding the concept clearly, then practicing it in real examples and interview scenarios.",
            }
        )
    return {"technology": technology.title(), "sections": selected_sections, "questions": questions}


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

        technology, sections = detect_technology(request.topic)
        quiz_data.setdefault("technology", technology.title())
        if not quiz_data.get("sections"):
            quiz_data["sections"] = sections[:max(1, min(len(sections), request.num_questions))]
        return quiz_data

    except Exception as e:
        print(f"Quiz generation failed: {e}")
        return build_fallback_quiz(request)
