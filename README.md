# ⚖️ Legal Metrology Compliance Scanner (Gemini Multimodal Vision)

An enterprise-grade, multimodal AI compliance validation service for packaged commodity labels under the **Legal Metrology (Packaged Commodities) Rules, 2011** (India).

Powered by **Google Gemini 2.5 Flash** (`google-genai` SDK), **FastAPI**, **Pydantic v2**, and **Streamlit**.

---

## 🌟 Key Upgrades & Features

- 🧠 **Multimodal Vision Intelligence:** Replaced brittle OCR and regex heuristics with Google's **Gemini 2.5 Flash** for native document understanding, layout analysis, and high-accuracy text extraction.
- 📐 **Direct Structured Output:** Utilizes `google-genai` structured outputs with Pydantic schemas (`ComplianceResponse`), guaranteeing type-safe, validated JSON responses.
- 📜 **Statutory Regulatory Engine:** Comprehensive audit against all 6 statutory declarations required under Indian Legal Metrology Rules:
  1. **Maximum Retail Price (MRP):** Verifies price in ₹/Rs. and strictly enforces mandatory *"inclusive of all taxes"* suffix.
  2. **Net Quantity / Metric Weight:** Enforces standard SI metric units (`g`, `kg`, `ml`, `l`, `units`) and automatically flags deprecated non-standard units (e.g., `gm`, `gms`, `kilos`) as non-compliant under Rule 13.
  3. **Date of Packing / Manufacture:** Identifies packaging/manufacturing/import month and year (`MM/YYYY`).
  4. **Consumer Care & Redressal:** Verifies email address, telephone/toll-free helpline number, or grievance contact address.
  5. **Manufacturer / Packer / Importer Details:** Identifies full entity name and registered physical address with qualifiers (`Mfg by`, `Packed by`, `Marketed by`).
  6. **Country of Origin:** Verifies mandatory geographic origin statement (`Made in India`, `Country of Origin`).
- ⚡ **High Performance & Lightweight:** Eliminated heavy local dependencies (OpenCV, PyTorch, EasyOCR) in favor of high-speed cloud multimodal inference via PIL and the `google-genai` client.
- 🖥️ **Interactive Web Dashboard:** Streamlit UI supporting both file uploads and live camera capture with visual compliance cards, score gauges, and raw text transcripts.

---

## 🏗️ Project Architecture

```plaintext
legal_metrology_scanner/
├── main.py                     # FastAPI REST API & endpoints
├── gemini_compliance_engine.py # Gemini 2.5 Flash multimodal audit engine
├── schemas.py                  # Pydantic v2 data models & validation
├── app.py                      # Streamlit interactive UI dashboard
├── requirements.txt            # Streamlined Python dependencies
├── .env.example                # Environment variables template
├── .env                        # Local configuration file (contains GEMINI_API_KEY)
└── README.md                   # Project documentation & runbook
```

---

## 🚀 Quickstart & Setup

### 1. Prerequisites
- Python 3.10+ (Python 3.10 – 3.14 supported)
- A Google Gemini API Key (Get a free API key at [Google AI Studio](https://aistudio.google.com/))

### 2. Clone & Activate Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` and configure your `GEMINI_API_KEY`:
```bash
cp .env.example .env
```
Edit `.env`:
```env
GEMINI_API_KEY=AIzaSy...your_actual_api_key_here
```

---

## 🖥️ Running the Application

### Option 1: Start the Full Stack (Two Terminals)

**Terminal 1 — Start the FastAPI Backend:**
```bash
python main.py
```
*API will run at:* `http://localhost:8000`  
*Swagger Documentation:* `http://localhost:8000/docs`

**Terminal 2 — Start the Streamlit Dashboard:**
```bash
streamlit run app.py
```
*Dashboard will open at:* `http://localhost:8501`

---

## 📡 API Reference

### `POST /scan-label`
Upload a packaged commodity label image and receive an automated compliance audit.

- **Endpoint:** `http://localhost:8000/scan-label`
- **Method:** `POST`
- **Content-Type:** `multipart/form-data`
- **Accepted Formats:** `image/jpeg`, `image/png`, `image/jpg`, `image/webp`

#### Example `curl` Request:
```bash
curl -X POST "http://localhost:8000/scan-label" \
  -F "file=@sample_packaged_label.jpg"
```

#### Example Response Body:
```json
{
  "status": "NON_COMPLIANT",
  "overall_compliance_score": 66.67,
  "violations_count": 2,
  "declarations": {
    "mrp": {
      "detected": true,
      "value": "MRP Rs. 45.00 (inclusive of all taxes)",
      "compliant": true,
      "remarks": "Valid MRP and mandatory 'inclusive of all taxes' declaration found."
    },
    "net_quantity": {
      "detected": true,
      "value": "500 gm",
      "compliant": false,
      "remarks": "Non-standard unit abbreviation detected. Use standard 'g'/'kg' instead of 'gm'/'gms' as mandated by Rule 13."
    },
    "date_of_packing": {
      "detected": true,
      "value": "08/2026",
      "compliant": true,
      "remarks": "Month and year of manufacture/packing detected."
    },
    "consumer_care": {
      "detected": true,
      "value": "Email: care@brand.com | Helpline: 1800-209-6929",
      "compliant": true,
      "remarks": "Valid consumer grievance contact channels verified."
    },
    "manufacturer_details": {
      "detected": true,
      "value": "Manufactured by ABC FMCG Ltd, Plot 14, Industrial Area, Mumbai 400001",
      "compliant": true,
      "remarks": "Complete manufacturer identity and registered address detected."
    },
    "country_of_origin": {
      "detected": false,
      "value": null,
      "compliant": false,
      "remarks": "Country of origin not declared."
    }
  },
  "raw_text": "ABC FMCG LTD ... MRP Rs. 45.00 (inclusive of all taxes) ... Net Qty: 500 gm ..."
}
```

---

## 🧪 Statutory Verification Checklist

| Rule # | Declaration Field | Compliant Example | Non-Compliant Trigger Example |
|:---|:---|:---|:---|
| 1 | **MRP** | `MRP ₹50.00 (incl. of all taxes)` | `MRP ₹50.00` *(missing tax clause)* |
| 2 | **Net Quantity** | `Net Wt: 500 g` or `Net Vol: 1 L` | `500 gm` or `500 gms` *(Rule 13 violation)* |
| 3 | **Date of Packing** | `Pkd: 09/2026` or `Mfg: Sept 2026` | Missing date or vague batch without date |
| 4 | **Consumer Care** | `care@example.com / 1800-111-222` | No grievance email or phone |
| 5 | **Manufacturer** | `Mfg by: XYZ Ltd, Industrial Area` | Missing registered address / entity name |
| 6 | **Country of Origin** | `Made in India` | Omitted origin declaration |

---

## 🛡️ Error Handling
- **Missing API Key:** Returns HTTP 500 with actionable error instructing the user to configure `GEMINI_API_KEY` in `.env`.
- **Invalid File Type:** Returns HTTP 400 when non-image formats are submitted.
- **Backend Disconnect:** Streamlit UI automatically alerts if the FastAPI server is unreachable.
