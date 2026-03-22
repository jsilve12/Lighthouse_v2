from datetime import UTC, datetime

from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from lighthouse_api.core.database import async_session
from lighthouse_api.core.security import decode_jwt_token, verify_api_key
from lighthouse_api.models.transformation import ApiKey

PUBLIC_PATHS = {"/api/v1/health", "/api/v1/health/ready", "/api/v1/auth/login", "/api/v1/auth/callback"}
PUBLIC_PREFIXES = ("/health",)

# TODO: Remove this flag once Google OAuth is configured (LIGHTHOUSE-7)
AUTH_DISABLED = True


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if AUTH_DISABLED:
            request.state.user_email = "anonymous"
            request.state.user_name = "Anonymous"
            request.state.auth_method = "none"
            return await call_next(request)

        path = request.url.path

        # Skip auth for public paths and non-API paths (frontend)
        if path in PUBLIC_PATHS or not path.startswith("/api/"):
            return await call_next(request)

        # Try API key auth first (Authorization: Bearer lh_...)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer lh_"):
            api_key = auth_header[7:]  # Remove "Bearer "
            user_email = await self._validate_api_key(api_key)
            if user_email:
                request.state.user_email = user_email
                request.state.auth_method = "api_key"
                return await call_next(request)
            return JSONResponse({"detail": "Invalid or expired API key"}, status_code=401)

        # Try JWT cookie
        token = request.cookies.get("lighthouse_session")
        if token:
            payload = decode_jwt_token(token)
            if payload:
                request.state.user_email = payload.get("email", "")
                request.state.user_name = payload.get("name", "")
                request.state.user_sub = payload.get("sub", "")
                request.state.auth_method = "oauth"
                return await call_next(request)

        return JSONResponse({"detail": "Authentication required"}, status_code=401)

    async def _validate_api_key(self, key: str) -> str | None:
        prefix = key[3:11] if len(key) > 11 else key[3:]  # Skip "lh_" prefix for the stored prefix
        async with async_session() as session:
            result = await session.execute(select(ApiKey).where(ApiKey.prefix == prefix, ApiKey.is_active.is_(True)))
            api_key_record = result.scalar_one_or_none()
            if api_key_record is None:
                return None

            if api_key_record.expires_at and api_key_record.expires_at < datetime.now(UTC):
                return None

            if not verify_api_key(key, api_key_record.key_hash):
                return None

            api_key_record.last_used_at = datetime.now(UTC)
            await session.commit()
            return api_key_record.created_by
