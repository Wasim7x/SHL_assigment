"""Application configuration via environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """All config is loaded from environment variables or .env file."""

    # LLM Provider - Groq (free, fast, Llama models)
    GROQ_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.1-8b-instant"  # Fast, free tier

    # Retrieval
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    FAISS_INDEX_PATH: str = "data/faiss_index"
    CATALOG_PATH: str = "data/catalog.json"

    # Agent settings
    MAX_TURNS: int = 8
    RETRIEVAL_TOP_K: int = 15
    MAX_RECOMMENDATIONS: int = 10
    LLM_TIMEOUT: float = 25.0

    # Server
    CORS_ORIGINS: str = "*"
    PORT: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
