from pydantic import validator
from pydantic_settings import BaseSettings
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Required environment variables
    DATABASE_URL: str
    REDIS_URL: str
    DISCORD_TOKEN: str
    LLM_MODEL: str
    OPENAI_API_KEY: str
    
    # Optional with defaults
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LOG_LEVEL: str = "INFO"
    
    # Database pool settings
    DB_MIN_SIZE: int = 5
    DB_MAX_SIZE: int = 20
    DB_COMMAND_TIMEOUT: int = 60
    
    # Redis settings
    REDIS_HEALTH_CHECK_INTERVAL: int = 30
    
    # Rate limiting settings
    USER_RATE_LIMIT_PER_MINUTE: int = 20
    CHANNEL_RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_TTL: int = 60
    
    # Cache settings
    CACHE_TTL_SECONDS: int = 86400  # 24 hours
    
    # OpenAI settings
    OPENAI_TIMEOUT: int = 30
    OPENAI_MAX_RETRIES: int = 3
    OPENAI_TEMPERATURE: float = 0.5
    OPENAI_MAX_TOKENS: int = 1000
    
    # Planner specific settings
    PLANNER_TEMPERATURE: float = 0.1
    PLANNER_MAX_TOKENS: int = 2000
    
    # Railway deployment settings
    PORT: Optional[int] = None
    RAILWAY_ENVIRONMENT: Optional[str] = None
    
    @validator('DATABASE_URL')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'postgres://')):
            raise ValueError('DATABASE_URL must be a valid PostgreSQL URL')
        return v
    
    @validator('REDIS_URL')
    def validate_redis_url(cls, v):
        if not v.startswith(('redis://', 'rediss://')):
            raise ValueError('REDIS_URL must be a valid Redis URL')
        return v
    
    @validator('LOG_LEVEL')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'LOG_LEVEL must be one of: {", ".join(valid_levels)}')
        return v.upper()
    
    @validator('OPENAI_TEMPERATURE')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError('OPENAI_TEMPERATURE must be between 0.0 and 2.0')
        return v
    
    @validator('PLANNER_TEMPERATURE')
    def validate_planner_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError('PLANNER_TEMPERATURE must be between 0.0 and 2.0')
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance - validates on import
try:
    settings = Settings()
    print(f"✅ Configuration loaded successfully")
    print(f"   Log Level: {settings.LOG_LEVEL}")
    print(f"   Database: {settings.DATABASE_URL[:30]}...")
    print(f"   Redis: {settings.REDIS_URL[:30]}...")
    print(f"   Discord Token: {'*' * 20}")
    print(f"   LLM Model: {settings.LLM_MODEL}")
except Exception as e:
    print(f"❌ Configuration validation failed: {e}")
    print("Please check your environment variables and .env file")
    print("\nRequired variables:")
    print("  - DATABASE_URL")
    print("  - REDIS_URL") 
    print("  - DISCORD_TOKEN")
    print("  - LLM_MODEL")
    print("  - OPENAI_API_KEY")
    exit(1)


def get_settings() -> Settings:
    """Get application settings"""
    return settings