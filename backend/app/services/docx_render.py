"""Render plain-text legal documents as styled .docx files (python-docx).
Layout convention for Kosovo court filings: A4, 2.5 cm margins, serif 12pt,
1.5 line spacing, justified body. The first non-empty line becomes a bold
centered title; lines in ALL CAPS become bold section headings."""
from io import BytesIO

from docx import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.shared import Cm, Pt


def _is_heading(line: str) -> bool:
    stripped = line.strip()
    if len(stripped) < 3 or len(stripped) > 120:
        return False
    letters = [c for c in stripped if c.isalpha()]
    return bool(letters) and all(c.isupper() for c in letters)


def build_docx(content: str, *, title: str | None = None) -> bytes:
    doc = DocxDocument()

    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)

    style = doc.styles["Normal"]
    style.font.name = "Times New Roman"
    style.font.size = Pt(12)
    style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    style.paragraph_format.space_after = Pt(6)

    lines = content.splitlines()
    title_done = False
    for line in lines:
        stripped = line.rstrip()
        if not stripped:
            doc.add_paragraph("")
            continue
        para = doc.add_paragraph()
        run = para.add_run(stripped)
        if not title_done:
            # First non-empty line: document title
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run.bold = True
            run.font.size = Pt(14)
            title_done = True
        elif _is_heading(stripped):
            run.bold = True
            para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        else:
            para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY

    if title:
        doc.core_properties.title = title

    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()
