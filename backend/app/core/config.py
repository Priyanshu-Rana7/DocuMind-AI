import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Core Application
    PROJECT_NAME: str = "DocuMind AI"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "structured"  # structured | json | console
    
    # Database
    DATABASE_URL: str = "sqlite:///./sql_app.db"
    
    # Security & Auth Readiness (Future expansion)
    ENABLE_AUTH: bool = False
    SECRET_KEY: str = "super-secret-development-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Prompt Management
    PROMPT_VERSION: str = "invoice_extraction_v1"
    PROMPTS_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "prompts"
    )
    
    # OCR Engine Settings
    OCR_PROVIDER: str = "easyocr"  # easyocr | tesseract | mock
    OCR_LANGUAGES: List[str] = ["en"]
    OCR_USE_GPU: bool = False
    OCR_MODEL_DIR: Optional[str] = None
    POPPLER_PATH: Optional[str] = None
    
    # AI / LLM Settings
    LLM_PROVIDER: str = "openrouter"  # openrouter | openai | mock
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "google/gemini-2.5-flash"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 4000
    LLM_TIMEOUT_SECONDS: int = 60
    EXTRACTION_MAX_ATTEMPTS: int = 3
    EXTRACTION_RETRY_BACKOFF_SECONDS: float = 0.5
    MAX_CONCURRENT_PROCESSING: int = 1
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_MAX_REQUESTS: int = 10
    RATE_LIMITED_PROCESSING_REQUESTS: int = 3
    MAX_DOCUMENT_PAGES: int = 5
    
    # Storage Settings
    STORAGE_PROVIDER: str = "local"  # local | supabase
    UPLOAD_DIR: str = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads"
    )
    MAX_UPLOAD_SIZE_MB: int = 15
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".png", ".jpg", ".jpeg"]
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/png",
        "image/jpeg",
        "image/jpg",
    ]

    # Supabase Storage
    SUPABASE_URL: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_STORAGE_BUCKET: str = "invoices"

    # Legacy S3 configuration
    S3_BUCKET_NAME: Optional[str] = None
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    AWS_REGION: str = "us-east-1"

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
