"""Build the editable ML Experiment Detective Markdown guide as a study PDF.

Run with the Codex bundled Python that has reportlab installed. This builder
only reads the guide source and writes its named PDF in docs/.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import simpleSplit
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable, HRFlowable, KeepTogether, PageBreak, Paragraph, Preformatted,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents


HERE = Path(__file__).resolve().parent
SOURCE = HERE / "ML_Experiment_Detective_Complete_Learning_Guide.md"
OUTPUT = HERE / "ML_Experiment_Detective_Complete_Learning_Guide.pdf"
INK = colors.HexColor("#17324B")
BLUE = colors.HexColor("#185B89")
TEAL = colors.HexColor("#087E8B")
PALE = colors.HexColor("#EAF4F7")
LIGHT = colors.HexColor("#F4F7FA")
MUTED = colors.HexColor("#536777")


def register_fonts():
    font_dir = Path("C:/Windows/Fonts")
    fonts = {
        "Guide": "arial.ttf", "Guide-Bold": "arialbd.ttf",
        "Guide-Italic": "ariali.ttf", "Code": "consola.ttf",
    }
    for name, filename in fonts.items():
        pdfmetrics.registerFont(TTFont(name, str(font_dir / filename)))
    pdfmetrics.registerFontFamily("Guide", normal="Guide", bold="Guide-Bold", italic="Guide-Italic")


def inline(text: str) -> str:
    """Small Markdown inline subset used by the authored guide."""
    saved = []

    def code(match):
        saved.append(f'<font name="Code" color="#146579">{html.escape(match.group(1))}</font>')
        return f"@@INLINE{len(saved)-1}@@"

    text = re.sub(r"`([^`]+)`", code, text)
    text = html.escape(text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", text)
    for i, token in enumerate(saved):
        text = text.replace(f"@@INLINE{i}@@", token)
    return text.replace("  ", " ")


class Diagram(Flowable):
    """Vector boxes and arrows generated from a simple row/branch flow spec."""

    def __init__(self, rows, width):
        super().__init__()
        self.rows = [[x.strip() for x in row.split("|")] for row in rows if row.strip()]
        self.width = width
        self.box_rows = []
        for row in self.rows:
            box_w = min(440, (width - 36 - 12 * (len(row) - 1)) / len(row))
            lines = [simpleSplit(s, "Guide", 9.1, box_w - 20) for s in row]
            height = max(34, max(len(item) for item in lines) * 12 + 14)
            self.box_rows.append((row, lines, box_w, height))
        self.height = 18 + sum(x[3] for x in self.box_rows) + 22 * max(0, len(self.box_rows) - 1) + 18

    def wrap(self, availWidth, availHeight):
        return self.width, self.height

    def draw(self):
        c = self.canv
        c.setFillColor(LIGHT)
        c.setStrokeColor(colors.HexColor("#D4E5EB"))
        c.roundRect(0, 0, self.width, self.height, 11, fill=1, stroke=1)
        top = self.height - 18
        for idx, (row, line_groups, box_w, height) in enumerate(self.box_rows):
            y = top - height
            total = len(row) * box_w + (len(row) - 1) * 12
            start = (self.width - total) / 2
            for col, lines in enumerate(line_groups):
                x = start + col * (box_w + 12)
                c.setFillColor(colors.white if idx % 2 else PALE)
                c.setStrokeColor(colors.HexColor("#7FB7C8"))
                c.roundRect(x, y, box_w, height, 6, fill=1, stroke=1)
                c.setFont("Guide", 9.1)
                c.setFillColor(INK)
                text_top = y + (height + 12 * len(lines)) / 2 - 10
                for line_i, line in enumerate(lines):
                    c.drawCentredString(x + box_w / 2, text_top - 12 * line_i, line)
            if idx < len(self.box_rows) - 1:
                c.setStrokeColor(TEAL)
                c.setFillColor(TEAL)
                cx = self.width / 2
                end_y = y - 18
                c.line(cx, y - 1, cx, end_y)
                p = c.beginPath()
                p.moveTo(cx - 4, end_y + 5)
                p.lineTo(cx + 4, end_y + 5)
                p.lineTo(cx, end_y)
                p.close()
                c.drawPath(p, fill=1, stroke=0)
            top = y - 22


class GuideDoc(SimpleDocTemplate):
    def afterFlowable(self, flowable):
        if isinstance(flowable, Paragraph) and hasattr(flowable, "toc_title"):
            title = flowable.toc_title
            key = "section_" + re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title, key, level=0, closed=False)
            self.notify("TOCEntry", (0, title, self.page, key))


def page_frame(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        canvas.restoreState()
        return
    w, h = letter
    canvas.setStrokeColor(colors.HexColor("#D2E0E8"))
    canvas.line(52, h - 43, w - 52, h - 43)
    canvas.setFont("Guide", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(52, h - 34, "ML EXPERIMENT DETECTIVE  /  COMPLETE LEARNING GUIDE")
    canvas.line(52, 40, w - 52, 40)
    canvas.drawString(52, 27, "Local project study edition  |  3 October 2026")
    canvas.drawRightString(w - 52, 27, str(doc.page))
    canvas.restoreState()


def styles():
    base = getSampleStyleSheet()
    result = {}
    result["body"] = ParagraphStyle(
        "body", parent=base["Normal"], fontName="Guide", fontSize=9.9,
        leading=14.3, textColor=INK, spaceAfter=8.5,
    )
    result["title"] = ParagraphStyle(
        "title", fontName="Guide-Bold", fontSize=29, leading=34,
        textColor=INK, spaceAfter=14,
    )
    result["deck"] = ParagraphStyle(
        "deck", fontName="Guide", fontSize=14, leading=21,
        textColor=BLUE, spaceAfter=20,
    )
    result["h1"] = ParagraphStyle(
        "h1", fontName="Guide-Bold", fontSize=19.5, leading=23.5,
        textColor=INK, spaceBefore=3, spaceAfter=15, keepWithNext=True,
    )
    result["h2"] = ParagraphStyle(
        "h2", fontName="Guide-Bold", fontSize=12.5, leading=16,
        textColor=BLUE, spaceBefore=14, spaceAfter=8, keepWithNext=True,
    )
    result["h3"] = ParagraphStyle(
        "h3", fontName="Guide-Bold", fontSize=10.6, leading=14,
        textColor=BLUE, spaceBefore=10, spaceAfter=7, keepWithNext=True,
    )
    result["part"] = ParagraphStyle(
        "part", fontName="Guide-Bold", fontSize=9.5, leading=12,
        textColor=TEAL, spaceBefore=0, spaceAfter=7, keepWithNext=True,
    )
    result["figure"] = ParagraphStyle(
        "figure", fontName="Guide-Bold", fontSize=9.3, leading=12,
        textColor=BLUE, spaceBefore=9, spaceAfter=6, keepWithNext=True,
    )
    result["list"] = ParagraphStyle(
        "list", parent=result["body"], leftIndent=17,
        firstLineIndent=-12, spaceAfter=5,
    )
    result["tablehead"] = ParagraphStyle(
        "tablehead", fontName="Guide-Bold", fontSize=8.8, leading=11.5,
        textColor=colors.white,
    )
    result["table"] = ParagraphStyle(
        "table", fontName="Guide", fontSize=8.5, leading=11.3,
        textColor=INK,
    )
    result["toc"] = ParagraphStyle(
        "toc", fontName="Guide", fontSize=9.5, leading=12.6,
        textColor=INK, leftIndent=4, firstLineIndent=0, spaceBefore=2,
    )
    return result


def make_table(lines, available, st):
    rows = []
    for line in lines:
        if re.fullmatch(r"[| :\-]+", line):
            continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        rows.append(cells)
    if not rows:
        return Spacer(1, 1)
    cols = len(rows[0])
    if cols == 2:
        widths = [available * .34, available * .66]
    elif cols == 3:
        widths = [available * .25, available * .37, available * .38]
    else:
        widths = [available / cols] * cols
    data = []
    for row_i, row in enumerate(rows):
        style = st["tablehead"] if row_i == 0 else st["table"]
        data.append([Paragraph(inline(cell), style) for cell in row])
    table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BLUE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), .6, BLUE),
        ("LINEBELOW", (0, 1), (-1, -1), .25, colors.HexColor("#DDE7ED")),
    ]))
    return table


def make_code(lines, available):
    longest = max((len(line.expandtabs(4)) for line in lines), default=0)
    size = 8.1 if longest < 98 else 7.4
    pre = Preformatted("\n".join(lines), ParagraphStyle(
        "code", fontName="Code", fontSize=size, leading=size * 1.48,
        textColor=INK,
    ))
    box = Table([[pre]], colWidths=[available], hAlign="LEFT")
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("BOX", (0, 0), (-1, -1), .6, colors.HexColor("#D3E0E6")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    return box


def make_callout(text, available, st):
    cell = Paragraph(inline(text), st["body"])
    box = Table([[cell]], colWidths=[available], hAlign="LEFT")
    box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PALE),
        ("LINEBEFORE", (0, 0), (0, -1), 3, TEAL),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return box


def parse_story(text, st, available):
    story = []
    lines = text.splitlines()
    i = 0
    pending_part = None
    first_section = True
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("```\u0066low"):
            i += 1
            rows = []
            while i < len(lines) and not lines[i].startswith("```"):
                rows.append(lines[i]); i += 1
            story.extend([Diagram(rows, available), Spacer(1, 8)])
            i += 1
            continue
        if line.startswith("```"):
            i += 1
            code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            story.extend([make_code(code, available), Spacer(1, 8)])
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i]); i += 1
            story.extend([make_table(rows, available, st), Spacer(1, 11)])
            continue
        if line.startswith("# "):
            title = line[2:]
            if first_section:
                story.extend([Spacer(1, 108), Paragraph(inline(title), st["title"]),
                              HRFlowable(width="32%", thickness=4, color=TEAL, hAlign="LEFT"),
                              Spacer(1, 18),
                              Paragraph("From Fashion-MNIST to semantic retrieval, RAG, and a local tool-using agent", st["deck"]),
                              Spacer(1, 18),
                              Paragraph("A beginner-first walkthrough of the working repository, its saved measurements, and the exact question-to-answer path.", st["body"]),
                              Spacer(1, 35),
                              Paragraph("44 chapters  /  22 vector figures  /  4 appendices", st["h2"]),
                              Paragraph("Study edition - 3 October 2026", st["body"]),
                              PageBreak(), Paragraph("Contents", st["title"])])
                toc = TableOfContents()
                toc.levelStyles = [st["toc"]]
                story.extend([toc, PageBreak()])
                first_section = False
            else:
                story.append(PageBreak())
                if pending_part:
                    story.append(Paragraph(inline(pending_part), st["part"]))
                    pending_part = None
                heading = Paragraph(inline(title), st["h1"])
                heading.toc_title = title
                story.extend([heading, HRFlowable(width="100%", thickness=.8, color=colors.HexColor("#C7DDE7")), Spacer(1, 12)])
            i += 1
            continue
        if line.startswith("## "):
            title = line[3:]
            if title.startswith("Part "):
                pending_part = title
            elif title.startswith("Appendix "):
                story.append(PageBreak())
                heading = Paragraph(inline(title), st["h1"])
                heading.toc_title = title
                story.extend([heading, HRFlowable(width="100%", thickness=.8, color=colors.HexColor("#C7DDE7")), Spacer(1, 12)])
            else:
                story.append(Paragraph(inline(title), st["h2"]))
            i += 1
            continue
        if line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), st["h3"]))
            i += 1
            continue
        if line.startswith("**Figure "):
            story.append(Paragraph(inline(line), st["figure"]))
            i += 1
            continue
        if re.match(r"^(?:\d+\.|-)\s+", line):
            item = re.sub(r"^(\d+\.|-)\s+", r"\1 ", line)
            story.append(Paragraph(inline(item), st["list"]))
            i += 1
            continue
        paragraph = [line]
        i += 1
        while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "|", "```")):
            if re.match(r"^(?:\d+\.|-)\s+", lines[i]):
                break
            paragraph.append(lines[i].strip())
            i += 1
        joined = " ".join(paragraph)
        if joined.startswith(("**Remember this:", "**You should now understand", "**What can go wrong?", "**Why we need this:")):
            story.extend([make_callout(joined, available, st), Spacer(1, 10)])
        else:
            story.append(Paragraph(inline(joined), st["body"]))
    return story


def main():
    register_fonts()
    st = styles()
    width = letter[0] - 104
    doc = GuideDoc(
        str(OUTPUT), pagesize=letter, leftMargin=52, rightMargin=52,
        topMargin=57, bottomMargin=55, title="ML Experiment Detective: Complete Learning Guide",
        author="ML Experiment Detective project", subject="Beginner learning guide to the working local experiment agent",
    )
    story = parse_story(SOURCE.read_text(encoding="utf-8"), st, width)
    doc.multiBuild(story, onFirstPage=page_frame, onLaterPages=page_frame, maxPasses=5)
    print(OUTPUT)


if __name__ == "__main__":
    main()
