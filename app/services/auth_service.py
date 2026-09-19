"""Supabase Auth proxy. Passwords are never logged or persisted by this service."""
import logging
import httpx
from app.config import get_settings

logger = logging.getLogger("sahayak.auth")


def configured() -> bool:
    settings = get_settings()
    return bool(settings.supabase_url and settings.supabase_anon_key)


def headers() -> dict[str, str]:
    key = get_settings().supabase_anon_key
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


async def sign_up(email: str, password: str) -> dict:
    return await _post("/auth/v1/signup", {"email": email, "password": password})


async def sign_in(email: str, password: str) -> dict:
    return await _post("/auth/v1/token?grant_type=password", {"email": email, "password": password})


async def current_user(access_token: str) -> dict | None:
    settings = get_settings()
    if not configured() or not access_token:
        return None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(f"{settings.supabase_url.rstrip('/')}/auth/v1/user", headers={"apikey": settings.supabase_anon_key, "Authorization": f"Bearer {access_token}"})
            response.raise_for_status()
        return response.json()
    except httpx.HTTPError:
        return None


async def _post(path: str, data: dict) -> dict:
    settings = get_settings()
    if not configured():
        raise RuntimeError("Authentication is not configured.")
    try:
        async with httpx.AsyncClient(timeout=12) as client:
            response = await client.post(f"{settings.supabase_url.rstrip('/')}{path}", headers=headers(), json=data)
        if response.status_code >= 400:
            logger.warning("supabase_auth_failed endpoint=%s status=%s", path.split("?")[0], response.status_code)
            raise ValueError("We could not sign you in. Please check your email and password.")
        return response.json()
    except httpx.HTTPError as error:
        logger.warning("supabase_auth_unavailable error_type=%s", type(error).__name__)
        raise RuntimeError("Sign-in is temporarily unavailable. Please try again.")
