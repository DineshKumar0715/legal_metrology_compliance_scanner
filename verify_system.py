import io
import sys
import requests
from PIL import Image, ImageDraw

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_verification():
    print("==================================================")
    print("⚖️ LEGAL METROLOGY SCANNER — VERIFICATION SUITE")
    print("==================================================")

    # 1. Health check
    print("\n[STEP 1] Testing Health Endpoint (GET /)...")
    resp = requests.get("http://127.0.0.1:8000/")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    health_data = resp.json()
    print(" Response:", health_data)
    assert health_data["status"] == "active"
    print("✅ Health check passed!")

    # 2. Test Compliant Sample
    print("\n[STEP 2] Testing Compliant Packaged Commodity Label...")
    img1 = Image.new("RGB", (700, 480), color=(255, 255, 255))
    draw1 = ImageDraw.Draw(img1)
    lines_compliant = [
        "COMMODITY: Nutri Delight Whole Wheat Biscuits",
        "NET QUANTITY: 500 g",
        "MRP: Rs. 95.00 (inclusive of all taxes)",
        "MFD & PKD BY: Golden Bake Foods Pvt Ltd, Industrial Area, Sector 4, Pune 411018",
        "DATE OF MFG: 05/2024",
        "CONSUMER CARE: Helpline: 1800-222-3333 | Email: care@goldenbake.com",
        "COUNTRY OF ORIGIN: India",
    ]
    y = 30
    for line in lines_compliant:
        draw1.text((30, y), line, fill=(0, 0, 0))
        y += 50

    buf1 = io.BytesIO()
    img1.save(buf1, format="PNG")
    buf1.seek(0)

    resp1 = requests.post(
        "http://127.0.0.1:8000/scan-label",
        files={"file": ("compliant_sample.png", buf1.getvalue(), "image/png")},
    )
    assert resp1.status_code == 200, f"Expected 200, got {resp1.status_code}"
    data1 = resp1.json()
    print(" Overall Status:", data1["status"])
    print(f" Compliance Score: {data1['overall_compliance_score']}%")
    print(" Violations Count:", data1["violations_count"])
    for key, decl in data1["declarations"].items():
        print(f"   • {key}: detected={decl['detected']}, compliant={decl['compliant']}, value='{decl['value']}'")

    assert data1["status"] == "COMPLIANT"
    assert data1["overall_compliance_score"] == 100.0
    assert data1["violations_count"] == 0
    print("✅ Compliant label verification passed!")

    # 3. Test Non-Compliant Sample (500 gm + missing tax text)
    print("\n[STEP 3] Testing Non-Compliant Label ('500 gm' + Missing Tax Clause)...")
    img2 = Image.new("RGB", (700, 480), color=(255, 255, 255))
    draw2 = ImageDraw.Draw(img2)
    lines_noncompliant = [
        "COMMODITY: Super Crunch Cookies",
        "NET QUANTITY: 500 gm",  # VIOLATION: gm instead of g
        "MRP: Rs. 100",        # VIOLATION: missing 'incl. of all taxes'
        "MFD & PKD BY: Apex Confectionery Works, Mumbai 400001",
        "DATE OF MFG: 04/2024",
        "CONSUMER CARE: Helpline: 1800-111-2222 | Email: support@apex.in",
        "COUNTRY OF ORIGIN: India",
    ]
    y = 30
    for line in lines_noncompliant:
        draw2.text((30, y), line, fill=(0, 0, 0))
        y += 50

    buf2 = io.BytesIO()
    img2.save(buf2, format="PNG")
    buf2.seek(0)

    resp2 = requests.post(
        "http://127.0.0.1:8000/scan-label",
        files={"file": ("non_compliant_sample.png", buf2.getvalue(), "image/png")},
    )
    assert resp2.status_code == 200, f"Expected 200, got {resp2.status_code}"
    data2 = resp2.json()
    print(" Overall Status:", data2["status"])
    print(f" Compliance Score: {data2['overall_compliance_score']}%")
    print(" Violations Count:", data2["violations_count"])
    print(" [Violation 1] MRP remarks:", data2["declarations"]["mrp"]["remarks"])
    print(" [Violation 2] Net Qty remarks:", data2["declarations"]["net_quantity"]["remarks"])

    assert data2["status"] == "NON_COMPLIANT"
    assert data2["declarations"]["mrp"]["compliant"] is False
    assert data2["declarations"]["net_quantity"]["compliant"] is False
    print("✅ Non-compliant label detection verified successfully!")

    # 4. Test Realistic Complex Wrapper (Parle-G Style Yellow Striped Packaging)
    print("\n[STEP 4] Testing Real FMCG Wrapper (Parle-G Biscuit Style)...")
    img3 = Image.new("RGB", (800, 320), color=(255, 230, 0))
    draw3 = ImageDraw.Draw(img3)
    for i in range(0, 800, 40):
        draw3.line([(i, 0), (i + 100, 320)], fill=(255, 245, 120), width=12)
    draw3.rectangle([(20, 20), (220, 90)], fill=(200, 20, 20))
    draw3.text((40, 35), "Parle-G", fill=(255, 255, 255))
    draw3.text((250, 30), "PKD: 08/24   BATCH: B12   USE BY: 02/25", fill=(30, 30, 30))
    draw3.text((250, 70), "NET WT. 55 g   MRP Rs. 5.00 (INCL. OF ALL TAXES)", fill=(30, 30, 30))
    draw3.text((250, 110), "Mfd. by Parle Products Pvt. Ltd., Mumbai 400057", fill=(30, 30, 30))
    draw3.text((250, 150), "Consumer Care: 1800-222-7777 | customercare@parle.biz", fill=(30, 30, 30))
    draw3.text((250, 190), "Made in India | Country of Origin: India", fill=(30, 30, 30))

    buf3 = io.BytesIO()
    img3.save(buf3, format="PNG")
    buf3.seek(0)

    resp3 = requests.post(
        "http://127.0.0.1:8000/scan-label",
        files={"file": ("parle_g_sample.png", buf3.getvalue(), "image/png")},
    )
    assert resp3.status_code == 200, f"Expected 200, got {resp3.status_code}"
    data3 = resp3.json()
    print(" Overall Status:", data3["status"])
    print(f" Compliance Score: {data3['overall_compliance_score']}%")
    print(" Violations Count:", data3["violations_count"])
    for key, decl in data3["declarations"].items():
        print(f"   • {key}: detected={decl['detected']}, compliant={decl['compliant']}, value='{decl['value']}'")
    assert data3["status"] == "COMPLIANT"
    assert data3["overall_compliance_score"] == 100.0
    print("✅ Complex packaging wrapper OCR & compliance verified successfully!")

    # 5. Test Streamlit Dashboard Connection
    print("\n[STEP 5] Testing Streamlit Frontend Accessibility (GET http://localhost:8501)...")
    st_resp = requests.get("http://localhost:8501")
    assert st_resp.status_code == 200
    print("✅ Streamlit Dashboard is accessible and returning HTTP 200!")

    print("\n==================================================")
    print("🎉 ALL VERIFICATIONS COMPLETED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    run_verification()
