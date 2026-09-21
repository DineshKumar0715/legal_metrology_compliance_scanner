from typing import Dict, Optional
from pydantic import BaseModel, Field


class ExtractedField(BaseModel):
    detected: bool = Field(..., description="Whether the declaration was detected in the OCR text")
    value: Optional[str] = Field(default=None, description="Extracted text snippet or value")
    compliant: bool = Field(..., description="Whether the declaration satisfies statutory rules")
    remarks: str = Field(..., description="Detailed compliance note, warning, or violation message")


class ComplianceResponse(BaseModel):
    status: str = Field(..., description="'COMPLIANT' or 'NON_COMPLIANT'")
    overall_compliance_score: float = Field(..., description="Percentage of passed rules (0.0 to 100.0)")
    violations_count: int = Field(..., description="Total count of non-compliant or missing mandatory declarations")
    declarations: Dict[str, ExtractedField] = Field(..., description="Dictionary of 6 statutory rule evaluations")
    raw_text: str = Field(..., description="Raw extracted OCR text from the image")
