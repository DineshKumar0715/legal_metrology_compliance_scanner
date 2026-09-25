"""
Multi-Input & Cross-Source Inconsistency Engine
Detects multi-panel contradictions (e.g. Front vs Back) and E-Commerce Listing vs Physical Package mismatches.
"""

import re
from typing import List, Dict, Optional, Tuple
from schemas import (
    CrossSourceConflict,
    EcommerceProductListing,
    ComplianceResponse,
    ViolationDetail,
    ViolationSeverity,
)

class CrossSourceConsistencyEngine:
    """
    Validates consistency across multiple packaging viewpoints and e-commerce listings.
    """

    @staticmethod
    def check_multi_panel_conflicts(
        panel_results: Dict[str, ComplianceResponse]
    ) -> List[CrossSourceConflict]:
        """
        Cross-checks declarations extracted from multiple angles (Front, Back, Side, etc.).
        Detects dual pricing (Rule 18), quantity discrepancy, and conflicting origins.
        """
        conflicts: List[CrossSourceConflict] = []
        panels = list(panel_results.keys())

        for i in range(len(panels)):
            for j in range(i + 1, len(panels)):
                p1, p2 = panels[i], panels[j]
                r1, r2 = panel_results[p1], panel_results[p2]

                # 1. Compare Net Quantity
                q1 = r1.declarations.get("net_quantity")
                q2 = r2.declarations.get("net_quantity")
                if q1 and q2 and q1.detected and q2.detected and q1.value and q2.value:
                    if q1.value.lower().replace(" ", "") != q2.value.lower().replace(" ", ""):
                        conflicts.append(CrossSourceConflict(
                            field_name="Net Quantity",
                            source_a=f"Panel: {p1}",
                            value_a=q1.value,
                            source_b=f"Panel: {p2}",
                            value_b=q2.value,
                            conflict_description=f"Conflicting Net Quantity declared across panels ({p1}: '{q1.value}' vs {p2}: '{q2.value}')."
                        ))

                # 2. Compare MRP (Dual Pricing Violation under Rule 18)
                m1 = r1.declarations.get("mrp")
                m2 = r2.declarations.get("mrp")
                if m1 and m2 and m1.detected and m2.detected and m1.value and m2.value:
                    # Extract numeric prices
                    n1 = re.findall(r"\d+(?:\.\d+)?", m1.value)
                    n2 = re.findall(r"\d+(?:\.\d+)?", m2.value)
                    if n1 and n2 and n1[0] != n2[0]:
                        conflicts.append(CrossSourceConflict(
                            field_name="Maximum Retail Price (MRP)",
                            source_a=f"Panel: {p1}",
                            value_a=m1.value,
                            source_b=f"Panel: {p2}",
                            value_b=m2.value,
                            conflict_description=f"Illegal Dual MRP detected across panels ({p1}: {m1.value} vs {p2}: {m2.value}). Violates Rule 18 prohibition against dual pricing."
                        ))

                # 3. Compare Country of Origin
                o1 = r1.declarations.get("country_of_origin")
                o2 = r2.declarations.get("country_of_origin")
                if o1 and o2 and o1.detected and o2.detected and o1.value and o2.value:
                    if o1.value.strip().lower() != o2.value.strip().lower():
                        conflicts.append(CrossSourceConflict(
                            field_name="Country of Origin",
                            source_a=f"Panel: {p1}",
                            value_a=o1.value,
                            source_b=f"Panel: {p2}",
                            value_b=o2.value,
                            conflict_description=f"Contradictory Country of Origin declared between {p1} and {p2}."
                        ))

        return conflicts

    @staticmethod
    def cross_check_ecommerce_listing(
        listing: EcommerceProductListing,
        package_response: ComplianceResponse
    ) -> Tuple[List[CrossSourceConflict], List[ViolationDetail]]:
        """
        Cross-checks E-commerce listing declaration against physical package evidence.
        Enforces 2026 E-commerce Country of Origin searchability amendment & price gouging checks.
        """
        conflicts: List[CrossSourceConflict] = []
        violations: List[ViolationDetail] = []

        # 1. 2026 Amendment Check: Country of Origin Search/Sort Filter
        if not listing.has_origin_filter:
            violations.append(ViolationDetail(
                violation_id="VIOL-ECOMM-2026-001",
                rule_number="Rule 6(10) (2026 Amendment)",
                field_name="E-Commerce Origin Filter",
                severity=ViolationSeverity.MAJOR,
                description="E-commerce listing fails to provide a searchable and sortable Country of Origin filter.",
                observed_value="Origin filter disabled/absent",
                expected_condition="Searchable and sortable Country of Origin filter enabled on marketplace",
                statutory_citation="Legal Metrology (Packaged Commodities) Amendment Rules, 2026 (Effective 1 July 2026)"
            ))

        # 2. Price Overcharge Check (Listing Price vs Package MRP)
        pkg_mrp_decl = package_response.declarations.get("mrp")
        if pkg_mrp_decl and pkg_mrp_decl.detected and pkg_mrp_decl.value:
            nums = re.findall(r"\d+(?:\.\d+)?", pkg_mrp_decl.value)
            if nums:
                pkg_mrp_num = float(nums[0])
                if listing.listed_mrp > pkg_mrp_num:
                    conflicts.append(CrossSourceConflict(
                        field_name="Maximum Retail Price (MRP)",
                        source_a="E-Commerce Listing",
                        value_a=f"₹{listing.listed_mrp}",
                        source_b="Physical Package Label",
                        value_b=f"₹{pkg_mrp_num}",
                        conflict_description=f"Listed price (₹{listing.listed_mrp}) exceeds physical package MRP (₹{pkg_mrp_num}). Illegal overcharging under Section 36(2)."
                    ))
                    violations.append(ViolationDetail(
                        violation_id="VIOL-ECOMM-OVERCHARGE",
                        rule_number="Section 36(2), LM Act 2009",
                        field_name="E-Commerce Price Inflation",
                        severity=ViolationSeverity.CRITICAL,
                        description=f"Online listed MRP (₹{listing.listed_mrp}) is higher than printed package MRP (₹{pkg_mrp_num}).",
                        observed_value=f"Listing: ₹{listing.listed_mrp} | Package: ₹{pkg_mrp_num}",
                        expected_condition="Online selling price must not exceed printed Maximum Retail Price",
                        statutory_citation="Legal Metrology Act, 2009 Section 36(2)"
                    ))

        # 3. Country of Origin Mismatch Check
        pkg_origin = package_response.declarations.get("country_of_origin")
        if pkg_origin and pkg_origin.detected and pkg_origin.value:
            if listing.country_of_origin.strip().lower() not in pkg_origin.value.strip().lower() and pkg_origin.value.strip().lower() not in listing.country_of_origin.strip().lower():
                conflicts.append(CrossSourceConflict(
                    field_name="Country of Origin",
                    source_a="E-Commerce Listing",
                    value_a=listing.country_of_origin,
                    source_b="Physical Package Label",
                    value_b=pkg_origin.value,
                    conflict_description=f"Listing origin ('{listing.country_of_origin}') contradicts printed package origin ('{pkg_origin.value}')."
                ))
                violations.append(ViolationDetail(
                    violation_id="VIOL-ECOMM-ORIGIN-MISMATCH",
                    rule_number="Rule 6(1)(g) / E-Comm Rules",
                    field_name="Origin Misrepresentation",
                    severity=ViolationSeverity.MAJOR,
                    description=f"E-commerce listing origin ('{listing.country_of_origin}') does not match physical package origin ('{pkg_origin.value}').",
                    observed_value=f"Listing: {listing.country_of_origin} | Label: {pkg_origin.value}",
                    expected_condition="E-commerce listing origin declaration must match physical packaging exactly",
                    statutory_citation="Legal Metrology (Packaged Commodities) Rules, 2011 Rule 6 & Consumer Protection (E-Commerce) Rules"
                ))

        # 4. Net Quantity Mismatch Check
        pkg_qty = package_response.declarations.get("net_quantity")
        if pkg_qty and pkg_qty.detected and pkg_qty.value:
            # Simple check if numbers match
            nums_listing = re.findall(r"\d+(?:\.\d+)?", listing.listed_net_quantity)
            nums_pkg = re.findall(r"\d+(?:\.\d+)?", pkg_qty.value)
            if nums_listing and nums_pkg and nums_listing[0] != nums_pkg[0]:
                conflicts.append(CrossSourceConflict(
                    field_name="Net Quantity",
                    source_a="E-Commerce Listing",
                    value_a=listing.listed_net_quantity,
                    source_b="Physical Package Label",
                    value_b=pkg_qty.value,
                    conflict_description=f"E-commerce declared quantity ({listing.listed_net_quantity}) does not match physical packaging ({pkg_qty.value})."
                ))

        return conflicts, violations
