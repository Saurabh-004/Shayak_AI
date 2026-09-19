# Sahayak Shield

**Pause. Understand. Stay Safe.** A senior-first scam protection proof of concept. It accepts pasted messages, call descriptions, website addresses, and image uploads, then explains warning signs in plain language.

## Features

- Large, high-contrast, responsive interface with keyboard focus and browser voice input/read-aloud.
- Three clear risk levels: LOW, MEDIUM, HIGH; no misleading percentages.
- Lightweight local scam heuristics and URL static analysis. No website is opened.
- Upload validation (JPG/PNG/WEBP only, magic bytes, size cap), in-memory rate limiting, CSP/security headers, privacy-safe behavior.
- `DEMO_MODE=true` works with no API key. The current image flow validates safely and asks for pasted text when no configured multimodal provider is available.

## Architecture

Browser → FastAPI → local heuristic/URL analyzer or optional server-side Gemini enrichment (including validated screenshots). No database, workers, persistent uploads, or local ML models. Set `DEMO_MODE=false` plus `GEMINI_API_KEY` to enable Gemini; invalid/failed AI output safely falls back to local guidance. No secret is sent to the browser.

## Run locally

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload
pytest
```

Open `http://127.0.0.1:8000`. API endpoints: `GET /health`, `POST /api/analyze/text`, `/url`, `/call`, and `/image`.

## Environment

`GEMINI_API_KEY`, `DEMO_MODE`, `ALLOWED_ORIGINS`, `MAX_UPLOAD_MB`, and `RATE_LIMIT_PER_MINUTE`. `.env` is ignored by Git.

## Deploy on Render

Push this repository and create a Render Blueprint from `render.yaml`, then set secrets in the Render dashboard. It binds to `0.0.0.0:$PORT` and has `/health` configured.

## Limitations

This is a proof of concept, and not a replacement for official bank, government, cybersecurity, or law-enforcement verification. Local detection is intentionally cautious and cannot prove that a message or site is genuine.
# Shayak_AI
