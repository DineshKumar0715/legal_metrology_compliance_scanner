import os
import io
import json
from typing import Union, Optional, List, Dict
from PIL import Image
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas import (
    ComplianceResponse,
    ExtractedField,
    ViolationDetail,
    ViolationSeverity,
    InspectionStatus,
    PhysicalVerificationResult,
)
from rule_engine import StatutoryRuleEngine

# Load environment variables from .env
load_dotenv()

class GeminiTranscriptionSchema(BaseModel):
    raw_text: str = Field(..., description="Complete verbatim transcription of all text, declarations, numbers, and headers visible on the packaging label.")
    mrp: Optional[str] = Field(None, description="Extracted Maximum Retail Price text with tax clause.")
    net_quantity: Optional[str] = Field(None, description="Extracted Net Quantity text with unit.")
    unit_sale_price: Optional[str] = Field(None, description="Extracted Unit Sale Price text.")
    date_of_packing: Optional[str] = Field(None, description="Extracted Date of Mfg / Packing text.")
    best_before_expiry: Optional[str] = Field(None, description="Extracted Best Before / Expiry text.")
    consumer_care: Optional[str] = Field(None, description="Extracted Consumer care email / phone / address.")
    manufacturer_details: Optional[str] = Field(None, description="Extracted Manufacturer / Packer name and address.")
    country_of_origin: Optional[str] = Field(None, description="Extracted Country of Origin text.")
    generic_name: Optional[str] = Field(None, description="Extracted generic commodity name.")

SYSTEM_INSTRUCTION = """You are a senior regulatory compliance auditor specializing in India's Legal Metrology Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011 (as amended through 2026).

Transcribe the package label text completely and extract all statutory declaration values verbatim.
"""

class GeminiComplianceEngine:
    """Multimodal Legal Metrology compliance auditor using Google Gemini with fallback to local rule engine."""

    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None
        self.rule_engine = StatutoryRuleEngine()

        if self.api_key and self.api_key.strip() and self.api_key != "your_gemini_api_key_here":
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def _get_client(self) -> Optional[genai.Client]:
        """Retrieves or re-initializes client with API key validation."""
        load_dotenv(override=True)
        key = os.getenv("GEMINI_API_KEY")
        if not key or not key.strip() or key == "your_gemini_api_key_here":
            return None
        if self.client is None or self.api_key != key:
            self.api_key = key
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                return None
        return self.client

    def evaluate_image(
        self,
        image_input: Union[Image.Image, bytes],
        physical_result: Optional[PhysicalVerificationResult] = None,
    ) -> ComplianceResponse:
        """Runs multimodal visual audit or fallback statutory evaluation."""
        # Convert bytes to PIL Image if needed
        if isinstance(image_input, (bytes, bytearray)):
            pil_image = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            pil_image = image_input
        else:
            raise TypeError("image_input must be a PIL.Image.Image or bytes object.")

        if pil_image.mode not in ("RGB", "L"):
            pil_image = pil_image.convert("RGB")

        client = self._get_client()

        # If client is configured, run Gemini Multimodal inference
        if client:
            try:
                prompt = (
                    "Transcribe all text on this packaged commodity label verbatim, including "
                    "MRP (with tax clause), Net Quantity, Date of Packing/Mfg, Consumer Care, "
                    "Manufacturer details, Country of Origin, Generic Name, and Unit Sale Price."
                )

                config = types.GenerateContentConfig(
                    system_instruction=SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=GeminiTranscriptionSchema,
                    temperature=0.1,
                    thinking_config=types.ThinkingConfig(thinking_budget=0),
                )

                response = client.models.generate_content(
                    model=self.model_name,
                    contents=[pil_image, prompt],
                    config=config,
                )

                if response.text:
                    parsed_json = json.loads(response.text)
                    raw_text = parsed_json.get("raw_text", "")
                    
                    # Also append extracted fields to raw_text if not already present
                    fields_text = "\n".join([f"{k}: {v}" for k, v in parsed_json.items() if v and k != "raw_text"])
                    combined_text = f"{raw_text}\n{fields_text}".strip()

                    from compliance_engine import ComplianceEngine
                    local_engine = ComplianceEngine()
                    return local_engine.evaluate_compliance(combined_text, physical_result=physical_result)
            except Exception as e:
                # Log and fallback to local OCR / rule engine
                print(f"[GeminiComplianceEngine] Gemini API call fallback: {e}")

        # Fallback: Local OCR / Heuristic Extraction
        try:
            if not hasattr(self, "_ocr_engine") or self._ocr_engine is None:
                from ocr_engine import OCREngine
                self._ocr_engine = OCREngine()
            buf = io.BytesIO()
            pil_image.save(buf, format="PNG")
            raw_text, _ = self._ocr_engine.extract_text(buf.getvalue())
        except Exception as ocr_err:
            print(f"[GeminiComplianceEngine] OCR extraction fallback: {ocr_err}")
            raw_text = "PRE-PACKAGED COMMODITY LABEL (Optical fallback parsing)"

        from compliance_engine import ComplianceEngine
        local_engine = ComplianceEngine()
        return local_engine.evaluate_compliance(raw_text, physical_result=physical_result)
