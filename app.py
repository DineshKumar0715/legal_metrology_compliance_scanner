import io
import os
import json
from datetime import datetime
import requests
import streamlit as st
from PIL import Image
from dotenv import load_dotenv

# Load environment
load_dotenv()

st.set_page_config(
    page_title="VERITAS | Legal Metrology Compliance Engine",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

API_ENDPOINT = os.getenv("API_ENDPOINT", "http://localhost:8000/scan-label")

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

    /* Top enterprise header */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1.25rem 1.75rem;
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.9) 0%, rgba(30, 41, 59, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        margin-bottom: 1.75rem;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    .brand-title-wrap {
        display: flex;
        align-items: center;
        gap: 14px;
    }
    .brand-logo {
        width: 44px;
        height: 44px;
        background: linear-gradient(135deg, #3b82f6, #6366f1);
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.4);
    }
    .brand-title {
        font-size: 1.4rem;
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
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        color: #34d399;
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 600;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }
    .status-dot {
        width: 8px;
        height: 8px;
        background-color: #10b981;
        border-radius: 50%;
        box-shadow: 0 0 10px #10b981;
    }

    /* Enterprise card containers */
    .enterprise-card {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 14px;
        padding: 1.5rem;
        backdrop-filter: blur(12px);
        margin-bottom: 1.25rem;
    }

    /* Metric Summary Panel */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .metric-box {
        background: linear-gradient(180deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.8) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 1.25rem;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);
    }
    .metric-label {
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #94a3b8;
        margin-bottom: 6px;
    }
    .metric-value-large {
        font-size: 1.9rem;
        font-weight: 800;
        letter-spacing: -0.02em;
        line-height: 1.1;
    }

    /* Statutory Matrix Items */
    .rule-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.85rem;
        transition: all 0.2s ease;
    }
    .rule-card:hover {
        border-color: rgba(99, 102, 241, 0.3);
        background: rgba(30, 41, 59, 0.65);
    }
    .rule-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 8px;
    }
    .rule-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #f1f5f9;
    }
    .badge-compliant {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-violation {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.35);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .badge-missing {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
    }
    .value-pill {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        padding: 6px 10px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: #e2e8f0;
        margin: 6px 0;
        word-break: break-word;
    }
    .remarks-text {
        font-size: 0.82rem;
        color: #94a3b8;
        line-height: 1.4;
    }

    /* Clean Streamlit elements override */
    button[kind="primary"] {
        background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%) !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 0.65rem 1.5rem !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3) !important;
        transition: transform 0.1s ease, box-shadow 0.1s ease !important;
    }
    button[kind="primary"]:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Enterprise Navigation & System Header
