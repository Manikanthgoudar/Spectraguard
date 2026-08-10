"""
PDF Report Generator using ReportLab.
Generates a clean, structured pharmaceutical authentication report.
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

logger = logging.getLogger("spectraguard.reports")

# ── Colour palette ─────────────────────────────────────────────────────────────
PRIMARY = colors.HexColor("#1A237E")       # deep navy
ACCENT = colors.HexColor("#0288D1")        # blue accent
GENUINE_COLOR = colors.HexColor("#2E7D32")  # forest green
COUNTERFEIT_COLOR = colors.HexColor("#C62828") # crimson red
VERIFY_COLOR = colors.HexColor("#E65100")   # amber orange
LIGHT_BG = colors.HexColor("#F8F9FA")
BORDER_COLOR = colors.HexColor("#CFD8DC")
TEXT_COLOR = colors.HexColor("#263238")
MID_GRAY = colors.HexColor("#78909C")


def _result_color(result: Any) -> colors.Color:
    val = str(result.value if hasattr(result, "value") else result)
    mapping = {
        "genuine": GENUINE_COLOR,
        "potentially_counterfeit": COUNTERFEIT_COLOR,
        "requires_verification": VERIFY_COLOR,
    }
    return mapping.get(val, colors.black)


def _result_label(result: Any) -> str:
    val = str(result.value if hasattr(result, "value") else result)
    labels = {
        "genuine": "✓ GENUINE",
        "potentially_counterfeit": "⚠ POTENTIALLY COUNTERFEIT",
        "requires_verification": "? REQUIRES FURTHER VERIFICATION",
        "pending": "PENDING",
    }
    return labels.get(val, val.upper())


def _make_cell(text: Any, is_header: bool = False, align: int = TA_LEFT) -> Paragraph:
    """Wrap string in Paragraph to enforce auto-wrapping inside Table cells without overflow."""
    val = str(text) if text is not None and str(text).strip() != "" else "N/A"
    style = ParagraphStyle(
        "TableCell",
        fontName="Helvetica-Bold" if is_header else "Helvetica",
        fontSize=9,
        leading=12,
        textColor=PRIMARY if is_header else TEXT_COLOR,
        alignment=align,
    )
    return Paragraph(val, style)


def generate_pdf_report(test: Any, user: Any, spectra: Any, reference: Any, output_path: str) -> str:
    """
    Generate a PDF report for a completed test.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=PRIMARY,
        alignment=TA_CENTER,
        spaceAfter=4,
    )
    sub_title_style = ParagraphStyle(
        "ReportSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=ACCENT,
        alignment=TA_CENTER,
        spaceAfter=3,
    )
    meta_style = ParagraphStyle(
        "ReportMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.gray,
        alignment=TA_CENTER,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=TEXT_COLOR,
        spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceAfter=6,
    )

    story.append(Paragraph("SpectraGuard", title_style))
    story.append(Paragraph("Pharmaceutical Authentication Report", sub_title_style))
    story.append(Paragraph(f"Report Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", meta_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=PRIMARY, spaceAfter=12))

    # Usable page width: A4 (21 cm) - left margin (1.5 cm) - right margin (1.5 cm) = 18 cm
    PAGE_W = 18.0 * cm
    # Column widths for 4-column tables: label | value | label | value
    COL_LABEL = 3.4 * cm
    COL_VALUE = 5.6 * cm  # (18 - 3.4 - 3.4) / 2 = 5.6 cm each

    TABLE_STYLE = TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), LIGHT_BG),
        ("BACKGROUND", (2, 0), (2, -1), LIGHT_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
    ])

    # ── Classification Result Banner ──────────────────────────────────────────
    result_label = _result_label(test.classification_result)
    result_color = _result_color(test.classification_result)

    banner_para_style = ParagraphStyle(
        "BannerText",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    banner_table = Table(
        [[Paragraph(result_label, banner_para_style)]],
        colWidths=[PAGE_W],
    )
    banner_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), result_color),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("ROUNDEDCORNERS", [4, 4, 4, 4]),
    ]))
    story.append(banner_table)
    story.append(Spacer(1, 0.3 * cm))

    # Normalize confidence score for display
    raw_conf = test.confidence_score
    if raw_conf is not None:
        conf_percent = raw_conf if raw_conf > 1.0 else raw_conf * 100.0
        conf_str = f"{conf_percent:.1f}%"
        cos_sim = f"{(conf_percent / 100.0):.4f}"
    else:
        conf_str = "N/A"
        cos_sim = "N/A"

    story.append(Paragraph(f"Confidence Score: <b>{conf_str}</b>", body_style))
    story.append(Spacer(1, 0.4 * cm))

    # ── Test Details ──────────────────────────────────────────────────────────
    story.append(Paragraph("Test Details", h2_style))
    test_data = [
        [
            _make_cell("Test ID", is_header=True),
            _make_cell(str(test.id)),
            _make_cell("Date Tested", is_header=True),
            _make_cell(test.tested_at.strftime("%Y-%m-%d %H:%M") if test.tested_at else "N/A"),
        ],
        [
            _make_cell("Drug Name", is_header=True),
            _make_cell(test.drug_name),
            _make_cell("Batch Number", is_header=True),
            _make_cell(test.batch_number),
        ],
        [
            _make_cell("Manufacturer", is_header=True),
            _make_cell(test.manufacturer),
            _make_cell("Expiry Date", is_header=True),
            _make_cell(test.expiry_date),
        ],
    ]
    test_table = Table(test_data, colWidths=[COL_LABEL, COL_VALUE, COL_LABEL, COL_VALUE])
    test_table.setStyle(TABLE_STYLE)
    story.append(test_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Submitted By ──────────────────────────────────────────────────────────
    story.append(Paragraph("Submitted By", h2_style))
    user_data = [
        [
            _make_cell("Name", is_header=True),
            _make_cell(user.full_name),
            _make_cell("Role", is_header=True),
            _make_cell(user.role.value.capitalize() if hasattr(user.role, 'value') else str(user.role)),
        ],
        [
            _make_cell("Email", is_header=True),
            _make_cell(user.email),
            _make_cell("Organization", is_header=True),
            _make_cell(user.organization),
        ],
        [
            _make_cell("License No.", is_header=True),
            _make_cell(user.license_number),
            _make_cell("City", is_header=True),
            _make_cell(user.city),
        ],
    ]
    user_table = Table(user_data, colWidths=[COL_LABEL, COL_VALUE, COL_LABEL, COL_VALUE])
    user_table.setStyle(TABLE_STYLE)
    story.append(user_table)
    story.append(Spacer(1, 0.5 * cm))

    # ── Matched Reference ──────────────────────────────────────────────────────
    if reference:
        story.append(Paragraph("Best-Matched Reference Spectrum", h2_style))
        ref_data = [
            [
                _make_cell("Reference ID", is_header=True),
                _make_cell(str(reference.id)),
                _make_cell("Drug Name", is_header=True),
                _make_cell(reference.drug_name),
            ],
            [
                _make_cell("Manufacturer", is_header=True),
                _make_cell(reference.manufacturer),
                _make_cell("Source", is_header=True),
                _make_cell(reference.source),
            ],
            [
                _make_cell("Batch Ref.", is_header=True),
                _make_cell(reference.batch_reference),
                _make_cell("Cosine Similarity", is_header=True),
                _make_cell(cos_sim),
            ],
        ]
        ref_table = Table(ref_data, colWidths=[COL_LABEL, COL_VALUE, COL_LABEL, COL_VALUE])
        ref_table.setStyle(TABLE_STYLE)
        story.append(ref_table)
        story.append(Spacer(1, 0.5 * cm))

    # ── Classification Explanation ─────────────────────────────────────────────
    story.append(Paragraph("Classification Methodology", h2_style))
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
    res_key = str(test.classification_result.value if hasattr(test.classification_result, "value") else test.classification_result)
    explanation = explanations.get(
        res_key,
        "Classification pending or result unavailable."
    )
    story.append(Paragraph(explanation, body_style))
    story.append(Spacer(1, 0.5 * cm))

    # ── Footer ─────────────────────────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceAfter=8))
    footer_style = ParagraphStyle(
        "FooterText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
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
