"""Application Configuration"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment"""
    
    # API Configuration
    app_name: str = "AIMS College Chatbot"
    app_version: str = "0.1.0"
    debug: bool = False
    api_prefix: str = "/api/v1"
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database
    database_url: str = "postgresql://user:password@localhost:5432/chatbot"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-3.5-turbo"
    openai_embedding_model: str = "text-embedding-3-small"
    
    # Salesforce
    salesforce_client_id: str = ""
    salesforce_client_secret: str = ""
    salesforce_username: str = ""
    salesforce_password: str = ""
    salesforce_security_token: str = ""
    salesforce_instance_url: str = "https://login.salesforce.com"
    
    # College Website
    college_website_url: str = "https://www.theaims.ac.in"
    
    # LLM Configuration
    llm_temperature: float = 0.1
    llm_max_tokens: int = 300
    confidence_threshold: float = 0.7
    retrieval_top_k: int = 5
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()
