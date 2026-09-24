import os
import io
import json
from typing import Union
from PIL import Image
from dotenv import load_dotenv
from google import genai
from google.genai import types

from schemas import ComplianceResponse, ExtractedField, GeminiComplianceSchema

# Load environment variables from .env
load_dotenv()

SYSTEM_INSTRUCTION = """You are a senior regulatory compliance auditor specializing in India's Legal Metrology Act, 2009 and the Legal Metrology (Packaged Commodities) Rules, 2011 (as amended).

Your mission is to perform a rigorous, multimodal visual audit of the provided packaged commodity label image.

Follow these statutory guidelines strictly:

1. FULL TRANSCRIPTION (`raw_text`):
   Transcribe all readable text visible on the package label verbatim, including headers, small print, tables, barcodes, and contact details.

2. STATUTORY DECLARATION AUDIT (`declarations` dictionary):
   Evaluate the presence and legal correctness of exactly these 6 mandatory declarations:

   a. "mrp" (Maximum Retail Price):
      - Must display currency (₹, Rs., or INR), numerical price, and the mandatory phrase "inclusive of all taxes" or "incl. of all taxes".
      - If price is found but the tax clause is missing, set `detected=True`, `compliant=False`, and note the missing tax clause in `remarks`.
      - If price is missing entirely, set `detected=False`, `compliant=False`, `remarks="MRP declaration not detected on package."`.

   b. "net_quantity" (Net Quantity / Weight / Volume / Count):
      - Must state quantity using standard metric SI units: 'g', 'kg', 'ml', 'l', 'ltr', 'N', 'U', or 'units'.
      - CRITICAL STATUTORY RULE: If deprecated or non-standard unit abbreviations such as 'gm', 'gms', or 'kilos' are used, set `detected=True`, `compliant=False`, and explicitly state in remarks: "Non-standard unit abbreviation detected. Use standard 'g'/'kg' instead of 'gm'/'gms' as mandated by Rule 13."
      - If net quantity is missing, set `detected=False`, `compliant=False`, `remarks="Net quantity declaration not detected."`.

   c. "date_of_packing" (Date of Packing / Manufacture / Import):
      - Must state month and year (e.g., MM/YYYY, Month Year, or DD/MM/YYYY) preceded by 'Mfg Date', 'Pkd On', 'Date of Mfg', 'Date of Packing', or 'Month & Year'.
      - If missing or unreadable, set `detected=False`, `compliant=False`, `remarks="Month and Year of packing/manufacture not detected."`.

   d. "consumer_care" (Consumer Grievance Redressal / Care Details):
      - Must provide customer care contact information including an email address, telephone/toll-free helpline number, or grievance officer postal address.
      - If contact info is missing, set `detected=False`, `compliant=False`, `remarks="Consumer grievance redressal contact details missing."`.

   e. "manufacturer_details" (Name and Address of Manufacturer / Packer / Importer):
      - Must state the complete name and registered address of the manufacturer, packer, or importer preceded by qualifying words like 'Mfg by', 'Manufactured by', 'Packed by', 'Marketed by', or 'Imported by'.
      - If manufacturer/packer name or address is absent, set `detected=False`, `compliant=False`, `remarks="Name and address of Manufacturer/Packer/Importer not detected."`.

   f. "country_of_origin" (Country of Origin / Manufacturing Origin):
      - Mandatory declaration stating where the product was manufactured or assembled (e.g., 'Made in India', 'Country of Origin: India', 'Product of India').
      - If country of origin is not explicitly stated, set `detected=False`, `compliant=False`, `remarks="Country of origin not declared."`.

3. SCORING & SUMMARY:
   - `violations_count`: Total count of mandatory fields among the 6 where `compliant == False`.
   - `overall_compliance_score`: Percentage of compliant fields = (number of compliant fields / 6.0) * 100.0.
   - `status`: Exactly 'COMPLIANT' if `violations_count == 0`, otherwise 'NON_COMPLIANT'.

Ensure every mandatory field has an entry in `declarations` with keys: 'mrp', 'net_quantity', 'date_of_packing', 'consumer_care', 'manufacturer_details', and 'country_of_origin'.
"""

