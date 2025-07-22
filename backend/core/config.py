"""
Configuration settings for Talktor backend
"""
import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # OpenAI
    openai_api_key: str
    openai_model: str = "gpt-4o-realtime-preview-2024-10-01"
    openai_ws_url: str = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01"
    openai_chat_model: str = "gpt-4o"  # For StandardAgent
    openai_voice: str = "alloy"  # Voice for realtime conversations
    
    # Audio settings
    audio_sample_rate: int = 24000
    audio_chunk_size: int = 1024
    audio_format: str = "pcm16"
    
    # Transcription settings
    enable_transcriptions: bool = True
    transcription_model: str = "whisper-1"
    
    # Session settings
    default_session_duration_minutes: int = 5
    max_session_duration_minutes: int = 30
    
    # API settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    class Config:
        # Get absolute path to .env file in repo root
        _current_file = Path(__file__).resolve()
        _repo_root = _current_file.parent.parent.parent
        env_file = str(_repo_root / ".env")
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from .env


# Global settings instance
settings = Settings()
