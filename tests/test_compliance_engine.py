import pytest
from compliance_engine import ComplianceEngine
from schemas import InspectionStatus


@pytest.fixture
def engine():
    return ComplianceEngine()


def test_mrp_compliant(engine):
    text = "MRP Rs. 250.00 (inclusive of all taxes)"
    res = engine.rule_engine.evaluate_mrp(text)
    assert res.detected is True
    assert res.compliant is True
    assert "250.00" in res.value or "250" in res.value


def test_mrp_missing_tax_clause(engine):
    text = "MRP: Rs. 100.00 ONLY"
    res = engine.rule_engine.evaluate_mrp(text)
    assert res.detected is True
    assert res.compliant is False
    assert "inclusive of all taxes" in res.remarks.lower()


def test_net_quantity_standard_unit(engine):
    text = "Net Weight: 500 g"
    res = engine.rule_engine.evaluate_net_quantity(text)
    assert res.detected is True
    assert res.compliant is True
    assert "500 g" in res.value


def test_net_quantity_illegal_gm_unit(engine):
    text = "Net Quantity: 500 gm"
    res = engine.rule_engine.evaluate_net_quantity(text)
    assert res.detected is True
    assert res.compliant is False
    assert "gm" in res.remarks.lower()


def test_date_of_packing_valid(engine):
    text = "Mfg Date: 05/2024"
    res = engine.rule_engine.evaluate_date_of_packing(text)
    assert res.detected is True
    assert res.compliant is True


def test_consumer_care_full(engine):
    text = "Customer Care Helpline: 1800-222-3333, Email: support@brand.in"
    res = engine.rule_engine.evaluate_consumer_care(text)
    assert res.detected is True
    assert res.compliant is True
    assert "1800-222-3333" in res.value


def test_manufacturer_details_valid(engine):
    text = "Mfg by: Royal Foods Pvt Ltd, Plot 12, Industrial Area, Mumbai 400001"
    res = engine.rule_engine.evaluate_manufacturer_details(text)
    assert res.detected is True
    assert res.compliant is True


def test_country_of_origin_valid(engine):
    text = "Country of Origin: India"
    res = engine.rule_engine.evaluate_country_of_origin(text)
    assert res.detected is True
    assert res.compliant is True


def test_evaluate_compliance_3tier_without_physical(engine):
    sample_text = """
    PREMIUM WHOLE WHEAT BISCUITS
    Net Quantity: 500 g
    MRP: Rs. 95.00 (inclusive of all taxes)
    Mfg by: Golden Bake Foods Pvt Ltd, Pune 411018
    Date of Mfg: 05/2024
    Customer Care Helpline: 1800-222-3333 | Email: care@goldenbake.com
    Country of Origin: India
    USP: Rs. 0.19 per g
    """
    response = engine.evaluate_compliance(sample_text)
    # When visual checks pass and physical is not performed, verdict is PHYSICAL_VERIFICATION_REQUIRED
    assert response.status == InspectionStatus.PHYSICAL_VERIFICATION_REQUIRED
    assert response.package_declaration_score >= 90.0
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
    assert response.status == InspectionStatus.NON_COMPLIANT
    assert response.violations_count > 0
