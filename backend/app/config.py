"""
Configuration module for SkillBridge backend.
Loads settings from environment variables or a .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from pathlib import Path

# Locate the directory containing this config file
BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """
    Application settings with default fallback values.
    Pydantic automatically validates and type-casts environment variables.
    """
    # Gemini API key used for structured LLM parsing, rejection reasons, and bullet rewrites
    gemini_api_key: str = ""

    # Name of the sentence-transformers model for semantic similarity
    embedding_model_name: str = "all-MiniLM-L6-v2"

    # Cosine similarity thresholds:
    # Scores >= 0.75 are considered Strong matches (e.g. React.js ~ JavaScript)
    similarity_threshold_strong: float = 0.75
    # Scores between 0.50 and 0.75 are considered Underrepresented / Partial matches
    similarity_threshold_partial: float = 0.50

    # Server binding configuration
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_port: int = 5173

    # SQLite database file connection string
    database_url: str = "sqlite:///./skillbridge.db"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Instantiate singleton settings object
settings = Settings()
