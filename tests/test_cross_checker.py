import pytest
from cross_checker import CrossSourceConsistencyEngine
from schemas import ComplianceResponse, ExtractedField, EcommerceProductListing, InspectionStatus

def test_multi_panel_conflict_detection():
    # Panel 1 says 500 g, Panel 2 says 450 g
    rep1 = ComplianceResponse(
        status=InspectionStatus.PHYSICAL_VERIFICATION_REQUIRED,
        package_declaration_score=100.0,
        applicable_rules_count=6,
        passed_rules_count=6,
        violations_count=0,
        declarations={
            "net_quantity": ExtractedField(detected=True, value="500 g", compliant=True, remarks="Valid"),
            "mrp": ExtractedField(detected=True, value="Rs. 100", compliant=True, remarks="Valid")
        }
    )
    rep2 = ComplianceResponse(
        status=InspectionStatus.PHYSICAL_VERIFICATION_REQUIRED,
        package_declaration_score=100.0,
        applicable_rules_count=6,
        passed_rules_count=6,
        violations_count=0,
        declarations={
            "net_quantity": ExtractedField(detected=True, value="450 g", compliant=True, remarks="Valid"),
            "mrp": ExtractedField(detected=True, value="Rs. 120", compliant=True, remarks="Dual MRP")
        }
    )

    conflicts = CrossSourceConsistencyEngine.check_multi_panel_conflicts({
        "Front": rep1,
        "Back": rep2
    })

    assert len(conflicts) == 2
    assert any("Net Quantity" in c.field_name for c in conflicts)
    assert any("Maximum Retail Price" in c.field_name for c in conflicts)

def test_ecommerce_price_overcharge():
    pkg_rep = ComplianceResponse(
        status=InspectionStatus.PHYSICAL_VERIFICATION_REQUIRED,
        package_declaration_score=100.0,
        applicable_rules_count=6,
        passed_rules_count=6,
        violations_count=0,
        declarations={
            "mrp": ExtractedField(detected=True, value="Rs. 100 (inclusive of all taxes)", compliant=True, remarks="Valid"),
            "country_of_origin": ExtractedField(detected=True, value="India", compliant=True, remarks="Valid"),
            "net_quantity": ExtractedField(detected=True, value="500 g", compliant=True, remarks="Valid"),
        }
    )
    listing = EcommerceProductListing(
        title="Test Cookie Pack 500g",
        listed_mrp=150.0, # Listed price exceeds printed MRP of 100
        listed_net_quantity="500 g",
        country_of_origin="India",
        has_origin_filter=True
    )

    conflicts, violations = CrossSourceConsistencyEngine.cross_check_ecommerce_listing(listing, pkg_rep)
    assert len(conflicts) > 0
    assert any(v.violation_id == "VIOL-ECOMM-OVERCHARGE" for v in violations)
