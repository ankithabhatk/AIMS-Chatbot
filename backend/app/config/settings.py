"""Application configuration with tolerant local parsing."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings


BACKEND_DIR = Path(__file__).resolve().parents[1]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    app_name: str = "AIMS College Chatbot"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = "postgresql://user:password@localhost:5432/chatbot"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_embedding_model: str = "text-embedding-3-small"

    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    salesforce_instance_url: str = "https://login.salesforce.com"

    college_website_url: str = "https://www.theaims.ac.in"

    llm_temperature: float = 0.1
    llm_max_tokens: int = 300
    confidence_threshold: float = 0.7
    retrieval_top_k: int = 5
    embedding_model_name: str = "all-MiniLM-L6-v2"
    answer_token_limit: int = 320
    context_token_limit: int = 900
    query_cache_ttl_seconds: int = 900
    query_cache_max_entries: int = 256
    embedding_cache_max_entries: int = 512

    log_level: str = "INFO"

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"1", "true", "yes", "on", "debug", "development"}:
            return True
        if text in {"0", "false", "no", "off", "release", "prod", "production"}:
            return False
        return False

    class Config:
        env_file = str(ENV_FILE)
        case_sensitive = False
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Return a cached settings object."""
    return Settings()
