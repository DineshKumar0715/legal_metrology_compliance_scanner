import re
from typing import Dict, Tuple
from schemas import ExtractedField, ComplianceResponse


def _normalize_digits(val: str) -> str:
    """Normalize common OCR misrecognitions of digits."""
    return (
        val.replace("I", "1")
        .replace("l", "1")
        .replace("O", "0")
        .replace("o", "0")
    )


class ComplianceEngine:
    """
    Statutory rule engine for Legal Metrology (Packaged Commodities) Rules, 2011.
    Audits 6 mandatory declarations under Rule 6:
      1. Maximum Retail Price (MRP) & Tax Declaration (Rule 6(1)(e))
      2. Net Quantity & Metric Unit Compliance (Rule 6(1)(c))
      3. Date of Packing / Manufacture (Rule 6(1)(d))
      4. Consumer Care / Grievance Redressal (Rule 6(1)(n))
      5. Name and Address of Manufacturer / Packer / Importer (Rule 6(1)(a))
      6. Country of Origin (Rule 6(1)(m))
    """

    def check_mrp(self, text: str) -> ExtractedField:
        """
        Audit Maximum Retail Price (MRP) declaration under Rule 6(1)(e):
        - Must state price in Indian Rupees (₹, Rs., Rs, INR, MRP, M.R.P.)
        - Must include the mandatory statutory statement: 'inclusive of all taxes' or 'incl. of all taxes'.
        """
        mrp_pattern = re.compile(
            r"(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price|rs\.?|₹|inr)\s*[:\.\-]?\s*(?:rs\.?|₹)?\s*([0-9IlOo]+(?:[.,][0-9IlOo]{1,2})?)\s*(?:/-)?",
            re.IGNORECASE,
        )

        tax_pattern = re.compile(
            r"(?:incl(?:usive)?\.?\s*(?:of)?\s*(?:all)?\s*taxes?|incl\.\s*taxes?|incl\s+all\s+taxes?|inclusive\s+of\s+taxes?|incl\s+of\s+all\s+taxes?)",
            re.IGNORECASE,
        )

        mrp_match = mrp_pattern.search(text)
        has_tax_clause = bool(tax_pattern.search(text))

        if mrp_match:
            price_str = mrp_match.group(0).strip()
            raw_val = mrp_match.group(1).strip()
            price_val = _normalize_digits(raw_val)

            if has_tax_clause:
                return ExtractedField(
                    detected=True,
                    value=f"MRP: Rs. {price_val} (incl. of all taxes)",
                    compliant=True,
                    remarks="Compliant: MRP declared with mandatory 'inclusive of all taxes' statement under Rule 6(1)(e).",
                )
            else:
                return ExtractedField(
                    detected=True,
                    value=f"MRP: Rs. {price_val}",
                    compliant=False,
                    remarks="Non-Compliant: MRP detected, but missing mandatory statutory clause 'inclusive of all taxes' or 'incl. of all taxes' under Rule 6(1)(e).",
                )

        # In case tax clause is found without clear numeric MRP prefix
        if has_tax_clause:
            return ExtractedField(
                detected=True,
                value="Tax clause detected without clear MRP figure",
                compliant=False,
                remarks="Non-Compliant: Tax declaration found, but clear numeric Maximum Retail Price (MRP) was not identified.",
            )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Missing: Maximum Retail Price (MRP) declaration not found. Mandatory under Rule 6(1)(e).",
        )

    def check_net_quantity(self, text: str) -> ExtractedField:
        """
        Audit Net Quantity declaration under Rule 6(1)(c):
        - Must declare quantity with standard metric units: g, kg, ml, l, L, N, U, units, pcs, count.
        - Non-standard/deprecated symbols like 'gm', 'gms', 'gm.', 'kgs', 'ltr', 'ltrs', 'mls' violate Rule 6(1)(c).
        """
        net_qty_label_pattern = re.compile(
            r"(?:net\s*(?:qty|quantity|weight|wt|vol|volume|content|contents)?)\s*[:\.\-]?\s*([0-9IlOo]+(?:\.[0-9IlOo]+)?)\s*([a-zA-Z\.]+)",
            re.IGNORECASE,
        )

        standalone_qty_pattern = re.compile(
            r"\b([0-9IlOo]+(?:\.[0-9IlOo]+)?)\s*(gms?|gm\.?|kgs?|kg\.?|ltrs?|ltr\.?|ml\.?|l|L|g|N|U|units?|pcs|count)\b",
            re.IGNORECASE,
        )

        label_match = net_qty_label_pattern.search(text)
        qty_match = standalone_qty_pattern.search(text)

        target_match = label_match if label_match else qty_match

        if target_match:
            amount = _normalize_digits(target_match.group(1).strip())
            unit = target_match.group(2).strip().lower()

            raw_value = f"{amount} {target_match.group(2).strip()}"

            deprecated_units = {"gm", "gms", "gm.", "kgs", "ltr", "ltrs", "mls", "ml."}
            valid_units = {"g", "kg", "ml", "l", "n", "u", "unit", "units", "pc", "pcs", "count"}

            clean_unit = unit.replace(".", "").lower()

            if unit in deprecated_units or clean_unit in {"gm", "gms", "kgs", "ltr", "ltrs", "mls"}:
                standard_counterpart = "g" if "gm" in clean_unit else ("kg" if "kg" in clean_unit else ("l" if "ltr" in clean_unit else "ml"))
                return ExtractedField(
                    detected=True,
                    value=raw_value,
                    compliant=False,
                    remarks=f"Non-Compliant: Non-standard unit '{target_match.group(2).strip()}' used. Rule 6(1)(c) mandates standard SI unit '{standard_counterpart}'. Abbreviations like 'gm' or 'gms' are strictly prohibited.",
                )
            elif clean_unit in valid_units or unit in {"g", "kg", "ml", "l", "L", "N", "U"}:
                return ExtractedField(
                    detected=True,
                    value=raw_value,
                    compliant=True,
                    remarks=f"Compliant: Net quantity '{raw_value}' declared in standard metric units per Rule 6(1)(c).",
                )
            else:
                return ExtractedField(
                    detected=True,
                    value=raw_value,
                    compliant=False,
                    remarks=f"Non-Compliant: Unrecognized or non-standard quantity unit '{unit}'. Standard metric units (g, kg, ml, l, N) are required.",
                )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Missing: Net Quantity declaration not found. Mandatory under Rule 6(1)(c).",
        )

    def check_date_of_packing(self, text: str) -> ExtractedField:
        """
        Audit Date of Packing / Manufacture under Rule 6(1)(d):
        - Detect indicators: Mfg, Pkd, Packed On, Date of Mfg, Month & Year, Use By, Best Before, etc.
        - Support formats: MM/YYYY, MM/YY, DD/MM/YYYY, DD-MM-YYYY, or Month YYYY (e.g. 'Jan 2024', '08/24').
        """
        date_pattern = re.compile(
            r"(?:mfg|mfd|pkd|pkg|packed\s*on|date\s*of\s*(?:mfg|mfd|packing|pkd)|month\s*(?:&|and)\s*year|use\s*by|useby|best\s*before|exp|expiry)\s*[:\.\-]?\s*"
            r"((?:0?[1-9]|1[0-2])[\/\.\\|\":\-\s]+(?:\d{4}|\d{2})|(?:\d{1,2}[\/\.\\|\":\-\s]+(?:0?[1-9]|1[0-2])[\/\.\\|\":\-\s]+\d{2,4})|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\s\.-]+\d{2,4})",
            re.IGNORECASE,
        )

        standalone_date_pattern = re.compile(
            r"\b((?:0[1-9]|1[0-2])[\/\-](?:20\d{2}|19\d{2}|\d{2})|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(?:20\d{2}))\b",
            re.IGNORECASE,
        )

        match = date_pattern.search(text)
        if match:
            date_val = match.group(0).strip()
            return ExtractedField(
                detected=True,
                value=date_val,
                compliant=True,
                remarks="Compliant: Month and year of manufacture/packing declared in prescribed format under Rule 6(1)(d).",
            )

        standalone_match = standalone_date_pattern.search(text)
        if standalone_match:
            date_val = standalone_match.group(1).strip()
            return ExtractedField(
                detected=True,
                value=f"Date: {date_val}",
                compliant=True,
                remarks="Compliant: Date format detected matching manufacturing/packing period under Rule 6(1)(d).",
            )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Missing: Month and Year of Manufacture/Packing not found. Mandatory under Rule 6(1)(d).",
        )

    def check_consumer_care(self, text: str) -> ExtractedField:
        """
        Audit Consumer Care Details under Rule 6(1)(n):
        - Detect email address, phone number (10-digit mobile, std telephone, or 1800 toll-free),
          and consumer care keywords (customer care, helpline, grievance, feedback).
        """
        email_pattern = re.compile(r"([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)")
        phone_pattern = re.compile(
            r"(?:tel|phone|ph|toll\s*free|helpline|contact|call)?\s*[:\.\-]?\s*(1800[\s\-]?\d{3}[\s\-]?\d{3,4}|(?:\+91[\s\-]?)?[6-9]\d{9}|0\d{2,4}[\s\-]?\d{6,8})",
            re.IGNORECASE,
        )
        care_keyword_pattern = re.compile(
            r"(?:customer\s*care|consumer\s*care|feedback|helpline|grievance|consumer\s*cell|contact\s*us|customercare)",
            re.IGNORECASE,
        )

        email_match = email_pattern.search(text)
        phone_match = phone_pattern.search(text)
        care_keyword_match = care_keyword_pattern.search(text)

        contact_parts = []
        if care_keyword_match:
            contact_parts.append(care_keyword_match.group(0).strip().title())
        if phone_match:
            contact_parts.append(f"Tel: {phone_match.group(1).strip()}")
        if email_match:
            contact_parts.append(f"Email: {email_match.group(1).strip()}")

        if email_match or phone_match:
            val_str = " | ".join(contact_parts) if contact_parts else (phone_match.group(1) if phone_match else email_match.group(1))
            return ExtractedField(
                detected=True,
                value=val_str,
                compliant=True,
                remarks="Compliant: Consumer Care contact channels (Helpline/Email) declared under Rule 6(1)(n).",
            )
        elif care_keyword_match:
            return ExtractedField(
                detected=True,
                value=care_keyword_match.group(0).strip(),
                compliant=False,
                remarks="Non-Compliant: Consumer care header detected, but missing actionable helpline phone number or email address under Rule 6(1)(n).",
            )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Missing: Consumer Care details (Helpline/Email/Address) not found. Mandatory under Rule 6(1)(n).",
        )

    def check_manufacturer_details(self, text: str) -> ExtractedField:
        """
        Audit Manufacturer / Packer / Importer Details under Rule 6(1)(a):
        - Detect keywords: 'mfg by', 'manufactured by', 'packed by', 'marketed by', 'imported by', 'mfd by', 'pkd by', or company identifiers.
        """
        mfg_pattern = re.compile(
            r"(?:mfg\.?\s*by|mfd\.?\s*by|manufactured\s*by|pkd\.?\s*by|packed\s*by|marketed\s*by|mktd\.?\s*by|imported\s*by|mfg\s*&\s*pkd\s*by)\s*[:\.\-]?\s*([^\n\r,]+(?:,[^\n\r]+){0,3})",
            re.IGNORECASE,
        )

        match = mfg_pattern.search(text)
        if match:
            mfg_text = match.group(0).strip()
            mfg_clean = re.sub(r"\s+", " ", mfg_text)
            return ExtractedField(
                detected=True,
                value=mfg_clean[:120],
                compliant=True,
                remarks="Compliant: Name and address of Manufacturer/Packer/Marketer declared under Rule 6(1)(a).",
            )

        fallback_keywords = re.compile(
            r"\b(?:parle|britannia|itc|nestle|unilever|marico|dabur|haldiram|manufactured|packer|imported|marketer|pvt\s*ltd|ltd\.|limited)\b",
            re.IGNORECASE,
        )
        fallback_match = fallback_keywords.search(text)
        if fallback_match:
            start = max(0, fallback_match.start() - 15)
            end = min(len(text), fallback_match.end() + 60)
            snippet = text[start:end].replace("\n", " ").strip()
            return ExtractedField(
                detected=True,
                value=snippet[:100],
                compliant=True,
                remarks="Compliant: Manufacturer/Entity identification detected on label under Rule 6(1)(a).",
            )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Missing: Name and complete address of Manufacturer/Packer/Importer not found. Mandatory under Rule 6(1)(a).",
        )

    def check_country_of_origin(self, text: str) -> ExtractedField:
        """
        Audit Country of Origin declaration under Rule 6(1)(m):
        - Detect phrases: 'country of origin', 'made in', 'produced in', 'product of', 'origin:'.
        """
        origin_pattern = re.compile(
            r"(?:country\s*of\s*origin|made\s*in|produced\s*in|product\s*of|origin)\s*[:\.\-]?\s*([a-zA-Z\s]{3,30})",
            re.IGNORECASE,
        )

        match = origin_pattern.search(text)
        if match:
            origin_val = match.group(0).strip()
            return ExtractedField(
                detected=True,
                value=origin_val,
                compliant=True,
                remarks="Compliant: Country of Origin explicitly declared on label under Rule 6(1)(m).",
            )

        india_pattern = re.compile(r"\b(?:made\s*in\s*india|product\s*of\s*india|origin\s*:\s*india|mfd\s*in\s*india)\b", re.IGNORECASE)
        india_match = india_pattern.search(text)
        if india_match:
            return ExtractedField(
                detected=True,
                value=india_match.group(0).strip(),
                compliant=True,
                remarks="Compliant: Country of Origin declared as India under Rule 6(1)(m).",
            )

        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Missing: Country of Origin declaration not found. Mandatory under Rule 6(1)(m).",
        )

    def evaluate_compliance(self, raw_text: str) -> ComplianceResponse:
        """
        Aggregate all 6 statutory rule checks, compute compliance metrics, and return ComplianceResponse.
        """
        declarations: Dict[str, ExtractedField] = {
            "mrp": self.check_mrp(raw_text),
            "net_quantity": self.check_net_quantity(raw_text),
            "date_of_packing": self.check_date_of_packing(raw_text),
            "consumer_care": self.check_consumer_care(raw_text),
            "manufacturer_details": self.check_manufacturer_details(raw_text),
            "country_of_origin": self.check_country_of_origin(raw_text),
        }

        total_rules = len(declarations)
        passed_rules = sum(1 for field in declarations.values() if field.compliant)
        violations_count = total_rules - passed_rules

        overall_compliance_score = round((passed_rules / total_rules) * 100.0, 2)
        status = "COMPLIANT" if violations_count == 0 else "NON_COMPLIANT"

        return ComplianceResponse(
            status=status,
            overall_compliance_score=overall_compliance_score,
            violations_count=violations_count,
            declarations=declarations,
            raw_text=raw_text,
        )
