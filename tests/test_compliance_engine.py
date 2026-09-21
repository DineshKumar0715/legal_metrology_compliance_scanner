import pytest
from compliance_engine import ComplianceEngine


@pytest.fixture
def engine():
    return ComplianceEngine()


def test_mrp_compliant(engine):
    text = "MRP Rs. 250.00 (inclusive of all taxes)"
    res = engine.check_mrp(text)
    assert res.detected is True
    assert res.compliant is True
    assert "250.00" in res.value or "250" in res.value


def test_mrp_missing_tax_clause(engine):
    text = "MRP: Rs. 100.00 ONLY"
    res = engine.check_mrp(text)
    assert res.detected is True
    assert res.compliant is False
    assert "inclusive of all taxes" in res.remarks.lower()


def test_net_quantity_standard_unit(engine):
    text = "Net Weight: 500 g"
    res = engine.check_net_quantity(text)
    assert res.detected is True
    assert res.compliant is True
    assert "500 g" in res.value


def test_net_quantity_illegal_gm_unit(engine):
    text = "Net Quantity: 500 gm"
    res = engine.check_net_quantity(text)
    assert res.detected is True
    assert res.compliant is False
    assert "gm" in res.remarks.lower()


def test_net_quantity_illegal_gms_unit(engine):
    text = "Net Wt: 250 gms"
    res = engine.check_net_quantity(text)
    assert res.detected is True
    assert res.compliant is False


def test_date_of_packing_valid(engine):
    text = "Mfg Date: 05/2024"
    res = engine.check_date_of_packing(text)
    assert res.detected is True
    assert res.compliant is True


def test_date_of_packing_month_year_text(engine):
    text = "Packed on: May 2024"
    res = engine.check_date_of_packing(text)
    assert res.detected is True
    assert res.compliant is True


def test_consumer_care_full(engine):
    text = "Customer Care Helpline: 1800-222-3333, Email: support@brand.in"
    res = engine.check_consumer_care(text)
    assert res.detected is True
    assert res.compliant is True
    assert "1800-222-3333" in res.value


def test_consumer_care_missing_phone_email(engine):
    text = "For queries contact our Customer Care Department."
    res = engine.check_consumer_care(text)
    assert res.detected is True
    assert res.compliant is False


def test_manufacturer_details_valid(engine):
    text = "Mfg by: Royal Foods Pvt Ltd, Plot 12, Industrial Area, Mumbai 400001"
    res = engine.check_manufacturer_details(text)
    assert res.detected is True
    assert res.compliant is True


def test_country_of_origin_valid(engine):
    text = "Country of Origin: India"
    res = engine.check_country_of_origin(text)
    assert res.detected is True
    assert res.compliant is True


def test_evaluate_compliance_full_pass(engine):
    sample_text = """
    PREMIUM WHOLE WHEAT BISCUITS
    Net Quantity: 500 g
    MRP: Rs. 95.00 (inclusive of all taxes)
    Mfg by: Golden Bake Foods Pvt Ltd, Pune 411018
    Date of Mfg: 05/2024
    Customer Care Helpline: 1800-222-3333 | Email: care@goldenbake.com
    Country of Origin: India
    """
    response = engine.evaluate_compliance(sample_text)
    assert response.status == "COMPLIANT"
    assert response.overall_compliance_score == 100.0
    assert response.violations_count == 0


def test_evaluate_compliance_with_violations(engine):
    sample_text = """
    COOKIE TREAT
    Net Quantity: 500 gm
    MRP: Rs. 100
    Mfg by: Apex Confectionery, Mumbai 400001
    Date of Mfg: 04/2024
    """
    response = engine.evaluate_compliance(sample_text)
    assert response.status == "NON_COMPLIANT"
    assert response.violations_count > 0
    assert response.overall_compliance_score < 100.0
