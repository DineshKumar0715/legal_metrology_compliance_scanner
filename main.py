import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from ocr_engine import OCREngine
from compliance_engine import ComplianceEngine
from schemas import ComplianceResponse

# Global engine instances
ocr_engine: OCREngine = None
compliance_engine: ComplianceEngine = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize OCR and Compliance engines."""
    global ocr_engine, compliance_engine
    print("[INIT] Initializing EasyOCR Reader and Compliance Engine...", flush=True)
    ocr_engine = OCREngine(gpu=False)
    compliance_engine = ComplianceEngine()
    print("[INIT] Legal Metrology Compliance Engines successfully loaded.", flush=True)
    yield


app = FastAPI(
    title="Legal Metrology Compliance API",
    description="Statutory rule engine and OCR auditor for packaged commodity labels under Legal Metrology (Packaged Commodities) Rules, 2011.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware allowing all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
async def root():
    """Health check and service status endpoint."""
    return {
        "status": "active",
        "service": "Legal Metrology Compliance API",
        "version": "1.0.0",
        "engine_ready": ocr_engine is not None,
    }


@app.post(
    "/scan-label",
    response_model=ComplianceResponse,
    tags=["Compliance Audit"],
    summary="Scan label image and perform Legal Metrology statutory compliance audit",
)
async def scan_label(file: UploadFile = File(...)):
    """
    Upload a packaged commodity label image.
    Performs:
    1. MIME type validation (JPEG, PNG, WEBP)
    2. Computer vision preprocessing and EasyOCR text extraction
    3. Rule 6 compliance evaluation across 6 statutory declarations
    """
    valid_mime_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type and file.content_type.lower() not in valid_mime_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type '{file.content_type}'. Please upload an image (JPEG, PNG, WEBP).",
        )

    try:
        image_bytes = await file.read()
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        # Fallback initialization if lifespan hasn't fired
        global ocr_engine, compliance_engine
        if ocr_engine is None:
            ocr_engine = OCREngine(gpu=False)
        if compliance_engine is None:
            compliance_engine = ComplianceEngine()

        # Step 1: Run OCR extraction
        raw_text, _ = ocr_engine.extract_text(image_bytes)

        # Step 2: Run Compliance Evaluation
        compliance_result = compliance_engine.evaluate_compliance(raw_text)

        return compliance_result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing image for compliance audit: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
