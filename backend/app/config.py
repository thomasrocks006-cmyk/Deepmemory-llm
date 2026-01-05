"""
Configuration management for DeepMemory LLM application.
Loads environment variables and provides centralized config access.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Union
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Application
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str
    
    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.cors_origins.split(',') if origin.strip()]
    
    # Google Cloud / Gemini
    google_api_key: str
    google_cloud_project: str
    vertex_ai_location: str = "us-central1"
    
    # Pinecone
    pinecone_api_key: str
    pinecone_environment: str
    pinecone_index_name: str = "deepmemory-vectors"
    
    # Neo4j
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    
    # PostgreSQL
    database_url: str
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # Context Caching
    context_cache_ttl: int = 3600
    max_cache_size: int = 1_048_576
    
    # Agent Configuration
    thinking_level: str = "high"
    max_output_tokens: int = 8192
    temperature_conservative: float = 0.3
    temperature_balanced: float = 0.7
    temperature_creative: float = 1.0
    
    # Learning Loop
    reflection_interval: int = 5
    nightly_reflection_time: str = "02:00"
    
    # Feature Flags
    enable_multi_agent_consensus: bool = False
    enable_proactive_insights: bool = True
    enable_voice_interface: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables like NEXT_PUBLIC_*


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings(_env_file=".env")  # type: ignore
