"""External audio safety: AssemblyAI diarization and a public HF detector."""
import asyncio
import json
import logging
import re
import httpx
from app.config import get_settings

logger = logging.getLogger("sahayak.audio")
SPACE_URL = "https://sara1708-deepfake-audio-detector.hf.space"
ALLOWED_AUDIO = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/ogg", "audio/mp4", "audio/x-m4a"}


def validate_audio(data: bytes, mime_type: str) -> None:
    magic = (b"ID3", b"\xff\xfb", b"\xff\xf3", b"RIFF", b"OggS")
    m4a = len(data) >= 8 and data[4:8] == b"ftyp"
    if mime_type not in ALLOWED_AUDIO or not (any(data.startswith(value) for value in magic) or m4a):
        raise ValueError("Please upload an MP3, WAV, OGG, or M4A audio recording.")


async def analyze_audio(data: bytes, mime_type: str, filename: str = "recording.wav") -> dict:
    try:
        async with httpx.AsyncClient(timeout=75) as client:
            upload = await client.post(f"{SPACE_URL}/gradio_api/upload", files={"files": (filename, data, mime_type)})
            upload.raise_for_status()
            paths = upload.json()
            if not isinstance(paths, list) or not paths:
                raise ValueError("unexpected_upload_response")
            file_data = {"path": paths[0], "orig_name": filename, "mime_type": mime_type, "meta": {"_type": "gradio.FileData"}}
            started = await client.post(f"{SPACE_URL}/gradio_api/call/predict_audio_router", json={"data": [file_data, None]})
            started.raise_for_status()
            event_id = started.json().get("event_id")
            if not event_id:
                raise ValueError("missing_event_id")
            values = await _read_result(client, event_id)
        return _format_result(values)
    except httpx.HTTPStatusError as error:
        logger.warning("audio_detector_failed status=%s", error.response.status_code)
        raise RuntimeError("The audio safety demo is busy or unavailable. Please try again shortly.")
    except (httpx.HTTPError, ValueError, KeyError, json.JSONDecodeError) as error:
        logger.warning("audio_detector_failed error_type=%s", type(error).__name__)
        raise RuntimeError("The audio safety demo is unavailable. Please try again shortly.")


async def _read_result(client: httpx.AsyncClient, event_id: str) -> list:
    async with client.stream("GET", f"{SPACE_URL}/gradio_api/call/predict_audio_router/{event_id}", timeout=75) as response:
        response.raise_for_status()
        async for line in response.aiter_lines():
            if line.startswith("data:"):
                payload = json.loads(line[5:].strip())
                if isinstance(payload, list):
                    return payload
                if isinstance(payload, dict) and "data" in payload:
                    return payload["data"]
    raise ValueError("detector_completed_without_result")


def _format_result(values: list) -> dict:
    html = str(values[0]) if values else ""
    details = values[3] if len(values) > 3 and isinstance(values[3], dict) else {}
    probability = details.get("spoof_probability") or details.get("spoof_pct")
    if probability is None:
        match = re.search(r"(?:spoof|synthetic)[^0-9]{0,80}(\d{1,3}(?:\.\d+)?)%", html, re.I)
        probability = float(match.group(1)) / 100 if match else (0.8 if "likely synthetic" in html.lower() else 0.2)
    score = max(0, min(100, round(float(probability) * 100)))
    return {"risk_level": "HIGH" if score >= 75 else "MEDIUM" if score >= 45 else "LOW", "score": score, "summary": "Possible synthetic-voice signals were detected." if score >= 45 else "No strong synthetic-voice signals were detected.", "disclaimer": "This is a research-demo risk estimate, not proof that a recording is real or AI-generated."}


async def first_speaker_turn(data: bytes) -> dict:
    key = get_settings().assemblyai_api_key
    if not key:
        raise RuntimeError("First-speaker analysis is not configured yet.")
    headers = {"Authorization": key}
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            uploaded = await client.post("https://api.assemblyai.com/v2/upload", headers=headers, content=data)
            uploaded.raise_for_status()
            created = await client.post("https://api.assemblyai.com/v2/transcript", headers=headers, json={"audio_url": uploaded.json()["upload_url"], "speaker_labels": True, "language_detection": True})
            created.raise_for_status()
            transcript_id = created.json()["id"]
            for _ in range(40):
                await asyncio.sleep(2)
                status = await client.get(f"https://api.assemblyai.com/v2/transcript/{transcript_id}", headers=headers)
                status.raise_for_status()
                result = status.json()
                if result.get("status") == "completed":
                    turns = result.get("utterances") or []
                    if not turns:
                        raise ValueError("no_speaker_turns")
                    first = turns[0]
                    return {"speaker": first.get("speaker", "A"), "start_ms": int(first["start"]), "end_ms": int(first["end"]), "transcript": first.get("text", "")[:300]}
                if result.get("status") == "error":
                    raise ValueError("diarization_error")
    except httpx.HTTPStatusError as error:
        logger.warning("diarization_failed status=%s", error.response.status_code)
        raise RuntimeError("Speaker separation is temporarily unavailable.")
    except (httpx.HTTPError, KeyError, ValueError) as error:
        logger.warning("diarization_failed error_type=%s", type(error).__name__)
        raise RuntimeError("Speaker separation could not complete for this recording.")
    raise RuntimeError("Speaker separation is taking too long. Please try a shorter recording.")
