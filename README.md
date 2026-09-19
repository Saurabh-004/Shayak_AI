# Shayak AI (Sahayak Shield)

A scam-risk detection and safety assistant for suspicious messages, calls, websites, screenshots, and audio recordings.

The app is built as a lightweight FastAPI service with a static frontend and is designed to help users pause, understand, and verify unusual requests before they take action.

## Overview

Shayak AI helps users assess whether a message, call description, URL, screenshot, or audio clip shows signs of a scam or manipulation attempt. It focuses on senior-friendly, calm language and avoids making claims of certainty.

The app can work in demo mode without an API key, while enabling stronger analysis when services like OpenAI, Supabase, and AssemblyAI are configured.

## Features

- Message analysis for suspicious text, OTP requests, urgent threats, payment demands, and phishing cues
- Call-description analysis for impersonation and scam-style conversations
- Website URL risk checks for suspicious domains, insecure links, and phishing patterns
- Screenshot review with upload validation and OCR fallback
- Audio deepfake / synthetic-voice risk detection for uploaded recordings
- First-speaker identification for call recordings, allowing the first voice segment to be isolated and checked
- Optional sign-up and sign-in using Supabase Auth
- Cookie-based session handling with filtered access to protected endpoints
- Safety-first rate limiting and security headers
- Browser voice input and read-aloud support for accessibility
- Demo mode for local or low-setup use without external API keys
- Health check endpoint and Render deployment configuration

## User experience

- Large, high-contrast interface
- Clear risk outputs: LOW, MEDIUM, HIGH
- Plain-language explanations and recommended actions
- No misleading percentages for text-based scam checks
- Read-aloud output using browser speech synthesis
- Optional voice input for English text capture

## Architecture

- Frontend: static HTML, CSS, and JavaScript served by FastAPI
- API layer: FastAPI routes for analysis, auth, health, and status
- Core analysis:
  - Local heuristic detection for text and URL patterns
  - OpenAI Responses API for stronger LLM-assisted analysis when configured
  - OCR using RapidOCR for image text extraction
  - Audio deepfake detection using a public Hugging Face Gradio detector
  - AssemblyAI speaker diarization for first-speaker detection
- Auth: Supabase Auth proxy for sign-up and sign-in
- Storage: no app-managed database for analysis data; session cookies are used for auth

## Tools and technologies used

### Backend
- Python
- FastAPI
- Uvicorn
- Pydantic
- Pydantic Settings
- Python Multipart
- HTTPX

### Frontend
- HTML
- CSS
- JavaScript
- Browser SpeechRecognition API
- Browser SpeechSynthesis API

### Safety and analysis libraries
- Pillow (image validation)
- RapidOCR OnnxRuntime (OCR for screenshots)
- OpenAI Responses API (AI-backed scam analysis)
- Supabase Auth (sign-up and sign-in)
- AssemblyAI API (speaker diarization and first-speaker detection)
- Hugging Face Gradio audio detector (deepfake/synthetic voice assessment)

### Testing and quality
- Pytest
- Pytest Asyncio

### Deployment / hosting
- Render
- Python 3.12 runtime

## Project structure

```text
.
├── app/
│   ├── main.py
│   ├── config.py
│   ├── logging_config.py
│   ├── schemas.py
│   ├── security.py
│   └── services/
│       ├── ai_service.py
│       ├── analyzer.py
│       ├── audio_service.py
│       ├── auth_service.py
│       ├── image_service.py
│       └── url_analyzer.py
├── static/
│   ├── index.html
│   ├── signin.html
│   ├── app.js
│   ├── signin.js
│   └── style.css
├── tests/
│   ├── test_ai_safety.py
│   ├── test_app.py
│   └── test_audio.py
├── .env.example
├── .gitignore
├── .python-version
├── README.md
├── render.yaml
├── requirements.txt
└── .
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Then open:

- http://127.0.0.1:8000

## Environment variables

The app reads configuration from a project-root `.env` file when present.

```env
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4.1-mini
DEMO_MODE=true
ALLOWED_ORIGINS=
MAX_UPLOAD_MB=5
RATE_LIMIT_PER_MINUTE=10
SUPABASE_URL=
SUPABASE_ANON_KEY=
COOKIE_SECURE=false
MAX_AUDIO_MB=10
ASSEMBLYAI_API_KEY=
```

### Variable notes
- `DEMO_MODE=true` enables a low-setup flow without requiring an OpenAI key.
- `OPENAI_API_KEY` enables richer LLM-based analysis for text, image, and call descriptions.
- `SUPABASE_URL` and `SUPABASE_ANON_KEY` enable optional email/password auth.
- `ASSEMBLYAI_API_KEY` enables first-speaker analysis for call recordings.
- `ALLOWED_ORIGINS` can be set for CORS access in hosted environments.

## API endpoints

- `GET /health`
- `GET /api/status`
- `POST /api/analyze/text`
- `POST /api/analyze/call`
- `POST /api/analyze/url`
- `POST /api/analyze/image`
- `POST /api/analyze/audio`
- `POST /api/analyze/first-speaker`
- `POST /api/auth/signup`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`

## Security and privacy notes

- Uploads are validated by file type and headers before processing
- Image uploads must be JPG, PNG, or WEBP
- Audio uploads must be MP3, WAV, OGG, or M4A
- Request rate limiting is applied to analysis endpoints
- Security headers include CSP, X-Frame-Options, and content-type protections
- Uploaded files are not stored persistently in the app
- The app is meant to support safer decision-making and is not a replacement for official bank, government, or cybersecurity verification

## Deployment on Render

A Render blueprint is included in `render.yaml` and is configured to run the FastAPI app with the Python runtime.

```bash
git push
# Create a Render service from the repository or the included blueprint
```

The service expects environment variables to be provided in the Render dashboard, and the app health check endpoint is configured for `/health`.

## Testing

```bash
pytest
```

## Disclaimer

This project is a proof of concept designed for scam-awareness support. It provides risk estimates and guidance, not definitive proof of fraud or legitimacy.

Use it as a decision-support tool, and always verify urgent requests using an official app, saved number, or direct website you enter yourself.
