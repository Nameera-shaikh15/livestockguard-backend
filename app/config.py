import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "LivestockGuard AI"
    VERSION: str = "1.0.0-hackathon-mvp"
    DEBUG: bool = True
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:5173,http://localhost:5174,http://localhost:3000"
    
    # Database
    DATABASE_URL: str = "sqlite:///./livestockguard.db"
    
    # Uploads
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    
    # Environmental Thresholds (Configurable Prototype Parameters - NOT medically validated)
    TEMP_WARNING_TH: float = 30.0
    TEMP_HIGH_TH: float = 35.0
    HUMIDITY_WARNING_TH: float = 70.0
    HUMIDITY_HIGH_TH: float = 80.0
    THI_MODERATE_STRESS: float = 75.0
    THI_SEVERE_STRESS: float = 84.0
    
    # Risk Engine Prototype Weights (Configurable Parameters - NOT scientifically validated)
    WEIGHT_VISUAL: float = 0.25
    WEIGHT_BEHAVIOUR: float = 0.30
    WEIGHT_AUDIO: float = 0.20
    WEIGHT_ENVIRONMENT: float = 0.25
    
    # Optional External AI Integrations
    VISION_API_KEY: str = ""
    VISION_API_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_API_URL: str = ""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origins(self) -> List[str]:
        if isinstance(self.ALLOWED_ORIGINS, str):
            return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
        return self.ALLOWED_ORIGINS


settings = Settings()

# Ensure uploads directory exists
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
