# News to Video Pipeline

A FastAPI-based MVP for automated news-to-video pipeline that extracts key points from YouTube or news URLs, generates a standalone German story script for YouTube videos, and prepares structure for voiceover and video generation.

## Features

- Extract text/transcripts from news articles or YouTube videos
- Summarize and translate content to German
- Generate structured script with title, hook, chapters, and full script
- RESTful API with FastAPI
- Docker support for Cloud Run deployment
- Modular project structure
- Logging and error handling

## API Endpoints

### POST /generate-script

Generate a video script from a URL.

**Request Body:**
```json
{
  "url": "string",
  "target_language": "de",
  "duration_minutes": 10
}
```

**Response:**
```json
{
  "title": "string",
  "hook": "string",
  "chapters": [
    {
      "title": "string",
      "content": "string"
    }
  ],
  "full_script": "string",
  "sources": ["string"],
  "warnings": ["string"]
}
```

### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

## Installation

1. Clone the repository
2. Create virtual environment: `python -m venv venv`
3. Activate: `venv\Scripts\activate` (Windows)
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and configure if needed

## Running Locally

```bash
uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## Docker

Build and run with Docker:

```bash
docker build -t news-to-video .
docker run -p 8080:8080 news-to-video
```

## Deployment to Cloud Run

1. Build and push Docker image to GCR or Artifact Registry
2. Deploy to Cloud Run with the image
3. Set environment variables if needed

## Project Structure

```
app/
├── __init__.py
├── main.py          # FastAPI app
├── config.py        # Settings
├── models.py        # Pydantic models
├── utils.py         # Utility functions
└── routes/
    ├── __init__.py
    └── generate.py  # Generate script endpoint
```

## Requirements

- Python 3.9+
- Internet access for URL fetching and translation