import pytest
from app.services.audio_service import validate_audio


def test_wav_audio_is_accepted():
    validate_audio(b"RIFF" + b"\x00" * 20, "audio/wav")


def test_unknown_audio_is_rejected():
    with pytest.raises(ValueError):
        validate_audio(b"<script>", "audio/wav")
