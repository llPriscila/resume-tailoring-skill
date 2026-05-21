from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import re
import os

PAGE_W, PAGE_H = A4
MARGIN = 18 * mm
# GitHub markdown colours
TEXT    = colors.HexColor("#24292e")
MUTED   = colors.HexColor("#57606a")
LINK    = colors.HexColor("#0366d6")
BORDER  = colors.HexColor("#d0d7de")

def make_styles():
    name = ParagraphStyle("name", fontName="Helvetica-Bold", fontSize=22,
                          leading=26, textColor=TEXT, spaceAfter=1, alignment=TA_CENTER)
    subtitle = ParagraphStyle("subtitle", fontName="Helvetica", fontSize=14,
                              leading=17, textColor=MUTED, spaceAfter=2, alignment=TA_CENTER)
    contact = ParagraphStyle("contact", fontName="Helvetica", fontSize=9,
                             leading=13, textColor=MUTED, spaceAfter=14, alignment=TA_CENTER)
    section = ParagraphStyle("section", fontName="Helvetica-Bold", fontSize=13,
                             leading=17, textColor=TEXT, spaceBefore=18, spaceAfter=4)
    role_title = ParagraphStyle("role_title", fontName="Helvetica-Bold", fontSize=10.5,
                                leading=15, textColor=TEXT, spaceBefore=12, spaceAfter=1,
                                keepWithNext=True)
    role_meta = ParagraphStyle("role_meta", fontName="Helvetica", fontSize=9,
                               leading=13, textColor=MUTED, spaceAfter=5,
                               keepWithNext=True)
    bullet = ParagraphStyle("bullet", fontName="Helvetica", fontSize=9.5,
                            leading=15, textColor=TEXT, leftIndent=14,
                            firstLineIndent=-10, spaceAfter=5)
    body = ParagraphStyle("body", fontName="Helvetica", fontSize=9.5,
                          leading=14.5, textColor=TEXT, spaceAfter=4)
    skills_label = ParagraphStyle("skills_label", fontName="Helvetica-Bold", fontSize=9.5,
                                  leading=14, textColor=TEXT)
    skills_body = ParagraphStyle("skills_body", fontName="Helvetica", fontSize=9.5,
                                 leading=14, textColor=TEXT, spaceAfter=5)
    summary = ParagraphStyle("summary", fontName="Helvetica", fontSize=9.5,
                             leading=14.5, textColor=TEXT, spaceAfter=4)
    currently = ParagraphStyle("currently", fontName="Helvetica-Oblique", fontSize=9,
                               leading=13, textColor=MUTED, spaceAfter=5)
    return dict(name=name, subtitle=subtitle, contact=contact, section=section, role_title=role_title,
                role_meta=role_meta, bullet=bullet, body=body,
                skills_label=skills_label, skills_body=skills_body,
                summary=summary, currently=currently)

def hr(width=None):
    return HRFlowable(width=width or "100%", thickness=0.5,
                      color=BORDER, spaceAfter=4, spaceBefore=2)

def parse_md_inline(text, linkcolor="#0366d6"):
    """Convert markdown inline bold/italic/links to reportlab XML."""
    # links: [text](url) → clickable hyperlink
    text = re.sub(
        r'\[([^\]]+)\]\(([^\)]+)\)',
        lambda m: f'<link href="{m.group(2)}" color="{linkcolor}"><u>{m.group(1)}</u></link>',
        text
    )
    # bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', text)
    # italic
    text = re.sub(r'\*([^*]+)\*', r'<i>\1</i>', text)
    # em dash
    text = text.replace('—', '–')
    return text

