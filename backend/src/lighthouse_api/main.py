from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from lighthouse_api.api.router import api_router
from lighthouse_api.core.config import settings
from lighthouse_api.core.logging import logger, setup_logging
from lighthouse_api.middleware.audit_logger import AuditLoggerMiddleware
from lighthouse_api.middleware.auth import AuthMiddleware
from lighthouse_api.middleware.rate_limiter import limiter
from lighthouse_api.middleware.request_id import RequestIDMiddleware
from lighthouse_api.middleware.security_headers import SecurityHeadersMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Lighthouse API starting", environment=settings.environment)
    yield
    logger.info("Lighthouse API shutting down")


app = FastAPI(
    title="Lighthouse API",
    description="Data Transformation Platform",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/v1/docs" if settings.environment == "development" else None,
    redoc_url=None,
)

# Rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Middleware stack (order matters - outermost first)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(AuditLoggerMiddleware)
app.add_middleware(AuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins.split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Routes
app.include_router(api_router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error("Unhandled exception", request_id=request_id, error=str(exc))
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id,
        },
    )
