import io
import os
from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Load .env file
load_dotenv()

from schemas import ComplianceResponse
from gemini_compliance_engine import GeminiComplianceEngine

app = FastAPI(
    title="Legal Metrology Compliance API (Gemini Multimodal)",
    description="Automated multimodal label verification under Legal Metrology (Packaged Commodities) Rules, 2011 powered by Google Gemini 2.5 Flash",
    version="2.0.0",
)

# Enable CORS for frontend integrations (Streamlit, React, etc.)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini Compliance Engine
compliance_engine = GeminiComplianceEngine()


@app.get("/")
def read_root():
    return {
        "status": "Active",
        "message": "Legal Metrology Compliance API (Gemini Multimodal) is running.",
        "model": "gemini-2.5-flash",
    }


@app.get("/health")
def health_check():
    load_dotenv(override=True)
    key = os.getenv("GEMINI_API_KEY")
    api_key_configured = bool(
        key
        and key.strip()
        and key != "your_gemini_api_key_here"
    )
    return {
        "status": "ok",
        "engine": "gemini-2.5-flash",
        "api_key_configured": api_key_configured,
    }


@app.post("/scan-label", response_model=ComplianceResponse)
def scan_label(file: UploadFile = File(...)):
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Supported formats are JPG, JPEG, PNG, and WEBP.",
        )

    try:
        contents = file.file.read()
        pil_image = Image.open(io.BytesIO(contents))
        report = compliance_engine.evaluate_image(pil_image)
        return report
    except ValueError as val_err:
        raise HTTPException(status_code=500, detail=str(val_err))
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Label compliance evaluation failed: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
