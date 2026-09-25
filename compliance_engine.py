"""
Local Offline Compliance Engine for Legal Metrology Verification.
Performs deterministic statutory analysis, regex parsing, and 3-tier compliance scoring.
"""

from typing import Dict, List, Optional
from schemas import (
    ComplianceResponse,
    ExtractedField,
    ViolationDetail,
    InspectionStatus,
    PhysicalVerificationResult,
)
from rule_engine import StatutoryRuleEngine


class ComplianceEngine:
    """
    Offline Local Compliance Engine adhering to Legal Metrology (Packaged Commodities) Rules, 2011 (as amended).
    """

    def __init__(self):
        self.rule_engine = StatutoryRuleEngine()

    def evaluate_compliance(
        self,
        text: str,
        pdp_area_cm2: Optional[float] = None,
        physical_result: Optional[PhysicalVerificationResult] = None,
    ) -> ComplianceResponse:
        """
        Evaluates raw label text across all statutory clauses.
        Produces structured 3-tier verdict and violation list.
        """
        declarations, violations = self.rule_engine.evaluate_all(text, pdp_area_cm2)

        # Count applicable checks
        total_applicable = sum(1 for d in declarations.values() if d.applicable)
        passed_rules = sum(1 for d in declarations.values() if d.applicable and d.compliant)
        violations_count = len(violations)

        score = round((passed_rules / total_applicable) * 100.0, 2) if total_applicable > 0 else 0.0

        # Physical verification status
        physical_verified = physical_result is not None
        physical_compliant = physical_result.is_within_mpe_limit if physical_result else True
        phys_status = physical_result.status if physical_result else "NOT_VERIFIED"

        if physical_result and not physical_compliant:
            violations_count += 1
            violations.append(
                ViolationDetail(
                    violation_id="VIOL-PHYS-001",
                    rule_number="Rule 11 / First Schedule",
                    field_name="Actual Net Quantity Content",
                    severity="CRITICAL",
                    description=physical_result.remarks,
                    observed_value=f"{physical_result.measured_actual_quantity} {physical_result.unit}",
                    expected_condition=f"{physical_result.declared_net_quantity} {physical_result.unit} (within ±{physical_result.max_permissible_error_allowed})",
                    statutory_citation="Legal Metrology Act, 2009 Section 36 & PCR 2011 First Schedule (MPE Violation)",
                )
            )

        # Determine 3-Tier Status
        verdict = self.rule_engine.determine_final_status(
            violations_count=violations_count,
            physical_verified=physical_verified,
            physical_is_compliant=physical_compliant,
        )

        return ComplianceResponse(
            status=verdict,
            package_declaration_score=score,
            applicable_rules_count=total_applicable,
            passed_rules_count=passed_rules,
            violations_count=violations_count,
            violations=violations,
            declarations=declarations,
            physical_verification_status=phys_status,
            physical_verification_result=physical_result,
            raw_text=text,
            pdp_area_sq_cm=pdp_area_cm2,
        )
