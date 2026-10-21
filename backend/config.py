"""Backend configuration for Lakeforge API."""

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # App
    app_name: str = "Lakeforge API"
    app_version: str = "0.2.0"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    # Database (for storing sessions, reports)
    database_url: str = "sqlite:///./lakeforge.db"
    # For production: "postgresql://user:password@localhost/lakeforge"

    # LLM
    llm_provider: str = "groq"
    groq_api_key: Optional[str] = None
    llm_model: str = "mixtral-8x7b-32768"

    # File storage
    reports_dir: str = ".lakeforge/reports"
    cache_dir: str = ".lakeforge/cache"

    # Query limits
    max_query_timeout: int = 60
    max_result_rows: int = 10000

    # Security
    api_key_required: bool = False
    api_key_header: str = "X-API-Key"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()
