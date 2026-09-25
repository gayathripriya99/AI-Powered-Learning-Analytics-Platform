from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from api.chat import router as chat_router
from api.documents import router as documents_router
from api.quiz import router as quiz_router


load_dotenv()

app = FastAPI(
    title="Priya Mentor AI",
    description="Your Personal AI Learning Companion",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:5173")],
    allow_credentials=False,
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
