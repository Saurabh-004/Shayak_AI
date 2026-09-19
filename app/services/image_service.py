from io import BytesIO
from PIL import Image, UnidentifiedImageError

ALLOWED_MAGIC = {b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF"}


def validate_image(data: bytes, content_type: str) -> str:
    if content_type not in {"image/jpeg", "image/png", "image/webp"} or not any(data.startswith(x) for x in ALLOWED_MAGIC):
        raise ValueError("Please upload a JPG, PNG, or WEBP image only.")
    try:
        image = Image.open(BytesIO(data)); image.verify()
    except (UnidentifiedImageError, OSError):
        raise ValueError("This image file could not be safely read.")
    return "Image received safely. Text reading requires an optional AI provider and is unavailable in this local demo. Please paste the visible message text for a full check."
