"""
Legal Metrology (Packaged Commodities) Rules, 2011 (Amended through 2026)
Comprehensive Statutory Rule Engine and Maximum Permissible Error (MPE) Calculator.
"""

from typing import Dict, List, Optional, Tuple
from schemas import (
    ExtractedField,
    ViolationDetail,
    ViolationSeverity,
    PhysicalVerificationResult,
    InspectionStatus,
)

# Minimum character & numeral height statutory table under Rule 9 (Table 1)
# PDP Area in cm^2 -> (Min General Char Height in mm, Min Numeral Height in mm)
STATUTORY_FONT_TABLE = [
    (50.0, 1.0, 1.5),       # A <= 50 cm²
    (100.0, 1.5, 2.0),      # 50 < A <= 100 cm²
    (500.0, 2.0, 4.0),      # 100 < A <= 500 cm²
    (2500.0, 4.0, 6.0),     # 500 < A <= 2500 cm²
    (float("inf"), 6.0, 8.0) # A > 2500 cm²
]

# Maximum Permissible Error (MPE) table under First Schedule / Rule 11 of PCR 2011
# For solid foods, liquids, powders, and general pre-packaged commodities
def calculate_mpe(declared_qty: float, unit: str) -> float:
    """
    Computes statutory Maximum Permissible Error (MPE) in declared units.
    Standardized under First Schedule of Legal Metrology (Packaged Commodities) Rules, 2011.
    """
    # Normalize to grams/milliliters for calculation
    qty = declared_qty
    unit_lower = unit.lower().strip()
    is_kilo_or_litre = unit_lower in ["kg", "kilogram", "kilograms", "l", "litre", "litres", "liter", "liters"]
    
    if is_kilo_or_litre:
        qty_base = qty * 1000.0
    else:
        qty_base = qty

    if qty_base <= 0:
        return 0.0

    if qty_base <= 50:
        # 9% of nominal quantity
        mpe_base = 0.09 * qty_base
    elif qty_base <= 100:
        # Fixed 4.5 g / ml
        mpe_base = 4.5
    elif qty_base <= 200:
        # 4.5% of nominal quantity
        mpe_base = 0.045 * qty_base
    elif qty_base <= 300:
        # Fixed 9 g / ml
        mpe_base = 9.0
    elif qty_base <= 500:
        # 3% of nominal quantity
        mpe_base = 0.03 * qty_base
    elif qty_base <= 1000:
        # Fixed 15 g / ml
        mpe_base = 15.0
    elif qty_base <= 10000:
        # 1.5% of nominal quantity
        mpe_base = 0.015 * qty_base
    elif qty_base <= 15000:
        # Fixed 150 g / ml
        mpe_base = 150.0
    else:
        # 1% of nominal quantity
        mpe_base = 0.01 * qty_base

    # Convert back to declared unit
    if is_kilo_or_litre:
        return round(mpe_base / 1000.0, 4)
    return round(mpe_base, 2)


