import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import auth, documents
from app.core.config import settings
from app.db.session import Base, engine
from app.models import chunk, document, user  # noqa: F401 — register models with Base
from app.services import search

logger = logging.getLogger(__name__)

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        search.ensure_index()
    except Exception as exc:  # ES may be unavailable at boot; don't crash the app
        logger.warning("Could not ensure Elasticsearch index: %s", exc)
    yield


app = FastAPI(title="OmniOps AI", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)


@app.get("/health")
def health():
    return {"status": "ok"}
