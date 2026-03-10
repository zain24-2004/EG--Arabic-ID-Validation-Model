from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import ocr, models, health
from config import settings
import os

# Ensure model directory exists on startup
os.makedirs(settings.MODEL_DIR, exist_ok=True)

app = FastAPI(
    title="Egyptian National ID Validation API",
    version="1.0.0",
    description="YOLO + OCR.space pipeline for Egyptian National ID data extraction and validation.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router,               tags=["Health"])
app.include_router(ocr.router,    prefix="/ocr",    tags=["OCR"])
app.include_router(models.router, prefix="/models", tags=["Models"])
