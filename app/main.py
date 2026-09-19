from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.schemas import TextRequest, UrlRequest
from app.security import apply_security_headers, limit_analysis
from app.services.analyzer import analyze_text
from app.services.ai_service import try_gemini, try_gemini_image
from app.services.image_service import validate_image
from app.services.url_analyzer import analyze_url

app = FastAPI(title="Sahayak Shield", docs_url=None, redoc_url=None)
app.mount("/static", StaticFiles(directory="static"), name="static")
origins = [o.strip() for o in get_settings().allowed_origins.split(",") if o.strip()]
if origins:
    app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])

@app.middleware("http")
async def security(request: Request, call_next):
    if request.method in {"POST", "PUT"} and request.headers.get("content-length") and int(request.headers["content-length"]) > get_settings().max_upload_mb * 1024 * 1024 + 20000:
        return apply_security_headers(JSONResponse({"success":False,"error":{"code":"TOO_LARGE","message":"That upload is too large. Please use an image under 5 MB."}}, status_code=413))
    response = await call_next(request)
    return apply_security_headers(response)

@app.exception_handler(HTTPException)
async def known_error(_, exc):
    return JSONResponse({"success":False,"error":{"code":"REQUEST_ERROR","message":str(exc.detail)}}, status_code=exc.status_code)

@app.get("/")
async def home(): return FileResponse("static/index.html")

@app.get("/health")
async def health(): return {"status":"ok"}

def payload(analysis): return {"success": True, "demo_mode": get_settings().demo_mode, "analysis": analysis.model_dump()}

@app.post("/api/analyze/text")
async def text_check(body: TextRequest, request: Request):
    await limit_analysis(request)
    if not body.text.strip(): raise HTTPException(400, "Please provide a message to check.")
    return payload(await try_gemini(body.text) or analyze_text(body.text))

@app.post("/api/analyze/call")
async def call_check(body: TextRequest, request: Request):
    await limit_analysis(request)
    if not body.text.strip(): raise HTTPException(400, "Please describe what the caller said.")
    return payload(await try_gemini(body.text) or analyze_text(body.text, "call description"))

@app.post("/api/analyze/url")
async def url_check(body: UrlRequest, request: Request):
    await limit_analysis(request)
    try: return payload(analyze_url(body.url))
    except ValueError as error: raise HTTPException(400, str(error))

@app.post("/api/analyze/image")
async def image_check(request: Request, image: UploadFile = File(...)):
    await limit_analysis(request, "image")
    data = await image.read()
    if not data: raise HTTPException(400, "Please choose an image to check.")
    if len(data) > get_settings().max_upload_mb * 1024 * 1024: raise HTTPException(413, "That image is too large. Please use an image under 5 MB.")
    try: note = validate_image(data, image.content_type or "")
    except ValueError as error: raise HTTPException(400, str(error))
    image_analysis = await try_gemini_image(data, image.content_type or "image/jpeg")
    if image_analysis:
        return payload(image_analysis)
    return {"success":True,"demo_mode":get_settings().demo_mode,"message":note}
