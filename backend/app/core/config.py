from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # extra="ignore": .env may hold provider keys (e.g. a parked ANTHROPIC_API_KEY)
    # that are not Settings fields — LiteLLM and libraries read them from the
    # process env directly.
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql://postgres:postgres@localhost:5432/omniops"
    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    upload_dir: str = "storage/uploads"
    elasticsearch_url: str = "http://localhost:9200"
    es_chunk_index: str = "document_chunks"
    cors_origins: list[str] = ["http://localhost:3000"]
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "document_chunks"
    embedding_model_name: str = "BAAI/bge-m3"
    reranker_model_name: str = "BAAI/bge-reranker-v2-m3"
    llm_model: str = "anthropic/claude-opus-4-8"
    llm_api_key: str = ""


settings = Settings()
