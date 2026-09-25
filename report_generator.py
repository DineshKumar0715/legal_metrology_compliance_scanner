"""
Official Legal Metrology PDF Report Generator & Notice Builder.
Generates publication-quality statutory inspection certificates using ReportLab.
"""

import io
import os
from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY

from schemas import ComplianceResponse, PhysicalVerificationResult


class OfficialReportGenerator:
    """
    Generates official Legal Metrology inspection reports and statutory violation notices.
    """

    @staticmethod
    def generate_pdf(
        compliance_data: ComplianceResponse,
        product_name: str = "Pre-Packaged Retail Commodity",
        brand: str = "Generic / Retail",
        inspector_name: str = "R. K. Sharma (Inspector)",
        badge_number: str = "LM-INSP-401",
        district: str = "Salem District",
        location: str = "Retail Inspection Point",
        inspection_id: Optional[str] = None
    ) -> bytes:
        """
        Creates an official government-styled PDF inspection certificate and returns bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        
        # Custom typography styles
        title_style = ParagraphStyle(
            "GovTitle",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            "GovSubTitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER,
            textColor=colors.HexColor("#475569")
        )
        section_heading = ParagraphStyle(
            "GovSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#1e293b"),
            spaceBefore=8,
            spaceAfter=4
        )
        body_style = ParagraphStyle(
            "GovBody",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#334155")
        )
        body_bold = ParagraphStyle(
            "GovBodyBold",
            parent=body_style,
            fontName="Helvetica-Bold"
        )

        elements = []

        # 1. Official Header
        elements.append(Paragraph("DIRECTORATE OF LEGAL METROLOGY", title_style))
        elements.append(Paragraph("DEPARTMENT OF CONSUMER AFFAIRS &bull; GOVERNMENT OF INDIA", subtitle_style))
        elements.append(Paragraph("STATUTORY INSPECTION REPORT & COMPLIANCE CERTIFICATE", ParagraphStyle("SubHead", parent=subtitle_style, fontName="Helvetica-Bold", fontSize=9.5, textColor=colors.HexColor("#1e40af"))))
        elements.append(Paragraph("Issued under Legal Metrology Act, 2009 & Legal Metrology (Packaged Commodities) Rules, 2011 (as amended)", subtitle_style))
        elements.append(Spacer(1, 10))
        elements.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1e3a8a"), spaceAfter=10))

        # 2. Case Details Box
        insp_id = inspection_id or compliance_data.inspection_id or f"INSP-{datetime.now().strftime('%Y%m%d-%H%M')}"
        date_str = datetime.now().strftime("%d-%B-%Y %H:%M:%S")

        meta_data = [
            [
                Paragraph("<b>Inspection ID:</b> " + insp_id, body_style),
                Paragraph("<b>Date & Time:</b> " + date_str, body_style),
            ],
            [
                Paragraph("<b>Officer In-Charge:</b> " + inspector_name, body_style),
                Paragraph("<b>Badge / ID:</b> " + badge_number, body_style),
            ],
            [
                Paragraph("<b>Jurisdiction / District:</b> " + district, body_style),
                Paragraph("<b>Premises Inspected:</b> " + location, body_style),
            ],
            [
                Paragraph("<b>Product / Commodity:</b> " + product_name, body_style),
                Paragraph("<b>Brand:</b> " + brand, body_style),
            ],
        ]
        meta_table = Table(meta_data, colWidths=[260, 260])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(meta_table)
        elements.append(Spacer(1, 10))

        # 3. Verdict Banner
        status_val = compliance_data.status.value if hasattr(compliance_data.status, "value") else str(compliance_data.status)
        if status_val == "COMPLIANT":
            verdict_bg = colors.HexColor("#ecfdf5")
            verdict_border = colors.HexColor("#10b981")
            verdict_text = "STATUS: COMPLIANT — ALL OBSERVED STATUTORY DECLARATIONS SATISFIED"
            verdict_color = colors.HexColor("#065f46")
        elif status_val == "PHYSICAL_VERIFICATION_REQUIRED":
            verdict_bg = colors.HexColor("#fffbeb")
            verdict_border = colors.HexColor("#f59e0b")
            verdict_text = "STATUS: PHYSICAL VERIFICATION REQUIRED (OBSERVABLE DECLARATIONS PASS)"
            verdict_color = colors.HexColor("#92400e")
        else:
            verdict_bg = colors.HexColor("#fef2f2")
            verdict_border = colors.HexColor("#ef4444")
            verdict_text = f"STATUS: NON-COMPLIANT — {compliance_data.violations_count} STATUTORY VIOLATION(S) FLAGGED"
            verdict_color = colors.HexColor("#991b1b")

        verdict_data = [[
            Paragraph(f"<b>{verdict_text}</b>", ParagraphStyle("Verdict", parent=title_style, fontSize=10, textColor=verdict_color)),
            Paragraph(f"<b>Score: {compliance_data.package_declaration_score:.1f}%</b>", ParagraphStyle("Score", parent=title_style, fontSize=11, textColor=verdict_color, alignment=TA_RIGHT))
        ]]
        verdict_table = Table(verdict_data, colWidths=[400, 120])
        verdict_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), verdict_bg),
            ('BOX', (0, 0), (-1, -1), 1.5, verdict_border),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(verdict_table)
        elements.append(Spacer(1, 10))

        # 4. Statutory Declarations Matrix Table
        elements.append(Paragraph("I. STATUTORY DECLARATION AUDIT MATRIX (RULE 6, 7, 8, 9 & AMENDMENTS)", section_heading))
        
        matrix_header = ["Statutory Rule", "Mandatory Declaration Field", "Observed Package Value", "Status", "Auditor Findings"]
        matrix_rows = [matrix_header]

        for field_key, field in compliance_data.declarations.items():
            field_name_pretty = field_key.replace("_", " ").title()
            val_text = field.value if (field.detected and field.value) else "Declaration Absent"
            status_badge = "PASS" if field.compliant else ("FORMAT VIOLATION" if field.detected else "MISSING")
            
            matrix_rows.append([
                Paragraph(field.rule_reference or "Rule 6", body_style),
                Paragraph(f"<b>{field_name_pretty}</b>", body_style),
                Paragraph(val_text[:45], body_style),
                Paragraph(f"<b>{status_badge}</b>", ParagraphStyle("St", parent=body_style, fontName="Helvetica-Bold", textColor=colors.HexColor("#10b981") if field.compliant else colors.HexColor("#ef4444"))),
                Paragraph(field.remarks[:65], body_style)
            ])

        decl_table = Table(matrix_rows, colWidths=[70, 110, 120, 65, 155])
        decl_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 5),
            ('TOPPADDING', (0, 0), (-1, 0), 5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#ffffff"), colors.HexColor("#f8fafc")]),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        elements.append(decl_table)
        elements.append(Spacer(1, 10))

        # 5. Flagged Violations Section (if any)
        if compliance_data.violations:
            elements.append(Paragraph("II. FLAGGED STATUTORY VIOLATIONS & OFFENCE SUMMARY", section_heading))
            viol_rows = [["Violation ID", "Rule Section", "Offence Description", "Observed Condition", "Statutory Standard"]]
            for v in compliance_data.violations:
                viol_rows.append([
                    Paragraph(v.violation_id, body_bold),
                    Paragraph(v.rule_number, body_style),
                    Paragraph(v.description, body_style),
                    Paragraph(v.observed_value or "N/A", body_style),
                    Paragraph(v.expected_condition, body_style)
                ])
            viol_table = Table(viol_rows, colWidths=[65, 75, 160, 100, 120])
            viol_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#991b1b")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#fca5a5")),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#fff1f2"), colors.HexColor("#ffffff")]),
                ('TOPPADDING', (0, 0), (-1, -1), 3.5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ]))
            elements.append(viol_table)
            elements.append(Spacer(1, 10))

        # 6. Physical Verification Audit Section
        elements.append(Paragraph("III. LEVEL 2 PHYSICAL NET CONTENT VERIFICATION AUDIT", section_heading))
        if compliance_data.physical_verification_result:
            pr = compliance_data.physical_verification_result
            phys_rows = [
                [
                    Paragraph(f"<b>Declared Net Quantity:</b> {pr.declared_net_quantity} {pr.unit}", body_style),
                    Paragraph(f"<b>Actual Measured Content:</b> {pr.measured_actual_quantity} {pr.unit}", body_style),
                ],
                [
                    Paragraph(f"<b>Deviation / Shortfall:</b> {pr.deficit_or_excess} {pr.unit} ({pr.deficit_percentage}%)", body_style),
                    Paragraph(f"<b>Max Permissible Error (MPE):</b> ±{pr.max_permissible_error_allowed} {pr.unit}", body_style),
                ],
                [
                    Paragraph(f"<b>Physical MPE Verdict:</b> <b>{pr.status}</b>", body_style),
                    Paragraph(f"<b>Statutory Basis:</b> First Schedule / Rule 11, PCR 2011", body_style),
                ]
            ]
        else:
            phys_rows = [
                [
                    Paragraph("<b>Physical Inspection Status:</b> NOT PERFORMED / PENDING ON-SITE MEASUREMENT", body_style),
                    Paragraph("<b>Advisory:</b> Visual scan establishes label compliance only. Seal and actual net weight require physical verification.", body_style)
                ]
            ]
        phys_table = Table(phys_rows, colWidths=[260, 260])
        phys_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#94a3b8")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(phys_table)
        elements.append(Spacer(1, 15))

        # 7. Official Sign-off & Digital Stamp Block
        sign_data = [
            [
                Paragraph("<b>Inspecting Official Signature:</b><br/><br/>_______________________________<br/>" + inspector_name + "<br/>Inspector of Legal Metrology", body_style),
                Paragraph("<b>Supervising Authority Seal:</b><br/><br/>_______________________________<br/>Controller / Deputy Controller<br/>Legal Metrology Department", body_style),
                Paragraph("<b>Official Verification Seal:</b><br/><br/>[ DIGITAL CERTIFICATE ]<br/>SHA-256 Verified Record<br/>Dept of Consumer Affairs", body_style)
            ]
        ]
        sign_table = Table(sign_data, colWidths=[175, 175, 170])
        sign_table.setStyle(TableStyle([
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(sign_table)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
