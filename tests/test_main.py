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
    assert data["status"] == "active"
    assert "Legal Metrology" in data["service"]


def test_scan_label_invalid_file_type():
    response = client.post(
        "/scan-label",
        files={"file": ("test.txt", b"plain text", "text/plain")},
    )
    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_scan_label_empty_file():
    response = client.post(
        "/scan-label",
        files={"file": ("empty.png", b"", "image/png")},
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


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
    assert "overall_compliance_score" in data
    assert "declarations" in data
    assert "mrp" in data["declarations"]
    assert "net_quantity" in data["declarations"]
    assert "country_of_origin" in data["declarations"]

