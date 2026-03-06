from fastapi import HTTPException
from config import settings

def verify_api_key(x_api_key: str = None):
    if not settings.REQUIRE_AUTH:
        return
    if x_api_key != settings.API_SECRET_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Api-Key.")
