"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All config is loaded from environment variables or .env file."""

    GEMINI_API_KEY: str = ""
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "data/faiss_index"
    CATALOG_PATH: str = "data/catalog.json"
    MAX_TURNS: int = 8
    RETRIEVAL_TOP_K: int = 15
    MAX_RECOMMENDATIONS: int = 10
    LLM_TIMEOUT: float = 25.0
    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
