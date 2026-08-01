"""
Configuration management for the Telegram bot.
Loads environment variables and provides settings.
"""

import os
import logging
from dotenv import load_dotenv
from typing import List

load_dotenv()

class Config:
    """Application configuration."""
    
    # Bot token
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is required")
    
    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    
    # Admin IDs
    ADMIN_IDS: List[int] = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
    
    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Rate limiting
    RATE_LIMIT: int = int(os.getenv("RATE_LIMIT", "30"))
    
    # Application name
    APP_NAME: str = "تعمیرکار کولر و پکیج"
    
    # Date format
    DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
    DATE_FORMAT_SHORT: str = "%Y-%m-%d"

    @classmethod
    def get_log_level(cls) -> int:
        """Convert string log level to logging constant."""
        return getattr(logging, cls.LOG_LEVEL.upper(), logging.INFO)
