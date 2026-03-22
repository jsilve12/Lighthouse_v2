import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from lighthouse_api.core.database import async_session
from lighthouse_api.models.audit import AuditLog

logger = structlog.get_logger()

MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
SKIP_PATHS = {"/api/v1/health", "/api/v1/health/ready", "/api/v1/auth/login", "/api/v1/auth/callback"}


class AuditLoggerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)

        if request.method in MUTATING_METHODS and request.url.path not in SKIP_PATHS:
            try:
                await self._log_action(request, response)
            except Exception:
                logger.warning("Failed to write audit log", path=request.url.path)

        return response

    async def _log_action(self, request: Request, response: Response) -> None:
        actor = getattr(request.state, "user_email", None)
        request_id_str = getattr(request.state, "request_id", None)
        ip = request.client.host if request.client else None

        path = request.url.path
        method = request.method

        action = "create" if method == "POST" else "update" if method in ("PUT", "PATCH") else "delete"
        if "trigger" in path:
            action = "pipeline_trigger"

        parts = path.strip("/").split("/")
        resource_type = "unknown"
        resource_id = None
        for i, part in enumerate(parts):
            if part in ("datasets", "folders", "schemas", "scripts", "pipelines", "alarm-rules", "alarm-events", "api-keys"):
                resource_type = part.replace("-", "_")
                if i + 1 < len(parts):
                    try:
                        resource_id = uuid.UUID(parts[i + 1])
                    except (ValueError, IndexError):
                        pass
                break

        if resource_id is None:
            resource_id = uuid.UUID(int=0)

        async with async_session() as session:
            log = AuditLog(
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                actor=actor,
                ip_address=ip,
                request_id=uuid.UUID(request_id_str) if request_id_str else None,
            )
            session.add(log)
            await session.commit()
