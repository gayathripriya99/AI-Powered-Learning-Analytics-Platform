from fastapi import APIRouter, UploadFile, File
import os

import pypdf
import docx2txt

from database.db import get_connection, is_sqlite_db

router = APIRouter()

# This function reads text from uploaded files
def extract_text(file_path: str, filename: str) -> str:
    # If PDF - use pypdf to read it
    if filename.endswith('.pdf'):
        reader = pypdf.PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    # If Word doc - use docx2txt
    elif filename.endswith('.docx'):
        return docx2txt.process(file_path)

    # If plain text - just read it
    elif filename.endswith('.txt'):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    return ""

@router.post("/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        temp_path = f"temp_{file.filename}"
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)

        text = extract_text(temp_path, file.filename)

        conn = get_connection()
        cursor = conn.cursor()
        if is_sqlite_db():
            cursor.execute(
                "INSERT INTO documents (filename, content) VALUES (?, ?)",
                (file.filename, text)
            )
            doc_id = cursor.lastrowid
        else:
            cursor.execute(
                "INSERT INTO documents (filename, content) VALUES (%s, %s) RETURNING id",
                (file.filename, text)
            )
            doc_id = cursor.fetchone()["id"]
        conn.commit()
        conn.close()

        os.remove(temp_path)

        return {
            "message": "Document uploaded successfully!",
            "document_id": doc_id,
            "filename": file.filename,
            "characters": len(text),
        }
    except Exception as e:
        return {"error": str(e)}

@router.get("/documents")
def get_documents():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, filename, created_at FROM documents ORDER BY created_at DESC")
        docs = cursor.fetchall()
        conn.close()
        return {"documents": [dict(d) for d in docs]}
    except Exception as e:
        return {"error": str(e)}