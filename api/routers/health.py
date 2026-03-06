from fastapi import APIRouter
from services.ocr_service import list_saved_models, _model_cache
from config import settings
from datetime import datetime

router = APIRouter()

@router.get("/")
def root(): return {"service": "Egyptian National ID Validation API", "version": "1.0.0", "docs": "/docs"}

@router.get("/health")
def health():
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "models_saved":  len(list_saved_models()),
        "models_cached": len(_model_cache),
        "ocr_key_set":   bool(settings.OCR_SPACE_API_KEY and settings.OCR_SPACE_API_KEY != "YOUR_API_KEY_HERE")
    }
