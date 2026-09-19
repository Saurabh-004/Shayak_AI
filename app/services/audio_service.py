"""External audio deepfake-risk integration; no audio is stored locally."""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger("sahayak.audio")
ALLOWED_AUDIO = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/ogg", "audio/mp4", "audio/x-m4a"}


def validate_audio(data: bytes, mime_type: str) -> None:
    magic = (b"ID3", b"\xff\xfb", b"\xff\xf3", b"RIFF", b"OggS", b"ftyp")
    if mime_type not in ALLOWED_AUDIO or not any(data.startswith(value) or value == b"ftyp" and data[4:8] == value for value in magic):
        raise ValueError("Please upload an MP3, WAV, OGG, or M4A audio recording.")


async def analyze_audio(data: bytes, mime_type: str) -> dict:
    settings = get_settings()
    if not settings.audio_detector_url:
        raise RuntimeError("Audio risk detection is not configured yet.")
    headers = {"Content-Type": mime_type}
    if settings.audio_detector_token:
        headers["Authorization"] = f"Bearer {settings.audio_detector_token}"
    try:
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(settings.audio_detector_url, headers=headers, content=data)
            response.raise_for_status()
        payload = response.json()
    except httpx.HTTPStatusError as error:
        logger.warning("audio_detector_failed status=%s", error.response.status_code)
        raise RuntimeError("The audio safety check is unavailable. Please try again later.")
    except (httpx.HTTPError, ValueError) as error:
        logger.warning("audio_detector_failed error_type=%s", type(error).__name__)
        raise RuntimeError("The audio safety check is unavailable. Please try again later.")
    labels = payload if isinstance(payload, list) else payload.get("labels", [])
    if not isinstance(labels, list) or not labels:
        logger.warning("audio_detector_failed error_type=unexpected_response")
        raise RuntimeError("The audio safety service returned an unexpected result.")
    synthetic = max((item for item in labels if any(word in str(item.get("label", "")).lower() for word in ("fake", "deepfake", "synthetic"))), key=lambda item: item.get("score", 0), default=None)
    score = float(synthetic.get("score", 0)) if synthetic else 0
    return {"risk_level": "HIGH" if score >= .75 else "MEDIUM" if score >= .45 else "LOW", "score": round(score * 100), "summary": "Possible synthetic-voice signals were detected." if score >= .45 else "No strong synthetic-voice signals were detected.", "disclaimer": "This is a risk estimate, not proof that a recording is real or AI-generated."}
