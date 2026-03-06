import os, shutil
from fastapi import APIRouter, File, UploadFile, HTTPException, Header
from typing import Optional
from services.ocr_service import list_saved_models, clear_cache
from config import settings
from auth import verify_api_key

router = APIRouter()

@router.get("/")
def list_models(x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    return list_saved_models()

@router.post("/upload")
async def upload_model(file: UploadFile = File(...), x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    if not file.filename.endswith(".pt"):
        raise HTTPException(400, "Only .pt files accepted.")
    path = os.path.join(settings.MODEL_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": f"{file.filename} saved", "size_mb": round(os.path.getsize(path)/1_048_576, 2)}

@router.delete("/{model_name}")
def delete_model(model_name: str, x_api_key: Optional[str] = Header(None)):
    verify_api_key(x_api_key)
    path = os.path.join(settings.MODEL_DIR, model_name)
    if not os.path.exists(path):
        raise HTTPException(404, "Not found.")
    os.remove(path)
    clear_cache(model_name)
    return {"message": f"{model_name} deleted"}
