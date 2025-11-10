"""
Configuration module for the Healthcare Assistant - Agno Framework with Gemini
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load .env file from current directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

class Settings(BaseSettings):
    """Application settings for Agno-based Healthcare Assistant"""

    # API Keys
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Agno Agent Configuration
    AGENT_MODEL: str = "gemini-2.5-flash-preview-09-2025"  # Gemini model
    AGENT_TEMPERATURE: float = 0.7
    AGENT_MAX_TOKENS: int = 4096

    # Database Configuration
    DB_FILE: str = "healthcare.db"
    DB_TYPE: str = "sqlite"

    # Medical Knowledge Base
    ENABLE_EXTERNAL_APIs: bool = True
    KNOWLEDGE_BASE_FILE: str = "medical_knowledge_base.json"

    # Application
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    MAX_REASONING_STEPS: int = 10

    # Agno Framework
    AGNO_HOST: str = os.getenv("AGNO_HOST", "localhost")
    AGNO_PORT: int = int(os.getenv("AGNO_PORT", "8081"))

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
