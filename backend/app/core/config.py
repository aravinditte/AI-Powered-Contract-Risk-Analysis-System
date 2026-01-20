from pydantic import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "AI Contract Risk Analysis System"
    ENVIRONMENT: str = "development"
    ENABLE_DOCS: bool = True

    # Security
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Database
    DATABASE_URL: str

    # CORS
    CORS_ALLOW_ORIGINS: List[str] = ["http://localhost:3000"]

    # File Storage
    FILE_STORAGE_PATH: str = "/var/lib/contracts"
    MAX_UPLOAD_SIZE_MB: int = 20

    # AI System Rules
    AI_DECISION_MODE: str = "HUMAN_REVIEW_ONLY"  # enforced policy
    ALLOW_AUTO_APPROVAL: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
