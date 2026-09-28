import os
from typing import List, Union, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator


class Settings(BaseSettings):
    """Application configuration settings loaded from environment or defaults."""

    # Project Information
    PROJECT_NAME: str = "AI-Based Train Traffic Management System"
    PROJECT_PHASE: str = "Phase 13: Final Integration Testing, Project Validation & Presentation-Ready Build"
    API_VERSION: str = "1.0.0"
    API_DEBUG: bool = True
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "INFO"

    # Server Binding
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Simulation & AI Engine
    SIMULATION_SPEED: float = 1.0
    ML_MODEL_PATH: str = "ml/saved_models/delay_prediction_model.pkl"

    # Google Gemini & OpenRouter AI Integration
    GEMINI_API_KEY: Optional[str] = None
    OPENROUTER_API_KEY: Optional[str] = None

    # Database
    DATABASE_URL: str = "sqlite:///./train_control.db"

    # Frontend Integration
    FRONTEND_URL: str = "https://ai-based-train-traffic-management-s.vercel.app"
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://ai-based-train-traffic-management-s.vercel.app",
        "https://traintrafficsystem.netlify.app",
        "https://*.netlify.app",
        "https://*.vercel.app",
        "*",
    ]


    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

