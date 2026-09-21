import io
import os
import requests
import streamlit as st
from PIL import Image

# Set Streamlit page configuration
st.set_page_config(
    page_title="Legal Metrology Compliance Scanner",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling for modern premium aesthetic
st.markdown(
    """
    <style>
    /* Main container styling */
    .main-header {
        font-size: 2.3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 50%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
        font-weight: 400;
    }
    /* Metric Cards */
    .metric-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.2rem;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        text-align: center;
    }
    .metric-val-pass {
        font-size: 2rem;
        font-weight: 800;
        color: #10B981;
    }
    .metric-val-fail {
        font-size: 2rem;
        font-weight: 800;
        color: #EF4444;
    }
    .metric-label {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-top: 0.3rem;
    }
    /* Status Badges */
    .badge-pass {
        display: inline-block;
        background-color: #ECFDF5;
        color: #065F46;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #A7F3D0;
    }
    .badge-warn {
        display: inline-block;
        background-color: #FFFBEB;
        color: #92400E;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #FDE68A;
    }
    .badge-fail {
        display: inline-block;
        background-color: #FEF2F2;
        color: #991B1B;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        border: 1px solid #FECACA;
    }
    .rule-title {
        font-weight: 700;
        font-size: 1.05rem;
        color: #1E293B;
    }
    .rule-statute {
        font-size: 0.8rem;
        color: #64748B;
        font-style: italic;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# API Endpoint URL
API_URL = os.getenv("API_URL", "http://localhost:8000/scan-label")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/scales.png", width=64)
    st.title("Audit Configuration")
    st.markdown(
        """
        **Statutory Framework:**
        - Legal Metrology Act, 2009
        - Packaged Commodities Rules, 2011 (PCR)
        - Rule 6 Mandatory Declarations
        """
    )
    st.divider()
    st.markdown("### 🔌 API Backend")
    api_endpoint = st.text_input("FastAPI Endpoint", value=API_URL)
    
    # Check API status
    try:
        health_resp = requests.get(api_endpoint.replace("/scan-label", "/"), timeout=2)
        if health_resp.status_code == 200:
            st.success("🟢 API Server Connected")
        else:
            st.warning("🟠 API Server Error")
    except Exception:
        st.error("🔴 API Server Offline (Check localhost:8000)")
    
    st.divider()
    st.info(
        "💡 **Tip:** Upload clear, front-facing images of product packaging or mandatory declaration panels."
    )

# Header Section
st.markdown('<div class="main-header">⚖️ Legal Metrology Compliance Scanner</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Automated statutory label audit for Packaged Commodities under Legal Metrology Rules, 2011</div>',
    unsafe_allow_html=True,
)

# Layout: Left Column (Input & Preview), Right Column (Audit Results)
col_left, col_right = st.columns([1, 1.2], gap="large")

with col_left:
    st.subheader("📷 Label Image Input")
    
    input_mode = st.radio(
        "Select Input Method:",
        ["Upload Image File", "Use Camera Scan", "Load Sample Test Label"],
        horizontal=True,
    )

    image_bytes = None
    preview_image = None

    if input_mode == "Upload Image File":
        uploaded_file = st.file_uploader(
            "Choose a label image (PNG, JPG, JPEG, WEBP):",
            type=["png", "jpg", "jpeg", "webp"],
            help="Upload a clear photograph or digital scan of the commodity label.",
        )
        if uploaded_file is not None:
            image_bytes = uploaded_file.getvalue()
            preview_image = Image.open(io.BytesIO(image_bytes))

    elif input_mode == "Use Camera Scan":
        camera_file = st.camera_input("Take a photo of the package label")
        if camera_file is not None:
            image_bytes = camera_file.getvalue()
            preview_image = Image.open(io.BytesIO(image_bytes))

    elif input_mode == "Load Sample Test Label":
        sample_choice = st.selectbox(
            "Select a pre-configured sample label:",
            [
                "Sample 1: Fully Compliant Biscuit Label (100% Score)",
                "Sample 2: Non-Compliant Net Qty ('500 gm') & Missing Tax Text",
                "Sample 3: Missing Country of Origin & Consumer Care Helpline",
            ],
        )
        # Generate on-the-fly sample image using Pillow
        from PIL import ImageDraw, ImageFont
        sample_img = Image.new("RGB", (700, 480), color=(252, 252, 253))
        draw = ImageDraw.Draw(sample_img)
        
        # Border
        draw.rectangle([(10, 10), (690, 470)], outline=(180, 190, 205), width=3)
        draw.rectangle([(20, 20), (680, 70)], fill=(30, 58, 138))
        draw.text((35, 30), "PREMIUM PACKAGED COMMODITY LABEL", fill=(255, 255, 255))
        
        if "Sample 1" in sample_choice:
            sample_lines = [
                ("COMMODITY:", "Nutri Delight Whole Wheat Biscuits"),
                ("NET QUANTITY:", "500 g"),
                ("MRP:", "Rs. 95.00 (inclusive of all taxes)"),
                ("MFD & PKD BY:", "Golden Bake Foods Pvt Ltd, Industrial Area, Sector 4, Pune 411018"),
                ("DATE OF MFG:", "05/2024"),
                ("CONSUMER CARE:", "Customer Care Helpline: 1800-222-3333 | Email: care@goldenbake.com"),
                ("COUNTRY OF ORIGIN:", "India"),
            ]
        elif "Sample 2" in sample_choice:
            sample_lines = [
                ("COMMODITY:", "Super Crunch Cookies"),
                ("NET QUANTITY:", "500 gm"),  # VIOLATION: gm instead of g
                ("MRP:", "Rs. 100"),        # VIOLATION: Missing 'incl. of all taxes'
                ("MFD & PKD BY:", "Apex Confectionery Works, Mumbai 400001"),
                ("DATE OF MFG:", "04/2024"),
                ("CONSUMER CARE:", "Consumer Cell: 1800-111-2222 | Email: support@apex.in"),
                ("COUNTRY OF ORIGIN:", "India"),
            ]
        else:
            sample_lines = [
                ("COMMODITY:", "Smart Wireless Earbuds"),
                ("NET QUANTITY:", "1 N"),
                ("MRP:", "Rs. 1499.00 (incl. of all taxes)"),
                ("IMPORTED BY:", "Global Tech Imports Ltd, Bengaluru 560001"),
                ("DATE OF IMPORT:", "03/2024"),
                ("CONSUMER CARE:", "For feedback contact: Customer Care"), # VIOLATION: Missing phone/email
                # VIOLATION: Missing Country of origin
            ]
        
        y_pos = 90
        for label, val in sample_lines:
            draw.text((35, y_pos), label, fill=(15, 23, 42))
            draw.text((220, y_pos), val, fill=(30, 41, 59))
            y_pos += 48
            draw.line([(35, y_pos - 8), (665, y_pos - 8)], fill=(226, 232, 240), width=1)
            
        buf = io.BytesIO()
        sample_img.save(buf, format="PNG")
        image_bytes = buf.getvalue()
        preview_image = sample_img

    # Image Preview
    if preview_image is not None:
        st.image(preview_image, caption="Label Preview", use_container_width=True)
        audit_button = st.button("🔍 Run Compliance Audit", type="primary", use_container_width=True)
    else:
        st.info("👆 Please upload an image or select a sample to begin.")
        audit_button = False

with col_right:
    st.subheader("📊 Statutory Compliance Audit Results")

    if audit_button and image_bytes:
        with st.spinner("⏳ Analyzing label via Computer Vision OCR & Legal Metrology Rule Engine..."):
            try:
                files = {"file": ("label.png", image_bytes, "image/png")}
                response = requests.post(api_endpoint, files=files, timeout=60)

                if response.status_code == 200:
                    data = response.json()
                    st.session_state["compliance_result"] = data
                else:
                    st.error(f"❌ Backend Error ({response.status_code}): {response.text}")
            except requests.exceptions.ConnectionError:
                st.error(
                    f"🔌 Connection Refused! Could not reach FastAPI at `{api_endpoint}`. Ensure `python -m uvicorn main:app --port 8000` is running."
                )
            except Exception as e:
                st.error(f"❌ Error during scan: {str(e)}")

    if "compliance_result" in st.session_state:
        result = st.session_state["compliance_result"]
        
        status = result.get("status", "NON_COMPLIANT")
        score = result.get("overall_compliance_score", 0.0)
        violations = result.get("violations_count", 0)
        declarations = result.get("declarations", {})
        raw_text = result.get("raw_text", "")

        # Summary Metric Cards
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            status_html = (
                f'<div class="metric-val-pass">COMPLIANT</div>'
                if status == "COMPLIANT"
                else f'<div class="metric-val-fail">NON-COMPLIANT</div>'
            )
            st.markdown(
                f"""
                <div class="metric-card">
                    {status_html}
                    <div class="metric-label">Overall Status</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col2:
            score_color = "metric-val-pass" if score >= 80 else ("metric-val-fail" if score < 50 else "metric-val-pass")
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="{score_color}">{score:.1f}%</div>
                    <div class="metric-label">Compliance Score</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col3:
            v_color = "metric-val-pass" if violations == 0 else "metric-val-fail"
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="{v_color}">{violations}</div>
                    <div class="metric-label">Violations / Missing</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Rule-by-rule Accordion
        rule_meta = {
            "mrp": {
                "title": "1. Maximum Retail Price (MRP)",
                "statute": "Rule 6(1)(e) - Inclusive of all taxes mandate",
                "icon": "💰",
            },
            "net_quantity": {
                "title": "2. Net Quantity & Standard Units",
                "statute": "Rule 6(1)(c) - Standard metric units (g, kg, ml, l, N)",
                "icon": "⚖️",
            },
            "date_of_packing": {
                "title": "3. Date of Packing / Manufacture",
                "statute": "Rule 6(1)(d) - Month & Year of packing/mfg",
                "icon": "📅",
            },
            "consumer_care": {
                "title": "4. Consumer Care & Grievance Redressal",
                "statute": "Rule 6(1)(n) - Contact name, helpline & email",
                "icon": "📞",
            },
            "manufacturer_details": {
                "title": "5. Manufacturer / Packer / Importer",
                "statute": "Rule 6(1)(a) - Complete name and address",
                "icon": "🏭",
            },
            "country_of_origin": {
                "title": "6. Country of Origin",
                "statute": "Rule 6(1)(m) - Origin declaration",
                "icon": "🌐",
            },
        }

        for rule_key, meta in rule_meta.items():
            field_data = declarations.get(rule_key, {})
            detected = field_data.get("detected", False)
            compliant = field_data.get("compliant", False)
            value = field_data.get("value")
            remarks = field_data.get("remarks", "")

            # Determine badge and expansion
            if compliant:
                badge = '<span class="badge-pass">✅ Compliant</span>'
                expanded = False
            elif detected and not compliant:
                badge = '<span class="badge-warn">⚠️ Detected (Non-Compliant)</span>'
                expanded = True
            else:
                badge = '<span class="badge-fail">❌ Missing Declaration</span>'
                expanded = True

            with st.expander(f"{meta['icon']} {meta['title']}", expanded=expanded):
                st.markdown(f"**Statutory Reference:** `{meta['statute']}`")
                st.markdown(f"**Compliance Status:** {badge}", unsafe_allow_html=True)
                
                if detected and value:
                    st.markdown(f"**Extracted Text:** `{value}`")
                else:
                    st.markdown("**Extracted Text:** *None detected*")
                
                if compliant:
                    st.success(remarks)
                elif detected and not compliant:
                    st.warning(remarks)
                else:
                    st.error(remarks)

        # Raw OCR Text Section
        with st.expander("📝 Raw OCR Extracted Text", expanded=False):
            if raw_text:
                st.text_area("Extracted OCR Content:", value=raw_text, height=180)
            else:
                st.write("No text extracted.")

    elif not audit_button:
        st.info("💡 Upload or capture an image on the left, then click **'Run Compliance Audit'** to view the statutory breakdown.")
