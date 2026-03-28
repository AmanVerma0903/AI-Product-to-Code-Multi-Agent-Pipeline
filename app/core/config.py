from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Product-to-Code Platform"
    
    # DB
    DATABASE_URL: str
    
    # LLM
    OPENAI_API_KEY: str
    TAVILY_API_KEY: Optional[str] = None
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Storage
    UPLOAD_DIR: str = "uploads"
    OUTPUT_DIR: str = "generated_code"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
