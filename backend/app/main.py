import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.routes import agent, auth, connectors, documents
from app.core.config import settings
from app.core.ratelimit import limiter
from app.db.session import Base, engine
from app.models import chunk, document, user  # noqa: F401 — register models with Base
from app.services import search

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.jwt_secret_key == "change-me-in-production" or len(settings.jwt_secret_key) < 32:  # nosec B105 — detects the weak default, is not a credential
        logger.warning(
            "JWT_SECRET_KEY is weak (default or under 32 bytes) — tokens are forgeable. "
            'Generate one: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    try:
        search.ensure_index()
    except Exception as exc:  # ES may be unavailable at boot; don't crash the app
        logger.warning("Could not ensure Elasticsearch index: %s", exc)
    yield


app = FastAPI(title="OmniOps AI", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(agent.router)
app.include_router(connectors.router)


@app.get("/health")
def health():
    return {"status": "ok"}
