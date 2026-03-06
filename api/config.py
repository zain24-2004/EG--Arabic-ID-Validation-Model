import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    OCR_SPACE_API_KEY : str        = os.getenv("OCR_SPACE_API_KEY", "YOUR_API_KEY_HERE")
    API_SECRET_KEY    : str        = os.getenv("API_SECRET_KEY",    "change-me")
    REQUIRE_AUTH      : bool       = False
    MODEL_DIR         : str        = os.getenv("MODEL_DIR", "/app/saved_models")
    ALLOWED_ORIGINS   : List[str]  = ["*"]
    OCR_ENGINE        : int        = 2
    OCR_LANGUAGE      : str        = "ara"
    OCR_RATE_LIMIT_S  : float      = 1.2
    DEFAULT_CONF      : float      = 0.4
    DEFAULT_PADDING   : int        = 8

    class Config:
        env_file = ".env"

settings = Settings()
os.makedirs(settings.MODEL_DIR, exist_ok=True)