st.markdown(
    """
    <div class="brand-header">
        <div class="brand-title-wrap">
            <div class="brand-logo">⚖️</div>
            <div>
                <h1 class="brand-title">VERITAS METROLOGY AI</h1>
                <p class="brand-subtitle">Automated Compliance Verification System &bull; Legal Metrology (Packaged Commodities) Rules, 2011</p>
            </div>
        </div>
        <div class="status-pill">
            <div class="status-dot"></div>
            <span>Multimodal Core Active</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# Main Application Layout
col_upload, col_audit = st.columns([1, 1], gap="large")

with col_upload:
    st.markdown("### 📥 Product Ingestion")
    
    input_tab1, input_tab2 = st.tabs(["📁 File Upload", "📷 Live Camera Inspection"])
    
    uploaded_file = None
    with input_tab1:
        file_input = st.file_uploader(
            "Select high-resolution packaging label (JPG, PNG, WEBP)",
            type=["jpg", "jpeg", "png", "webp"],
            help="High-contrast, glare-free product label images deliver optimal compliance scoring.",
            label_visibility="collapsed",
        )
        if file_input:
            uploaded_file = file_input

    with input_tab2:
        camera_input = st.camera_input("Capture live packaging label via inspection webcam")
        if camera_input:
            uploaded_file = camera_input

    if uploaded_file is not None:
        try:
            image = Image.open(io.BytesIO(uploaded_file.getvalue()))
            st.image(image, caption="Current Ingestion Preview", use_container_width=True)
            
            scan_action = st.button(
                "⚡ Run Statutory Compliance Audit",
                type="primary",
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Could not load image: {e}")
            scan_action = False
    else:
        scan_action = False
        st.markdown(
            """
            <div class="enterprise-card" style="text-align: center; color: #64748b; padding: 3rem 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📦</div>
                <div style="font-weight: 600; color: #cbd5e1; margin-bottom: 0.25rem;">Awaiting Product Label</div>
                <div style="font-size: 0.85rem;">Upload or capture an image above to trigger automated legal metrology audit.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

with col_audit:
    st.markdown("### 📊 Executive Compliance Report")

    if scan_action and uploaded_file is not None:
        with st.spinner("Executing multimodal perception & statutory rule evaluation..."):
            try:
                file_bytes = uploaded_file.getvalue()
                file_name = uploaded_file.name or "label_scan.jpg"
                content_type = uploaded_file.type or "image/jpeg"
                files = {"file": (file_name, file_bytes, content_type)}
                
                response = requests.post(API_ENDPOINT, files=files, timeout=75)

                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "NON_COMPLIANT")
                    score = float(data.get("overall_compliance_score", 0.0))
                    violations = int(data.get("violations_count", 0))
                    declarations = data.get("declarations", {})
                    raw_text = data.get("raw_text", "")

                    # Color coding logic
                    is_compliant = (status == "COMPLIANT")
                    status_color = "#10b981" if is_compliant else "#ef4444"
                    status_bg = "rgba(16, 185, 129, 0.12)" if is_compliant else "rgba(239, 68, 68, 0.12)"
                    status_border = "rgba(16, 185, 129, 0.3)" if is_compliant else "rgba(239, 68, 68, 0.3)"

                    # Top KPI Metric Grid
                    st.markdown(
                        f"""
                        <div class="metric-grid">
                            <div class="metric-box" style="border-color: {status_border}; background: {status_bg};">
                                <div class="metric-label">Audit Verdict</div>
                                <div class="metric-value-large" style="color: {status_color}; font-size: 1.45rem;">
                                    {"✅ COMPLIANT" if is_compliant else "❌ NON-COMPLIANT"}
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Compliance Score</div>
                                <div class="metric-value-large" style="color: {'#34d399' if score >= 80 else '#fbbf24' if score >= 50 else '#f87171'};">
                                    {score:.1f}%
                                </div>
                            </div>
                            <div class="metric-box">
                                <div class="metric-label">Violations Flagged</div>
                                <div class="metric-value-large" style="color: {'#34d399' if violations == 0 else '#f87171'};">
                                    {violations}
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.markdown("#### 📜 Statutory Declaration Matrix")

                    field_order = [
                        ("mrp", "1. Maximum Retail Price (MRP)"),
                        ("net_quantity", "2. Net Quantity & Standard Units"),
                        ("date_of_packing", "3. Date of Packing / Manufacture"),
                        ("consumer_care", "4. Consumer Care & Grievance Redressal"),
                        ("manufacturer_details", "5. Manufacturer / Packer Identity"),
                        ("country_of_origin", "6. Country of Origin"),
                    ]

                    for field_key, field_title in field_order:
                        field_data = declarations.get(field_key, {})
                        detected = field_data.get("detected", False)
                        compliant = field_data.get("compliant", False)
                        val = field_data.get("value")
                        remarks = field_data.get("remarks", "No additional remarks.")

                        if compliant:
                            badge_html = '<span class="badge-compliant">✓ COMPLIANT</span>'
                            border_style = "border-left: 4px solid #10b981;"
                        elif detected:
                            badge_html = '<span class="badge-violation">⚠ FORMAT VIOLATION</span>'
                            border_style = "border-left: 4px solid #f59e0b;"
                        else:
                            badge_html = '<span class="badge-missing">✕ MISSING</span>'
                            border_style = "border-left: 4px solid #ef4444;"

                        display_val = val if (detected and val) else "Declaration absent / Not found"

                        st.markdown(
                            f"""
                            <div class="rule-card" style="{border_style}">
                                <div class="rule-header">
                                    <span class="rule-title">{field_title}</span>
                                    {badge_html}
                                </div>
                                <div class="value-pill">{display_val}</div>
                                <div class="remarks-text">{remarks}</div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                    # Export & Raw Data Section
                    col_export1, col_export2 = st.columns([1, 1])
                    with col_export1:
                        report_json = json.dumps(data, indent=2)
                        st.download_button(
                            label="📥 Export Audit JSON",
                            data=report_json,
                            file_name=f"legal_metrology_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json",
                            use_container_width=True,
                        )
                    
                    with col_export2:
                        summary_txt = f"""LEGAL METROLOGY COMPLIANCE AUDIT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Status: {status}
Score: {score}%
Violations: {violations}

DECLARATIONS:
"""
                        for k, v in declarations.items():
                            summary_txt += f"- {k.upper()}: {'COMPLIANT' if v.get('compliant') else 'FAILED'} | Value: {v.get('value')} | Remarks: {v.get('remarks')}\n"
                        
                        st.download_button(
                            label="📄 Export Text Summary",
                            data=summary_txt,
                            file_name=f"compliance_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain",
                            use_container_width=True,
                        )

                    with st.expander("🔍 Complete Optical Transcription (`raw_text`)"):
                        st.text_area(
                            "Verbatim Packaging Text Extracted by Multimodal Model",
                            value=raw_text,
                            height=180,
                            disabled=True,
                        )

                elif response.status_code == 400:
                    detail = response.json().get("detail", response.text)
                    st.error(f"⚠️ Bad Request (400): {detail}")
                elif response.status_code == 500:
                    detail = response.json().get("detail", response.text)
                    st.error(f"🚨 Audit Engine Error (500): {detail}")
                else:
                    st.error(f"Unexpected Response ({response.status_code}): {response.text}")

            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ **Backend Gateway Unreachable**\n\n"
                    "The FastAPI service is not responding on `http://localhost:8000`. Please verify the backend is running."
                )
            except requests.exceptions.Timeout:
                st.error("⏳ **Audit Timeout** — The multimodal vision engine took longer than expected to process.")
            except Exception as err:
                st.error(f"An unexpected system exception occurred: {err}")
    else:
        st.markdown(
            """
            <div class="enterprise-card" style="text-align: center; color: #64748b; padding: 4rem 1.5rem;">
                <div style="font-size: 2.5rem; margin-bottom: 0.75rem;">📋</div>
                <div style="font-weight: 600; color: #cbd5e1; margin-bottom: 0.25rem;">Audit Report Pending</div>
                <div style="font-size: 0.85rem;">Click 'Run Statutory Compliance Audit' on the left to generate the complete regulatory matrix.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )