from fastapi import FastAPI, UploadFile, File
from services.review_service import review_project
from fastapi.responses import FileResponse, StreamingResponse
from services.github_review_service import (
    review_github_repository
)
from services.chat_service import (
    ask_review_question,
    ask_review_question_stream,
    build_review_context,
    chat_cache
)
from pydantic import BaseModel
import os
from typing import List, Optional

app = FastAPI()

UPLOAD_FOLDER = "../uploads"
REPORT_FOLDER = "../reports"

os.makedirs(
    UPLOAD_FOLDER,
    exist_ok=True
)

class GithubRequest(
    BaseModel
):
    repo_url: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    report: Optional[str] = ""
    question: str
    history: Optional[List[ChatMessage]] = []
    review_context: Optional[dict] = None

@app.get("/")
def home():
    return {
        "message": "AI Code Reviewer Running"
    }

@app.get("/download-report/{filename}")
def download_report(filename: str):
    file_path = f"../reports/{filename}"
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="text/plain"
    )

@app.get("/download-pdf/{filename}")
def download_pdf(filename):
    path = os.path.join(
        REPORT_FOLDER,
        filename
    )
    print("PDF Path:", path)
    if not os.path.exists(path):
        return {
            "error": f"PDF not found: {path}"
        }
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=filename
    )

@app.post("/upload-zip")
async def upload_zip(
    file: UploadFile = File(...)
):
    print(f"Received: {file.filename}")
    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )
    with open(
        file_path,
        "wb"
    ) as buffer:
        buffer.write(
            await file.read()
        )
    print(f"Saved to: {file_path}")
    return {
        "message": "ZIP uploaded successfully",
        "filename": file.filename
    }

@app.post("/review-github")
async def review_github(
    request: GithubRequest
):
    result = review_github_repository(
        request.repo_url
    )
    
    # Read full report from file to generate structured context
    try:
        with open(result["report_file"], "r", encoding="utf-8") as f:
            full_report = f.read()
    except Exception as e:
        print(f"Error reading report file for github: {e}")
        full_report = result.get("report", "")

    review_context = build_review_context(full_report)

    return {
        "message": "Repository review completed",
        "report": full_report,
        "report_file": os.path.basename(
            result["report_file"]
        ),
        "pdf_file": os.path.basename(
            result["pdf_file"]
        ),
        "review_context": review_context
    }

@app.post("/review-project")
async def review_uploaded_project(
    file: UploadFile = File(...)
):
    file_path = os.path.join(
        UPLOAD_FOLDER,
        file.filename
    )
    with open(
        file_path,
        "wb"
    ) as buffer:
        buffer.write(
            await file.read()
        )

    result = review_project(
        file_path
    )

    # Read full report from file to generate structured context
    try:
        with open(result["report_file"], "r", encoding="utf-8") as f:
            full_report = f.read()
    except Exception as e:
        print(f"Error reading report file for project: {e}")
        full_report = result.get("report", "")

    review_context = build_review_context(full_report)

    return {
        "message": "Review completed successfully",
        "report": full_report,
        "report_file": os.path.basename(
            result["report_file"]
        ),
        "pdf_file": os.path.basename(
            result["pdf_file"]
        ),
        "review_context": review_context
    }

@app.post("/ask-review")
async def ask_review(request: ChatRequest):
    answer = ask_review_question(
        request.report,
        request.question,
        request.history,
        request.review_context
    )
    return {"answer": answer}

@app.post("/ask-review-stream")
async def ask_review_stream(request: ChatRequest):
    generator = ask_review_question_stream(
        request.report,
        request.question,
        request.history,
        request.review_context
    )
    return StreamingResponse(generator, media_type="text/event-stream")

@app.post("/clear-chat")
async def clear_chat():
    chat_cache.clear()
    return {"message": "Chat cache cleared"}