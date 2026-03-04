# EG--Arabic-ID-Validation-Model
An intelligent validation module for verifying Egyptian National ID data extracted using OCR systems.
This project ensures structural, logical, and semantic correctness of ID card information before further processing.

------ Overview----------------------
This project is designed to work as a post-processing validation layer in AI-powered document processing pipelines.
It validates Egyptian National ID cards after:
1-ID Detection
2-OCR Text Extraction
Then performs rule-based validation to ensure data consistency and correctness.

------------- System Pipeline-----------
Input Image
    ↓
ID Detection Model
    ↓
OCR Model (Arabic Text Extraction)
    ↓
Arabic ID Validation Model
    ↓
Validated Structured Output


----------------Egyptian National ID Structure-------------
Position	Description
1	Century Code
2-7	Date of Birth (YYMMDD)
8-9	Governorate Code
10-13	Serial Number
14	Gender Indicator

Example:
  name= محمد احمد عبالله
  id=29801011234567
  2 → Born in 1900s
  98 → Year
  01 → Month
  01 → Day
  Last digit 7 → Male

--------- Tech Stack---------

Python 3.x
---- Computer Vision Layer
OpenCV (cv2) – Image preprocessing, resizing, cropping, enhancement
YOLO (You Only Look Once) – Real-time ID card detection and localization
Used for detecting and extracting the ID card region from input images
Supports bounding box prediction with high accuracy and speed

------- OCR Layer
OCR API Integration – Arabic text extraction from detected ID card
Extracts:
National ID Number
Full Name
Date of Birth
Address
Supports Arabic language recognition

--------Backend / API Layer 
FastAPI (for deployment)
JSON structured responses
