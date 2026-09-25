# Priya Mentor AI

AI-powered learning assistant built with React, TypeScript, FastAPI, PostgreSQL, and Ollama.

## Features

- Conversational AI learning assistant
- Document upload for PDF, DOCX, and TXT files
- PostgreSQL-backed document storage and chat history
- Document-grounded responses using stored document content
- AI-generated multiple-choice quizzes with difficulty and question-count controls
- React/TypeScript frontend with separate Chat, Documents, and Quiz workflows
- REST API backend with FastAPI

## Architecture

```text
React + TypeScript frontend
          |
          | REST API
          v
FastAPI backend
   |          |
   |          +---- Ollama (local LLM)
   |
   +---- PostgreSQL
```

## Project Structure

```text
priya-mentor-ai/
├── backend/
│   ├── api/
│   │   ├── chat.py
│   │   ├── documents.py
│   │   └── quiz.py
│   ├── database/
│   │   ├── db.py
│   │   └── schema.sql
│   ├── .env.example
│   ├── main.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   ├── .env.example
│   ├── package.json
│   └── vite.config.ts
└── README.md
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/gayathripriya99/AI-Powered-Learning-Analytics-Platform.git
cd AI-Powered-Learning-Analytics-Platform
```

### 2. Configure PostgreSQL

Create a PostgreSQL database named `priya_mentor`, then run:

```bash
psql -d priya_mentor -f backend/database/schema.sql
```

### 3. Configure the backend

Copy `backend/.env.example` to `backend/.env` and set your local PostgreSQL connection and Ollama settings.

Install dependencies:

```bash
cd backend
python -m venv .venv
# Windows
.venv\\Scripts\\activate
# macOS/Linux
# source .venv/bin/activate
pip install -r requirements.txt
```

Start FastAPI:

```bash
uvicorn main:app --reload --port 8000
```

### 4. Configure the frontend

Copy `frontend/.env.example` to `frontend/.env`, then:

```bash
cd frontend
npm install
npm run dev
```

The frontend defaults to `http://localhost:5173` and the backend to `http://localhost:8000`.

## LLM Configuration

The application is designed to use Ollama for local LLM inference. Credentials and environment-specific configuration are intentionally excluded from the repository. Never commit API keys, passwords, private keys, or `.env` files.

## Security Note

This public repository intentionally excludes local credentials, SSH keys, virtual environments, dependency directories, and other machine-specific files.
