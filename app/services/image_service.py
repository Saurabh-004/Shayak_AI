import logging
from io import BytesIO
from PIL import Image, UnidentifiedImageError

logger = logging.getLogger("sahayak.image")
ALLOWED_MAGIC = {b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"RIFF"}
IMAGE_HELP_MESSAGE = (
    "We could not read text from this screenshot automatically. "
    "Please paste the message shown in the image using the text box below, then check again."
)


def validate_image(data: bytes, content_type: str) -> None:
    if content_type not in {"image/jpeg", "image/png", "image/webp"} or not any(data.startswith(x) for x in ALLOWED_MAGIC):
        raise ValueError("Please upload a JPG, PNG, or WEBP image only.")
    try:
        image = Image.open(BytesIO(data))
        image.verify()
    except (UnidentifiedImageError, OSError, SyntaxError):
        raise ValueError("This image file could not be safely read.")


def extract_text_from_image(data: bytes) -> str:
    try:
        from rapidocr_onnxruntime import RapidOCR

        result, _ = RapidOCR()(data)
        if not result:
            return ""
        text = " ".join(str(line[1]).strip() for line in result if len(line) > 1 and str(line[1]).strip())
        logger.info("image_ocr_complete chars=%d", len(text))
        return text.strip()
    except Exception as error:
        logger.warning("image_ocr_failed error_type=%s", type(error).__name__)
        return ""
