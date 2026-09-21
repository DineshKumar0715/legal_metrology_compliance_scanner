# ⚖️ Legal Metrology Scanner

An end-to-end, production-grade statutory compliance auditor for packaged commodity labels under the **Legal Metrology (Packaged Commodities) Rules, 2011** and the **Legal Metrology Act, 2009**.

---

## 📌 Architecture Overview

```
legal_metrology_scanner/
├── main.py               # FastAPI backend with /scan-label endpoint & CORS
├── ocr_engine.py         # EasyOCR with bilateral filtering & adaptive thresholding
├── compliance_engine.py  # Statutory rule engine auditing 6 Rule 6 declarations
├── schemas.py            # Pydantic v2 data models
├── app.py                # Streamlit interactive UI dashboard with camera & samples
├── requirements.txt      # Pinned dependency requirements
└── README.md             # Project documentation
```

---

## 🏛️ Statutory Declarations Audited (Rule 6)

1. **Maximum Retail Price (MRP) & Tax Declaration** (`Rule 6(1)(e)`):
   - Audits presence of retail sale price in Indian Rupees (`₹`, `Rs.`, `INR`).
   - Mandates explicit declaration: `"inclusive of all taxes"` or `"incl. of all taxes"`.
   - Flags non-compliance if tax phrase is missing or if dual pricing is detected.

2. **Net Quantity & Metric Unit Compliance** (`Rule 6(1)(c)`):
   - Audits net weight, volume, or count declared in standard SI metric units (`g`, `kg`, `ml`, `l`, `N`, `units`).
   - Flags prohibited abbreviations such as `gm`, `gms`, `kgs`, `ltr`, `ltrs`, `mls` as strict violations.

3. **Date of Packing / Manufacture** (`Rule 6(1)(d)`):
   - Audits presence of month and year of manufacture/packing (e.g. `MM/YYYY`, `MM/YY`, or `Month YYYY`).

4. **Consumer Care & Grievance Redressal** (`Rule 6(1)(n)`):
   - Audits presence of grievance redressal channel including contact telephone number / toll-free helpline and email address.

5. **Name and Address of Manufacturer / Packer / Importer** (`Rule 6(1)(a)`):
   - Audits complete postal address and identity prefixed by `Mfg by`, `Manufactured by`, `Packed by`, `Marketed by`, or `Imported by`.

6. **Country of Origin** (`Rule 6(1)(m)`):
   - Mandates declaration of the country of manufacture/origin for domestic and imported goods (e.g. `"Country of Origin: India"` or `"Made in India"`).

---

## 🚀 Quickstart Guide

### 1. Prerequisites & Virtual Environment

```powershell
# Create a virtual environment with Python 3.12+
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch FastAPI Backend

```powershell
# Start Uvicorn ASGI server on port 8000
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

- Health Status: [http://localhost:8000/](http://localhost:8000/)
- Interactive OpenAPI Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### 3. Launch Streamlit Frontend Dashboard

```powershell
# In a separate terminal (with venv activated)
streamlit run app.py --server.port 8501
```

- Open Dashboard: [http://localhost:8501](http://localhost:8501)

---

## 🔌 API Documentation

### `POST /scan-label`

Upload a packaged commodity label image for compliance auditing.

**Request:**
- `file`: Multipart image file (`image/jpeg`, `image/png`, `image/webp`).

**Response Schema (`ComplianceResponse`):**
```json
{
  "status": "COMPLIANT",
  "overall_compliance_score": 100.0,
  "violations_count": 0,
  "declarations": {
    "mrp": {
      "detected": true,
      "value": "MRP: Rs. 95.00 (incl. of all taxes)",
      "compliant": true,
      "remarks": "Compliant: MRP declared with mandatory 'inclusive of all taxes' statement under Rule 6(1)(e)."
    },
    "net_quantity": {
      "detected": true,
      "value": "500 g",
      "compliant": true,
      "remarks": "Compliant: Net quantity '500 g' declared in standard metric units per Rule 6(1)(c)."
    },
    "date_of_packing": {
      "detected": true,
      "value": "Date of Mfg: 05/2024",
      "compliant": true,
      "remarks": "Compliant: Month and year of manufacture/packing declared in prescribed format under Rule 6(1)(d)."
    },
    "consumer_care": {
      "detected": true,
      "value": "Customer Care | Tel: 1800-222-3333 | Email: care@goldenbake.com",
      "compliant": true,
      "remarks": "Compliant: Consumer Care contact channels (Helpline/Email) declared under Rule 6(1)(n)."
    },
    "manufacturer_details": {
      "detected": true,
      "value": "Mfd & Pkd By: Golden Bake Foods Pvt Ltd, Industrial Area, Sector 4, Pune 411018",
      "compliant": true,
      "remarks": "Compliant: Name and address of Manufacturer/Packer/Marketer declared under Rule 6(1)(a)."
    },
    "country_of_origin": {
      "detected": true,
      "value": "Country of Origin: India",
      "compliant": true,
      "remarks": "Compliant: Country of Origin explicitly declared on label under Rule 6(1)(m)."
    }
  },
  "raw_text": "PREMIUM PACKAGED COMMODITY LABEL\nCOMMODITY: Nutri Delight Whole Wheat Biscuits\n..."
}
```

---

## 🧪 Self-Test & Automated Verification

Run automated test suite:
```powershell
pytest tests/ -v
```
