# Import every model so any consumer of the package (API app, Celery
# worker) gets the full SQLAlchemy registry — a partial import breaks
# foreign-key resolution (e.g. documents.owner_id -> users.id).
from app.models.chunk import DocumentChunk  # noqa: F401
from app.models.document import Document  # noqa: F401
from app.models.user import User  # noqa: F401
