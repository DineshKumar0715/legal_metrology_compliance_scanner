import io
import os
from typing import Optional, List
from PIL import Image
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

# Load environment variables
load_dotenv()

from schemas import (
    ComplianceResponse,
    PhysicalVerificationInput,
    PhysicalVerificationResult,
    EcommerceProductListing,
    UserLogin,
    InspectionStatus,
)
from gemini_compliance_engine import GeminiComplianceEngine
from compliance_engine import ComplianceEngine
from rule_engine import StatutoryRuleEngine
from cross_checker import CrossSourceConsistencyEngine
from cv_pipeline import VisualCompliancePipeline
from report_generator import OfficialReportGenerator
import database

app = FastAPI(
    title="VERITAS | Legal Metrology Compliance & Inspection Platform API",
    description="Automated AI-assisted statutory compliance verification for pre-packaged commodities under the Legal Metrology Act, 2009 & PCR 2011 (Amended 2026).",
    version="3.0.0",
)

# Enable CORS for frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize engines
gemini_engine = GeminiComplianceEngine()
local_engine = ComplianceEngine()
cv_pipeline = VisualCompliancePipeline()
rule_engine = StatutoryRuleEngine()


@app.get("/")
def read_root():
    return {
        "platform": "VERITAS AI Legal Metrology Platform",
        "status": "Active",
        "statutory_basis": "Legal Metrology Act, 2009 & PCR 2011 (Amended 2026)",
        "version": "3.0.0",
        "capabilities": [
            "Multimodal Vision Inspection",
            "Statutory 10+ Declaration Matrix",
            "3-Tier Verdict Decisioning (Compliant / Non-Compliant / Physical Verification Required)",
            "Level 2 Physical Net Content & MPE Verification",
            "Multi-View Cross-Panel Conflict Detection",
            "E-Commerce Listing vs Package Cross-Verification (2026 Origin Filter Rule)",
            "Visual Evidence Bounding Crop Generator",
            "Official ReportLab PDF Certificate Generation",
            "Central Inspection Case Repository & Analytics"
        ]
    }


@app.get("/health")
def health_check():
    load_dotenv(override=True)
    key = os.getenv("GEMINI_API_KEY")
    api_key_configured = bool(key and key.strip() and key != "your_gemini_api_key_here")
    return {
        "status": "ok",
        "gemini_multimodal_ready": api_key_configured,
        "local_rule_engine_ready": True,
        "database_connected": True,
    }


@app.post("/auth/login")
def login(credentials: UserLogin, role: Optional[str] = None):
    user = database.authenticate_user(credentials.username, credentials.password, required_role=role)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username, password, or unauthorized role.")
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "full_name": user["full_name"],
        "role": user["role"],
        "district": user["district"],
        "badge_number": user["badge_number"],
    }


@app.post("/auth/register")
def register(
    username: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(...),
    role: str = Form(...),
    district: str = Form(...),
    badge_number: str = Form(...),
):
    try:
        user = database.register_user(
            username=username,
            password=password,
            full_name=full_name,
            role=role,
            district=district,
            badge_number=badge_number,
        )
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Registration failed: {str(e)}")


@app.get("/users")
def list_users():
    return database.get_all_users()


@app.post("/scan-label", response_model=ComplianceResponse)
async def scan_label(
    file: UploadFile = File(...),
    declared_net_qty: Optional[float] = Form(None),
    unit: Optional[str] = Form("g"),
    measured_net_qty: Optional[float] = Form(None),
    tare_weight: Optional[float] = Form(0.0),
):
    """
    Standard single-view package label inspection with optional Level 2 physical verification.
    """
    if file.content_type not in ["image/jpeg", "image/png", "image/jpg", "image/webp"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid image format. Supported formats are JPG, JPEG, PNG, and WEBP.",
        )

    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents))

        # Evaluate Physical Verification if provided
        physical_result = None
        if declared_net_qty is not None and measured_net_qty is not None and declared_net_qty > 0:
            physical_result = StatutoryRuleEngine.verify_physical_quantity(
                declared_qty=declared_net_qty,
                unit=unit or "g",
                measured_qty=measured_net_qty,
                tare_weight=tare_weight or 0.0,
            )

        # Multimodal / Vision Inspection
        report = gemini_engine.evaluate_image(pil_image, physical_result=physical_result)

        # Generate evidence crops for all violations
        for v in report.violations:
            try:
                v.evidence_crop_base64 = cv_pipeline.generate_evidence_crop(pil_image, v)
            except Exception:
                pass

        return report
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Label compliance evaluation failed: {str(exc)}",
        )


