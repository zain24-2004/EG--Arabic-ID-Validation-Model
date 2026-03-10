import os, shutil
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from typing import List
from services.ocr_service import list_saved_models, clear_cache
from config import settings
from auth import verify_api_key

router = APIRouter(dependencies=[Depends(verify_api_key)])

@router.get("/", response_model=List[dict])
def list_models():
    return list_saved_models()

@router.post("/upload")
async def upload_model(file: UploadFile = File(...)):
    # Sanitize filename to prevent path traversal
    filename = os.path.basename(file.filename)
    if not filename.endswith(".pt"):
        raise HTTPException(400, "Only .pt files accepted.")

    path = os.path.join(settings.MODEL_DIR, filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "message": f"{filename} saved",
        "size_mb": round(os.path.getsize(path) / 1_048_576, 2)
    }

@router.delete("/{model_name}")
def delete_model(model_name: str):
    # Sanitize model_name to prevent path traversal
    filename = os.path.basename(model_name)
    path = os.path.join(settings.MODEL_DIR, filename)

    if not os.path.exists(path):
        raise HTTPException(404, "Model not found.")

    os.remove(path)
    clear_cache(filename)
    return {"message": f"{filename} deleted"}
