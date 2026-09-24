from pydantic import BaseModel, Field
from typing import Optional, Dict, Union

class ExtractedField(BaseModel):
    detected: bool = Field(..., description="Whether the mandatory field was found on the package.")
    value: Optional[str] = Field(None, description="The exact raw text extracted from the label.")
    compliant: bool = Field(..., description="Whether the declaration strictly complies with Legal Metrology Rules, 2011.")
    remarks: str = Field(..., description="Reasoning for compliance status, noting missing clauses, invalid units, or proper declaration.")

class DeclarationsContainer(BaseModel):
    mrp: ExtractedField = Field(..., description="Maximum Retail Price declaration with tax clause.")
    net_quantity: ExtractedField = Field(..., description="Net Quantity declaration in standard SI units.")
    date_of_packing: ExtractedField = Field(..., description="Month and Year of manufacture or packing.")
    consumer_care: ExtractedField = Field(..., description="Customer care email or helpline number.")
    manufacturer_details: ExtractedField = Field(..., description="Manufacturer, packer, or importer name and address.")
    country_of_origin: ExtractedField = Field(..., description="Country of origin declaration.")

class GeminiComplianceSchema(BaseModel):
    status: str = Field(..., description="'COMPLIANT' if violations_count == 0 else 'NON_COMPLIANT'")
    overall_compliance_score: float = Field(..., description="Percentage of compliant fields (0.0 to 100.0).")
    violations_count: int = Field(..., description="Count of non-compliant or missing mandatory fields.")
    declarations: DeclarationsContainer = Field(..., description="Declarations for all 6 mandatory statutory fields.")
    raw_text: str = Field(..., description="Complete readable text transcribed from the package.")

class ComplianceResponse(BaseModel):
    status: str = Field(..., description="'COMPLIANT' if violations_count == 0 else 'NON_COMPLIANT'")
    overall_compliance_score: float = Field(..., description="Percentage of compliant fields (0.0 to 100.0).")
    violations_count: int = Field(..., description="Count of non-compliant or missing mandatory fields.")
    declarations: Dict[str, ExtractedField] = Field(
        ...,
        description="Keys: 'mrp', 'net_quantity', 'date_of_packing', 'consumer_care', 'manufacturer_details', 'country_of_origin'"
    )
    raw_text: str = Field(..., description="Complete readable text transcribed from the package.")