@app.post("/scan-multi-view", response_model=ComplianceResponse)
async def scan_multi_view(
    front_file: UploadFile = File(...),
    back_file: Optional[UploadFile] = File(None),
    side_file: Optional[UploadFile] = File(None),
):
    """
    Multi-panel package inspection (Front + Back + Side panels).
    Cross-checks for contradictory declarations and dual MRP (Rule 18).
    """
    try:
        front_bytes = await front_file.read()
        front_img = Image.open(io.BytesIO(front_bytes))
        front_rep = gemini_engine.evaluate_image(front_img)

        panel_results = {"Front Panel": front_rep}
        combined_text = f"--- FRONT PANEL ---\n{front_rep.raw_text}"

        if back_file:
            back_bytes = await back_file.read()
            back_img = Image.open(io.BytesIO(back_bytes))
            back_rep = gemini_engine.evaluate_image(back_img)
            panel_results["Back Panel"] = back_rep
            combined_text += f"\n\n--- BACK PANEL ---\n{back_rep.raw_text}"

        if side_file:
            side_bytes = await side_file.read()
            side_img = Image.open(io.BytesIO(side_bytes))
            side_rep = gemini_engine.evaluate_image(side_img)
            panel_results["Side Panel"] = side_rep
            combined_text += f"\n\n--- SIDE PANEL ---\n{side_rep.raw_text}"

        # Cross-check panels
        conflicts = CrossSourceConsistencyEngine.check_multi_panel_conflicts(panel_results)

        # Run complete unified evaluation
        final_rep = local_engine.evaluate_compliance(combined_text)
        final_rep.cross_source_conflicts = conflicts

        if conflicts:
            final_rep.status = InspectionStatus.NON_COMPLIANT
            final_rep.violations_count += len(conflicts)

        return final_rep
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Multi-view inspection failed: {str(exc)}")


@app.post("/scan-ecommerce", response_model=ComplianceResponse)
async def scan_ecommerce_listing(
    file: UploadFile = File(...),
    title: str = Form(...),
    listed_mrp: float = Form(...),
    listed_net_quantity: str = Form(...),
    country_of_origin: str = Form(...),
    has_origin_filter: bool = Form(True),
):
    """
    E-Commerce listing verification against physical package evidence.
    Validates price overcharge and 2026 Country of Origin searchability amendment.
    """
    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents))
        package_rep = gemini_engine.evaluate_image(pil_image)

        listing = EcommerceProductListing(
            title=title,
            listed_mrp=listed_mrp,
            listed_net_quantity=listed_net_quantity,
            country_of_origin=country_of_origin,
            has_origin_filter=has_origin_filter,
        )

        conflicts, ecomm_violations = CrossSourceConsistencyEngine.cross_check_ecommerce_listing(
            listing, package_rep
        )

        package_rep.cross_source_conflicts = conflicts
        if ecomm_violations:
            package_rep.violations.extend(ecomm_violations)
            package_rep.violations_count += len(ecomm_violations)
            package_rep.status = InspectionStatus.NON_COMPLIANT

        return package_rep
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"E-commerce cross-check failed: {str(exc)}")


@app.post("/physical-verify", response_model=PhysicalVerificationResult)
def physical_verify(input_data: PhysicalVerificationInput):
    """
    Standalone Level 2 Physical Verification API.
    Computes Maximum Permissible Error (MPE) and net quantity shortfall.
    """
    return StatutoryRuleEngine.verify_physical_quantity(
        declared_qty=input_data.declared_net_quantity,
        unit=input_data.unit,
        measured_qty=input_data.measured_actual_quantity,
        tare_weight=input_data.tare_weight or 0.0,
    )