def build_pdf(md_path, pdf_path):
    with open(md_path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    S = make_styles()
    doc = SimpleDocTemplate(
        pdf_path, pagesize=A4,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=14*mm, bottomMargin=14*mm
    )

    story = []
    i = 0
    n = len(lines)
    after_h1 = False

    while i < n:
        line = lines[i]

        # Skip horizontal rules
        if line.strip() in ("---", "___", "***"):
            i += 1
            continue

        # H1 — name
        if line.startswith("# ") and not line.startswith("## "):
            story.append(Paragraph(line[2:].strip(), S["name"]))
            after_h1 = True
            i += 1
            continue

        # H3 immediately after H1 → subtitle
        if after_h1 and line.startswith("### "):
            clean = re.sub(r'<[^>]+>', '', line[4:].strip())
            story.append(Paragraph(clean, S["subtitle"]))
            after_h1 = False
            i += 1
            continue

        # Subtitle — first non-empty non-heading non-bullet line after H1
        if after_h1 and line.strip() and not line.startswith("#") and not line.startswith("-"):
            clean = re.sub(r'<[^>]+>', '', line.strip())
            story.append(Paragraph(clean, S["subtitle"]))
            after_h1 = False
            i += 1
            continue

        if after_h1 and not line.strip():
            i += 1
            continue

        # H2 — section headers
        if line.startswith("## "):
            title = line[3:].strip()
            story.append(Spacer(1, 1))
            story.append(Paragraph(title, S["section"]))
            story.append(hr())
            i += 1
            continue

        # H3 — role title
        if line.startswith("### "):
            story.append(Paragraph(parse_md_inline(line[4:].strip()), S["role_title"]))
            i += 1
            continue

        # Bold line (role meta: **Company — Location | Dates**)
        if line.startswith("**") and line.endswith("**") and not line.startswith("**Technical") \
                and not line.startswith("**Analytics") and not line.startswith("**Leadership") \
                and not line.startswith("**Visualisation") and not line.startswith("**Analysis") \
                and not line.startswith("**Delivery") and not line.startswith("**Currently"):
            inner = line[2:-2].strip()
            story.append(Paragraph(parse_md_inline(inner), S["role_meta"]))
            i += 1
            continue

        # Bullet point
        if line.startswith("- "):
            text = parse_md_inline(line[2:].strip())
            story.append(Paragraph(f"• &nbsp;{text}", S["bullet"]))
            i += 1
            continue

        # Skills line with bold label: **Label:** content
        m = re.match(r'^\*\*([^*]+)\*\*[:\s]+(.*)', line)
        if m:
            label = m.group(1).strip().rstrip(':')
            rest = parse_md_inline(m.group(2).strip())
            if label.lower().startswith("currently"):
                story.append(Paragraph(f"<b>{label}:</b> <i>{rest}</i>", S["currently"]))
            else:
                story.append(Paragraph(f"<b>{label}:</b> {rest}", S["skills_body"]))
            i += 1
            continue

        # Non-empty line — body text (contact info, plain paragraphs)
        if line.strip():
            story.append(Paragraph(parse_md_inline(line.strip()), S["summary"]))
            i += 1
            continue

        # Empty line
        story.append(Spacer(1, 5))
        i += 1

    doc.build(story)
    print(f"Generated: {pdf_path}")

def md_to_pdf(md_filename, base_dir=None):
    """Convert a markdown CV to PDF. Naming convention: every word separated by _.
    Pass the .md filename; PDF will be written alongside it with same stem + .pdf"""
    base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
    md_path = os.path.join(base_dir, md_filename)
    pdf_path = os.path.join(base_dir, os.path.splitext(md_filename)[0] + ".pdf")
    build_pdf(md_path, pdf_path)
    return pdf_path

if __name__ == "__main__":
    base = os.path.dirname(os.path.abspath(__file__))
    # Naming convention: First_Last_Company_Role_Title_Resume.md (every word separated by _)
    md_to_pdf("Ioana_Criclevit_Wise_Staff_Data_Analyst_Resume.md", base)
    md_to_pdf("Ioana_Criclevit_Ravio_Insights_Analyst_Resume.md", base)
    md_to_pdf("Ioana_Criclevit_FCA_Financial_Crime_Senior_Data_Analyst_Resume.md", base)
    md_to_pdf("Ioana_Criclevit_Zopa_Data_Analyst_Fraud_Financial_Crime_Resume.md", base)
    md_to_pdf("Ioana_Criclevit_Zopa_Senior_Analyst_Lending_Operations_Resume.md", base)
    md_to_pdf("Ioana_Criclevit_Monzo_Senior_Data_Analyst_Financial_Health_Resume.md", base)
    md_to_pdf("Ioana_Criclevit_Elsevier_Senior_Data_Analyst_Resume.md", base)
