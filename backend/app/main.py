import os
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger, request_id_ctx
from app.core.exceptions import BaseAppException
from app.core.exceptions import RateLimitExceededError
from app.core.guardrails import rate_limiter
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.PROJECT_NAME} (v{settings.VERSION})...")
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    yield
    logger.info("Shutting down application...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_tracing_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    token = request_id_ctx.set(request_id)
    started_at = time.perf_counter()

    try:
        response = await call_next(request)
    finally:
        duration_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info(
            "Completed HTTP request",
            extra={
                "extra_fields": {
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration_ms,
                    "status_code": getattr(locals().get("response"), "status_code", 500),
                }
            },
        )
        request_id_ctx.reset(token)

    response.headers["X-Request-ID"] = request_id
    return response


@app.middleware("http")
async def abuse_guardrail_middleware(request: Request, call_next):
    if request.method == "POST" and request.url.path.startswith(f"{settings.API_V1_STR}/invoices"):
        client_key = request.client.host if request.client else "unknown"
        scope = "processing" if any(
            request.url.path.endswith(suffix)
            for suffix in ("/process", "/extract", "/retry")
        ) else "upload"
        limit = (
            settings.RATE_LIMITED_PROCESSING_REQUESTS
            if scope == "processing"
            else settings.RATE_LIMIT_MAX_REQUESTS
        )
        try:
            rate_limiter.check(client_key, scope, limit)
        except RateLimitExceededError as exc:
            response = JSONResponse(
                status_code=exc.status_code,
                content={
                    "error_code": exc.error_code,
                    "message": exc.detail,
                    "extra": exc.extra,
                    "request_id": getattr(request.state, "request_id", None),
                },
                headers={"Retry-After": str(exc.extra["retry_after_seconds"])},
            )
            return response
    return await call_next(request)


@app.exception_handler(BaseAppException)
async def custom_app_exception_handler(request: Request, exc: BaseAppException):
    logger.warning(f"Application Exception [{exc.error_code}]: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "message": exc.detail,
            "extra": exc.extra,
            "request_id": request.state.request_id,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled Server Error: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "An unexpected error occurred on the server.",
            "request_id": request.state.request_id,
        },
    )


# Include API v1 routes
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root_redirect():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
