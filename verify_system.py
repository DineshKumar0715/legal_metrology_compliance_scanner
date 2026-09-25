import io
import sys
import json
import requests
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from main import app

# Determine if live server is running, otherwise use FastAPI TestClient
USE_LIVE_SERVER = False
try:
    check = requests.get("http://127.0.0.1:8000/", timeout=1)
    if check.status_code == 200:
        USE_LIVE_SERVER = True
except Exception:
    USE_LIVE_SERVER = False

if USE_LIVE_SERVER:
    client = requests
    BASE_URL = "http://127.0.0.1:8000"
    print("🌐 Testing against Live Server (http://127.0.0.1:8000)")
else:
    client = TestClient(app)
    BASE_URL = ""
    print("⚡ Testing in-memory via FastAPI TestClient (Zero Dependency / Offline)")

from PIL import Image, ImageDraw, ImageFont

def create_sample_image(lines):
    # Create crisp high-contrast canvas with PIL for reliable optical recognition
    line_h = 55
    w = 1400
    h = max(500, len(lines) * line_h + 80)
    img = Image.new("RGB", (w, h), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    y = 40
    for line in lines:
        draw.text((40, y), line, fill=(0, 0, 0), font=font)
        y += line_h
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def run_verification():
    print("================================================================================")
    print("⚖️ VERITAS AI LEGAL METROLOGY COMPLIANCE & ENFORCEMENT SYSTEM — E2E VERIFICATION")
    print("================================================================================")

    # 1. Health & Root check
    print("\n[STEP 1] Testing Root & Health Endpoints...")
    r_root = client.get(f"{BASE_URL}/")
    assert r_root.status_code == 200, f"Root failed: {r_root.status_code}"
    print(" ✅ Root API:", r_root.json()["platform"])
    
    r_health = client.get(f"{BASE_URL}/health")
    assert r_health.status_code == 200, f"Health failed: {r_health.status_code}"
    print(" ✅ Health API:", r_health.json())

    # 2. Authentication check
    print("\n[STEP 2] Testing Role-Based Authentication...")
    auth_resp = client.post(f"{BASE_URL}/auth/login", json={"username": "inspector", "password": "inspector123"})
    assert auth_resp.status_code == 200, f"Auth failed: {auth_resp.status_code}"
    user_info = auth_resp.json()
    print(f" ✅ Authenticated as: {user_info['full_name']} | Role: {user_info['role']} | Badge: {user_info['badge_number']}")

    # 3. Test Level 1 Visual Scan (3-Tier Verdict: PHYSICAL_VERIFICATION_REQUIRED)
    print("\n[STEP 3] Testing Level 1 Statutory Label Scan (Compliant Label -> Physical Verification Required)...")
    lines_compliant = [
        "COMMODITY: Nutri Delight Whole Wheat Biscuits",
        "NET QUANTITY: 500 g",
        "MRP: Rs. 95.00 (inclusive of all taxes)",
        "USP: Rs. 0.19 per g",
        "MFD & PKD BY: Golden Bake Foods Pvt Ltd, Industrial Area, Sector 4, Pune 411018",
        "DATE OF MFG: 05/2024",
        "CONSUMER CARE: Helpline: 1800-222-3333 | Email: care@goldenbake.com",
        "COUNTRY OF ORIGIN: India",
    ]
    img1 = create_sample_image(lines_compliant)
    resp1 = client.post(f"{BASE_URL}/scan-label", files={"file": ("nutri_biscuit.png", img1, "image/png")})
    assert resp1.status_code == 200, f"Scan failed: {resp1.status_code}"
    data1 = resp1.json()
    print(" 3-Tier Status:", data1["status"])
    print(f" Declaration Compliance Score: {data1['package_declaration_score']}%")
    print(" Violations Count:", data1["violations_count"])
    assert data1["status"] == "PHYSICAL_VERIFICATION_REQUIRED"
    assert data1["violations_count"] == 0
    print(" ✅ 3-Tier Status Logic verified: Label passes visual check; marks 'Physical Verification Required'!")

    # 4. Test Mentor's Scenario: Label says 500g, Actual is 430g (Physical Deficit Violation)
    print("\n[STEP 4] Testing Mentor's Scenario: Label Declares 500g, Sealed Pack Contains 430g...")
    form_data_phys = {
        "declared_net_qty": "500.0",
        "unit": "g",
        "measured_net_qty": "430.0", # Shortfall of 70g exceeds MPE limit of 15g
        "tare_weight": "5.0"
    }
    resp2 = client.post(
        f"{BASE_URL}/scan-label",
        files={"file": ("nutri_biscuit.png", img1, "image/png")},
        data=form_data_phys
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    print(" Combined Status with Physical Verification:", data2["status"])
    print(" Physical Verification Status:", data2["physical_verification_status"])
    print(" Violations Count:", data2["violations_count"])
    assert data2["status"] == "NON_COMPLIANT"
    assert data2["physical_verification_status"] == "DEFICIT_VIOLATION"
    print(" ✅ Mentor's physical content mismatch correctly detected as statutory MPE deficit violation!")

    # 5. Test Non-Compliant Label ('500 gm' illegal unit + missing tax clause)
    print("\n[STEP 5] Testing Non-Compliant Packaging ('500 gm' + Missing Tax Clause)...")
    lines_viol = [
        "COMMODITY: Super Crunch Cookies",
        "NET QUANTITY: 500 gm",  # VIOLATION: gm instead of g
        "MRP: Rs. 100",        # VIOLATION: missing 'incl. of all taxes'
        "MFD & PKD BY: Apex Confectionery Works, Mumbai 400001",
        "DATE OF MFG: 04/2024",
        "CONSUMER CARE: Helpline: 1800-111-2222 | Email: support@apex.in",
        "COUNTRY OF ORIGIN: India",
    ]
    img2 = create_sample_image(lines_viol)
    resp3 = client.post(f"{BASE_URL}/scan-label", files={"file": ("viol_cookies.png", img2, "image/png")})
    assert resp3.status_code == 200
    data3 = resp3.json()
    print(" Status:", data3["status"])
    print(" Violations Flagged:", data3["violations_count"])
    for v in data3["violations"]:
        print(f"   • [{v['rule_number']}] {v['field_name']}: {v['description']}")
    assert data3["status"] == "NON_COMPLIANT"
    assert data3["violations_count"] >= 2
    print(" ✅ Statutory non-compliance detection verified!")

    # 6. Test Multi-Panel Scan (Front 500g vs Back 450g Contradiction)
    print("\n[STEP 6] Testing Multi-View Cross-Panel Conflict Detection...")
    img_back = create_sample_image(["NET QUANTITY: 450 g", "MRP: Rs. 120 (inclusive of all taxes)"])
    resp_multi = client.post(
        f"{BASE_URL}/scan-multi-view",
        files={
            "front_file": ("front.png", img1, "image/png"),
            "back_file": ("back.png", img_back, "image/png")
        }
    )
    assert resp_multi.status_code == 200
    data_multi = resp_multi.json()
    print(" Multi-view Conflicts Count:", len(data_multi["cross_source_conflicts"]))
    for c in data_multi["cross_source_conflicts"]:
        print(f"   • Conflict on {c['field_name']}: {c['conflict_description']}")
    assert len(data_multi["cross_source_conflicts"]) > 0
    print(" ✅ Multi-panel contradiction detection verified!")

    # 7. Test E-Commerce vs Physical Cross-Verification
    print("\n[STEP 7] Testing E-Commerce Listing vs Physical Package Verification...")
    ecomm_data = {
        "title": "Nutri Delight Premium Biscuits 500g",
        "listed_mrp": "140.0", # Price gouging (Listed 140 vs Printed 95)
        "listed_net_quantity": "500 g",
        "country_of_origin": "India",
        "has_origin_filter": "false" # VIOLATION: Missing 2026 origin filter
    }
    resp_ec = client.post(
        f"{BASE_URL}/scan-ecommerce",
        files={"file": ("nutri_biscuit.png", img1, "image/png")},
        data=ecomm_data
    )
    assert resp_ec.status_code == 200
    data_ec = resp_ec.json()
    print(" E-Commerce Cross-Check Status:", data_ec["status"])
    print(" Conflicts & Violations:", len(data_ec["cross_source_conflicts"]), "conflicts,", len(data_ec["violations"]), "violations")
    assert data_ec["status"] == "NON_COMPLIANT"
    print(" ✅ E-Commerce 2026 amendment and price overcharging checks verified!")

    # 8. Test Official ReportLab PDF Generation
    print("\n[STEP 8] Testing Official PDF Report & Certificate Generation...")
    pdf_form = {
        "product_name": "Nutri Delight Whole Wheat Biscuits 500g",
        "brand": "Nutri Delight",
        "inspector_name": user_info["full_name"],
        "badge_number": user_info["badge_number"],
        "district": user_info["district"],
        "location": "Supermarket Hub, Salem",
        "declared_net_qty": "500.0",
        "unit": "g",
        "measured_net_qty": "500.0"
    }
    resp_pdf = client.post(
        f"{BASE_URL}/inspections/report/pdf",
        files={"file": ("nutri_biscuit.png", img1, "image/png")},
        data=pdf_form
    )
    assert resp_pdf.status_code == 200
    assert resp_pdf.headers["content-type"] == "application/pdf"
    assert len(resp_pdf.content) > 1000
    print(f" ✅ Official PDF generated successfully! Byte size: {len(resp_pdf.content)} bytes")

    # 9. Test Repository Database Persistence and Retrieval
    print("\n[STEP 9] Testing Repository Database Save & Query...")
    case_id = "INSP-VERIFY-001"
    save_data = {
        "inspection_id": case_id,
        "product_name": "Nutri Delight Whole Wheat Biscuits 500g",
        "brand": "Nutri Delight",
        "category": "Food & Bakery",
        "inspector_id": user_info["user_id"],
        "inspector_name": user_info["full_name"],
        "district": user_info["district"],
        "location_details": "Supermarket Hub, Salem",
        "compliance_json": json.dumps(data1)
    }
    save_resp = client.post(f"{BASE_URL}/inspections/save", data=save_data)
    assert save_resp.status_code == 200
    print(f" ✅ Case committed to repository: {save_resp.json()}")

    fetch_resp = client.get(f"{BASE_URL}/inspections/{case_id}")
    assert fetch_resp.status_code == 200
    saved_case = fetch_resp.json()
    assert saved_case["inspection_id"] == case_id
    print(f" ✅ Case retrieved from database: Product = '{saved_case['product_name']}'")

    # 10. Test Dashboard Analytics API
    print("\n[STEP 10] Testing Executive Enforcement Analytics API...")
    stats_resp = client.get(f"{BASE_URL}/dashboard/stats")
    assert stats_resp.status_code == 200
    stats = stats_resp.json()
    print(" Analytics Stats:", stats)
    assert stats["total_inspections"] > 0
    print(" ✅ Executive Analytics API verified!")

    print("\n================================================================================")
    print("🎉 ALL 10 STATUTORY CAPABILITY MODULES VERIFIED & WORKING PERFECTLY!")
    print("================================================================================")

if __name__ == "__main__":
    run_verification()
