# AI-Powered Code Review System

An AI-powered code review platform that analyzes ZIP projects and GitHub repositories using Retrieval-Augmented Generation (RAG) and Large Language Models (LLMs).

## Features

* ZIP Project Review
* GitHub Repository Review
* Hybrid Retrieval (Semantic + Keyword Search)
* AI-Based Bug Detection
* Security Issue Detection
* Improvement Suggestions
* PDF Report Generation
* Markdown Report Generation
* Streamlit Frontend
* FastAPI Backend

## Architecture

1. User uploads a ZIP project or provides a GitHub repository URL.
2. Files are extracted and processed.
3. Project files are vectorized using embeddings.
4. Hybrid retrieval selects the most relevant files.
5. Retrieved files are reviewed by the LLM.
6. A consolidated review report is generated.
7. Reports can be downloaded as PDF or Markdown.

## Tech Stack

### Backend

* FastAPI
* Python
* ChromaDB
* LangChain
* Sentence Transformers
* Ollama
* Qwen 7B

### Frontend

* Streamlit

### Report Generation

* ReportLab

## Project Structure

```text
AI-Code-Reviewer/
│
├── backend/
│   ├── rag/
│   ├── utils/
│   ├── tests/
│   ├── main.py
│   └── requirements.txt
│
├── frontend/
│   └── app.py
│
├── sample_project/
│
├── uploads/
├── reports/
├── vector_db/
│
└── README.md
```

## Installation

### Clone Repository

```bash
git clone <repository-url>
cd AI-Code-Reviewer
```

### Backend Setup

```bash
cd backend

python -m venv venv

venv\Scripts\activate

pip install -r requirements.txt
```

### Start Ollama

```bash
ollama serve
```

Pull the model:

```bash
ollama pull qwen2.5-coder:7b
```

### Run Backend

```bash
uvicorn main:app --reload
```

### Run Frontend

```bash
cd frontend

streamlit run app.py
```

## Usage

### ZIP Review

1. Open Streamlit UI.
2. Upload a ZIP project.
3. Click Review ZIP Project.
4. Download the generated report.

### GitHub Review

1. Enter a GitHub repository URL.
2. Click Review GitHub Repository.
3. Download the generated report.

## Future Improvements

* Static Analysis Integration (Bandit)
* Automated Test Coverage
* Multi-LLM Support
* Docker Deployment
* CI/CD Integration

## Author

Subhransu Bhol
