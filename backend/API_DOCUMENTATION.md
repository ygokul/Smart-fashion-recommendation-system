# Resumini API Documentation

Base URL: `http://127.0.0.1:8000`

## 1. Health Check

**Endpoint**: `GET /`
**Description**: Checks if the API server is running.
**Response**:

```json
{
  "message": "Resumini API is running"
}
```

## 2. Upload Resume (File)

**Endpoint**: `POST /upload/file`
**Description**: Upload a resume file (PDF, DOCX, etc.) to extract text and store it in the in-memory RAG system.
**Request**: `multipart/form-data`

- `file`: The resume file.
  **Response**:

```json
{
    "status": "success",
    "extracted_text": "...",
    "rag_status": { ... },
    "message": "Resume processed and stored in memory."
}
```

## 3. Upload Resume (Text)

**Endpoint**: `POST /upload/text`
**Description**: Upload raw text of a resume directly.
**Request**: JSON

```json
{
  "text": "Full text of the resume..."
}
```

## 4. Analyze Summary

**Endpoint**: `POST /analyze/summary`
**Description**: Generates a professional single-paragraph summary of the provided resume text.
**Request**: JSON

```json
{
  "text": "Full text of the resume..."
}
```

**Response**:

```json
{
  "status": "success",
  "report": "Candidate Summary Report..."
}
```

## 5. Analyze ATS Score

**Endpoint**: `POST /analyze/ats`
**Description**: Calculates an ATS compatibility score based on keywords and structure. Can optionally provide an AI-based evaluation against a job description.
**Request**: JSON

```json
{
  "resume_text": "Resume content...",
  "role": "Target Job Role",
  "job_description": "Optional job description..."
}
```

**Response**:

```json
{
    "status": "success",
    "ats_report": {
        "overall_score": 85.5,
        "keyword_score": 90,
        ...
    },
    "ai_feedback": "Detailed AI feedback...",
    "match_score": 80
}
```

## 6. Optimize Resume

**Endpoint**: `POST /optimize`
**Description**: Rewrites the resume content to better align with a specific role.
**Request**: JSON

```json
{
  "request": {
    "text": "Original resume text..."
  },
  "role": "Senior Python Developer"
}
```

**Response**:

```json
{
  "status": "success",
  "optimized_content": "Rewritten resume content..."
}
```

## 7. Chat (RAG)

**Endpoint**: `POST /chat`
**Description**: Ask questions about the uploaded resume using RAG (Retrieval-Augmented Generation).
**Request**: JSON

```json
{
  "query": "Does the candidate have experience with FastAPI?",
  "top_k": 4
}
```

**Response**:

```json
{
  "status": "success",
  "report": "Yes, the candidate has 3 years of experience..."
}
```

## 8. Job Search

**Endpoint**: `POST /jobs`
**Description**: Searches for jobs on LinkedIn using Selenium (Headless Chrome).
**Request**: JSON

```json
{
  "role": "Python Developer",
  "location": "Remote"
}
```

**Response**:

```json
{
  "status": "success",
  "jobs": [{ "title": "...", "company": "...", "link": "..." }]
}
```

## 9. LaTeX Preview

**Endpoint**: `POST /preview/latex`
**Description**: Generates a LaTeX version of the resume and attempts to compile it to PDF.
**Request**: JSON

```json
{
  "request": {
    "text": "Resume text..."
  },
  "role": "Target Role"
}
```

**Response**: Returns JSON containing `latex_source`, `pdf_base64`, and an `html_preview` string.
