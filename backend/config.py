"""Backend configuration for Lakeforge API."""

import os
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
    llm_model: str = "openai/gpt-oss-120b"

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
        extra = "ignore"


# Global settings instance
settings = Settings()

# Ensure environment variable is set for Groq client and SQL generator
if settings.groq_api_key and not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = settings.groq_api_key
