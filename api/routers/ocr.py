import base64
from fastapi import APIRouter, File, UploadFile, HTTPException, Query, Header
from fastapi.responses import Response, JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from services.ocr_service import run_pipeline
from services.validation_service import validate_national_id, cross_validate
from auth import verify_api_key
from config import settings

router = APIRouter()

class Box(BaseModel):
    x1: int; y1: int; x2: int; y2: int

class Detection(BaseModel):
    id: int; label: str; confidence: float; text: str; box: Box

class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[str]
    extraction: Dict[str, Optional[str]]

class OCRResponse(BaseModel):
    total: int
    detections: List[Detection]
    ocr_json: Dict[str, str]
    validation: Optional[ValidationResult] = None
    annotated_image: Optional[str] = None

@router.post("/detect", response_model=OCRResponse)
async def detect(
    file:          UploadFile      = File(...),
    model_name:    str             = Query("model.pt"),
    conf:          float           = Query(settings.DEFAULT_CONF),
    padding:       int             = Query(settings.DEFAULT_PADDING),
    include_image: bool            = Query(True),
    validate:      bool            = Query(True),
    x_api_key:     Optional[str]   = Header(None),
):
    verify_api_key(x_api_key)
    try:
        result = run_pipeline(await file.read(), model_name, conf, padding)

        validation_data = None
        if validate:
            national_id = result["ocr_json"].get("ID-Number") or result["ocr_json"].get("Personal-ID")
            if national_id:
                validation_data = validate_national_id(national_id)
                # Cross-validate with other OCR data
                cross_errors = cross_validate(result["ocr_json"], validation_data)
                validation_data["errors"].extend(cross_errors)
                if cross_errors:
                    validation_data["is_valid"] = False

        return OCRResponse(
            total=result["total"],
            detections=result["detections"],
            ocr_json=result["ocr_json"],
            validation=validation_data,
            annotated_image=base64.b64encode(result["annotated_image_bytes"]).decode()
                            if include_image and result["annotated_image_bytes"] else None
        )
    except FileNotFoundError as e: raise HTTPException(404, str(e))
    except ValueError        as e: raise HTTPException(422, str(e))
    except Exception         as e: raise HTTPException(500, str(e))

@router.post("/detect/json")
async def detect_json(
    file:          UploadFile      = File(...),
    model_name:    str             = Query("model.pt"),
    conf:          float           = Query(settings.DEFAULT_CONF),
    padding:       int             = Query(settings.DEFAULT_PADDING),
    validate:      bool            = Query(True),
    x_api_key:     Optional[str]   = Header(None),
):
    verify_api_key(x_api_key)
    try:
        result = run_pipeline(await file.read(), model_name, conf, padding)
        validation_data = None
        if validate:
            national_id = result["ocr_json"].get("ID-Number") or result["ocr_json"].get("Personal-ID")
            if national_id:
                validation_data = validate_national_id(national_id)

        return JSONResponse({
            "total": result["total"],
            "detections": result["detections"],
            "ocr_json": result["ocr_json"],
            "validation": validation_data
        })
    except Exception as e: raise HTTPException(500, str(e))
