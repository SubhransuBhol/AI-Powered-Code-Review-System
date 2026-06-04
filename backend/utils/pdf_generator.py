from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)
from reportlab.lib import colors
from datetime import datetime

SUBSECTION_HEADINGS = [
    "Executive Assessment",
    "Code Quality Score",
    "Strengths",
    "Weaknesses",
    "Critical Issues",
    "Security Assessment",
    "Recommended Actions",
    "Final Verdict",
    "Risk Level",
    "Bugs",
    "Security Issues",
    "Improvements",
    "Static Analysis Findings"
]

def md_to_html(text):
    """
    Converts markdown bold **text** to HTML bold <b>text</b> for ReportLab Paragraph compatibility.
    """
    parts = text.split("**")
    html_parts = []
    for idx, part in enumerate(parts):
        if idx % 2 == 1:
            html_parts.append(f"<b>{part}</b>")
        else:
            html_parts.append(part)
    return "".join(html_parts)

def generate_pdf_report(
    report_text,
    pdf_path,
    summary,
    overall_risk
):
    # Set up document with consistent margins (0.75 in / 54 pt)
    doc = SimpleDocTemplate(
        pdf_path,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()

    # Define clean, professional ParagraphStyles with specified hierarchy
    title_style = ParagraphStyle(
        "CustomTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=26,
        leading=32,
        spaceAfter=10,
        textColor=colors.HexColor("#1A365D"),  # Deep Navy
        alignment=0  # Left aligned
    )

    meta_style = ParagraphStyle(
        "CustomMeta",
        fontName="Helvetica-Oblique",
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#718096"),  # Slate Grey
        spaceAfter=20
    )

    major_section_style = ParagraphStyle(
        "CustomMajorSection",
        fontName="Helvetica-Bold",
        fontSize=16,
        leading=20,
        spaceBefore=22,
        spaceAfter=10,
        textColor=colors.HexColor("#2B6CB0"),  # Medium Blue
        keepWithNext=True
    )

    subsection_style = ParagraphStyle(
        "CustomSubsection",
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        spaceBefore=14,
        spaceAfter=6,
        textColor=colors.HexColor("#2D3748"),  # Dark Charcoal
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        "CustomBody",
        fontName="Helvetica",
        fontSize=10.5,
        leading=15,
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=6
    )

    bullet_style = ParagraphStyle(
        "CustomBullet",
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=4
    )

    suggested_fix_header_style = ParagraphStyle(
        "SuggestedFixHeader",
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2B6CB0"),  # Medium Blue
        spaceBefore=10,
        spaceAfter=4,
        leftIndent=15,
        keepWithNext=True
    )

    code_style = ParagraphStyle(
        "CodeSnippet",
        fontName="Courier",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#2D3748"),  # Dark Charcoal
        leftIndent=25,
        spaceAfter=2
    )

    footer_style = ParagraphStyle(
        "CustomFooter",
        fontName="Helvetica-Oblique",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#A0AEC0"),
        spaceBefore=10
    )

    elements = []

    # =========================
    # TITLE & METADATA
    # =========================
    elements.append(
        Paragraph("AI Code Review Report", title_style)
    )
    elements.append(
        Paragraph(f"Generated On: {datetime.now().strftime('%d %B %Y %H:%M')}", meta_style)
    )

    # =========================
    # EXECUTIVE SUMMARY CARD
    # =========================
    elements.append(
        Paragraph("Executive Summary", major_section_style)
    )

    # Risk level color indicators
    risk_color = "#2D3748"
    risk_val = str(overall_risk).upper()
    if "HIGH" in risk_val:
        risk_color = "#E53E3E"  # Red
    elif "MEDIUM" in risk_val:
        risk_color = "#DD6B20"  # Orange
    elif "LOW" in risk_val:
        risk_color = "#38A169"  # Green

    summary_data = [
        [Paragraph("<b>Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
        [Paragraph("Files Reviewed", body_style), Paragraph(str(summary.get('files_reviewed', 0)), body_style)],
        [Paragraph("Total Bugs Found", body_style), Paragraph(str(summary.get('bugs', 0)), body_style)],
        [Paragraph("Total Security Issues Found", body_style), Paragraph(str(summary.get('security', 0)), body_style)],
        [Paragraph("Total Improvements Suggested", body_style), Paragraph(str(summary.get('improvements', 0)), body_style)],
        [Paragraph("Overall Risk Level", body_style), Paragraph(f"<font color='{risk_color}'><b>{overall_risk}</b></font>", body_style)],
    ]
    
    summary_table = Table(summary_data, colWidths=[250, 250])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#E2E8F0")),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F7FAFC")),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 15))

    # =========================
    # REPORT CONTENT PARSING
    # =========================
    in_suggested_fix = False

    for raw_line in report_text.splitlines():
        line = raw_line.strip()

        # Check for Suggested Fix header
        if line == "Suggested Fix:":
            in_suggested_fix = True
            elements.append(
                Paragraph("Suggested Fix", suggested_fix_header_style)
            )
            continue

        if in_suggested_fix:
            # Check if this line ends the suggested fix block (e.g. starts with a bullet or section)
            is_bullet = line.startswith("•") or line.startswith("* ") or line.startswith("- ") or (line.startswith("*") and not line.startswith("**"))
            
            if line.startswith("#") or line.upper() == "PROJECT LEVEL ANALYSIS" or is_bullet or line.startswith("---"):
                in_suggested_fix = False
                elements.append(Spacer(1, 8))
            else:
                # Format this code line
                escaped_line = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                # Strip the first 2 markdown indentation spaces if present
                code_line = raw_line
                if code_line.startswith("  "):
                    code_line = code_line[2:]
                
                num_spaces = len(code_line) - len(code_line.lstrip(' '))
                if num_spaces > 0:
                    escaped_line = "&nbsp;" * num_spaces + code_line.lstrip(' ')
                else:
                    escaped_line = code_line
                
                elements.append(
                    Paragraph(escaped_line, code_style)
                )
                continue

        if not line:
            continue

        # Check for Horizontal Rules
        if line.startswith("---"):
            divider = Table([[""]], colWidths=[500])
            divider.setStyle(TableStyle([
                ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(Spacer(1, 10))
            elements.append(divider)
            elements.append(Spacer(1, 10))
            continue

        # Check for Major Sections (starts with # or matches PROJECT LEVEL ANALYSIS)
        if line.startswith("# ") or line.upper() == "PROJECT LEVEL ANALYSIS":
            title_text = line.replace("#", "").strip()
            
            # Visual section separator divider line
            if elements:
                divider = Table([[""]], colWidths=[500])
                divider.setStyle(TableStyle([
                    ('LINEABOVE', (0, 0), (-1, -1), 1, colors.HexColor("#2B6CB0")),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
                    ('TOPPADDING', (0, 0), (-1, -1), 0),
                ]))
                elements.append(Spacer(1, 15))
                elements.append(divider)
                elements.append(Spacer(1, 10))

            elements.append(
                Paragraph(title_text, major_section_style)
            )
            continue

        # Check for Subsections
        temp_line = line.replace("##", "").replace("**", "").strip()
        temp_compare = temp_line.rstrip(":").strip()

        if line.startswith("##") or temp_compare in SUBSECTION_HEADINGS:
            elements.append(
                Paragraph(temp_compare, subsection_style)
            )
            continue

        # Check for Bullet Lists
        is_bullet = False
        bullet_content = ""
        if line.startswith("•"):
            is_bullet = True
            bullet_content = line[1:].strip()
        elif line.startswith("* ") or line.startswith("- "):
            is_bullet = True
            bullet_content = line[2:].strip()
        elif line.startswith("*") and not line.startswith("**"):
            is_bullet = True
            bullet_content = line[1:].strip()

        if is_bullet:
            if bullet_content:
                elements.append(
                    Paragraph(md_to_html(f"• {bullet_content}"), bullet_style)
                )
            continue

        # Regular Body Paragraphs
        elements.append(
            Paragraph(md_to_html(line), body_style)
        )

    # =========================
    # FOOTER
    # =========================
    elements.append(Spacer(1, 20))
    divider = Table([[""]], colWidths=[500])
    divider.setStyle(TableStyle([
        ('LINEABOVE', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    elements.append(divider)
    elements.append(Spacer(1, 5))
    elements.append(
        Paragraph("Generated by AI Code Reviewer", footer_style)
    )

    doc.build(elements)
    return pdf_path
