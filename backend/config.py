from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    gemini_api_key: str = ""
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""
    jwt_secret: str = "development-secret-change-in-production-min-32-chars"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    app_env: str = "development"
    log_level: str = "INFO"
    backend_port: int = 8000
    backend_host: str = "0.0.0.0"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    return Settings()
