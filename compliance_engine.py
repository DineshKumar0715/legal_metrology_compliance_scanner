import re
from datetime import datetime
from typing import Dict
from schemas import ExtractedField

class ComplianceEngine:
    @staticmethod
    def check_mrp(text: str) -> ExtractedField:
        # Regex for MRP with currency symbol/code and numeric price
        mrp_pattern = r"(?:MRP|M\.R\.P\.|MAX\.?\s*RETAIL\s*PRICE|Rs\.?|₹)\s*[:.]?\s*(\d+(?:\.\d{1,2})?)"
        tax_pattern = r"(?:incl|inclusive)\.?\s*(?:of)?\s*all\s*taxes"

        match = re.search(mrp_pattern, text, re.IGNORECASE)
        has_tax_clause = bool(re.search(tax_pattern, text, re.IGNORECASE))

        if match:
            price_val = match.group(0)
            if has_tax_clause:
                return ExtractedField(
                    detected=True,
                    value=price_val,
                    compliant=True,
                    remarks="Valid MRP and 'inclusive of all taxes' declaration found."
                )
            return ExtractedField(
                detected=True,
                value=price_val,
                compliant=False,
                remarks="MRP found, but missing mandatory 'inclusive of all taxes' suffix."
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="MRP declaration not detected."
        )

    @staticmethod
    def check_net_quantity(text: str) -> ExtractedField:
        # Standard metric units: g, kg, ml, l, N, U, units
        qty_pattern = r"(?:Net\s*(?:Qty|Quantity|Weight|Wt|Vol|Volume)?)\s*[:.]?\s*(\d+(?:\.\d+)?\s*(?:kg|g|gm|ml|l|ltr|litres|unit|units|N|U))\b"
        match = re.search(qty_pattern, text, re.IGNORECASE)

        if match:
            val = match.group(1)
            # Flag deprecated/non-standard units like 'gm' or 'gms'
            if re.search(r"\bgms?\b", val, re.IGNORECASE):
                return ExtractedField(
                    detected=True,
                    value=val,
                    compliant=False,
                    remarks="Non-standard unit abbreviation detected. Use standard 'g' instead of 'gm/gms'."
                )
            return ExtractedField(
                detected=True,
                value=val,
                compliant=True,
                remarks="Valid Net Quantity in standardized metric units detected."
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Net Quantity declaration not found."
        )

    @staticmethod
    def check_date_of_packing(text: str) -> ExtractedField:
        # Matches MM/YYYY, MM/YY, or Month Year formats
        date_pattern = r"(?:Mfg|Pkd|Mfg\s*Date|Packed\s*On|Date\s*of\s*Mfg|Date\s*of\s*Packing|Month\s*&\s*Year)\s*[:.]?\s*([0-1]?\d[/-](?:20\d{2}|\d{2})|[A-Za-z]{3,9}\s*(?:20\d{2}|\d{2}))"
        match = re.search(date_pattern, text, re.IGNORECASE)

        if match:
            return ExtractedField(
                detected=True,
                value=match.group(1),
                compliant=True,
                remarks="Date of manufacture/packing detected."
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Month & Year of Manufacture/Packing not detected."
        )

    @staticmethod
    def check_consumer_care(text: str) -> ExtractedField:
        email_pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
        phone_pattern = r"(?:(?:\+|0{0,2})91(\s*[\-]\s*)?|[0]?)?[6789]\d{9}|1800\s*\d{3}\s*\d{3,4}"
        care_keyword = r"(?:customer\s*care|consumer\s*care|feedback|grievance|helpline)"

        has_email = re.search(email_pattern, text)
        has_phone = re.search(phone_pattern, text)
        has_keyword = re.search(care_keyword, text, re.IGNORECASE)

        contact_info = []
        if has_email: contact_info.append(f"Email: {has_email.group(0)}")
        if has_phone: contact_info.append(f"Phone: {has_phone.group(0)}")

        if has_keyword and (has_email or has_phone):
            return ExtractedField(
                detected=True,
                value=" | ".join(contact_info),
                compliant=True,
                remarks="Consumer Care contact info (email/phone) verified."
            )
        elif has_email or has_phone:
            return ExtractedField(
                detected=True,
                value=" | ".join(contact_info),
                compliant=True,
                remarks="Contact details found without explicit 'Consumer Care' tag."
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Consumer grievance contact details missing."
        )

    @staticmethod
    def check_manufacturer_details(text: str) -> ExtractedField:
        mfg_pattern = r"(?:mfg\s*by|manufactured\s*by|packed\s*by|marketed\s*by|imported\s*by)\s*[:.]?\s*([^\n\r]+)"
        match = re.search(mfg_pattern, text, re.IGNORECASE)

        if match:
            return ExtractedField(
                detected=True,
                value=match.group(1).strip(),
                compliant=True,
                remarks="Manufacturer/Packer identity declaration detected."
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Name and address of Manufacturer/Packer/Importer not detected."
        )

    @staticmethod
    def check_country_of_origin(text: str) -> ExtractedField:
        origin_pattern = r"(?:country\s*of\s*origin|made\s*in|produced\s*in)\s*[:.]?\s*([A-Za-z]+)"
        match = re.search(origin_pattern, text, re.IGNORECASE)

        if match:
            return ExtractedField(
                detected=True,
                value=match.group(1).strip(),
                compliant=True,
                remarks=f"Country of origin identified as {match.group(1)}."
            )
        return ExtractedField(
            detected=False,
            value=None,
            compliant=False,
            remarks="Country of origin not declared."
        )

    def evaluate_compliance(self, text: str) -> Dict[str, object]:
        results = {
            "mrp": self.check_mrp(text),
            "net_quantity": self.check_net_quantity(text),
            "date_of_packing": self.check_date_of_packing(text),
            "consumer_care": self.check_consumer_care(text),
            "manufacturer_details": self.check_manufacturer_details(text),
            "country_of_origin": self.check_country_of_origin(text)
        }

        total_rules = len(results)
        passed_rules = sum(1 for field in results.values() if field.compliant)
        score = round((passed_rules / total_rules) * 100, 2)
        violations = total_rules - passed_rules

        return {
            "status": "COMPLIANT" if violations == 0 else "NON_COMPLIANT",
            "overall_compliance_score": score,
            "violations_count": violations,
            "declarations": results,
            "raw_text": text
        }
