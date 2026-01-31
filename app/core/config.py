"""
Application Configuration Settings
Loads all configuration from environment variables
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "Secure File Sharing System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # PostgreSQL Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "SECUREFILE_SHARING_APPLICATION"
    DATABASE_URL: Optional[str] = None
    
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_URL: Optional[str] = None
    
    # AWS S3
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "ap-south-2"
    S3_BUCKET_NAME: str
    
    # JWT Configuration
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 20
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # File Upload Configuration
    MAX_FILE_SIZE_MB: int = 200
    MAX_FILE_SIZE_BYTES: int = 209715200  # 200 * 1024 * 1024
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Default Admin User
    ADMIN_EMAIL: str = "admin@securefile.com"
    ADMIN_PASSWORD: str = "AbhiMH33"
    
    @property
    def database_url(self) -> str:
        """Construct database URL from components"""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL from components"""
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "allow"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


settings = get_settings()
