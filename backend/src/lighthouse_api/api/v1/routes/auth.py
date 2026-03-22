from datetime import UTC, datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lighthouse_api.api.deps import get_current_user
from lighthouse_api.core.config import settings
from lighthouse_api.core.database import get_db
from lighthouse_api.core.security import create_jwt_token, generate_api_key, hash_api_key
from lighthouse_api.models.transformation import ApiKey
from lighthouse_api.schemas.transformation import ApiKeyCreate, ApiKeyCreateResponse, ApiKeyResponse

router = APIRouter(prefix="/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/login")
async def login() -> Response:
    redirect_uri = f"{settings.base_url}/api/v1/auth/callback"
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return Response(
        status_code=302,
        headers={"Location": f"{GOOGLE_AUTH_URL}?{query}"},
    )


@router.get("/callback")
async def callback(code: str, request: Request) -> Response:
    redirect_uri = f"{settings.base_url}/api/v1/auth/callback"

    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            },
        )
        token_data = token_response.json()

        if "error" in token_data:
            return Response(status_code=400, content="Authentication failed")

        userinfo_response = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo = userinfo_response.json()

    jwt_token = create_jwt_token(
        {
            "sub": userinfo.get("id", ""),
            "email": userinfo.get("email", ""),
            "name": userinfo.get("name", ""),
        }
    )

    response = Response(
        status_code=302,
        headers={"Location": "/"},
    )
    response.set_cookie(
        key="lighthouse_session",
        value=jwt_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=settings.jwt_expiration_hours * 3600,
        path="/",
    )
    return response


@router.get("/me")
async def me(user: dict = Depends(get_current_user)) -> dict:
    return {"email": user["email"], "name": user["name"]}


@router.post("/logout")
async def logout() -> Response:
    response = Response(status_code=200, content='{"status": "logged out"}')
    response.delete_cookie("lighthouse_session", path="/")
    return response


@router.post("/api-keys", response_model=ApiKeyCreateResponse)
async def create_api_key(
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    raw_key = generate_api_key()
    prefix = raw_key[3:11]  # First 8 chars after "lh_"
    hashed = hash_api_key(raw_key)

    expires_at = None
    if body.expires_in_days:
        expires_at = datetime.now(UTC) + timedelta(days=body.expires_in_days)

    api_key = ApiKey(
        name=body.name,
        key_hash=hashed,
        prefix=prefix,
        created_by=user["email"],
        expires_at=expires_at,
    )
    db.add(api_key)
    await db.flush()

    return {
        **{c.name: getattr(api_key, c.name) for c in api_key.__table__.columns},
        "key": raw_key,
    }


@router.get("/api-keys", response_model=list[ApiKeyResponse])
async def list_api_keys(
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> list:
    result = await db.execute(select(ApiKey).where(ApiKey.created_by == user["email"]).order_by(ApiKey.created_at.desc()))
    return list(result.scalars().all())


@router.delete("/api-keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    db: AsyncSession = Depends(get_db),
    user: dict = Depends(get_current_user),
) -> dict:
    import uuid

    result = await db.execute(select(ApiKey).where(ApiKey.id == uuid.UUID(key_id), ApiKey.created_by == user["email"]))
    api_key = result.scalar_one_or_none()
    if not api_key:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="API key not found")
    api_key.is_active = False
    return {"status": "revoked"}
