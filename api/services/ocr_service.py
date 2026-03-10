import os, time, tempfile, requests, re, asyncio
import cv2
import numpy as np
import httpx
from ultralytics import YOLO
from typing import List, Dict, Any, Optional
from config import settings

_model_cache: Dict[str, YOLO] = {}

def get_model(name="model.pt") -> YOLO:
    path = os.path.join(settings.MODEL_DIR, name)
    if not os.path.exists(path):
        # If it doesn't exist, we'll try to use a default YOLOv8n model
        # or raise an error if specifically requested.
        if name == "model.pt":
            return YOLO("yolov8n.pt")
        raise FileNotFoundError(f"Model {name!r} not found at {path}.")

    if name not in _model_cache:
        _model_cache[name] = YOLO(path)
    return _model_cache[name]

def clear_cache(name=None):
    if name:
        _model_cache.pop(name, None)
    else:
        _model_cache.clear()

def list_saved_models():
    if not os.path.isdir(settings.MODEL_DIR):
        return []
    out = []
    for fn in os.listdir(settings.MODEL_DIR):
        if fn.endswith(".pt"):
            p = os.path.join(settings.MODEL_DIR, fn)
            s = os.stat(p)
            out.append({
                "name": fn,
                "size_mb": round(s.st_size/1_048_576, 2),
                "cached": fn in _model_cache,
                "modified_at": int(s.st_mtime)
            })
    return out

def preprocess_crop(crop_bgr: np.ndarray, label: str) -> np.ndarray:
    h, w = crop_bgr.shape[:2]

    # Scale up small crops
    scale = 3 if (w < 200 or h < 40) else 2
    up = cv2.resize(crop_bgr, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)

    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)

    # Denoise
    gray = cv2.fastNlMeansDenoising(gray, h=10)

    lbl = label.lower()
    if any(k in lbl for k in ("id", "number", "رقم")):
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif any(k in lbl for k in ("date", "birth", "تاريخ")):
        binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    else:
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        mean_val = np.mean(binary)
        if mean_val < 50 or mean_val > 200:
            binary = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 3)

    # Add white border
    padded = cv2.copyMakeBorder(binary, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=255)
    return cv2.cvtColor(padded, cv2.COLOR_GRAY2BGR)

def _clean_text(text: str, label: str) -> str:
    """
    Cleans OCR text based on field label.
    """
    if not text:
        return ""

    lbl = label.lower()
    if any(k in lbl for k in ("id", "number", "personal", "رقم")):
        # Keep only digits
        return re.sub(r"\D", "", text)
    elif any(k in lbl for k in ("name", "اسم")):
        # Keep Arabic characters and spaces
        # Arabic range: \u0600-\u06FF
        return "".join(re.findall(r"[\u0600-\u06FF\s]+", text)).strip()
    elif any(k in lbl for k in ("date", "birth", "تاريخ")):
        # Keep digits and common separators
        return "".join(re.findall(r"[\d\/\-\.]+", text)).strip()

    return text.strip()

async def _call_ocr_space_async(img_bgr: np.ndarray, label: str) -> str:
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        cv2.imwrite(tmp.name, img_bgr)
        tmp_path = tmp.name

    try:
        async with httpx.AsyncClient() as client:
            with open(tmp_path, "rb") as f:
                resp = await client.post(
                    "https://api.ocr.space/parse/image",
                    files={"file": ("crop.jpg", f, "image/jpeg")},
                    data={
                        "apikey": settings.OCR_SPACE_API_KEY,
                        "language": settings.OCR_LANGUAGE,
                        "OCREngine": settings.OCR_ENGINE,
                        "isOverlayRequired": False,
                        "detectOrientation": True,
                        "scale": True,
                    },
                    timeout=30,
                )
            result = resp.json()
            if result.get("IsErroredOnProcessing"):
                print(f"[OCR] API error: {result.get('ErrorMessage')}")
                return ""
            parsed = result.get("ParsedResults", [])
            raw_text = parsed[0]["ParsedText"].strip() if parsed else ""
            return _clean_text(raw_text, label)
    except Exception as e:
        print(f"[OCR] Exception: {e}")
        return ""
    finally:
        os.unlink(tmp_path)

def _draw_annotations(image: np.ndarray, detections: List[Dict]) -> bytes:
    annotated = image.copy()
    colors = [(0, 255, 127), (0, 180, 255), (255, 100, 0), (180, 0, 255), (255, 220, 0)]
    for i, det in enumerate(detections):
        b = det["box"]
        col = colors[i % len(colors)]
        cv2.rectangle(annotated, (b["x1"], b["y1"]), (b["x2"], b["y2"]), col, 2)

        label_txt = f"{det['label']}: {det['text'][:20]}" if det.get("text") else det["label"]
        (tw, th), _ = cv2.getTextSize(label_txt, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
        ty = max(b["y1"] - 5, th + 4)
        cv2.rectangle(annotated, (b["x1"], ty - th - 4), (b["x1"] + tw + 4, ty + 2), col, -1)
        cv2.putText(annotated, label_txt, (b["x1"] + 2, ty - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1)

    ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return buf.tobytes() if ok else b""

async def run_pipeline_async(image_bytes: bytes, model_name: str = "model.pt", conf: Optional[float] = None, padding: Optional[int] = None):
    conf = conf or settings.DEFAULT_CONF
    padding = padding or settings.DEFAULT_PADDING

    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Could not decode image.")

    img_h, img_w = image.shape[:2]
    img_area = img_h * img_w

    model = get_model(model_name)
    # YOLO inference is still synchronous as it's typically CPU/GPU bound
    results = model(image, conf=conf)[0]
    boxes = results.boxes

    # Filter bleed boxes (>50% area)
    valid_indices = [
        i for i, xyxy in enumerate(boxes.xyxy)
        if ((int(xyxy[2]) - int(xyxy[0])) * (int(xyxy[3]) - int(xyxy[1]))) / img_area <= 0.50
    ]

    detections = []
    for idx, vi in enumerate(valid_indices):
        xyxy = boxes.xyxy[vi]
        label = model.names[int(boxes.cls[vi])]
        conf_val = float(boxes.conf[vi])

        x1 = max(0, int(xyxy[0]) - padding)
        y1 = max(0, int(xyxy[1]) - padding)
        x2 = min(img_w, int(xyxy[2]) + padding)
        y2 = min(img_h, int(xyxy[3]) + padding)

        crop = image[y1:y2, x1:x2]
        prep = preprocess_crop(crop, label)
        text = await _call_ocr_space_async(prep, label)

        detections.append({
            "id": idx + 1,
            "label": label,
            "confidence": round(conf_val, 4),
            "text": text,
            "box": {"x1": x1, "y1": y1, "x2": x2, "y2": y2}
        })
        if idx < len(valid_indices) - 1:
            await asyncio.sleep(settings.OCR_RATE_LIMIT_S)

    ocr_json = {d["label"]: d["text"] for d in detections}
    annotated_image_bytes = _draw_annotations(image, detections)

    return {
        "total": len(detections),
        "detections": detections,
        "ocr_json": ocr_json,
        "annotated_image_bytes": annotated_image_bytes
    }
