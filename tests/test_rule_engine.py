import pytest
from rule_engine import StatutoryRuleEngine, calculate_mpe
from schemas import InspectionStatus

def test_mpe_calculation():
    # 500g declared -> MPE is 15g
    assert calculate_mpe(500.0, "g") == 15.0
    # 100g declared -> MPE is 4.5g
    assert calculate_mpe(100.0, "g") == 4.5
    # 1kg declared -> MPE is 0.015 kg (15g)
    assert calculate_mpe(1.0, "kg") == 0.015

def test_physical_verification_compliant():
    res = StatutoryRuleEngine.verify_physical_quantity(
        declared_qty=500.0,
        unit="g",
        measured_qty=495.0 # Shortfall of 5g is within 15g MPE
    )
    assert res.is_within_mpe_limit is True
    assert res.status == "WITHIN_TOLERANCE"

def test_physical_verification_deficit_violation():
    # Mentor's exact case: 500g label vs 430g inside (-70g deficit)
    res = StatutoryRuleEngine.verify_physical_quantity(
        declared_qty=500.0,
        unit="g",
        measured_qty=430.0
    )
    assert res.is_within_mpe_limit is False
    assert res.status == "DEFICIT_VIOLATION"
    assert res.deficit_or_excess == -70.0
    assert "DEFICIT VIOLATION" in res.remarks

def test_3tier_verdict_physical_verification_required():
    # All visual declarations pass, but physical inspection not performed
    status = StatutoryRuleEngine.determine_final_status(
        violations_count=0,
        physical_verified=False
    )
    assert status == InspectionStatus.PHYSICAL_VERIFICATION_REQUIRED

def test_3tier_verdict_compliant():
    # Visual declarations pass AND physical inspection passes
    status = StatutoryRuleEngine.determine_final_status(
        violations_count=0,
        physical_verified=True,
        physical_is_compliant=True
    )
    assert status == InspectionStatus.COMPLIANT

def test_3tier_verdict_non_compliant():
    # Any violation -> Non-compliant
    status = StatutoryRuleEngine.determine_final_status(
        violations_count=1,
        physical_verified=True,
        physical_is_compliant=True
    )
    assert status == InspectionStatus.NON_COMPLIANT
