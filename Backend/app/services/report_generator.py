"""
PDF Report Generator using ReportLab.
Generates a structured pharmaceutical authentication report.
"""

import json
import os
import logging
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from app.config import settings

logger = logging.getLogger("spectraguard.reports")


# ── Colour palette ─────────────────────────────────────────────────────────────
PRIMARY = colors.HexColor("#1A237E")       # deep navy
ACCENT = colors.HexColor("#0288D1")        # blue
GENUINE_COLOR = colors.HexColor("#2E7D32")
COUNTERFEIT_COLOR = colors.HexColor("#C62828")
VERIFY_COLOR = colors.HexColor("#E65100")
LIGHT_GRAY = colors.HexColor("#F5F5F5")
MID_GRAY = colors.HexColor("#BDBDBD")


def _result_color(result: str) -> colors.Color:
    mapping = {
        "genuine": GENUINE_COLOR,
        "potentially_counterfeit": COUNTERFEIT_COLOR,
        "requires_verification": VERIFY_COLOR,
    }
    return mapping.get(result, colors.black)


def _result_label(result: str) -> str:
    labels = {
        "genuine": "✓ GENUINE",
        "potentially_counterfeit": "⚠ POTENTIALLY COUNTERFEIT",
        "requires_verification": "? REQUIRES FURTHER VERIFICATION",
        "pending": "PENDING",
    }
    return labels.get(result, result.upper())


def generate_pdf_report(test: Any, user: Any, spectra: Any, reference: Any, output_path: str) -> str:
    """
    Generate a PDF report for a completed test.

    Parameters
    ----------
    test       : Test ORM object
    user       : User ORM object
    spectra    : SpectraData ORM object (or None)
    reference  : ReferenceSpectrum ORM object (or None)
    output_path: full path where the PDF should be saved

    Returns
    -------
    output_path (same as input)
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Normal"],
        fontSize=20,
        textColor=PRIMARY,
        spaceAfter=4,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    sub_style = ParagraphStyle(
        "Sub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=ACCENT,
        spaceAfter=2,
        alignment=TA_CENTER,
    )
    body_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        spaceAfter=4,
        leading=14,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.gray,
        fontName="Helvetica-Bold",
    )

    story.append(Paragraph("SpectraGuard", title_style))
    story.append(Paragraph("Pharmaceutical Authentication Report", sub_style))
    story.append(Paragraph(f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", sub_style))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceAfter=12))

    # ── Classification Result Banner ──────────────────────────────────────────
    result_label = _result_label(test.classification_result)
    result_color = _result_color(test.classification_result)

    banner_style = ParagraphStyle(
        "Banner",
        parent=styles["Normal"],
        fontSize=14,
        textColor=colors.white,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
        backColor=result_color,
        borderPadding=10,
        spaceAfter=16,
    )
    story.append(Paragraph(result_label, banner_style))

    confidence = f"{test.confidence_score:.1f}%" if test.confidence_score is not None else "N/A"
    story.append(Paragraph(f"Confidence Score: <b>{confidence}</b>", body_style))
    story.append(Spacer(1, 0.4 * cm))

    # ── Test Details ──────────────────────────────────────────────────────────
    story.append(Paragraph("Test Details", ParagraphStyle("H2", parent=styles["Normal"],
                                                           fontSize=12, textColor=PRIMARY,
                                                           fontName="Helvetica-Bold", spaceAfter=6)))
    test_data = [
        ["Test ID", str(test.id), "Date Tested", test.tested_at.strftime("%Y-%m-%d %H:%M") if test.tested_at else "N/A"],
        ["Drug Name", test.drug_name, "Batch Number", test.batch_number or "N/A"],
        ["Manufacturer", test.manufacturer or "N/A", "Expiry Date", test.expiry_date or "N/A"],
    ]
    test_table = Table(test_data, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 6 * cm])
    test_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_GRAY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(test_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Submitted By ──────────────────────────────────────────────────────────
    story.append(Paragraph("Submitted By", ParagraphStyle("H2", parent=styles["Normal"],
                                                           fontSize=12, textColor=PRIMARY,
                                                           fontName="Helvetica-Bold", spaceAfter=6)))
    user_data = [
        ["Name", user.full_name, "Role", user.role.value.capitalize()],
        ["Email", user.email, "Organization", user.organization or "N/A"],
        ["License No.", user.license_number or "N/A", "City", user.city or "N/A"],
    ]
    user_table = Table(user_data, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 6 * cm])
    user_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_GRAY),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(user_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Matched Reference ──────────────────────────────────────────────────────
    if reference:
        story.append(Paragraph("Best-Matched Reference Spectrum", ParagraphStyle(
            "H2", parent=styles["Normal"], fontSize=12, textColor=PRIMARY,
            fontName="Helvetica-Bold", spaceAfter=6)))
        ref_data = [
            ["Reference ID", str(reference.id), "Drug Name", reference.drug_name],
            ["Manufacturer", reference.manufacturer or "N/A", "Source", reference.source or "N/A"],
            ["Batch Ref.", reference.batch_reference or "N/A", "Cosine Similarity",
             f"{test.confidence_score / 100:.4f}" if test.confidence_score else "N/A"],
        ]
        ref_table = Table(ref_data, colWidths=[3.5 * cm, 6 * cm, 3.5 * cm, 6 * cm])
        ref_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), LIGHT_GRAY),
            ("BACKGROUND", (2, 0), (2, -1), LIGHT_GRAY),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("GRID", (0, 0), (-1, -1), 0.5, MID_GRAY),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        story.append(ref_table)
        story.append(Spacer(1, 0.5 * cm))

    # ── Classification Explanation ─────────────────────────────────────────────
    story.append(Paragraph("Classification Methodology", ParagraphStyle(
        "H2", parent=styles["Normal"], fontSize=12, textColor=PRIMARY,
        fontName="Helvetica-Bold", spaceAfter=6)))
    explanations = {
        "genuine": (
            "The uploaded spectrum exhibits a high cosine similarity (≥ 97%) with the reference spectrum. "
            "The spectral profile, peak positions, and relative intensities closely match those of the "
            "authenticated reference compound. This product is classified as <b>Genuine</b>."
        ),
        "potentially_counterfeit": (
            "The uploaded spectrum shows low cosine similarity (< 85%) with the reference database. "
            "Significant deviations in peak positions and/or intensities suggest the sample may not "
            "contain the claimed active pharmaceutical ingredient. This product is classified as "
            "<b>Potentially Counterfeit</b>. Immediate regulatory action is recommended."
        ),
        "requires_verification": (
            "The uploaded spectrum shows intermediate similarity (85%–97%) with available references. "
            "This may indicate a degraded sample, different formulation, or manufacturing variation. "
            "Further laboratory analysis is required before a definitive conclusion can be drawn."
        ),
    }
    explanation = explanations.get(
        test.classification_result,
        "Classification pending or result unavailable."
    )
    story.append(Paragraph(explanation, body_style))
    story.append(Spacer(1, 0.5 * cm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceAfter=8))
    footer_style = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.gray,
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        "This report is generated by the SpectraGuard Pharmaceutical Authentication System. "
        "It is intended for informational purposes and should be used in conjunction with "
        "laboratory analysis and regulatory assessment. SpectraGuard is not liable for decisions "
        "made solely on the basis of this report.",
        footer_style,
    ))
    story.append(Paragraph(f"Report ID: TEST-{test.id:06d}", footer_style))

    doc.build(story)
    logger.info(f"Generated PDF report: {output_path}")
    return output_path
