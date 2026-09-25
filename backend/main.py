from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api.chat import router as chat_router
from api.documents import router as documents_router
from api.quiz import router as quiz_router


load_dotenv()


def get_allowed_origins():
    raw_value = os.getenv(
        "FRONTEND_URL",
        "http://localhost:5173,http://127.0.0.1:5173,https://ai-powered-learning-analytics-platform-g6w1g8w8r.vercel.app"
    )
    origins = [item.strip() for item in str(raw_value).split(",") if item.strip()]
    if not origins:
        origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "https://ai-powered-learning-analytics-platform-g6w1g8w8r.vercel.app"
        ]
    return origins


app = FastAPI(
    title="Priya Mentor AI",
    description="Your Personal AI Learning Companion",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)

app.include_router(documents_router)
app.include_router(quiz_router)

@app.on_event("startup")
async def startup():
    from database.db import test_connection
    test_connection()

@app.get("/")
def root():
    return {"message": "Priya Mentor AI is running!"}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}
