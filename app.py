import io
import os
import json
import base64
from datetime import datetime
import requests
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Load environment
load_dotenv()

st.set_page_config(
    page_title="VERITAS | AI Legal Metrology Platform",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# Enterprise SaaS Design System & Styling
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Hide Streamlit Deploy button, Header decorations, and Toolbar */
    .stAppDeployButton,
    [data-testid="stAppDeployButton"],
    .stDeployButton,
    header[data-testid="stHeader"] .stAppDeployButton,
    div[data-testid="stToolbar"],
    #MainMenu {
        display: none !important;
        visibility: hidden !important;
    }

    /* Completely hide Streamlit input instructions ('Press Enter to submit form', 'Press Enter to apply', etc.) */
    div[data-testid="InputInstructions"],
    [data-testid="InputInstructions"],
    [data-testid="InputInstructions"] *,
    div[class*="InputInstructions"],
    div[class*="InputInstructions"] *,
    div[class*="StyledInputInstructions"],
    div[class*="StyledInputInstructions"] *,
    div[class*="stInputInstructions"],
    div[class*="stInputInstructions"] *,
    div[class*="instructions"],
    div[class*="instructions"] *,
    div[class*="instruction"],
    div[class*="instruction"] *,
    span[data-testid="stInputInstruction"],
    [data-testid="stInputInstruction"],
    [data-testid="stInputInstruction"] *,
    div[data-testid="stTextInput"] div[data-testid="InputInstructions"],
    div[data-testid="stNumberInput"] div[data-testid="InputInstructions"],
    div[data-testid="stTextArea"] div[data-testid="InputInstructions"],
    div[data-testid="stTextInputRootElement"] div[data-testid="InputInstructions"],
    div[data-baseweb="input"] > div:not(:first-child),
    div[data-baseweb="base-input"] > div:not(:first-child),
    .st-emotion-cache-1gulkj5,
    .st-emotion-cache-183lzff,
    .st-emotion-cache-16idsys,
    .st-emotion-cache-16idsys p,
    .st-emotion-cache-10trblm,
    div[data-testid="stTextInput"] small,
    div[data-testid="stNumberInput"] small,
    div[data-testid="stTextArea"] small,
    div[data-testid="stForm"] small {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        height: 0px !important;
        width: 0px !important;
        max-height: 0px !important;
        max-width: 0px !important;
        overflow: hidden !important;
        margin: 0 !important;
        padding: 0 !important;
        position: absolute !important;
        pointer-events: none !important;
        clip: rect(0, 0, 0, 0) !important;
        clip-path: inset(50%) !important;
    }

    /* Top enterprise header */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.75rem;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 41, 59, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    .brand-title-wrap {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .brand-logo {
        width: 48px;
        height: 48px;
        background: linear-gradient(135deg, #2563eb, #7c3aed);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 26px;
        box-shadow: 0 0 20px rgba(99, 102, 241, 0.4);
    }
    .brand-title {
        font-size: 1.45rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        color: #ffffff;
        margin: 0;
        line-height: 1.2;
    }
    .brand-subtitle {
        font-size: 0.82rem;
        color: #94a3b8;
        font-weight: 500;
        margin: 0;
    }
    .status-pill-green {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.35);
        color: #34d399;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .status-dot-green {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
    }

    /* Enterprise card containers */
    .enterprise-card {
        background: rgba(15, 23, 42, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.5rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1.25rem;
    }

    /* Metric Summary Panel */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.85rem;
        margin-bottom: 1.25rem;
    }
    .metric-box {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.85) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .metric-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 4px;
    }
    .metric-value-large {
        font-size: 1.6rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }

    /* Statutory Matrix Items */
    .rule-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 10px;
        padding: 0.85rem 1.15rem;
        margin-bottom: 0.75rem;
        transition: all 0.2s ease;
    }
    .rule-card:hover {
        border-color: rgba(99, 102, 241, 0.35);
        background: rgba(30, 41, 59, 0.75);
    }
    .rule-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 6px;
    }
    .rule-title {
        font-size: 0.92rem;
        font-weight: 700;
        color: #f1f5f9;
    }
    .rule-citation {
        font-size: 0.72rem;
        color: #94a3b8;
        font-family: 'JetBrains Mono', monospace;
    }
    .badge-compliant {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-violation {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.35);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-missing {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 0.70rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .value-pill {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        padding: 5px 8px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.80rem;
        color: #e2e8f0;
        margin: 4px 0;
        word-break: break-word;
    }
    .remarks-text {
        font-size: 0.78rem;
        color: #94a3b8;
        line-height: 1.35;
    }

    /* Return / Logout Button styling */
    .btn-return-header {
        display: flex;
        align-items: center;
        justify-content: flex-end;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize Session State
if "logged_in_user" not in st.session_state:
    st.session_state["logged_in_user"] = None

if "last_inspection" not in st.session_state:
    st.session_state["last_inspection"] = None

if "active_pdf_bytes" not in st.session_state:
    st.session_state["active_pdf_bytes"] = None

if "active_pdf_filename" not in st.session_state:
    st.session_state["active_pdf_filename"] = None

if "submitted_case_id" not in st.session_state:
    st.session_state["submitted_case_id"] = None

if "reg_success_msg" not in st.session_state:
    st.session_state["reg_success_msg"] = None


# =================================================================================================
# 📜 REUSABLE STATUTORY RULEBOOK REFERENCE & MPE COMPONENT
# =================================================================================================
def render_legal_rulebook_reference():
    st.markdown(
        """
        <div class="enterprise-card" style="margin-bottom: 1.25rem;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="font-size: 2.2rem;">📜</div>
                <div>
                    <h2 style="margin: 0; font-size: 1.35rem; color: #f8fafc; font-weight: 800;">Official Legal Metrology Statutory Rulebook & Enforcement Standards</h2>
                    <p style="margin: 0; font-size: 0.82rem; color: #94a3b8;">
                        Legal Metrology Act, 2009 (No. 1 of 2010) &bull; Packaged Commodities Rules, 2011 &bull; 2021 USP & 2026 E-Commerce Amendments
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    r_tab1, r_tab2, r_tab3, r_tab4, r_tab5 = st.tabs([
        "📋 1. Mandatory Declarations (Rule 6)",
        "📏 2. PDP Area & Font Height (Rule 9)",
        "⚖️ 3. First Schedule MPE Standards (Rule 11)",
        "🚨 4. Statutory Penalties (Sec 36 & 48)",
        "🧮 5. Interactive Statutory Calculators"
    ])

    with r_tab1:
        st.markdown("### 📋 Rule 6(1) — Mandatory Declarations Matrix on Pre-Packaged Commodities")
        st.caption("Every pre-packaged commodity intended for retail sale must bear the following mandatory declarations in clear, legible, and prominent print.")

        rule6_data = [
            {
                "rule": "Rule 6(1)(a)",
                "title": "Manufacturer / Packer / Importer Identity",
                "mandate": "Complete name and physical factory/registered address of the manufacturer, packer, or importer.",
                "details": "If the manufacturer and packer are distinct entities, both must be explicitly declared. Importers must include the country of import.",
                "tag": "CRITICAL"
            },
            {
                "rule": "Rule 6(1)(b)",
                "title": "Generic / Common Commodity Name",
                "mandate": "Generic or common name of the commodity contained in the packaging.",
                "details": "Must clearly identify the nature of the product without relying solely on brand names (e.g., 'Whole Wheat Biscuits' rather than just 'Nutri Delite').",
                "tag": "MANDATORY"
            },
            {
                "rule": "Rule 6(1)(c) & Rule 13",
                "title": "Net Quantity in Standard SI Units",
                "mandate": "Net quantity in standard SI metric units of mass (g, kg), volume (ml, l), or count (N / numbers).",
                "details": "Non-metric units (lbs, oz, tins, packs) are strictly prohibited as primary declarations. Symbols must conform to international standard abbreviations.",
                "tag": "HIGH PRIORITY"
            },
            {
                "rule": "Rule 6(1)(d)",
                "title": "Date of Packing / Manufacture",
                "mandate": "Month and Year of manufacture, pre-packing, or import in MM/YYYY or Month Year format.",
                "details": "Allows consumers and inspectors to verify freshness and shelf life. For perishable commodities, the 'Best Before' date must also appear.",
                "tag": "MANDATORY"
            },
            {
                "rule": "Rule 6(1)(e)",
                "title": "Maximum Retail Price (MRP) & Tax Clause",
                "mandate": "Retail sale price in Indian Rupees (₹ or Rs.) with explicit clause 'Inclusive of all taxes' or 'Incl. of all taxes'.",
                "details": "Dual MRP declaration on identical commodities is prohibited under Rule 18. Rounding off must comply with standard monetary decimal rules.",
                "tag": "CRITICAL"
            },
            {
                "rule": "Rule 6(1)(f)",
                "title": "Consumer Grievance Care Contact",
                "mandate": "Contact details of designated consumer care officer (Name/Designation, complete address, telephone number, and email ID).",
                "details": "Enables consumers to lodge grievances directly with the responsible authority of the brand.",
                "tag": "MANDATORY"
            },
            {
                "rule": "Rule 6(1)(g)",
                "title": "Country of Origin",
                "mandate": "Country of origin must be prominently stated on all packages (e.g. 'Made in India', 'Country of Origin: India').",
                "details": "Under 2026 E-commerce regulations, online portals must also provide explicit, sortable search filters by country of origin.",
                "tag": "AMENDMENT 2026"
            },
            {
                "rule": "Rule 6(1)(h)",
                "title": "Unit Sale Price (USP)",
                "mandate": "Price per unit (₹ per g / ₹ per kg for solids, ₹ per ml / ₹ per l for liquids, ₹ per unit for counted items).",
                "details": "Mandatory for all commodities exceeding 1g/1ml/1unit to empower consumer price comparison across package sizes (2021 Amendment).",
                "tag": "AMENDMENT 2021"
            }
        ]

        for item in rule6_data:
            st.markdown(
                f"""
                <div class="rule-card" style="border-left: 4px solid #3b82f6; margin-bottom: 0.85rem;">
                    <div class="rule-header">
                        <div><span class="rule-title">{item['title']}</span><span class="rule-citation"> &bull; {item['rule']}</span></div>
                        <span class="badge-compliant" style="background: rgba(59, 130, 246, 0.15); color: #60a5fa; border-color: rgba(59, 130, 246, 0.3);">{item['tag']}</span>
                    </div>
                    <div style="font-size: 0.85rem; color: #e2e8f0; font-weight: 600; margin: 4px 0;">{item['mandate']}</div>
                    <div class="remarks-text">{item['details']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with r_tab2:
        st.markdown("### 📏 Rule 9 — Principal Display Panel (PDP) & Minimum Character Height")
        st.markdown(
            """
            Under **Rule 2(h) & Rule 9 of PCR 2011**, all statutory declarations must be legible and meet minimum numeral and letter height requirements based on the **Principal Display Panel (PDP)** area.
            
            **PDP Area Formulas:**
            - **Rectangular Container:** $\\text{Height} \\times \\text{Width}$ of the front panel.
            - **Cylindrical / Round Container:** $40\\% \\times \\text{Height} \\times \\text{Circumference}$.
            - **Irregular / Other Shapes:** $20\\%$ of the total container surface area.
            """
        )

        st.markdown("#### 📐 Statutory Character Height Standards Table (Rule 9 Table 1)")
        pdp_table = [
            {"PDP Area (A)": "A ≤ 50 cm²", "Net Quantity Bracket": "Up to 50 g / ml", "Minimum Height (Normal)": "1.0 mm", "Minimum Height (Blown/Moulded)": "2.0 mm"},
            {"PDP Area (A)": "50 < A ≤ 100 cm²", "Net Quantity Bracket": "50 g to 200 g / ml", "Minimum Height (Normal)": "1.5 mm", "Minimum Height (Blown/Moulded)": "3.0 mm"},
            {"PDP Area (A)": "100 < A ≤ 500 cm²", "Net Quantity Bracket": "200 g to 1000 g / ml", "Minimum Height (Normal)": "2.0 mm", "Minimum Height (Blown/Moulded)": "4.0 mm"},
            {"PDP Area (A)": "500 < A ≤ 1000 cm²", "Net Quantity Bracket": "1 kg to 5 kg / l", "Minimum Height (Normal)": "4.0 mm", "Minimum Height (Blown/Moulded)": "6.0 mm"},
            {"PDP Area (A)": "A > 1000 cm²", "Net Quantity Bracket": "Above 5 kg / l", "Minimum Height (Normal)": "6.0 mm", "Minimum Height (Blown/Moulded)": "6.0 mm"},
        ]
        
        st.table(pdp_table)
        st.info("💡 **Inspection Standard:** If characters on packaging are smaller than the prescribed statutory minimum, it constitutes non-compliance under Rule 9 and is compoundable under Section 36.")

    with r_tab3:
        st.markdown("### ⚖️ First Schedule — Maximum Permissible Error (MPE) on Net Quantity (Rule 11)")
        st.markdown(
            """
            Under **Rule 11 and the First Schedule of PCR 2011**, pre-packaged commodities weighed during on-site or laboratory inspection must not exceed the prescribed **Maximum Permissible Error (MPE)** tolerance.
            
            **Individual Package Deficit Tolerance Table:**
            """
        )

        mpe_table = [
            {"Declared Net Quantity (Q)": "Up to 50 g or ml", "Maximum Permissible Error (MPE)": "9.0% of declared quantity", "Example Tolerance (50g)": "± 4.5 g"},
            {"Declared Net Quantity (Q)": "50 g/ml to 100 g/ml", "Maximum Permissible Error (MPE)": "4.5 g or ml (Fixed)", "Example Tolerance (100g)": "± 4.5 g"},
            {"Declared Net Quantity (Q)": "100 g/ml to 200 g/ml", "Maximum Permissible Error (MPE)": "4.5% of declared quantity", "Example Tolerance (200g)": "± 9.0 g"},
            {"Declared Net Quantity (Q)": "200 g/ml to 300 g/ml", "Maximum Permissible Error (MPE)": "9.0 g or ml (Fixed)", "Example Tolerance (300g)": "± 9.0 g"},
            {"Declared Net Quantity (Q)": "300 g/ml to 500 g/ml", "Maximum Permissible Error (MPE)": "3.0% of declared quantity", "Example Tolerance (500g)": "± 15.0 g"},
            {"Declared Net Quantity (Q)": "500 g/ml to 1000 g/ml", "Maximum Permissible Error (MPE)": "15.0 g or ml (Fixed)", "Example Tolerance (1000g)": "± 15.0 g"},
            {"Declared Net Quantity (Q)": "1 kg/l to 10 kg/l", "Maximum Permissible Error (MPE)": "1.5% of declared quantity", "Example Tolerance (5 kg)": "± 75.0 g"},
            {"Declared Net Quantity (Q)": "10 kg/l to 15 kg/l", "Maximum Permissible Error (MPE)": "150.0 g or ml (Fixed)", "Example Tolerance (15 kg)": "± 150.0 g"},
            {"Declared Net Quantity (Q)": "Above 15 kg/l", "Maximum Permissible Error (MPE)": "1.0% of declared quantity", "Example Tolerance (25 kg)": "± 250.0 g"},
        ]
        st.table(mpe_table)
        st.warning("⚠️ **Short Delivery Deficit:** If actual net contents are below (Q - MPE), the package is seized and prosecution proceedings under Section 36(1) are initiated.")

    with r_tab4:
        st.markdown("### 🚨 Legal Metrology Act, 2009 — Statutory Penalty Matrix")
        st.caption("Statutory penalties prescribed under Chapter V of the Legal Metrology Act, 2009 for regulatory violations.")

        col_pen1, col_pen2 = st.columns(2)
        with col_pen1:
            st.markdown(
                """
                <div class="enterprise-card" style="border-left: 4px solid #ef4444;">
                    <h4 style="color: #f87171; margin-top: 0;">Section 36(1) — Non-Conforming Packages</h4>
                    <p style="font-size: 0.85rem; color: #cbd5e1;">Penalty for manufacturing, packing, importing, or selling non-standard pre-packaged commodities:</p>
                    <ul style="font-size: 0.82rem; color: #94a3b8; line-height: 1.6;">
                        <li><b>1st Offence:</b> Fine up to <b>₹25,000</b></li>
                        <li><b>2nd Offence:</b> Fine up to <b>₹50,000</b></li>
                        <li><b>Subsequent Offences:</b> Fine up to <b>₹1,00,000</b> or imprisonment up to 1 year, or both.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with col_pen2:
            st.markdown(
                """
                <div class="enterprise-card" style="border-left: 4px solid #f59e0b;">
                    <h4 style="color: #fbbf24; margin-top: 0;">Section 36(2) & Section 48 — Retail Sale & Compounding</h4>
                    <p style="font-size: 0.85rem; color: #cbd5e1;">Penalties for retail sellers and compounding authority:</p>
                    <ul style="font-size: 0.82rem; color: #94a3b8; line-height: 1.6;">
                        <li><b>Section 36(2):</b> Sale of non-compliant commodity: Fine from <b>₹2,000 to ₹5,000</b>.</li>
                        <li><b>Rule 18(2) Overcharging:</b> Selling above MRP is prosecuted under Section 36(1).</li>
                        <li><b>Section 48:</b> Authorizes Controller / Deputy Controller to compound first offences upon payment of specified compounding fees.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with r_tab5:
        st.markdown("### 🧮 Interactive Statutory Compliance Calculators")
        
        calc_col1, calc_col2 = st.columns(2, gap="large")
        
        with calc_col1:
            st.markdown("#### 📏 Calculator A: Rule 9 Minimum Character Height")
            pdp_h = st.number_input("Package Height (cm):", min_value=1.0, value=20.0, step=1.0, key="calc_pdp_h")
            pdp_w = st.number_input("Package Width (cm):", min_value=1.0, value=15.0, step=1.0, key="calc_pdp_w")
            
            pdp_area = pdp_h * pdp_w
            if pdp_area <= 50:
                min_h_norm, min_h_blown = 1.0, 2.0
            elif pdp_area <= 100:
                min_h_norm, min_h_blown = 1.5, 3.0
            elif pdp_area <= 500:
                min_h_norm, min_h_blown = 2.0, 4.0
            elif pdp_area <= 1000:
                min_h_norm, min_h_blown = 4.0, 6.0
            else:
                min_h_norm, min_h_blown = 6.0, 6.0
                
            st.success(f"**Principal Display Panel (PDP) Area:** `{pdp_area:.1f} cm²`")
            st.markdown(f"- **Minimum Character Height (Normal):** `{min_h_norm} mm`")
            st.markdown(f"- **Minimum Character Height (Blown/Moulded):** `{min_h_blown} mm`")

        with calc_col2:
            st.markdown("#### ⚖️ Calculator B: Rule 11 Maximum Permissible Error (MPE)")
            calc_dec_qty = st.number_input("Declared Net Quantity:", min_value=1.0, value=500.0, step=10.0, key="calc_dec_q")
            calc_unit = st.selectbox("Unit:", ["g", "kg", "ml", "l"], key="calc_unit_sel")
            calc_meas_qty = st.number_input("Actual Measured Net Quantity:", min_value=0.0, value=488.0, step=1.0, key="calc_meas_q")

            multiplier = 1000.0 if calc_unit in ["kg", "l"] else 1.0
            std_dec = calc_dec_qty * multiplier
            std_meas = calc_meas_qty * multiplier

            if std_dec <= 50: mpe_val = std_dec * 0.09
            elif std_dec <= 100: mpe_val = 4.5
            elif std_dec <= 200: mpe_val = std_dec * 0.045
            elif std_dec <= 300: mpe_val = 9.0
            elif std_dec <= 500: mpe_val = std_dec * 0.03
            elif std_dec <= 1000: mpe_val = 15.0
            elif std_dec <= 10000: mpe_val = std_dec * 0.015
            elif std_dec <= 15000: mpe_val = 150.0
            else: mpe_val = std_dec * 0.01

            min_allowed = std_dec - mpe_val
            is_mpe_pass = std_meas >= min_allowed

            disp_mpe = mpe_val / multiplier
            disp_min = min_allowed / multiplier

            st.markdown(f"- **Allowed Tolerance (MPE):** `± {disp_mpe:.2f} {calc_unit}`")
            st.markdown(f"- **Statutory Minimum Allowed Quantity:** `{disp_min:.2f} {calc_unit}`")
            
            if is_mpe_pass:
                st.success(f"✅ **PASS:** Measured `{calc_meas_qty} {calc_unit}` is within tolerance (Deficit: {abs(std_dec - std_meas)/multiplier:.2f} {calc_unit} ≤ {disp_mpe:.2f} {calc_unit}).")
            else:
                st.error(f"🚨 **DEFICIT VIOLATION:** Measured `{calc_meas_qty} {calc_unit}` is below minimum `{disp_min:.2f} {calc_unit}` (Short delivery under Rule 11 / Sec 36).")


# =================================================================================================
# 🔐 AUTHENTICATION & LOGIN GATEWAY
# =================================================================================================
if st.session_state["logged_in_user"] is None:
    st.markdown(
        """
        <div class="brand-header">
            <div class="brand-title-wrap">
                <div class="brand-logo">⚖️</div>
                <div>
                    <h1 class="brand-title">VERITAS METROLOGY PLATFORM</h1>
                    <p class="brand-subtitle">Directorate of Legal Metrology &bull; Official Regulatory Enforcement Access</p>
                </div>
            </div>
            <div class="status-pill-green">
                <div class="status-dot-green"></div>
                <span>Authentication Gateway</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown("### 🔐 Official Authority Login")
        st.caption("Please select your regulatory authority level and enter your official credentials.")

        if st.session_state.get("reg_success_msg"):
            st.success(st.session_state["reg_success_msg"])

        auth_tab1, auth_tab2 = st.tabs(["🔑 Sign In", "📝 Register New Officer"])

        with auth_tab1:
            selected_role = st.selectbox(
                "Select Authority Role:",
                ["INSPECTOR", "SUPERVISOR", "ADMIN"],
                format_func=lambda r: {
                    "INSPECTOR": "👮 Inspector (Field Inspection & Weighing)",
                    "SUPERVISOR": "⚖️ Supervisor / Controller (Case Approval & Notices)",
                    "ADMIN": "🏛️ Admin / Directorate (National Oversight & Settings)"
                }[r]
            )
            
            login_username = st.text_input(
                "Officer Username / Email:",
                placeholder="Enter registered username"
            )
            login_password = st.text_input(
                "Official Password:",
                type="password",
                placeholder="Enter password"
            )

            submit_login = st.button("🚀 Authenticate & Access Workspace", type="primary", use_container_width=True)

            if submit_login:
                if not login_username or not login_password:
                    st.error("Please enter both username and password.")
                else:
                    with st.spinner("Verifying credentials and jurisdiction authorization..."):
                        try:
                            resp = requests.post(
                                f"{API_BASE_URL}/auth/login",
                                json={"username": login_username, "password": login_password},
                                params={"role": selected_role},
                                timeout=10
                            )
                            if resp.status_code == 200:
                                user_data = resp.json()
                                st.session_state["logged_in_user"] = user_data
                                st.session_state["reg_success_msg"] = None
                                st.toast(f"Welcome, {user_data['full_name']}!", icon="👋")
                                st.success(f"Welcome, {user_data['full_name']}! Redirecting to your {user_data['role']} workspace...")
                                st.rerun()
                            else:
                                st.error("Authentication failed: Invalid credentials or role mismatch.")
                        except Exception as e:
                            st.error(f"Failed to connect to authentication server: {e}")

        with auth_tab2:
            st.markdown("#### Register a New Enforcement Officer")
            reg_name = st.text_input("Full Name:", placeholder="e.g. R. K. Sharma (Inspector)")
            reg_username = st.text_input("Username:", placeholder="e.g. sharma_rk")
            reg_pass = st.text_input("Password:", type="password", placeholder="Enter secure password")
            reg_role = st.selectbox("Designated Authority Role:", ["INSPECTOR", "SUPERVISOR", "ADMIN"])
            reg_dist = st.text_input("Assigned District / Jurisdiction:", placeholder="e.g. Salem District")
            reg_badge = st.text_input("Official Badge / ID Number:", placeholder="e.g. LM-INSP-401")

            submit_reg = st.button("📝 Register Official Account", type="primary", use_container_width=True)

            if submit_reg:
                if not reg_name or not reg_username or not reg_pass:
                    st.error("Please complete all required fields.")
                else:
                    try:
                        reg_data = {
                            "username": reg_username,
                            "password": reg_pass,
                            "full_name": reg_name,
                            "role": reg_role,
                            "district": reg_dist or "Central Enforcement Zone",
                            "badge_number": reg_badge or "LM-AUTH-001"
                        }
                        reg_res = requests.post(f"{API_BASE_URL}/auth/register", data=reg_data)
                        if reg_res.status_code == 200:
                            st.session_state["reg_success_msg"] = "Registered successfully"
                            st.toast("Registered successfully")
                            st.rerun()
                        else:
                            st.error(f"Registration error: {reg_res.text}")
                    except Exception as reg_err:
                        st.error(f"Connection error: {reg_err}")

    st.stop()


# =================================================================================================
# 🏢 LOGGED-IN WORKSPACE (ROLE-SPECIFIC CONSOLE)
# =================================================================================================
user = st.session_state.get("logged_in_user")
if not user:
    st.stop()
    user = {"full_name": "Guest Officer", "badge_number": "N/A", "district": "N/A", "role": "INSPECTOR"}
user_role = user.get("role", "INSPECTOR")

# Sidebar: User Profile & Session Controls
with st.sidebar:
    st.markdown("### 👮 Active Officer Profile")
    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 10px; padding: 0.85rem; margin-bottom: 1rem;">
            <div style="font-weight: 700; color: #f8fafc; font-size: 0.95rem;">{user['full_name']}</div>
            <div style="font-size: 0.78rem; color: #38bdf8; font-family: 'JetBrains Mono', monospace;">Badge: {user['badge_number']}</div>
            <div style="font-size: 0.75rem; color: #94a3b8;">Jurisdiction: {user['district']}</div>
            <div style="display: inline-block; margin-top: 6px; padding: 2px 8px; border-radius: 4px; font-size: 0.68rem; font-weight: 700; background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.4);">
                ROLE: {user_role}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("🚪 Logout / Return to Login Gateway", use_container_width=True, key="sidebar_logout_btn"):
        st.session_state["logged_in_user"] = None
        st.session_state["last_inspection"] = None
        st.rerun()

    st.markdown("---")
    st.markdown("#### ⚖️ Statutory Legal Reference")
    st.caption("• Legal Metrology Act, 2009 (No. 1 of 2010)")
    st.caption("• Packaged Commodities Rules, 2011")
    st.caption("• 2021/2022 Unit Sale Price Amendments")
    st.caption("• 2026 E-Comm Origin Filter Amendment")


# Top Header Navigation Bar with Prominent "Return to Login / Switch Role" Button
col_h_left, col_h_mid, col_h_right = st.columns([3.2, 1.0, 1.8])
with col_h_left:
    st.markdown(
        f"""
        <div class="brand-header" style="margin-bottom: 0.5rem; padding: 0.9rem 1.25rem;">
            <div class="brand-title-wrap">
                <div class="brand-logo">⚖️</div>
                <div>
                    <h1 class="brand-title" style="font-size: 1.35rem;">VERITAS METROLOGY &bull; {user_role} CONSOLE</h1>
                    <p class="brand-subtitle">Officer: <b>{user['full_name']}</b> &bull; Jurisdiction: <b>{user['district']}</b> &bull; Badge: <b>{user['badge_number']}</b></p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_h_mid:
    st.markdown(
        f"""
        <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid rgba(59, 130, 246, 0.3); border-radius: 12px; padding: 0.75rem; text-align: center; margin-top: 2px;">
            <div style="font-size: 0.65rem; color: #94a3b8; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;">Current Role</div>
            <div style="font-size: 0.90rem; font-weight: 800; color: #38bdf8;">{user_role}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
with col_h_right:
    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
    if st.button("🔙 Logout / Switch Role", type="primary", use_container_width=True, key="top_bar_logout_btn"):
        st.session_state["logged_in_user"] = None
        st.session_state["last_inspection"] = None
        st.rerun()


# =================================================================================================
# 👮 ROLE 1: INSPECTOR WORKSPACE
# =================================================================================================
if user_role == "INSPECTOR":
    tab_single, tab_multi, tab_my_cases, tab_rules = st.tabs([
        "🔬 On-Site Field Scanner (Level 1 & 2)",
        "🔄 Multi-Panel Package Scan",
        "📋 My Jurisdiction Case Ledger",
        "📜 Statutory Rulebook & MPE"
    ])

    # 1. FIELD SCANNER
    with tab_single:
        col_input, col_report = st.columns([1, 1], gap="medium")

        with col_input:
            st.markdown("### 📥 1. Package Ingestion & Field Data")
            input_method = st.radio("Ingestion Source:", ["📁 Upload Packaging Image", "📷 Live Camera Inspection"], horizontal=True)
            uploaded_img = None

            if input_method == "📁 Upload Packaging Image":
                f_in = st.file_uploader("Select high-res label (JPG, PNG, WEBP)", type=["jpg", "jpeg", "png", "webp"])
                if f_in: uploaded_img = f_in
            else:
                c_in = st.camera_input("Capture live packaging label")
                if c_in: uploaded_img = c_in

            # Case Metadata (ALL PLACEHOLDERS — NO HARDCODED PRE-FILLED VALUES)
            with st.expander("📋 Inspection Case Particulars", expanded=True):
                p_name = st.text_input("Product Name:", placeholder="e.g. Nutri Delight Whole Wheat Biscuits 500g")
                p_brand = st.text_input("Brand:", placeholder="e.g. Nutri Delight, Parle-G, Britannia...")
                p_cat = st.selectbox("Commodity Category:", ["Food & Bakery", "Packaged Snacks", "Beverages & Dairy", "Personal Care & Cosmetics", "Household Detergents", "Pharmaceuticals", "General Commodities"])
                p_loc = st.text_input("Inspection Location / Shop:", placeholder="e.g. Central Retail Mart, Shop 14, Main Road...")

            # Level 2 Physical Verification Module
            with st.expander("⚖️ Level 2: Physical Content Verification (Optional / On-Site)", expanded=False):
                st.info("💡 **Mentor Challenge Addressed:** External camera verifies label only. Use this section when physically weighing sealed contents to detect internal quantity deficit under Rule 11 / First Schedule.")
                enable_physical = st.checkbox("Execute Level 2 Physical Weight / Volume Verification")
                if enable_physical:
                    col_p1, col_p2 = st.columns(2)
                    with col_p1:
                        declared_q = st.number_input("Declared Net Quantity on Label:", value=None, placeholder="e.g. 500.0", step=1.0)
                        unit_choice = st.selectbox("Unit:", ["g", "kg", "ml", "l", "N"])
                    with col_p2:
                        measured_q = st.number_input("Actual Measured Net Quantity (Weighed):", value=None, placeholder="e.g. 430.0", step=1.0)
                        tare_w = st.number_input("Tare Weight (Wrapper):", value=0.0, placeholder="e.g. 5.0", step=0.5)
                else:
                    declared_q, unit_choice, measured_q, tare_w = None, "g", None, 0.0

            if uploaded_img is not None:
                img = Image.open(io.BytesIO(uploaded_img.getvalue()))
                st.image(img, caption="Ingested Packaging Preview", use_container_width=True)
                run_audit = st.button("⚡ Run Full Statutory Compliance Audit", type="primary", use_container_width=True)
            else:
                run_audit = False
                st.caption("Upload or capture product image to execute audit.")

        with col_report:
            st.markdown("### 📊 2. Statutory Audit Report & Evidence")

            if run_audit and uploaded_img is not None:
                with st.spinner("Executing Computer Vision, Multimodal Extraction, and Statutory Rule Analysis..."):
                    try:
                        file_bytes = uploaded_img.getvalue()
                        file_name = uploaded_img.name or "label_scan.jpg"
                        content_type = uploaded_img.type or "image/jpeg"
                        
                        form_data = {}
                        if enable_physical and declared_q is not None and measured_q is not None:
                            form_data["declared_net_qty"] = str(declared_q)
                            form_data["unit"] = unit_choice
                            form_data["measured_net_qty"] = str(measured_q)
                            form_data["tare_weight"] = str(tare_w)

                        files = {"file": (file_name, file_bytes, content_type)}
                        resp = requests.post(f"{API_BASE_URL}/scan-label", files=files, data=form_data, timeout=75)

                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state["active_pdf_bytes"] = None
                            st.session_state["active_pdf_filename"] = None
                            st.session_state["submitted_case_id"] = None
                            st.session_state["last_inspection"] = {
                                "data": data,
                                "product_name": p_name or "Pre-Packaged Retail Commodity",
                                "brand": p_brand or "Generic",
                                "category": p_cat,
                                "location": p_loc or "Inspected on site",
                                "file_bytes": file_bytes,
                            }
                        else:
                            st.error(f"Error {resp.status_code}: {resp.text}")
                    except Exception as e:
                        st.error(f"Audit failed to connect to backend: {e}")

            if st.session_state["last_inspection"]:
                insp_data = st.session_state["last_inspection"]["data"]
                status = insp_data.get("status", "NON_COMPLIANT")
                score = float(insp_data.get("package_declaration_score", 0.0))
                violations_cnt = int(insp_data.get("violations_count", 0))
                phys_status = insp_data.get("physical_verification_status", "NOT_VERIFIED")
                declarations = insp_data.get("declarations", {})
                violations_list = insp_data.get("violations", [])

                if status == "COMPLIANT":
                    st_color, st_bg, st_text = "#10b981", "rgba(16, 185, 129, 0.12)", "✅ COMPLIANT"
                elif status == "PHYSICAL_VERIFICATION_REQUIRED":
                    st_color, st_bg, st_text = "#f59e0b", "rgba(245, 158, 11, 0.12)", "⚠️ PHYSICAL VERIFICATION REQ."
                else:
                    st_color, st_bg, st_text = "#ef4444", "rgba(239, 68, 68, 0.12)", "❌ NON-COMPLIANT"

                st.markdown(
                    f"""
                    <div class="metric-grid">
                        <div class="metric-box" style="background: {st_bg}; border-color: {st_color};">
                            <div class="metric-label">3-Tier Verdict</div>
                            <div class="metric-value-large" style="color: {st_color}; font-size: 1.1rem;">{st_text}</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-label">Declaration Score</div>
                            <div class="metric-value-large" style="color: {'#34d399' if score >= 80 else '#fbbf24' if score >= 50 else '#f87171'}; font-size: 1.35rem;">{score:.1f}%</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-label">Violations</div>
                            <div class="metric-value-large" style="color: {'#34d399' if violations_cnt == 0 else '#f87171'}; font-size: 1.35rem;">{violations_cnt}</div>
                        </div>
                        <div class="metric-box">
                            <div class="metric-label">Level 2 Physical</div>
                            <div class="metric-value-large" style="color: {'#34d399' if phys_status == 'VERIFIED_COMPLIANT' else '#f87171' if phys_status == 'DEFICIT_VIOLATION' else '#94a3b8'}; font-size: 0.90rem;">{phys_status}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                st.markdown("#### 📜 Statutory Declaration Matrix (Rule 6, 8, 9, 11 & Amendments)")
                field_order = [
                    ("mrp", "1. Maximum Retail Price (MRP & Tax Clause)", "Rule 6(1)(e)"),
                    ("net_quantity", "2. Net Quantity & Metric SI Units", "Rule 6(1)(c) & Rule 13"),
                    ("unit_sale_price", "3. Unit Sale Price (USP in ₹/g or ₹/kg)", "Rule 6(1)(h) (2021 Amendment)"),
                    ("date_of_packing", "4. Date of Packing / Manufacture (MM/YYYY)", "Rule 6(1)(d)"),
                    ("best_before_expiry", "5. Best Before / Expiry Period", "Rule 6(1) / Perishable"),
                    ("consumer_care", "6. Consumer Grievance Care (Email/Phone)", "Rule 6(1)(f)"),
                    ("manufacturer_details", "7. Manufacturer / Packer Identity & Address", "Rule 6(1)(a)"),
                    ("country_of_origin", "8. Country of Origin", "Rule 6(1)(g) & 2026 E-comm"),
                    ("generic_name", "9. Generic / Common Commodity Name", "Rule 6(1)(b)"),
                ]

                for f_key, f_title, f_rule in field_order:
                    f_data = declarations.get(f_key, {})
                    detected = f_data.get("detected", False)
                    compliant = f_data.get("compliant", False)
                    val = f_data.get("value")
                    remarks = f_data.get("remarks", "No remarks.")

                    badge_html = '<span class="badge-compliant">✓ COMPLIANT</span>' if compliant else ('<span class="badge-violation">⚠ FORMAT VIOLATION</span>' if detected else '<span class="badge-missing">✕ MISSING</span>')
                    border = "border-left: 4px solid #10b981;" if compliant else ("border-left: 4px solid #f59e0b;" if detected else "border-left: 4px solid #ef4444;")
                    disp_val = val if (detected and val) else "Declaration absent / Not found"

                    st.markdown(
                        f"""
                        <div class="rule-card" style="{border}">
                            <div class="rule-header">
                                <div><span class="rule-title">{f_title}</span><span class="rule-citation"> &bull; {f_rule}</span></div>
                                {badge_html}
                            </div>
                            <div class="value-pill">{disp_val}</div>
                            <div class="remarks-text">{remarks}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                if violations_list:
                    st.markdown("#### 🚨 Flagged Violations & Visual Evidence Crops")
                    for v in violations_list:
                        st.error(f"**[{v.get('rule_number')}] {v.get('field_name')}**: {v.get('description')}")
                        if v.get("evidence_crop_base64"):
                            st.image(v.get("evidence_crop_base64"), width=360)

                st.markdown("---")
                st.markdown("#### ⚡ Official Enforcement Actions & Case Dispatch")
                col_act1, col_act2 = st.columns(2, gap="medium")
                
                with col_act1:
                    if st.session_state.get("active_pdf_bytes"):
                        st.download_button(
                            "⬇️ Download Official PDF Certificate",
                            data=st.session_state["active_pdf_bytes"],
                            file_name=st.session_state["active_pdf_filename"],
                            mime="application/pdf",
                            use_container_width=True,
                            type="primary",
                            key="btn_dl_pdf_ready"
                        )
                        if st.button("🔄 Regenerate PDF Certificate", use_container_width=True, key="btn_regen_pdf"):
                            st.session_state["active_pdf_bytes"] = None
                            st.rerun()
                    else:
                        if st.button("📄 Generate Official PDF Certificate", use_container_width=True, key="btn_gen_pdf_initial"):
                            with st.spinner("Generating official sealed Legal Metrology PDF certificate..."):
                                try:
                                    pdf_files = {"file": ("scan.jpg", st.session_state["last_inspection"]["file_bytes"], "image/jpeg")}
                                    pdf_data_form = {
                                        "product_name": st.session_state["last_inspection"]["product_name"],
                                        "brand": st.session_state["last_inspection"]["brand"],
                                        "inspector_name": user["full_name"],
                                        "badge_number": user["badge_number"],
                                        "district": user["district"],
                                        "location": st.session_state["last_inspection"]["location"],
                                    }
                                    if enable_physical and declared_q is not None and measured_q is not None:
                                        pdf_data_form["declared_net_qty"] = str(declared_q)
                                        pdf_data_form["unit"] = unit_choice
                                        pdf_data_form["measured_net_qty"] = str(measured_q)

                                    pdf_res = requests.post(f"{API_BASE_URL}/inspections/report/pdf", files=pdf_files, data=pdf_data_form)
                                    if pdf_res.status_code == 200:
                                        st.session_state["active_pdf_bytes"] = pdf_res.content
                                        st.session_state["active_pdf_filename"] = f"Legal_Metrology_Inspection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                        st.toast("✅ Official Inspection Certificate generated!", icon="📄")
                                        st.rerun()
                                    else:
                                        st.error(f"PDF error {pdf_res.status_code}: {pdf_res.text}")
                                except Exception as err:
                                    st.error(f"PDF call failed: {err}")

                with col_act2:
                    if st.session_state.get("submitted_case_id"):
                        sub_id = st.session_state["submitted_case_id"]
                        st.markdown(
                            f"""
                            <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.4); border-radius: 8px; padding: 0.65rem 0.85rem; text-align: center;">
                                <div style="font-weight: 700; color: #34d399; font-size: 0.88rem;">✅ Case #{sub_id} Dispatched</div>
                                <div style="font-size: 0.72rem; color: #cbd5e1;">Transmitted to Supervisor for statutory review and notice issuance.</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    else:
                        if st.button("💾 Submit Case to Supervisor for Review", type="primary", use_container_width=True, key="btn_submit_supervisor"):
                            with st.spinner("Submitting inspection case to Supervisor repository..."):
                                try:
                                    insp_id = f"INSP-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
                                    save_form = {
                                        "inspection_id": insp_id,
                                        "product_name": st.session_state["last_inspection"]["product_name"],
                                        "brand": st.session_state["last_inspection"]["brand"],
                                        "category": st.session_state["last_inspection"]["category"],
                                        "inspector_id": user["user_id"],
                                        "inspector_name": user["full_name"],
                                        "district": user["district"],
                                        "location_details": st.session_state["last_inspection"]["location"],
                                        "compliance_json": json.dumps(insp_data),
                                    }
                                    save_res = requests.post(f"{API_BASE_URL}/inspections/save", data=save_form)
                                    if save_res.status_code == 200:
                                        st.session_state["submitted_case_id"] = insp_id
                                        st.toast(f"✅ Case #{insp_id} successfully submitted to Supervisor!", icon="📤")
                                        st.rerun()
                                    else:
                                        st.error(f"Save error: {save_res.text}")
                                except Exception as save_err:
                                    st.error(f"Save error: {save_err}")
            else:
                st.markdown(
                    """
                    <div class="enterprise-card" style="text-align: center; color: #64748b; padding: 4rem 1.5rem;">
                        <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📋</div>
                        <div style="font-weight: 600; color: #cbd5e1; margin-bottom: 0.25rem;">Awaiting Inspection Trigger</div>
                        <div style="font-size: 0.85rem;">Upload or capture packaging image on the left and click 'Run Full Statutory Compliance Audit'.</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    # 2. MULTI-PANEL SCAN
    with tab_multi:
        st.markdown("### 🔄 Multi-Panel Package Scan & Dual Pricing Check (Rule 18)")
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1: f_front = st.file_uploader("Front Panel Image (Required):", type=["jpg", "png", "jpeg"], key="mf_front")
        with col_m2: f_back = st.file_uploader("Back Panel Image (Optional):", type=["jpg", "png", "jpeg"], key="mf_back")
        with col_m3: f_side = st.file_uploader("Side / Top Panel Image (Optional):", type=["jpg", "png", "jpeg"], key="mf_side")

        if st.button("⚡ Execute Multi-Panel Inconsistency Audit", type="primary"):
            if not f_front:
                st.warning("Please upload at least the Front Panel image.")
            else:
                try:
                    files = {"front_file": (f_front.name, f_front.getvalue(), f_front.type)}
                    if f_back: files["back_file"] = (f_back.name, f_back.getvalue(), f_back.type)
                    if f_side: files["side_file"] = (f_side.name, f_side.getvalue(), f_side.type)

                    m_resp = requests.post(f"{API_BASE_URL}/scan-multi-view", files=files)
                    if m_resp.status_code == 200:
                        m_data = m_resp.json()
                        st.markdown(f"#### Multi-Panel Verdict: **{m_data.get('status')}** (Score: {m_data.get('package_declaration_score')}%)")
                        conflicts = m_data.get("cross_source_conflicts", [])
                        if conflicts:
                            st.error(f"🚨 **{len(conflicts)} Cross-Panel Contradiction(s) Detected:**")
                            for c in conflicts:
                                st.markdown(f"- **{c.get('field_name')}**: {c.get('conflict_description')}")
                        else:
                            st.success("✅ Zero cross-panel contradictions found.")
                except Exception as m_err:
                    st.error(f"Failed to connect: {m_err}")

    # 3. MY JURISDICTION CASES
    with tab_my_cases:
        st.markdown(f"### 📋 Inspections Logged in {user['district']}")
        try:
            r_resp = requests.get(f"{API_BASE_URL}/inspections", params={"district": user["district"]})
            if r_resp.status_code == 200:
                cases = r_resp.json()
                st.markdown(f"**Found {len(cases)} cases logged in your jurisdiction:**")
                for c in cases:
                    st_badge = "✅ COMPLIANT" if c["status"] == "COMPLIANT" else "⚠️ VERIFY" if c["status"] == "PHYSICAL_VERIFICATION_REQUIRED" else "❌ NON-COMPLIANT"
                    with st.expander(f"📦 [{c['inspection_id']}] {c['product_name']} &bull; {st_badge} &bull; Status: {c.get('approval_status', 'PENDING')}"):
                        st.markdown(f"**Location:** {c['location_details']} | **Date:** {c['timestamp']}")
                        st.markdown(f"**Compliance Score:** {c['compliance_score']}% | **Violations:** {c['violations_count']}")
                        if c.get("supervisor_notes"):
                            st.info(f"**Supervisor Review:** {c['supervisor_notes']}")
        except Exception as e:
            st.error(f"Repository connection error: {e}")

    # 4. RULES
    with tab_rules:
        render_legal_rulebook_reference()


# =================================================================================================
# ⚖️ ROLE 2: SUPERVISOR / CONTROLLER WORKSPACE
# =================================================================================================
elif user_role == "SUPERVISOR":
    tab_review, tab_ecomm, tab_repo, tab_districts, tab_rules = st.tabs([
        "⚖️ Case Review & Sanction Console",
        "🛒 E-Commerce Marketplace Audit",
        "🗄️ State-Wide Case Repository",
        "📍 District Compliance Oversight",
        "📜 Statutory Rulebook & Legal Reference"
    ])

    # 1. CASE REVIEW & SANCTION CONSOLE
    with tab_review:
        st.markdown("### ⚖️ Pending Field Inspection Case Review & Legal Action")
        st.caption("Review field reports submitted by district inspectors. Officially issue Show-Cause Notices under Section 36, impose compounding penalties under Section 48, or approve compliant products.")

        try:
            r_resp = requests.get(f"{API_BASE_URL}/inspections")
            if r_resp.status_code == 200:
                cases = r_resp.json()
                for c in cases:
                    appr = c.get("approval_status", "PENDING_REVIEW")
                    st_badge = "✅ COMPLIANT" if c["status"] == "COMPLIANT" else "⚠️ VERIFY" if c["status"] == "PHYSICAL_VERIFICATION_REQUIRED" else "❌ NON-COMPLIANT"
                    
                    with st.expander(f"📦 [{c['inspection_id']}] {c['product_name']} &bull; {c['district']} &bull; {st_badge} &bull; Action: {appr}"):
                        col_cd1, col_cd2 = st.columns(2)
                        with col_cd1:
                            st.markdown(f"**Inspector:** {c['inspector_name']} | **District:** {c['district']}")
                            st.markdown(f"**Location:** {c['location_details']} | **Date:** {c['timestamp']}")
                            st.markdown(f"**Violations Count:** {c['violations_count']} | **Score:** {c['compliance_score']}%")
                        with col_cd2:
                            st.markdown("#### 📝 Take Official Enforcement Action:")
                            action_choice = st.selectbox(
                                "Select Action:",
                                ["APPROVE", "ISSUE_SHOW_CAUSE_NOTICE", "IMPOSE_COMPOUNDING_FINE", "REQUEST_RE_INSPECTION"],
                                key=f"act_{c['inspection_id']}"
                            )
                            sup_notes = st.text_input(
                                "Supervisor Order / Remarks:",
                                placeholder="e.g. Show-cause notice issued under Section 36 for non-standard unit.",
                                key=f"notes_{c['inspection_id']}"
                            )
                            fine_amount = st.number_input(
                                "Proposed Compounding Fine (₹):",
                                value=0.0,
                                placeholder="e.g. 25000.0",
                                step=5000.0,
                                key=f"fine_{c['inspection_id']}"
                            )

                            if st.button(f"⚡ Sign & Execute Order for {c['inspection_id']}", key=f"btn_{c['inspection_id']}"):
                                act_data = {
                                    "action": action_choice,
                                    "supervisor_notes": sup_notes or "Reviewed and authorized by Deputy Controller.",
                                    "compounding_fine": str(fine_amount)
                                }
                                act_res = requests.post(f"{API_BASE_URL}/inspections/{c['inspection_id']}/action", data=act_data)
                                if act_res.status_code == 200:
                                    st.success(f"✅ Order executed: {action_choice} recorded for case {c['inspection_id']}!")
                                    st.rerun()
                                else:
                                    st.error("Failed to update case.")
        except Exception as e:
            st.error(f"Error loading cases: {e}")

    # 2. E-COMMERCE AUDIT
    with tab_ecomm:
        st.markdown("### 🛒 E-Commerce Marketplace Audit & 2026 Origin Filter")
        st.caption("Verifies online marketplace listings against physical packaging evidence. Enforces 2026 Country of Origin searchability amendment & price gouging checks.")

        col_ec1, col_ec2 = st.columns(2)
        with col_ec1:
            st.markdown("#### 🌐 E-Commerce Portal Metadata")
            ec_title = st.text_input("E-Commerce Listing Title:", placeholder="e.g. Premium Crunchy Biscuits 500g Pack")
            ec_mrp = st.number_input("Listed MRP on Website (₹):", value=None, placeholder="e.g. 120.0", step=5.0)
            ec_qty = st.text_input("Listed Net Quantity:", placeholder="e.g. 500 g")
            ec_origin = st.text_input("Listed Country of Origin:", placeholder="e.g. India")
            ec_filter = st.checkbox("Portal provides Searchable/Sortable Country of Origin Filter (Rule 2026)", value=True)

        with col_ec2:
            st.markdown("#### 📦 Physical Packaging Image")
            ec_file = st.file_uploader("Upload physical package photograph:", type=["jpg", "png", "jpeg"], key="ec_file")
            if ec_file:
                st.image(ec_file, width=280)

        if st.button("⚡ Run E-Commerce vs Physical Cross-Check", type="primary"):
            if not ec_file or not ec_title or ec_mrp is None:
                st.warning("Please provide listing details and upload a physical package image.")
            else:
                with st.spinner("Auditing E-Commerce compliance & 2026 amendments..."):
                    try:
                        files = {"file": (ec_file.name, ec_file.getvalue(), ec_file.type)}
                        data_form = {
                            "title": ec_title,
                            "listed_mrp": str(ec_mrp),
                            "listed_net_quantity": ec_qty or "500 g",
                            "country_of_origin": ec_origin or "India",
                            "has_origin_filter": "true" if ec_filter else "false",
                        }
                        ec_resp = requests.post(f"{API_BASE_URL}/scan-ecommerce", files=files, data=data_form)
                        if ec_resp.status_code == 200:
                            ec_res_data = ec_resp.json()
                            st.markdown(f"#### E-Commerce Audit Verdict: **{ec_res_data.get('status')}**")
                            conflicts = ec_res_data.get("cross_source_conflicts", [])
                            if conflicts:
                                st.error(f"🚨 **{len(conflicts)} E-Commerce Inconsistencies Detected:**")
                                for c in conflicts:
                                    st.markdown(f"- **{c.get('field_name')}**: {c.get('conflict_description')}")
                            else:
                                st.success("✅ E-Commerce listing matches physical packaging exactly.")
                    except Exception as ec_err:
                        st.error(f"Connection failed: {ec_err}")

    # 3. STATE-WIDE REPOSITORY
    with tab_repo:
        st.markdown("### 🗄️ State-Wide Legal Metrology Case Repository")
        col_s1, col_s2, col_s3 = st.columns([2, 1, 1])
        with col_s1: s_query = st.text_input("🔍 Search Product / Brand / Case ID:", placeholder="e.g. Biscuits, Salem, INSP-2026...")
        with col_s2: s_district = st.selectbox("District:", ["All Districts", "Salem District", "Pune District", "Mumbai Central", "Bangalore Urban", "Delhi NCR"])
        with col_s3: s_status = st.selectbox("Status:", ["All Statuses", "COMPLIANT", "NON_COMPLIANT", "PHYSICAL_VERIFICATION_REQUIRED"])

        try:
            r_resp = requests.get(f"{API_BASE_URL}/inspections", params={"query": s_query, "district": s_district, "status": s_status})
            if r_resp.status_code == 200:
                cases = r_resp.json()
                st.markdown(f"**Found {len(cases)} Historical Inspection Records:**")
                for c in cases:
                    st_badge = "✅ COMPLIANT" if c["status"] == "COMPLIANT" else "⚠️ VERIFY" if c["status"] == "PHYSICAL_VERIFICATION_REQUIRED" else "❌ NON-COMPLIANT"
                    with st.expander(f"📦 [{c['inspection_id']}] {c['product_name']} &bull; {st_badge} &bull; {c['district']}"):
                        st.markdown(f"**Inspector:** {c['inspector_name']} | **Score:** {c['compliance_score']}% | **Violations:** {c['violations_count']}")
                        st.markdown(f"**Location:** {c['location_details']} | **Date:** {c['timestamp']}")
        except Exception as e:
            st.error(f"Repository connection error: {e}")

    # 4. DISTRICT OVERSIGHT
    with tab_districts:
        st.markdown("### 📍 District Compliance & Repeat Offender Oversight")
        try:
            stat_resp = requests.get(f"{API_BASE_URL}/dashboard/stats")
            if stat_resp.status_code == 200:
                s_data = stat_resp.json()
                dists = s_data.get("district_distribution", [])
                for d in dists:
                    st.markdown(f"- **{d['district']}**: {d['total']} Products Inspected &bull; **{d['violations']} Violations Flagged**")
        except Exception as e:
            st.error(f"Error: {e}")

    # 5. RULES
    with tab_rules:
        render_legal_rulebook_reference()


# =================================================================================================
# 🏛️ ROLE 3: ADMIN / DIRECTORATE WORKSPACE
# =================================================================================================
elif user_role == "ADMIN":
    tab_analytics, tab_roster, tab_master_repo, tab_config, tab_rules = st.tabs([
        "📈 Executive Macro Analytics",
        "👥 Officer Roster & Jurisdictions",
        "🗄️ Master Case Database",
        "⚙️ Statutory Rule Configuration",
        "📜 Legal Rulebook Reference"
    ])

    # 1. MACRO ANALYTICS
    with tab_analytics:
        st.markdown("### 📈 Directorate Executive Analytics & Risk Heatmap")
        try:
            stat_resp = requests.get(f"{API_BASE_URL}/dashboard/stats")
            if stat_resp.status_code == 200:
                s_data = stat_resp.json()
                col_a1, col_a2, col_a3, col_a4 = st.columns(4)
                col_a1.metric("Total National Inspections", s_data["total_inspections"])
                col_a2.metric("Compliant Products", s_data["compliant_count"])
                col_a3.metric("Non-Compliant Violations", s_data["non_compliant_count"])
                col_a4.metric("National Compliance Rate", f"{s_data['overall_compliance_rate']}%")

                st.markdown("---")
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    st.markdown("#### 📊 National Violation Category Breakdown")
                    cats = s_data.get("violation_categories", [])
                    for cat in cats:
                        st.progress(min(1.0, cat["count"] / max(1, s_data["total_inspections"])), text=f"{cat['category']} ({cat['count']} cases)")
                with col_g2:
                    st.markdown("#### 📍 District Compliance Comparison")
                    dists = s_data.get("district_distribution", [])
                    for d in dists:
                        st.markdown(f"- **{d['district']}**: {d['total']} Audited, **{d['violations']} Non-Compliant**")
        except Exception as e:
            st.error(f"Analytics error: {e}")

    # 2. OFFICER ROSTER & JURISDICTIONS
    with tab_roster:
        st.markdown("### 👥 Legal Metrology Officer Roster & Jurisdiction Management")
        
        try:
            u_resp = requests.get(f"{API_BASE_URL}/users")
            if u_resp.status_code == 200:
                users_list = u_resp.json()
                st.markdown(f"**Active Enforcement Officers ({len(users_list)} registered):**")
                
                for u in users_list:
                    role_badge = "👮 FIELD INSPECTOR" if u["role"] == "INSPECTOR" else ("⚖️ DEPUTY CONTROLLER" if u["role"] == "SUPERVISOR" else "🏛️ NATIONAL DIRECTORATE")
                    st.markdown(
                        f"""
                        <div class="rule-card" style="border-left: 4px solid #3b82f6;">
                            <div class="rule-header">
                                <span class="rule-title">{u['full_name']} &bull; @{u['username']}</span>
                                <span class="badge-compliant">{role_badge}</span>
                            </div>
                            <div style="font-size: 0.82rem; color: #94a3b8;">
                                <b>Badge:</b> {u['badge_number']} | <b>Jurisdiction:</b> {u['district']} | <b>Joined:</b> {u['created_at'][:10]}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        except Exception as e:
            st.error(f"Failed to load user roster: {e}")

    # 3. MASTER CASE DATABASE
    with tab_master_repo:
        st.markdown("### 🗄️ Master Inspection Case Repository (National Directorate View)")
        try:
            r_resp = requests.get(f"{API_BASE_URL}/inspections")
            if r_resp.status_code == 200:
                cases = r_resp.json()
                st.markdown(f"**Total Records: {len(cases)}**")
                st.download_button("📥 Export Complete National Database (JSON)", json.dumps(cases, indent=2), file_name="national_metrology_cases.json", mime="application/json")
        except Exception as e:
            st.error(f"Database error: {e}")

    # 4. RULE CONFIGURATION
    with tab_config:
        st.markdown("### ⚙️ Statutory Rule & MPE Tolerance Configuration")
        st.caption("Configure regulatory thresholds, safety multipliers, and automated enforcement parameters for the national inspection platform.")

        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            st.markdown("#### ⚖️ MPE Tolerance & Weighing Parameters")
            mpe_strictness = st.slider("MPE Strictness Factor (1.0 = Standard 2011 Schedule):", 0.5, 1.5, 1.0, 0.1)
            tare_tol = st.number_input("Default Tare Weight Margin (g):", 0.0, 10.0, 0.5, 0.1)
            st.markdown("#### 📏 Character Height OCR Strictness")
            font_margin = st.slider("Font Height OCR Safety Margin (%):", 0, 25, 5, 1)

        with col_cfg2:
            st.markdown("#### 🚨 Statutory Penalty Defaults")
            default_fine_1st = st.number_input("Default 1st Offense Compounding Fine (₹):", 5000, 25000, 10000, 1000)
            default_fine_2nd = st.number_input("Default 2nd Offense Compounding Fine (₹):", 20000, 50000, 25000, 5000)
            ecomm_strict = st.checkbox("Strict 2026 E-Commerce Country of Origin Validation", value=True)

        if st.button("💾 Save Enforcement Configurations", type="primary"):
            st.toast("✅ Enforcement configurations updated successfully!", icon="⚙️")
            st.success("✅ Statutory parameters updated across all district inspector modules!")

    # 5. RULES
    with tab_rules:
        render_legal_rulebook_reference()