REQUIRED_FIELDS = (
    "mrp",
    "net_quantity",
    "date_of_packing",
    "consumer_care",
    "manufacturer_details",
    "country_of_origin",
)


class GeminiComplianceEngine:
    """Multimodal Legal Metrology compliance auditor using Google Gemini 2.5 Flash."""

    def __init__(self, api_key: Union[str, None] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name
        self.client = None

        if self.api_key and self.api_key.strip() and self.api_key != "your_gemini_api_key_here":
            self.client = genai.Client(api_key=self.api_key)

    def _get_client(self) -> genai.Client:
        """Retrieves or re-initializes client with API key validation."""
        load_dotenv(override=True)
        key = os.getenv("GEMINI_API_KEY")
        if not key or not key.strip() or key == "your_gemini_api_key_here":
            raise ValueError(
                "GEMINI_API_KEY is not configured. Please set a valid Gemini API Key in your .env file "
                "or as an environment variable (get one at https://aistudio.google.com/)."
            )
        if self.client is None or self.api_key != key:
            self.api_key = key
            self.client = genai.Client(api_key=self.api_key)
        return self.client

    def evaluate_image(self, image_input: Union[Image.Image, bytes]) -> ComplianceResponse:
        """Runs multimodal visual audit on a PIL Image or raw bytes."""
        client = self._get_client()

        # Convert bytes to PIL Image if needed
        if isinstance(image_input, (bytes, bytearray)):
            pil_image = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, Image.Image):
            pil_image = image_input
        else:
            raise TypeError("image_input must be a PIL.Image.Image or bytes object.")

        # Ensure image is in RGB format for processing
        if pil_image.mode not in ("RGB", "L"):
            pil_image = pil_image.convert("RGB")

        prompt = (
            "Perform a complete statutory compliance audit on this packaged commodity label "
            "under the Legal Metrology (Packaged Commodities) Rules, 2011. Transcribe the raw text "
            "and evaluate all 6 statutory declarations."
        )

        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            response_mime_type="application/json",
            response_schema=GeminiComplianceSchema,
            temperature=0.1,
            thinking_config=types.ThinkingConfig(thinking_budget=0),
        )

        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=[pil_image, prompt],
                config=config,
            )
        except Exception as err:
            raise RuntimeError(f"Gemini API inference failed: {str(err)}") from err

        raw_json_str = response.text
        if not raw_json_str:
            raise RuntimeError("Gemini returned an empty response. Please check image clarity.")

        # Parse with Pydantic using GeminiComplianceSchema
        try:
            parsed_gemini = GeminiComplianceSchema.model_validate_json(raw_json_str)
        except Exception:
            dict_data = json.loads(raw_json_str)
            parsed_gemini = GeminiComplianceSchema.model_validate(dict_data)

        # Convert DeclarationsContainer into a standard dictionary
        declarations_dict = {
            "mrp": parsed_gemini.declarations.mrp,
            "net_quantity": parsed_gemini.declarations.net_quantity,
            "date_of_packing": parsed_gemini.declarations.date_of_packing,
            "consumer_care": parsed_gemini.declarations.consumer_care,
            "manufacturer_details": parsed_gemini.declarations.manufacturer_details,
            "country_of_origin": parsed_gemini.declarations.country_of_origin,
        }

        # Post-process sanity check to guarantee all 6 required fields are populated & scores accurate
        for field_name in REQUIRED_FIELDS:
            if field_name not in declarations_dict or declarations_dict[field_name] is None:
                declarations_dict[field_name] = ExtractedField(
                    detected=False,
                    value=None,
                    compliant=False,
                    remarks=f"Declaration '{field_name}' not evaluated or detected.",
                )

        # Recalculate deterministic metrics
        total_rules = len(declarations_dict)
        passed_rules = sum(1 for f in declarations_dict.values() if f.compliant)
        violations = total_rules - passed_rules
        score = round((passed_rules / total_rules) * 100.0, 2)
        status = "COMPLIANT" if violations == 0 else "NON_COMPLIANT"

        return ComplianceResponse(
            status=status,
            overall_compliance_score=score,
            violations_count=violations,
            declarations=declarations_dict,
            raw_text=parsed_gemini.raw_text or "",
        )
