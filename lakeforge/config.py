"""Configuration loader for Lakeforge."""

import os
from pathlib import Path
from typing import Any, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import yaml
from pydantic import BaseModel, ConfigDict, Field


class LakeforgeConfig(BaseModel):
    """Main configuration model for Lakeforge."""

    # LLM Configuration
    llm_provider: str = Field(default="groq", description="LLM provider (groq, ollama, gemini)")
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")

    # Output Configuration
    output_dir: Path = Field(default=Path("./.lakeforge"), description="Output directory")
    log_level: str = Field(default="INFO", description="Logging level")

    # Query Configuration
    max_query_timeout_sec: int = Field(default=30, description="Max query timeout in seconds")
    max_result_bytes: int = Field(default=10 * 1024 * 1024, description="Max result size in bytes (10MB)")
    max_sample_rows: int = Field(default=1000, description="Max sample rows to extract")

    # Cost Configuration
    max_cost_per_run: float = Field(default=1.0, description="Max cost per run in dollars")

    # Databricks Configuration
    databricks_host: Optional[str] = Field(default=None, description="Databricks host")
    databricks_token: Optional[str] = Field(default=None, description="Databricks token")
    databricks_workspace_id: Optional[str] = Field(default=None, description="Databricks workspace ID")

    # Postgres Configuration
    postgres_host: Optional[str] = Field(default=None, description="Postgres host")
    postgres_port: int = Field(default=5432, description="Postgres port")
    postgres_user: Optional[str] = Field(default=None, description="Postgres user")
    postgres_password: Optional[str] = Field(default=None, description="Postgres password")
    postgres_db: Optional[str] = Field(default=None, description="Postgres database")

    # PII Configuration
    pii_detection_method: str = Field(default="regex", description="PII detection method")
    pii_masking_method: str = Field(default="hash", description="PII masking method")

    model_config = ConfigDict(
        case_sensitive=False,
    )

    def model_dump(self, **kwargs: Any) -> dict[str, Any]:
        """Override model_dump to handle Path objects."""
        data = super().model_dump(**kwargs)
        # Convert Path objects to strings
        for key, value in data.items():
            if isinstance(value, Path):
                data[key] = str(value)
        return data


def load_config_from_file(config_path: Optional[Path] = None) -> LakeforgeConfig:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config YAML file. If None, looks for .lakeforge.yaml in current dir.

    Returns:
        LakeforgeConfig object.
    """
    if config_path is None:
        config_path = Path(".lakeforge.yaml")

    if config_path.exists():
        with open(config_path) as f:
            config_dict = yaml.safe_load(f) or {}
    else:
        config_dict = {}

    # Merge with environment variables (env vars take precedence)
    env_config = {
        k.lower().replace("lakeforge_", ""): v
        for k, v in os.environ.items()
        if k.startswith("LAKEFORGE_")
    }

    config_dict.update(env_config)

    return LakeforgeConfig(**config_dict)


def get_config() -> LakeforgeConfig:
    """Get configuration from file and environment."""
    return load_config_from_file()
