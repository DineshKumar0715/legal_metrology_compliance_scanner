import io
from PIL import Image, ImageDraw
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def create_test_image(text_lines):
    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    y = 20
    for line in text_lines:
        draw.text((20, y), line, fill=(0, 0, 0))
        y += 40
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "Active"
    assert "VERITAS" in data["platform"]


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["local_rule_engine_ready"] is True


def test_auth_login():
    response = client.post("/auth/login", json={"username": "inspector", "password": "inspector123"})
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "inspector"
    assert data["role"] == "INSPECTOR"


def test_physical_verify_api():
    # 500g declared vs 430g measured -> deficit violation
    payload = {
        "declared_net_quantity": 500.0,
        "unit": "g",
        "measured_actual_quantity": 430.0,
        "tare_weight": 0.0
    }
    response = client.post("/physical-verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_within_mpe_limit"] is False
    assert data["status"] == "DEFICIT_VIOLATION"


def test_dashboard_stats_api():
    response = client.get("/dashboard/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_inspections" in data
    assert "overall_compliance_rate" in data


def test_scan_label_e2e_image():
    lines = [
        "PREMIUM ORGANIC TEA",
        "Net Quantity: 250 g",
        "MRP: Rs. 150.00 (inclusive of all taxes)",
        "Mfg by: Assam Tea Valley, Guwahati 781001",
        "Date of Mfg: 06/2024",
        "Consumer Helpline: 1800-123-4567 | care@assamtea.in",
        "Country of Origin: India",
    ]
    img_bytes = create_test_image(lines)
    response = client.post(
        "/scan-label",
        files={"file": ("test_tea.png", img_bytes, "image/png")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "package_declaration_score" in data
    assert "declarations" in data
    assert "mrp" in data["declarations"]
    assert "net_quantity" in data["declarations"]
    assert "country_of_origin" in data["declarations"]