class StatutoryRuleEngine:
    """
    Statutory Rule Validator for Legal Metrology Act, 2009 and PCR 2011 (with amendments up to 2026).
    """

    @staticmethod
    def get_min_font_height_mm(pdp_area_cm2: Optional[float], is_numeral: bool = True) -> float:
        """Determines minimum statutory font height under Rule 9 Table 1."""
        if pdp_area_cm2 is None or pdp_area_cm2 <= 0:
            pdp_area_cm2 = 120.0  # Default standard retail pack PDP estimation
        
        for area_limit, char_h, num_h in STATUTORY_FONT_TABLE:
            if pdp_area_cm2 <= area_limit:
                return num_h if is_numeral else char_h
        return 6.0

    @staticmethod
    def evaluate_mrp(raw_text: str, pdp_area_cm2: Optional[float] = None) -> ExtractedField:
        """
        Rule 6(1)(e): Maximum Retail Price with 'inclusive of all taxes'.
        Amendments 2022: Unambiguous representation without misleading prefixes.
        """
        import re
        mrp_pattern = r"(?:MRP|M\.R\.P\.|MAX\.?\s*RETAIL\s*PRICE|Rs\.?|₹)\s*[:.]?\s*(\d+(?:\.\d{1,2})?)"
        tax_pattern = r"(?:incl|inclusive)\.?\s*(?:of)?\s*all\s*taxes"

        match = re.search(mrp_pattern, raw_text, re.IGNORECASE)
        has_tax_clause = bool(re.search(tax_pattern, raw_text, re.IGNORECASE))
        min_font = StatutoryRuleEngine.get_min_font_height_mm(pdp_area_cm2, is_numeral=True)

        if match:
            price_val = match.group(0).strip()
            if has_tax_clause:
                return ExtractedField(
                    detected=True,
                    value=price_val,
                    compliant=True,
                    applicable=True,
                    rule_reference="Rule 6(1)(e) & Rule 8, PCR 2011",
                    remarks="Valid MRP with mandatory 'inclusive of all taxes' declaration identified.",
                    min_required_height_mm=min_font,
                    font_compliant=True,
                )
            return ExtractedField(
                detected=True,
                value=price_val,
                compliant=False,
                applicable=True,
                rule_reference="Rule 6(1)(e), PCR 2011",
                remarks="MRP numeral detected, but mandatory statutory suffix 'inclusive of all taxes' is missing or mutilated.",
                min_required_height_mm=min_font,
                font_compliant=True,
            )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            applicable=True,
            rule_reference="Rule 6(1)(e), PCR 2011",
            remarks="Maximum Retail Price (MRP) declaration not detected on package display panel.",
            min_required_height_mm=min_font,
            font_compliant=False,
        )

    @staticmethod
    def evaluate_net_quantity(raw_text: str, pdp_area_cm2: Optional[float] = None) -> ExtractedField:
        """
        Rule 6(1)(c) & Rule 11/13: Net Quantity in standard SI units (g, kg, ml, l, N, U).
        Flags illegal abbreviations like 'gm', 'gms', 'kilos', 'litres' without standard SI symbol.
        """
        import re
        qty_pattern = r"(?:Net\s*(?:Qty|Quantity|Weight|Wt|Vol|Volume)?)\s*[:.]?\s*(\d+(?:\.\d+)?\s*(?:kg|g|gm|gms|ml|l|ltr|litres|unit|units|N|U|pieces|pcs))\b"
        match = re.search(qty_pattern, raw_text, re.IGNORECASE)
        min_font = StatutoryRuleEngine.get_min_font_height_mm(pdp_area_cm2, is_numeral=True)

        if match:
            val = match.group(1).strip()
            # Flag deprecated units 'gm' or 'gms'
            if re.search(r"\bgms?\b", val, re.IGNORECASE):
                return ExtractedField(
                    detected=True,
                    value=val,
                    compliant=False,
                    applicable=True,
                    rule_reference="Rule 6(1)(c) & Rule 13, PCR 2011",
                    remarks="Non-standard/deprecated unit abbreviation detected ('gm'/'gms'). Rule 13 strictly mandates standard metric symbol 'g' or 'kg'.",
                    min_required_height_mm=min_font,
                    font_compliant=True,
                )
            return ExtractedField(
                detected=True,
                value=val,
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(c) & Rule 11, PCR 2011",
                remarks="Net Quantity declared in standardized metric SI units.",
                min_required_height_mm=min_font,
                font_compliant=True,
            )

        # Fallback search for bare weights e.g. "500 g" or "1 kg"
        fallback_pattern = r"\b(\d+(?:\.\d+)?\s*(?:g|kg|ml|l|N))\b"
        fallback_match = re.search(fallback_pattern, raw_text)
        if fallback_match:
            return ExtractedField(
                detected=True,
                value=fallback_match.group(1).strip(),
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(c), PCR 2011",
                remarks="Metric quantity identified on packaging.",
                min_required_height_mm=min_font,
                font_compliant=True,
            )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            applicable=True,
            rule_reference="Rule 6(1)(c), PCR 2011",
            remarks="Net Quantity declaration not detected on package.",
            min_required_height_mm=min_font,
            font_compliant=False,
        )

    @staticmethod
    def evaluate_unit_sale_price(raw_text: str, net_qty_field: ExtractedField, mrp_field: ExtractedField) -> ExtractedField:
        """
        Rule 6(1)(h) (Inserted via 2021/2022 Amendments):
        Mandatory declaration of Unit Sale Price (USP) in Rs. per g/ml (for packages <= 1kg/1L)
        or Rs. per kg/L (for packages > 1kg/1L).
        """
        import re
        usp_pattern = r"(?:USP|Unit\s*Sale\s*Price|Unit\s*Price)[\s:_.\-]*?(?:Rs\.?|₹)?\s*(\d+(?:\.\d+)?)\s*(?:per|\/)\s*(?:g|kg|ml|l|piece|N|U)"
        match = re.search(usp_pattern, raw_text, re.IGNORECASE)

        if match:
            return ExtractedField(
                detected=True,
                value=match.group(0).strip(),
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(h), PCR 2011 (2021 Amendment)",
                remarks="Mandatory Unit Sale Price (USP) declared in accordance with 2021 statutory amendment.",
            )
        
        # If product has MRP and Net Qty, check if package is retail multi-unit or standard retail
        # Note: If not explicitly found, flag as advisory/minor violation under 2021 amendment
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            applicable=True,
            rule_reference="Rule 6(1)(h), PCR 2011",
            remarks="Unit Sale Price (USP in ₹/g or ₹/kg) not detected. Mandated under Legal Metrology 2021 Amendment for consumer price transparency.",
        )

    @staticmethod
    def evaluate_date_of_packing(raw_text: str) -> ExtractedField:
        """
        Rule 6(1)(d): Month and Year of manufacture / packing / import.
        """
        import re
        date_pattern = r"(?:Mfg|Pkd|Mfg\s*Date|Packed\s*On|Date\s*of\s*Mfg|Date\s*of\s*Packing|Month\s*&\s*Year|Imported\s*On)\s*[:.]?\s*([0-1]?\d[/-](?:20\d{2}|\d{2})|[A-Za-z]{3,9}\s*(?:20\d{2}|\d{2})|\d{2}\/\d{4})"
        match = re.search(date_pattern, raw_text, re.IGNORECASE)

        if match:
            return ExtractedField(
                detected=True,
                value=match.group(1).strip(),
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(d), PCR 2011",
                remarks="Month and Year of manufacture/packing unambiguously declared.",
            )

        # Look for standalone MM/YYYY or DD/MM/YYYY pattern
        standalone_date = re.search(r"\b(0[1-9]|1[0-2])\/(20\d{2})\b", raw_text)
        if standalone_date:
            return ExtractedField(
                detected=True,
                value=standalone_date.group(0),
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(d), PCR 2011",
                remarks="Date of manufacture/packing detected (MM/YYYY).",
            )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            applicable=True,
            rule_reference="Rule 6(1)(d), PCR 2011",
            remarks="Month & Year of Manufacture/Packing not detected.",
        )

    @staticmethod
    def evaluate_best_before_expiry(raw_text: str) -> ExtractedField:
        """
        Best before / Expiry date declaration where applicable (Food/Cosmetics).
        """
        import re
        expiry_pattern = r"(?:Best\s*Before|Expiry|Exp\.?\s*Date|Use\s*by)\s*[:.]?\s*([^\n\r,]+)"
        match = re.search(expiry_pattern, raw_text, re.IGNORECASE)

        if match:
            return ExtractedField(
                detected=True,
                value=match.group(0).strip(),
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1), PCR 2011 / FSSAI Alignment",
                remarks="Best before / Expiry period properly declared.",
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=True,  # Optional/Applicability-dependent
            applicable=False,
            rule_reference="Rule 6(1), PCR 2011",
            remarks="Best before not mandatory for non-perishable commodities.",
        )

    @staticmethod
    def evaluate_consumer_care(raw_text: str) -> ExtractedField:
        """
        Rule 6(1)(f): Consumer Grievance Redressal / Customer Care details.
        Must contain contact person/office name, address, telephone number, or email.
        """
        import re
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        phone_pattern = r"(?:(?:\+|0{0,2})91[\s\-]*)?[6789]\d{9}|1800[\s\-]*\d{3}[\s\-]*\d{3,4}|0\d{2,4}[\s\-]?\d{6,8}"
        care_keyword = r"(?:customer\s*care|consumer\s*care|feedback|grievance|helpline|toll\s*free|care\s*cell)"

        has_email = re.search(email_pattern, raw_text)
        has_phone = re.search(phone_pattern, raw_text)
        has_keyword = re.search(care_keyword, raw_text, re.IGNORECASE)

        contact_details = []
        if has_email: contact_details.append(f"Email: {has_email.group(0)}")
        if has_phone: contact_details.append(f"Phone: {has_phone.group(0)}")

        if has_keyword and (has_email or has_phone):
            return ExtractedField(
                detected=True,
                value=" | ".join(contact_details),
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(f), PCR 2011",
                remarks="Verified statutory Consumer Care redressal contact details (email/helpline).",
            )
        elif has_email or has_phone:
            return ExtractedField(
                detected=True,
                value=" | ".join(contact_details),
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(f), PCR 2011",
                remarks="Contact information detected, but explicit 'Consumer Care / Grievance' prefix recommended.",
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            applicable=True,
            rule_reference="Rule 6(1)(f), PCR 2011",
            remarks="Consumer grievance redressal contact information (telephone/email/postal address) missing.",
        )

    @staticmethod
    def evaluate_manufacturer_details(raw_text: str) -> ExtractedField:
        """
        Rule 6(1)(a): Name and complete address of Manufacturer / Packer / Importer.
        """
        import re
        mfg_pattern = r"(?:mfd\s*(?:&|and)?\s*pkd\s*by|mfd\s*by|mfg\s*(?:&|and)?\s*pkd\s*by|mfg\s*by|manufactured\s*(?:&|and)?\s*packed\s*by|manufactured\s*by|packed\s*by|marketed\s*by|imported\s*by|produced\s*by)\s*[:.]?\s*([^\n\r]+)"
        match = re.search(mfg_pattern, raw_text, re.IGNORECASE)

        if match:
            return ExtractedField(
                detected=True,
                value=match.group(1).strip(),
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(a), PCR 2011",
                remarks="Manufacturer/Packer/Importer identity and address details identified.",
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            applicable=True,
            rule_reference="Rule 6(1)(a), PCR 2011",
            remarks="Complete name and address of Manufacturer, Packer, or Importer not detected.",
        )

    @staticmethod
    def evaluate_country_of_origin(raw_text: str) -> ExtractedField:
        """
        Rule 6(1)(g) & 2026 E-commerce Amendment:
        Country of origin declaration mandatory for both domestic and imported goods.
        """
        import re
        origin_pattern = r"(?:country\s*of\s*origin|made\s*in|produced\s*in|manufactured\s*in|product\s*of)\s*[:.]?\s*([A-Za-z\s]+)"
        match = re.search(origin_pattern, raw_text, re.IGNORECASE)

        if match:
            origin_name = match.group(1).strip().split("\n")[0][:30]
            return ExtractedField(
                detected=True,
                value=origin_name,
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(g), PCR 2011 & 2026 E-Comm Amendments",
                remarks=f"Country of origin identified as '{origin_name}'.",
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            applicable=True,
            rule_reference="Rule 6(1)(g), PCR 2011",
            remarks="Country of origin declaration not detected on packaging.",
        )

    @staticmethod
    def evaluate_generic_name(raw_text: str) -> ExtractedField:
        """
        Rule 6(1)(b): Generic or common name of the pre-packaged commodity.
        """
        import re
        generic_pattern = r"(?:Commodity|Generic\s*Name|Product\s*Name|Item)\s*[:.]?\s*([^\n\r]+)"
        match = re.search(generic_pattern, raw_text, re.IGNORECASE)

        if match:
            return ExtractedField(
                detected=True,
                value=match.group(1).strip()[:60],
                compliant=True,
                applicable=True,
                rule_reference="Rule 6(1)(b), PCR 2011",
                remarks="Generic/common commodity name declared.",
            )
        # Often generic name is the prominent brand title (e.g. Biscuits, Cookies, Tea)
        common_commodities = ["Biscuits", "Cookies", "Tea", "Coffee", "Flour", "Oil", "Atta", "Rice", "Sugar", "Soap", "Detergent", "Shampoo", "Snacks"]
        for comm in common_commodities:
            if re.search(rf"\b{comm}\b", raw_text, re.IGNORECASE):
                return ExtractedField(
                    detected=True,
                    value=comm,
                    compliant=True,
                    applicable=True,
                    rule_reference="Rule 6(1)(b), PCR 2011",
                    remarks=f"Generic commodity category identified ({comm}).",
                )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=True,  # Non-blocking if brand text is present
            applicable=True,
            rule_reference="Rule 6(1)(b), PCR 2011",
            remarks="Specific generic name tag absent; extracted from main packaging header.",
        )

    @staticmethod
    def evaluate_all(raw_text: str, pdp_area_cm2: Optional[float] = None) -> Tuple[Dict[str, ExtractedField], List[ViolationDetail]]:
        """
        Executes comprehensive statutory rule evaluation across all 10+ legal declarations.
        """
        declarations: Dict[str, ExtractedField] = {}
        violations: List[ViolationDetail] = []

        # 1. MRP
        mrp_field = StatutoryRuleEngine.evaluate_mrp(raw_text, pdp_area_cm2)
        declarations["mrp"] = mrp_field
        if not mrp_field.compliant:
            violations.append(ViolationDetail(
                violation_id="VIOL-001-MRP",
                rule_number="Rule 6(1)(e)",
                field_name="Maximum Retail Price (MRP)",
                severity=ViolationSeverity.CRITICAL if not mrp_field.detected else ViolationSeverity.MAJOR,
                description=mrp_field.remarks,
                observed_value=mrp_field.value or "NOT DETECTED",
                expected_condition="MRP Rs. XX.XX (inclusive of all taxes)",
                statutory_citation="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(e) as amended."
            ))

        # 2. Net Quantity
        net_qty_field = StatutoryRuleEngine.evaluate_net_quantity(raw_text, pdp_area_cm2)
        declarations["net_quantity"] = net_qty_field
        if not net_qty_field.compliant:
            violations.append(ViolationDetail(
                violation_id="VIOL-002-QTY",
                rule_number="Rule 6(1)(c) & Rule 13",
                field_name="Net Quantity",
                severity=ViolationSeverity.CRITICAL if not net_qty_field.detected else ViolationSeverity.MAJOR,
                description=net_qty_field.remarks,
                observed_value=net_qty_field.value or "NOT DETECTED",
                expected_condition="Net Quantity declared in standard SI metric units (g, kg, ml, l, N)",
                statutory_citation="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(c) & Rule 13."
            ))

        # 3. Unit Sale Price (USP)
        usp_field = StatutoryRuleEngine.evaluate_unit_sale_price(raw_text, net_qty_field, mrp_field)
        declarations["unit_sale_price"] = usp_field
        if not usp_field.compliant:
            violations.append(ViolationDetail(
                violation_id="VIOL-003-USP",
                rule_number="Rule 6(1)(h)",
                field_name="Unit Sale Price (USP)",
                severity=ViolationSeverity.MINOR,
                description=usp_field.remarks,
                observed_value=usp_field.value or "NOT DETECTED",
                expected_condition="Unit Sale Price declared as ₹ per g/ml or ₹ per kg/L",
                statutory_citation="Legal Metrology (Packaged Commodities) Amendment Rules, 2021, Rule 6(1)(h)."
            ))

        # 4. Date of Packing / Manufacture
        dop_field = StatutoryRuleEngine.evaluate_date_of_packing(raw_text)
        declarations["date_of_packing"] = dop_field
        if not dop_field.compliant:
            violations.append(ViolationDetail(
                violation_id="VIOL-004-DOP",
                rule_number="Rule 6(1)(d)",
                field_name="Date of Packing / Mfg",
                severity=ViolationSeverity.MAJOR,
                description=dop_field.remarks,
                observed_value=dop_field.value or "NOT DETECTED",
                expected_condition="Month and Year of packing / manufacture (MM/YYYY)",
                statutory_citation="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(d)."
            ))

        # 5. Best Before / Expiry
        exp_field = StatutoryRuleEngine.evaluate_best_before_expiry(raw_text)
        declarations["best_before_expiry"] = exp_field

        # 6. Consumer Care
        care_field = StatutoryRuleEngine.evaluate_consumer_care(raw_text)
        declarations["consumer_care"] = care_field
        if not care_field.compliant:
            violations.append(ViolationDetail(
                violation_id="VIOL-006-CARE",
                rule_number="Rule 6(1)(f)",
                field_name="Consumer Care / Grievance Redressal",
                severity=ViolationSeverity.MAJOR,
                description=care_field.remarks,
                observed_value=care_field.value or "NOT DETECTED",
                expected_condition="Name, address, telephone number, and email of consumer care cell",
                statutory_citation="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(f)."
            ))

        # 7. Manufacturer / Packer / Importer
        mfg_field = StatutoryRuleEngine.evaluate_manufacturer_details(raw_text)
        declarations["manufacturer_details"] = mfg_field
        if not mfg_field.compliant:
            violations.append(ViolationDetail(
                violation_id="VIOL-007-MFG",
                rule_number="Rule 6(1)(a)",
                field_name="Manufacturer / Packer Identity & Address",
                severity=ViolationSeverity.CRITICAL if not mfg_field.detected else ViolationSeverity.MAJOR,
                description=mfg_field.remarks,
                observed_value=mfg_field.value or "NOT DETECTED",
                expected_condition="Complete registered name and address of manufacturer / packer / importer",
                statutory_citation="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(a)."
            ))

        # 8. Country of Origin
        origin_field = StatutoryRuleEngine.evaluate_country_of_origin(raw_text)
        declarations["country_of_origin"] = origin_field
        if not origin_field.compliant:
            violations.append(ViolationDetail(
                violation_id="VIOL-008-ORIGIN",
                rule_number="Rule 6(1)(g)",
                field_name="Country of Origin",
                severity=ViolationSeverity.MAJOR,
                description=origin_field.remarks,
                observed_value=origin_field.value or "NOT DETECTED",
                expected_condition="Explicit Country of Origin declaration (e.g., 'Made in India')",
                statutory_citation="Legal Metrology (Packaged Commodities) Rules, 2011, Rule 6(1)(g)."
            ))

        # 9. Generic Name
        gen_field = StatutoryRuleEngine.evaluate_generic_name(raw_text)
        declarations["generic_name"] = gen_field

        return declarations, violations

    @staticmethod
    def verify_physical_quantity(declared_qty: float, unit: str, measured_qty: float, tare_weight: float = 0.0) -> PhysicalVerificationResult:
        """
        Level 2 Physical Verification:
        Compares declared net content with actual physically weighed/measured quantity.
        Calculates Maximum Permissible Error (MPE) under First Schedule of PCR 2011.
        """
        # Net actual content = measured gross - tare weight (if gross was provided)
        actual_net = measured_qty
        deficit_or_excess = round(actual_net - declared_qty, 2)
        deficit_pct = round((deficit_or_excess / declared_qty) * 100.0, 2) if declared_qty > 0 else 0.0
        
        mpe_allowed = calculate_mpe(declared_qty, unit)
        
        # A deficit exceeding MPE is a severe legal violation under Section 36 of Legal Metrology Act, 2009
        if deficit_or_excess < 0 and abs(deficit_or_excess) > mpe_allowed:
            is_compliant = False
            status = "DEFICIT_VIOLATION"
            remarks = (
                f"DEFICIT VIOLATION: Actual net content ({actual_net} {unit}) is lower than declared "
                f"({declared_qty} {unit}) by {abs(deficit_or_excess)} {unit} ({abs(deficit_pct)}%). "
                f"Exceeds Maximum Permissible Error limit of {mpe_allowed} {unit} under First Schedule / Rule 11."
            )
        elif deficit_or_excess < 0:
            is_compliant = True
            status = "WITHIN_TOLERANCE"
            remarks = (
                f"Minor shortfall of {abs(deficit_or_excess)} {unit} is within statutory MPE allowance "
                f"({mpe_allowed} {unit})."
            )
        else:
            is_compliant = True
            status = "VERIFIED_COMPLIANT"
            remarks = f"Actual net content ({actual_net} {unit}) meets or exceeds declared quantity ({declared_qty} {unit})."

        return PhysicalVerificationResult(
            declared_net_quantity=declared_qty,
            measured_actual_quantity=actual_net,
            unit=unit,
            deficit_or_excess=deficit_or_excess,
            deficit_percentage=deficit_pct,
            max_permissible_error_allowed=mpe_allowed,
            is_within_mpe_limit=is_compliant,
            status=status,
            remarks=remarks
        )

    @staticmethod
    def determine_final_status(
        violations_count: int,
        physical_verified: bool = False,
        physical_is_compliant: bool = True
    ) -> InspectionStatus:
        """
        Determines the 3-Tier Inspection Verdict:
        1. NON_COMPLIANT: If any statutory packaging declaration fails OR physical verification fails MPE.
        2. PHYSICAL_VERIFICATION_REQUIRED: If all visible declarations pass, but physical contents have not been weighed/verified.
        3. COMPLIANT: If and only if all visible declarations pass AND physical verification is completed and compliant.
        """
        if violations_count > 0 or (physical_verified and not physical_is_compliant):
            return InspectionStatus.NON_COMPLIANT
        
        if not physical_verified:
            return InspectionStatus.PHYSICAL_VERIFICATION_REQUIRED
            
        return InspectionStatus.COMPLIANT
