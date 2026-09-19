# Sahayak Shield

**Pause. Understand. Stay Safe.** A senior-first scam protection proof of concept. It accepts pasted messages, call descriptions, website addresses, and image uploads, then explains warning signs in plain language.

## Features

- Large, high-contrast, responsive interface with keyboard focus and browser voice input/read-aloud.
- Three clear risk levels: LOW, MEDIUM, HIGH; no misleading percentages.
- Lightweight local scam heuristics and URL static analysis. No website is opened.
- Upload validation (JPG/PNG/WEBP only, magic bytes, size cap), in-memory rate limiting, CSP/security headers, privacy-safe behavior.
- `DEMO_MODE=true` works with no API key. The current image flow validates safely and asks for pasted text when no configured multimodal provider is available.
- Persistent account signup and login through Supabase Auth. Password hashing is handled by Supabase; this app never stores plaintext passwords.
- Authenticated call-recording safety checks via an optional external audio deepfake-risk detector. Results are estimates, never proof.

## Architecture

Browser → FastAPI → local heuristic/URL analyzer or optional server-side OpenAI analysis (including validated screenshots). No database, workers, persistent uploads, or local ML models. Set `DEMO_MODE=false` plus `OPENAI_API_KEY` to enable OpenAI analysis; invalid/failed AI output safely falls back to local guidance. No secret is sent to the browser.

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

`OPENAI_API_KEY`, `OPENAI_MODEL`, `DEMO_MODE`, `ALLOWED_ORIGINS`, `MAX_UPLOAD_MB`, `RATE_LIMIT_PER_MINUTE`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `COOKIE_SECURE`, `ASSEMBLYAI_API_KEY`, and `MAX_AUDIO_MB`. `.env` is ignored by Git.

For local development, copy `.env.example` to the project-root `.env` file. On Render, configure the same names in the service Environment page; Render variables override local-file values.

## Authentication and audio setup

Create a Supabase project, enable Email/Password authentication, and add its project URL and publishable/anon key as `SUPABASE_URL` and `SUPABASE_ANON_KEY`. Set `COOKIE_SECURE=true` on Render and `false` locally. Supabase Auth manages persistent users and password hashing.

Set `ASSEMBLYAI_API_KEY` to enable the First Speaker Call Check. It uses AssemblyAI diarization to identify the first real speaker turn, trims that range in the browser, and then submits only the segment to the public Hugging Face audio detector. The app does not persist recordings.

## Deploy on Render

Push this repository and create a Render Blueprint from `render.yaml`, then set secrets in the Render dashboard. It binds to `0.0.0.0:$PORT` and has `/health` configured.

## Limitations

This is a proof of concept, and not a replacement for official bank, government, cybersecurity, or law-enforcement verification. Local detection is intentionally cautious and cannot prove that a message or site is genuine.
# Shayak_AI
