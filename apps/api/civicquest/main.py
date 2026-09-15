import json
import logging
import time
import uuid
from contextlib import asynccontextmanager

import redis
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from starlette.exceptions import HTTPException

from .catch_routes import router as catches
from .community_routes import router as community
from .config import settings
from .db import engine

log = logging.getLogger("civicquest.api")


@asynccontextmanager
async def lifespan(app):
    settings()
    yield


app = FastAPI(title="CivicQuest API", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def guard(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    started = time.monotonic()
    cfg = settings()
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        origin = request.headers.get("origin")
        if origin and origin != cfg.origin:
            return JSONResponse(
                {
                    "error": {
                        "code": "ORIGIN_REJECTED",
                        "message": "Request origin is not allowed",
                        "request_id": request.state.request_id,
                    }
                },
                403,
            )
        if (
            request.headers.get("content-length", "0").isdigit()
            and int(request.headers.get("content-length", "0")) > cfg.max_upload_bytes
        ):
            return JSONResponse(
                {
                    "error": {
                        "code": "TOO_LARGE",
                        "message": "Request too large",
                        "request_id": request.state.request_id,
                    }
                },
                413,
            )
        if request.url.path.startswith("/api/"):
            try:
                from .common import digest

                client = redis.Redis.from_url(cfg.redis_url, socket_connect_timeout=1, socket_timeout=1)
                identity = digest(
                    (
                        request.cookies.get("cq_session")
                        or (request.client.host if request.client else "unknown")
                    )
                )
                bucket = "cq:limit:" + identity + ":" + str(int(time.time()) // 60)
                pipe = client.pipeline()
                pipe.incr(bucket)
                pipe.expire(bucket, 120)
                n = pipe.execute()[0]
                if n > 60:
                    return JSONResponse(
                        {
                            "error": {
                                "code": "RATE_LIMITED",
                                "message": "Please wait a minute",
                                "request_id": request.state.request_id,
                            }
                        },
                        429,
                        headers={"Retry-After": "60"},
                    )
            except redis.RedisError:
                if cfg.env not in {"local", "test"}:
                    return JSONResponse(
                        {
                            "error": {
                                "code": "SERVICE_UNAVAILABLE",
                                "message": "Try again shortly",
                                "request_id": request.state.request_id,
                            }
                        },
                        503,
                    )
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Frame-Options"] = "DENY"
    if cfg.env not in {"local", "test"}:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    log.info(
        json.dumps(
            {
                "request_id": request.state.request_id,
                "route": request.url.path,
                "status": response.status_code,
                "latency_ms": round((time.monotonic() - started) * 1000, 1),
            }
        )
    )
    return response


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    detail = (
        exc.detail if isinstance(exc.detail, dict) else {"code": "REQUEST_FAILED", "message": str(exc.detail)}
    )
    return JSONResponse(
        {"error": {**detail, "request_id": getattr(request.state, "request_id", "")}},
        status_code=exc.status_code,
    )


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return JSONResponse(
        {
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "Check the submitted fields",
                "fields": [
                    {"path": ".".join(str(i) for i in e["loc"]), "message": e["msg"]} for e in exc.errors()
                ],
                "request_id": getattr(request.state, "request_id", ""),
            }
        },
        status_code=422,
    )


@app.exception_handler(IntegrityError)
async def constraint_error(request, exc):
    return JSONResponse(
        {
            "error": {
                "code": "CONFLICT",
                "message": "This operation conflicts with an existing record",
                "request_id": getattr(request.state, "request_id", ""),
            }
        },
        status_code=409,
    )


@app.exception_handler(Exception)
async def unexpected_error(request, exc):
    log.error(
        json.dumps({"request_id": getattr(request.state, "request_id", ""), "error_type": type(exc).__name__})
    )
    return JSONResponse(
        {
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Something went wrong. Please try again.",
                "request_id": getattr(request.state, "request_id", ""),
            }
        },
        status_code=500,
    )


@app.get("/health/live")
def live():
    return {"status": "ok"}


@app.get("/health/ready")
def ready():
    with engine.connect() as db:
        version = db.scalar(text("SELECT PostGIS_Version()"))
    return {"status": "ok", "postgis": version}


from .action_routes import router as actions  # noqa: E402
from .operations import router as operations  # noqa: E402
from .routes import router  # noqa: E402
from .sharing import router as sharing  # noqa: E402
from .trust_routes import router as trust  # noqa: E402
from .ward_goals import router as ward_goals  # noqa: E402

app.include_router(router)
app.include_router(actions)
app.include_router(trust)
app.include_router(sharing)
app.include_router(operations)
app.include_router(ward_goals)
app.include_router(community)
app.include_router(catches)