@app.post("/inspections/save")
def save_inspection_record(
    inspection_id: str = Form(...),
    product_name: str = Form(...),
    brand: Optional[str] = Form("Generic"),
    category: Optional[str] = Form("General Retail Pack"),
    inspector_id: str = Form("INSP-001"),
    inspector_name: str = Form("Enforcement Officer"),
    district: str = Form("Salem District"),
    location_details: Optional[str] = Form("Retail Inspection Point"),
    compliance_json: str = Form(...),
):
    """
    Saves an official inspection case into the central repository database.
    """
    import json
    try:
        data = json.loads(compliance_json)
        saved_id = database.save_inspection(
            inspection_id=inspection_id,
            product_name=product_name,
            brand=brand,
            category=category,
            inspector_id=inspector_id,
            inspector_name=inspector_name,
            district=district,
            location_details=location_details,
            status=data.get("status", "NON_COMPLIANT"),
            compliance_score=data.get("package_declaration_score", 0.0),
            violations_count=data.get("violations_count", 0),
            physical_status=data.get("physical_verification_status", "NOT_VERIFIED"),
            raw_text=data.get("raw_text", ""),
            declarations_dict=data.get("declarations", {}),
            violations_list=data.get("violations", []),
            physical_record=data.get("physical_verification_result"),
        )
        return {"status": "saved", "inspection_id": saved_id}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to save inspection: {str(exc)}")


@app.post("/inspections/{inspection_id}/action")
def take_supervisor_action(
    inspection_id: str,
    action: str = Form(...),
    supervisor_notes: str = Form(...),
    compounding_fine: float = Form(0.0),
):
    """
    Allows Supervisors/Controllers to officially approve, issue show-cause notices, or compound fines.
    """
    ok = database.update_case_action(inspection_id, action, supervisor_notes, compounding_fine)
    if not ok:
        raise HTTPException(status_code=404, detail="Inspection case not found.")
    return {"status": "updated", "inspection_id": inspection_id, "action": action}


@app.get("/inspections")
def get_inspections_list(
    query: Optional[str] = None,
    district: Optional[str] = None,
    status: Optional[str] = None,
    inspector_id: Optional[str] = None,
):
    """Fetches and filters inspection case records from the repository."""
    return database.get_inspections(query=query, district=district, status=status, inspector_id=inspector_id)


@app.get("/inspections/{inspection_id}")
def get_inspection_record(inspection_id: str):
    record = database.get_inspection_details(inspection_id)
    if not record:
        raise HTTPException(status_code=404, detail="Inspection case not found.")
    return record


@app.post("/inspections/report/pdf")
async def generate_inspection_pdf(
    file: UploadFile = File(...),
    product_name: str = Form("Pre-Packaged Retail Commodity"),
    brand: str = Form("Generic"),
    inspector_name: str = Form("R. K. Sharma (Inspector)"),
    badge_number: str = Form("LM-INSP-401"),
    district: str = Form("Salem District"),
    location: str = Form("Retail Inspection Point"),
    declared_net_qty: Optional[float] = Form(None),
    unit: Optional[str] = Form("g"),
    measured_net_qty: Optional[float] = Form(None),
):
    """
    Generates and streams an official publication-grade PDF inspection certificate.
    """
    try:
        contents = await file.read()
        pil_image = Image.open(io.BytesIO(contents))

        physical_result = None
        if declared_net_qty is not None and measured_net_qty is not None and declared_net_qty > 0:
            physical_result = StatutoryRuleEngine.verify_physical_quantity(
                declared_qty=declared_net_qty,
                unit=unit or "g",
                measured_qty=measured_net_qty,
            )

        report = gemini_engine.evaluate_image(pil_image, physical_result=physical_result)

        pdf_bytes = OfficialReportGenerator.generate_pdf(
            compliance_data=report,
            product_name=product_name,
            brand=brand,
            inspector_name=inspector_name,
            badge_number=badge_number,
            district=district,
            location=location,
        )

        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Legal_Metrology_Inspection_{district.replace(' ', '_')}.pdf"}
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(exc)}")


@app.get("/dashboard/stats")
def get_dashboard_stats():
    """Returns aggregated executive analytics for the enforcement dashboard."""
    return database.get_dashboard_analytics()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
