# ⚖️ VERITAS AI: Legal Metrology Compliance & Inspection Platform
### AI-Assisted Regulatory Enforcement System for Pre-Packaged Commodities
**Statutory Framework:** Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (Amended through 2026)  
**Problem Statement Code:** SIH26034 &bull; Directorate of Legal Metrology, Department of Consumer Affairs, Government of India

---

## 🌟 Executive Overview & Key Innovations

**VERITAS AI** is an enterprise-grade statutory compliance verification and enforcement platform built for Legal Metrology Officers, State Controllers, and Regulatory Inspectors. Moving far beyond simple optical character recognition (OCR), VERITAS provides a complete statutory compliance, visual inspection, physical deficit verification, and case management pipeline.

### Core Capabilities:
1. **3-Tier Decision Engine:**
   - `COMPLIANT`: All observable statutory requirements satisfied **and** physical content weighed within statutory tolerance.
   - `NON-COMPLIANT`: Detectable packaging violation found **or** net content deficit exceeds statutory Maximum Permissible Error (MPE).
   - `PHYSICAL_VERIFICATION_REQUIRED`: All visible packaging declarations pass statutory review, but physical net contents await on-site verification.
2. **Two-Level Inspection Workflow (Resolving the Mentor's Challenge):**
   - **Level 1 (Digital/Vision Audit):** High-speed multimodal perception extracting 10+ statutory declarations and measuring character dimensions.
   - **Level 2 (Physical Verification):** Integrates measured gross/net weights, computes net shortfall, and strictly enforces Maximum Permissible Error (MPE) thresholds under the First Schedule of PCR 2011.
3. **Statutory Rule Engine (Base 2011 + Amendments up to 2026):**
   - Rule 6(1)(a)-(g): Mandatory declarations (MRP with tax clause, Net Qty in SI units, Date of Mfg, Consumer Care, Manufacturer, Country of Origin, Generic Name).
   - Rule 6(1)(h) (2021 Amendment): Unit Sale Price (USP in ₹/g or ₹/kg).
   - Rule 6(10) (2026 Amendment): E-Commerce mandatory searchable & sortable Country of Origin filter.
   - Rule 8 & 9: Principal Display Panel (PDP) placement and minimum font height statutory table.
   - Rule 18: Prohibition against dual pricing across multi-panel viewpoints.
4. **Multi-Input Ingestion & Cross-Source Consistency:**
   - Single packaging label scan (Upload / Live Camera).
   - Multi-view panel scan (Front + Back + Sides) to detect cross-panel contradictions.
   - E-Commerce listing vs Physical package cross-check (detects online price inflation and origin misrepresentation).
5. **Automated Visual Evidence Annotation:**
   - Crops offending bounding regions with high-contrast red warning borders and stamps statutory clause tags.
6. **Official Government PDF Certificate & Legal Notice Engine:**
   - Uses `reportlab` to generate publication-grade PDF inspection reports with official Directorate formatting, violation tables, physical audit logs, and digital seal blocks.
7. **Enforcement Case Repository & Analytics Dashboard:**
   - Central SQLite / SQLAlchemy database tracking cases across districts (Salem, Pune, Mumbai, etc.).
   - Executive compliance analytics, violation category breakdowns, and district risk heatmaps.

---

## 🏗️ System Architecture

```
                 PACKAGED COMMODITY INGESTION
          (Single Label / Multi-Panel / E-Commerce Listing)
                                │
                                ▼
                 ┌───────────────────────────────┐
                 │    Multimodal Vision Core     │
                 │   Google Gemini 2.5 Flash /   │
                 │   OpenCV + EasyOCR Fallback   │
                 └──────────────┬────────────────┘
                                │ Optical Transcription & Bounding Regions
                                ▼
                 ┌───────────────────────────────┐
                 │     Statutory Rule Engine     │
                 │   (Rules 6, 7, 8, 9, 11, 13,  │
                 │   2021 USP, 2026 E-Comm Amd)  │
                 └──────────────┬────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
  Statutory Matrix       Font/Layout Check      Cross-Panel & E-Comm
  (10+ Declarations)     (Rule 9 Height mm)      Conflict Detection
         │                      │                      │
         └──────────────────────┼──────────────────────┘
                                │
                                ▼
                 ┌───────────────────────────────┐
                 │      3-Tier Decision Engine   │
                 └──────────────┬────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
     COMPLIANT            NON-COMPLIANT         PHYSICAL VERIFICATION
 (All visible passed &  (Detectable statutory        REQUIRED
 physical verified)     infraction / deficit)   (Visual passes; physical
                                                seal/weight unverified)
                                │
                                ▼
                 ┌───────────────────────────────┐
                 │    Level 2 Physical Engine    │
                 │    Weighed Net Content vs     │
                 │    MPE Limits (First Schedule)│
                 └──────────────┬────────────────┘
                                │
         ┌──────────────────────┼──────────────────────┐
         ▼                      ▼                      ▼
  Official PDF Notices   Case Repository DB    Executive Dashboard
  (ReportLab Govt Std)   (Search & Audit Logs) (District Analytics)
```

---

## 🚀 Quickstart & Setup

### 1. Install Dependencies
```bash
python -m pip install -r requirements.txt
```

### 2. Configure Environment Variables
Create or update `.env`:
```env
GEMINI_API_KEY=your_gemini_api_key_here
API_BASE_URL=http://localhost:8000
```
*(Note: If `GEMINI_API_KEY` is not provided, the platform automatically falls back to the embedded local OCR and statutory rule engine for 100% offline functionality).*

### 3. Run the Verification Test Suite
```bash
# Run 24 unit tests
python -m pytest tests/

# Run complete End-to-End System Verification (all 10 capability modules)
python verify_system.py
```

### 4. Start the Application Full-Stack

**Terminal 1 — Start the FastAPI Backend:**
```bash
python main.py
```
*Backend API:* `http://localhost:8000`  
*Interactive Swagger API Docs:* `http://localhost:8000/docs`

**Terminal 2 — Start the Enterprise Streamlit Dashboard:**
```bash
streamlit run app.py
```
*Enforcement Console:* `http://localhost:8501`

---

## 📜 Statutory Rules Reference Table

| Rule | Mandatory Declaration | Standard Required by Law |
| :--- | :--- | :--- |
| **Rule 6(1)(a)** | Manufacturer / Packer Identity | Complete name and registered physical address of Manufacturer, Packer, or Importer. |
| **Rule 6(1)(b)** | Generic Commodity Name | Generic or common name of the pre-packaged commodity. |
| **Rule 6(1)(c) & Rule 13** | Net Quantity & Standard Units | Quantity in standard SI symbols (`g`, `kg`, `ml`, `l`, `N`). Prohibits deprecated abbreviations (`gm`, `gms`). |
| **Rule 6(1)(d)** | Date of Packing / Manufacture | Month and Year of packing, manufacture, or import (`MM/YYYY`). |
| **Rule 6(1)(e) & Rule 8** | Maximum Retail Price (MRP) | Retail price with mandatory suffix *"inclusive of all taxes"*. |
| **Rule 6(1)(f)** | Consumer Grievance Care | Name, address, telephone helpline, and email for grievance redressal. |
| **Rule 6(1)(g)** | Country of Origin | Explicit country of origin declaration on packaging for domestic and imported goods. |
| **Rule 6(1)(h) (2021 Amd)** | Unit Sale Price (USP) | Mandatory unit sale price breakdown in `₹/g`, `₹/ml`, `₹/kg`, or `₹/L`. |
| **Rule 6(10) (2026 Amd)** | E-Commerce Origin Searchability | Searchable and sortable Country of Origin filter on e-commerce product listings. |
| **Rule 11 / First Schedule** | Maximum Permissible Error (MPE) | Restricts allowable net quantity shortfall within statutory tolerance limits. |
| **Rule 18** | Dual Pricing Prohibition | Prohibits declaring different MRPs for identical commodities across panels. |

---

## 👥 Default Demo Credentials

| Role | Username | Password | Jurisdiction | Badge # |
| :--- | :--- | :--- | :--- | :--- |
| **Inspector** | `inspector` | `inspector123` | Salem District | LM-INSP-401 |
| **Supervisor / Controller** | `supervisor` | `supervisor123` | State Enforcement HQ | LM-SUP-102 |
| **Directorate Admin** | `admin` | `admin123` | Central Directorate | LM-DIR-001 |
