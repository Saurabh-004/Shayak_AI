import logging
import time
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.logging_config import configure_logging
from app.schemas import AuthRequest, TextRequest, UrlRequest
from app.security import apply_security_headers, limit_analysis
from app.services.ai_service import try_openai, try_openai_image
from app.services.analyzer import analyze_text
from app.services.audio_service import analyze_audio, validate_audio
from app.services.auth_service import configured as auth_configured, current_user, sign_in, sign_up
from app.services.image_service import validate_image
from app.services.url_analyzer import analyze_url

configure_logging()
logger = logging.getLogger("sahayak.api")
app = FastAPI(title="Sahayak Shield", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
origins = [item.strip() for item in get_settings().allowed_origins.split(",") if item.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])


@app.middleware("http")
async def security(request: Request, call_next):
    started = time.perf_counter()
    upload_limit_mb = get_settings().max_audio_mb if request.url.path == "/api/analyze/audio" else get_settings().max_upload_mb
    max_bytes = upload_limit_mb * 1024 * 1024 + 20_000
    if request.method in {"POST", "PUT"} and request.headers.get("content-length") and int(request.headers["content-length"]) > max_bytes:
        logger.warning("request_rejected route=%s reason=content_length_limit", request.url.path)
        response = JSONResponse({"success": False, "error": {"code": "TOO_LARGE", "message": "That upload is too large. Please use an image under 5 MB."}}, status_code=413)
        return apply_security_headers(response)
    response = await call_next(request)
    if request.url.path.startswith("/api/"):
        logger.info("request_complete route=%s method=%s status=%s duration_ms=%d", request.url.path, request.method, response.status_code, (time.perf_counter() - started) * 1000)
    return apply_security_headers(response)


@app.exception_handler(HTTPException)
async def known_error(_, exc):
    return JSONResponse({"success": False, "error": {"code": "REQUEST_ERROR", "message": str(exc.detail)}}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def invalid_input(_, __):
    return JSONResponse({"success": False, "error": {"code": "INVALID_INPUT", "message": "Please check the information you entered and try again."}}, status_code=422)


@app.exception_handler(Exception)
async def unexpected_error(_, __):
    logger.exception("unexpected_server_error")
    return JSONResponse({"success": False, "error": {"code": "SERVICE_UNAVAILABLE", "message": "We could not complete that safety check right now. Please try again."}}, status_code=500)


@app.get("/")
async def home():
    return FileResponse("static/index.html")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/status")
async def status():
    settings = get_settings()
    return {"demo_mode": settings.demo_mode, "image_analysis_available": not settings.demo_mode and bool(settings.openai_api_key), "authentication_available": auth_configured(), "audio_detection_available": bool(settings.audio_detector_url)}


def session_response(data: dict, message: str) -> JSONResponse:
    token = data.get("access_token")
    if not token:
        return JSONResponse({"success": True, "authenticated": False, "message": message})
    response = JSONResponse({"success": True, "authenticated": True, "message": message})
    response.set_cookie("sahayak_session", token, httponly=True, secure=get_settings().cookie_secure, samesite="lax", max_age=3600)
    return response


@app.post("/api/auth/signup")
async def signup(body: AuthRequest):
    try:
        data = await sign_up(body.email.strip().lower(), body.password)
        logger.info("auth_signup_complete")
        return session_response(data, "Account created. Check your email if verification is enabled.")
    except (RuntimeError, ValueError) as error:
        raise HTTPException(400, str(error))


@app.post("/api/auth/login")
async def login(body: AuthRequest):
    try:
        data = await sign_in(body.email.strip().lower(), body.password)
        logger.info("auth_login_complete")
        return session_response(data, "You are signed in.")
    except (RuntimeError, ValueError) as error:
        raise HTTPException(401, str(error))


@app.post("/api/auth/logout")
async def logout():
    response = JSONResponse({"success": True, "message": "You are signed out."})
    response.delete_cookie("sahayak_session")
    return response


@app.get("/api/auth/me")
async def me(request: Request):
    user = await current_user(request.cookies.get("sahayak_session", ""))
    if not user:
        raise HTTPException(401, "Please sign in to continue.")
    return {"success": True, "user": {"email": user.get("email", "")}}


def payload(analysis):
    return {"success": True, "demo_mode": get_settings().demo_mode, "analysis": analysis.model_dump()}


@app.post("/api/analyze/text")
async def text_check(body: TextRequest, request: Request):
    await limit_analysis(request)
    if not body.text.strip():
        raise HTTPException(400, "Please provide a message to check.")
    logger.info("analysis_started type=text chars=%d demo_mode=%s", len(body.text), get_settings().demo_mode)
    return payload(await try_openai(body.text) or analyze_text(body.text))


@app.post("/api/analyze/call")
async def call_check(body: TextRequest, request: Request):
    await limit_analysis(request)
    if not body.text.strip():
        raise HTTPException(400, "Please describe what the caller said.")
    logger.info("analysis_started type=call chars=%d demo_mode=%s", len(body.text), get_settings().demo_mode)
    return payload(await try_openai(body.text) or analyze_text(body.text, "call description"))


@app.post("/api/analyze/url")
async def url_check(body: UrlRequest, request: Request):
    await limit_analysis(request)
    logger.info("analysis_started type=url chars=%d", len(body.url))
    try:
        return payload(analyze_url(body.url))
    except ValueError as error:
        raise HTTPException(400, str(error))


@app.post("/api/analyze/image")
async def image_check(request: Request, image: UploadFile = File(...)):
    await limit_analysis(request, "image")
    data = await image.read()
    if not data:
        raise HTTPException(400, "Please choose an image to check.")
    if len(data) > get_settings().max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "That image is too large. Please use an image under 5 MB.")
    try:
        note = validate_image(data, image.content_type or "")
    except ValueError as error:
        raise HTTPException(400, str(error))
    logger.info("image_validated bytes=%d mime_type=%s demo_mode=%s", len(data), image.content_type or "unknown", get_settings().demo_mode)
    image_analysis = await try_openai_image(data, image.content_type or "image/jpeg")
    if image_analysis:
        logger.info("image_analysis_complete outcome=openai risk_level=%s category=%s", image_analysis.risk_level, image_analysis.category)
        return payload(image_analysis)
    logger.info("image_analysis_complete outcome=fallback reason=demo_mode_or_ai_unavailable")
    return {"success": True, "demo_mode": get_settings().demo_mode, "message": note}


@app.post("/api/analyze/audio")
async def audio_check(request: Request, audio: UploadFile = File(...)):
    await limit_analysis(request, "audio")
    if not await current_user(request.cookies.get("sahayak_session", "")):
        raise HTTPException(401, "Please sign in before checking an audio recording.")
    data = await audio.read()
    settings = get_settings()
    if not data:
        raise HTTPException(400, "Please choose an audio recording to check.")
    if len(data) > settings.max_audio_mb * 1024 * 1024:
        raise HTTPException(413, "That audio file is too large. Please use a recording under 10 MB.")
    try:
        validate_audio(data, audio.content_type or "")
        logger.info("audio_validated bytes=%d mime_type=%s", len(data), audio.content_type or "unknown")
        result = await analyze_audio(data, audio.content_type or "audio/mpeg")
        logger.info("audio_analysis_complete risk_level=%s", result["risk_level"])
        return {"success": True, "analysis": result}
    except (ValueError, RuntimeError) as error:
        raise HTTPException(503 if isinstance(error, RuntimeError) else 400, str(error))
