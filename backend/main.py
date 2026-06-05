from fastapi import FastAPI, UploadFile, File
from services.review_service import review_project
from fastapi.responses import FileResponse
from services.github_review_service import (
    review_github_repository
)
from pydantic import BaseModel
import os

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

    return {
    "message": "Repository review completed",
    "report": result["report"],
    "report_file": os.path.basename(
        result["report_file"]
    ),
    "pdf_file": os.path.basename(
        result["pdf_file"]
    )
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

    return {
    "message": "Review completed successfully",
    "report": result["report"],
    "report_file": os.path.basename(
        result["report_file"]
    ),
    "pdf_file": os.path.basename(
        result["pdf_file"] )
}