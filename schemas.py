from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any, Union
from enum import Enum
from datetime import datetime

class InspectionStatus(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON_COMPLIANT"
    PHYSICAL_VERIFICATION_REQUIRED = "PHYSICAL_VERIFICATION_REQUIRED"

class ViolationSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    ADVISORY = "ADVISORY"

class UserRole(str, Enum):
    INSPECTOR = "INSPECTOR"
    SUPERVISOR = "SUPERVISOR"
    ADMIN = "ADMIN"

class ExtractedField(BaseModel):
    detected: bool = Field(..., description="Whether the statutory field was found on the packaging.")
    value: Optional[str] = Field(None, description="The raw or normalized text extracted from the label.")
    compliant: bool = Field(..., description="Whether the declaration strictly complies with applicable Legal Metrology rules.")
    applicable: bool = Field(default=True, description="Whether this rule is legally applicable for this commodity/package type.")
    rule_reference: str = Field(default="Rule 6, PCR 2011", description="Legal section/rule reference.")
    remarks: str = Field(..., description="Reasoning for compliance status, noting missing clauses, invalid units, or proper declaration.")
    character_height_mm: Optional[float] = Field(None, description="Measured character/numeral height in mm.")
    min_required_height_mm: Optional[float] = Field(None, description="Statutory minimum character height required by Rule 9.")
    font_compliant: Optional[bool] = Field(None, description="Whether the font/numeral size satisfies Rule 9 minimum height.")
    bounding_box: Optional[List[int]] = Field(None, description="[x_min, y_min, x_max, y_max] coordinate of declaration.")
    evidence_crop_base64: Optional[str] = Field(None, description="Base64-encoded cropped image snippet showing evidence.")

class DeclarationsContainer(BaseModel):
    mrp: ExtractedField = Field(..., description="Maximum Retail Price declaration with mandatory 'inclusive of all taxes' clause (Rule 6(1)(e)).")
    net_quantity: ExtractedField = Field(..., description="Net Quantity declaration in standard SI units (Rule 6(1)(c) & Rule 11/13).")
    unit_sale_price: Optional[ExtractedField] = Field(None, description="Unit Sale Price (₹ per g/ml/piece) as mandated by 2021/2022 amendments (Rule 6(1)(h)).")
    date_of_packing: ExtractedField = Field(..., description="Month and Year of manufacture, packing, or import (Rule 6(1)(d)).")
    best_before_expiry: Optional[ExtractedField] = Field(None, description="Best before / use by date where applicable for perishable/food/cosmetic goods.")
    consumer_care: ExtractedField = Field(..., description="Consumer grievance redressal email, phone/helpline, or postal address (Rule 6(1)(f)).")
    manufacturer_details: ExtractedField = Field(..., description="Name and complete registered address of Manufacturer / Packer / Importer (Rule 6(1)(a)).")
    country_of_origin: ExtractedField = Field(..., description="Country of origin / manufacturing origin declaration (Rule 6(1)(g) & 2026 e-commerce amendments).")
    generic_name: Optional[ExtractedField] = Field(None, description="Generic or common name of the commodity (Rule 6(1)(b)).")
    dimensions: Optional[ExtractedField] = Field(None, description="Dimensions / sizes where relevant for commodities sold by size (Rule 6(1)(i)).")

class ViolationDetail(BaseModel):
    violation_id: str = Field(..., description="Unique violation code.")
    rule_number: str = Field(..., description="Legal section/rule reference.")
    field_name: str = Field(..., description="Statutory declaration field.")
    severity: ViolationSeverity = Field(default=ViolationSeverity.MAJOR, description="Severity level.")
    description: str = Field(..., description="Concise description of the legal infraction.")
    observed_value: Optional[str] = Field(None, description="Observed text or condition on package.")
    expected_condition: str = Field(..., description="Statutory standard expected by law.")
    statutory_citation: str = Field(..., description="Official clause citation under Legal Metrology (Packaged Commodities) Rules, 2011 (as amended).")
    evidence_crop_base64: Optional[str] = Field(None, description="Cropped image snippet of the offending region.")

class PhysicalVerificationInput(BaseModel):
    declared_net_quantity: float = Field(..., description="Declared net quantity value (e.g., 500.0).")
    unit: str = Field(..., description="Unit of measurement ('g', 'kg', 'ml', 'l', 'pieces').")
    measured_actual_quantity: float = Field(..., description="Actual measured net content in physical inspection (e.g., 430.0).")
    tare_weight: Optional[float] = Field(0.0, description="Measured tare weight of wrapper/packaging in grams.")
    instrument_id: Optional[str] = Field(None, description="Calibrated weighing/measuring instrument serial number.")
    inspection_notes: Optional[str] = Field(None, description="Inspector field notes.")

class PhysicalVerificationResult(BaseModel):
    declared_net_quantity: float
    measured_actual_quantity: float
    unit: str
    deficit_or_excess: float
    deficit_percentage: float
    max_permissible_error_allowed: float
    is_within_mpe_limit: bool
    status: str
    remarks: str

class CrossSourceConflict(BaseModel):
    field_name: str
    source_a: str
    value_a: str
    source_b: str
    value_b: str
    conflict_description: str

class ComplianceResponse(BaseModel):
    status: InspectionStatus = Field(..., description="Overall 3-tier verdict: 'COMPLIANT', 'NON_COMPLIANT', or 'PHYSICAL_VERIFICATION_REQUIRED'.")
    package_declaration_score: float = Field(..., description="Percentage of applicable declarations that are compliant (0.0 to 100.0).")
    applicable_rules_count: int = Field(..., description="Total applicable statutory checks for this product.")
    passed_rules_count: int = Field(..., description="Number of statutory checks passed.")
    violations_count: int = Field(..., description="Total count of non-compliant or missing mandatory fields.")
    violations: List[ViolationDetail] = Field(default=[], description="Structured breakdown of every detected legal violation.")
    declarations: Dict[str, ExtractedField] = Field(..., description="Dictionary of statutory declarations.")
    physical_verification_status: str = Field(default="NOT_VERIFIED", description="'VERIFIED_COMPLIANT', 'DEFICIT_VIOLATION', or 'NOT_VERIFIED'.")
    physical_verification_result: Optional[PhysicalVerificationResult] = Field(None, description="Details if physical verification was executed.")
    cross_source_conflicts: List[CrossSourceConflict] = Field(default=[], description="Detected conflicts between multiple image panels or e-commerce listing vs package.")
    raw_text: str = Field(default="", description="Complete readable text transcribed from the package.")
    pdp_area_sq_cm: Optional[float] = Field(None, description="Estimated Principal Display Panel (PDP) surface area.")
    inspection_id: Optional[str] = Field(None, description="Unique database inspection tracking ID.")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO timestamp of inspection.")
    inspector_id: Optional[str] = Field(None, description="ID of the conducting inspector.")
    district: Optional[str] = Field(None, description="District/jurisdiction where inspection was logged.")

class GeminiComplianceSchema(BaseModel):
    status: str = Field(..., description="'COMPLIANT' if violations_count == 0 else 'NON_COMPLIANT'")
    overall_compliance_score: float = Field(..., description="Percentage of compliant fields (0.0 to 100.0).")
    violations_count: int = Field(..., description="Count of non-compliant or missing mandatory fields.")
    declarations: DeclarationsContainer = Field(..., description="Declarations for statutory fields.")
    raw_text: str = Field(..., description="Complete readable text transcribed from the package.")
    generic_name: Optional[str] = Field(None, description="Generic commodity name identified.")
    estimated_pdp_area_cm2: Optional[float] = Field(None, description="Estimated Principal Display Panel area in cm².")
    usp_detected: Optional[bool] = Field(False, description="Whether Unit Sale Price was identified.")
    best_before_detected: Optional[bool] = Field(False, description="Whether Best Before / Expiry date was identified.")

class EcommerceProductListing(BaseModel):
    title: str = Field(..., description="Product title on e-commerce platform.")
    listed_mrp: float = Field(..., description="Listed Maximum Retail Price on web page.")
    listed_selling_price: Optional[float] = Field(None, description="Current selling/discounted price.")
    listed_net_quantity: str = Field(..., description="Declared net quantity on listing (e.g., '500 g').")
    country_of_origin: str = Field(..., description="Country of Origin listed on portal.")
    has_origin_filter: bool = Field(default=True, description="Whether listing has sortable/searchable Country of Origin filter (Rule 2026 amendment).")
    manufacturer_packer: Optional[str] = Field(None, description="Manufacturer/Packer details on listing.")
    seller_name: Optional[str] = Field(None, description="Registered seller name.")

class InspectionCaseCreate(BaseModel):
    product_name: str
    brand: Optional[str] = "Unbranded / Generic"
    category: Optional[str] = "General Pre-Packaged Food"
    batch_number: Optional[str] = None
    district: str = "Central Enforcement Zone"
    location_details: Optional[str] = "Retail Inspection Point"
    inspector_name: str = "Enforcement Officer"
    inspector_id: str = "INSP-001"

class UserLogin(BaseModel):
    username: str
    password: str

class UserProfile(BaseModel):
    user_id: str
    username: str
    full_name: str
    role: UserRole
    district: str
    badge_number: str
