from fastapi import FastAPI

from app.api.routes import auth, documents
from app.db.session import Base, engine
from app.models import document, user  # noqa: F401 — register models with Base

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OmniOps AI", version="0.1.0")

app.include_router(auth.router)
app.include_router(documents.router)


@app.get("/health")
def health():
    return {"status": "ok"}
