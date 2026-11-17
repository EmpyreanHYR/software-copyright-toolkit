from __future__ import annotations

import os
import random
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from docx import Document
from docx.document import Document as DocumentType
from docx.enum.section import WD_SECTION
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.section import Section
from docx.shared import Cm, Pt
from docx.text.paragraph import Paragraph
from docx.text.run import Run
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

from software_copyright_toolkit.counter import SkippedFile, count_supported_file
from software_copyright_toolkit.scanner import iter_files, read_text_lossless

LINES_PER_PAGE = 50
FRONT_BACK_PAGES = 30
FRONT_BACK_LINES = LINES_PER_PAGE * FRONT_BACK_PAGES
IDENTIFICATION_TOTAL_LINES = FRONT_BACK_LINES * 2
MAX_WORD_LINE_WIDTH = 80
MODULE_END_PATTERNS = (
    re.compile(r"^\s*[}\])]+[;,\])}]*\s*$"),
    re.compile(r"^\s*};?\s*$"),
    re.compile(r"^\s*end\s*[;,%#]*\s*$", re.IGNORECASE),
    re.compile(r"^\s*end(?:function|class|methods|properties|for|if|while|switch)\b.*$", re.IGNORECASE),
)

_REGISTERED_PDF_FONT: str | None = None


def get_registered_cjk_font() -> str:
    """查找并注册适用于 PDF 的中文字体，返回注册的字体名称。"""
    global _REGISTERED_PDF_FONT
    if _REGISTERED_PDF_FONT is not None:
        return _REGISTERED_PDF_FONT

    candidates: list[tuple[str, list[str]]] = [
        (
            "SimSun",
            [
                "C:/Windows/Fonts/simsun.ttc",
                "C:/Windows/Fonts/simsun.ttf",
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            ],
        ),
        (
            "STSong",
            [
                "/System/Library/Fonts/PingFang.ttc",
                "/Library/Fonts/Songti.ttc",
                "/System/Library/Fonts/STHeiti Light.ttc",
                "/Library/Fonts/Arial Unicode.ttf",
            ],
        ),
        (
            "NotoSansCJK",
            [
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
                "/usr/share/fonts/google-noto-cjk/NotoSansCJK-Regular.ttc",
            ],
        ),
    ]

    for font_name, paths in candidates:
        for font_path in paths:
            if os.path.exists(font_path):
                try:
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    _REGISTERED_PDF_FONT = font_name
                    return font_name
                except Exception:
                    continue

    _REGISTERED_PDF_FONT = "Helvetica"
    return _REGISTERED_PDF_FONT


@dataclass(frozen=True)
class GeneratedDocuments:
    identification_docx: Path | None
    full_docx: Path | None
    source_line_count: int
    source_content_line_count: int
    identification_line_count: int
    identification_content_line_count: int
    identification_pdf: Path | None = None
    full_pdf: Path | None = None


def sanitize_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", value).strip()
    cleaned = re.sub(r"\s+", "_", cleaned)
    return cleaned or "未命名软件"


@dataclass(frozen=True)
class SourceLine:
    text: str
    counts_as_source: bool
    is_source_text: bool


DEFAULT_SEPARATOR = "===== 文件: {path} ====="


def collect_source_lines(
    target: Path,
    separator_template: str = DEFAULT_SEPARATOR,
    include_paths: frozenset[Path] | set[Path] | None = None,
    seed: int | None = None,
) -> tuple[list[SourceLine], list[SkippedFile]]:
    """扫描并收集所有已适配文件的源代码行。

    Args:
        target: 目标文件夹。
        separator_template: 文件分隔行模板。
        include_paths: 可选的文件白名单集合。
        seed: 可选的随机种子。指定后会在内存中以此种子打乱文件拼接顺序，
              但绝对不修改磁盘上的源文件本身，保证原始项目功能完全正常。
    """
    lines: list[SourceLine] = []
    skipped: list[SkippedFile] = []

    files = sorted(iter_files(target), key=lambda item: str(item.relative_to(target)).lower())
    if seed is not None:
        files = list(files)
        random.Random(seed).shuffle(files)

    for path in files:
        if include_paths is not None and path.resolve() not in include_paths:
            continue
        try:
            text = read_text_lossless(path)
        except (OSError, UnicodeError) as exc:
            skipped.append(SkippedFile(path, f"读取失败或非文本文件: {exc}"))
            continue

        if count_supported_file(path, text) is None:
            skipped.append(SkippedFile(path, f"未适配的文件后缀: {path.suffix.lower() or '(无后缀)'}"))
            continue

        rel = str(path.relative_to(target)).replace("\\", "/")
        lines.append(SourceLine(separator_template.format(path=rel), counts_as_source=False, is_source_text=False))
        lines.extend(
            SourceLine(line.expandtabs(4), counts_as_source=True, is_source_text=True)
            for line in text.splitlines()
            if line.strip()
        )

    return lines, skipped


def generate_identification_documents(
    target: Path,
    output_dir: Path,
    software_name: str,
    version: str,
    include_identification: bool = True,
    include_full: bool = True,
    separator_template: str = DEFAULT_SEPARATOR,
    include_paths: frozenset[Path] | set[Path] | None = None,
    generate_docx: bool = True,
    generate_pdf: bool = True,
    seed: int | None = None,
    front_back_pages: int = FRONT_BACK_PAGES,
) -> GeneratedDocuments:
    """生成软著程序鉴别材料及全量代码文档（支持 Word 和 PDF 格式）。"""
    source_lines, _ = collect_source_lines(
        target,
        separator_template=separator_template,
        include_paths=include_paths,
        seed=seed,
    )
    if not source_lines:
        raise ValueError("没有可用于生成程序鉴别材料的已适配代码文件。")
    if not include_identification and not include_full:
        raise ValueError("请至少选择一种材料内容（鉴别材料或全量代码）。")
    if not generate_docx and not generate_pdf:
        raise ValueError("请至少选择一种导出格式（Word 或 PDF）。")

    name_part = sanitize_filename(software_name)
    version_part = sanitize_filename(version)
    prefix = f"{name_part}_{version_part}_程序鉴别材料"
    page_tag = f"前后{front_back_pages}页"

    identification_docx = output_dir / f"{prefix}_{page_tag}.docx" if (include_identification and generate_docx) else None
    full_docx = output_dir / f"{prefix}_全量代码.docx" if (include_full and generate_docx) else None
    identification_pdf = output_dir / f"{prefix}_{page_tag}.pdf" if (include_identification and generate_pdf) else None
    full_pdf = output_dir / f"{prefix}_全量代码.pdf" if (include_full and generate_pdf) else None

    source_content_line_count = count_source_content_lines(source_lines)
    display_lines = wrap_source_lines(source_lines)
    identification_lines = select_identification_lines(
        display_lines,
        source_content_line_count,
        front_back_pages=front_back_pages,
    )
    identification_content_line_count = count_source_content_lines(identification_lines)

    target_total_lines = front_back_pages * LINES_PER_PAGE * 2
    break_interval = LINES_PER_PAGE if len(identification_lines) >= target_total_lines else None

    # 生成 Word 文档
    if identification_docx is not None:
        write_code_docx(
            identification_docx,
            identification_lines,
            software_name=software_name,
            version=version,
            page_break_interval=break_interval,
        )
    if full_docx is not None:
        write_code_docx(
            full_docx,
            display_lines,
            software_name=software_name,
            version=version,
        )

    # 生成 PDF 文档
    if identification_pdf is not None:
        write_code_pdf(
            identification_pdf,
            identification_lines,
            software_name=software_name,
            version=version,
            page_break_interval=LINES_PER_PAGE,
        )
    if full_pdf is not None:
        write_code_pdf(
            full_pdf,
            display_lines,
            software_name=software_name,
            version=version,
            page_break_interval=LINES_PER_PAGE,
        )

    return GeneratedDocuments(
        identification_docx=identification_docx,
        full_docx=full_docx,
        source_line_count=len(display_lines),
        source_content_line_count=source_content_line_count,
        identification_line_count=len(identification_lines),
        identification_content_line_count=identification_content_line_count,
        identification_pdf=identification_pdf,
        full_pdf=full_pdf,
    )


def wrap_source_lines(lines: list[SourceLine]) -> list[SourceLine]:
    wrapped: list[SourceLine] = []
    for line in lines:
        if display_width(line.text) <= MAX_WORD_LINE_WIDTH:
            wrapped.append(line)
            continue

        parts = split_long_line(line.text, MAX_WORD_LINE_WIDTH)
        for index, part in enumerate(parts):
            wrapped.append(
                SourceLine(
                    part,
                    counts_as_source=line.counts_as_source and index == 0,
                    is_source_text=line.is_source_text,
                )
            )
    return wrapped


def split_long_line(line: str, width: int) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    current_width = 0

    for char in line:
        char_width = display_width(char)
        if current and current_width + char_width > width:
            parts.append("".join(current))
            current = []
            current_width = 0
        current.append(char)
        current_width += char_width

    if current:
        parts.append("".join(current))
    return parts or [line]


def display_width(text: str) -> int:
    width = 0
    for char in text:
        width += 2 if unicodedata.east_asian_width(char) in {"F", "W"} else 1
    return width


def select_identification_lines(
    lines: list[SourceLine],
    source_content_line_count: int,
    front_back_pages: int = FRONT_BACK_PAGES,
) -> list[SourceLine]:
    """根据软著规范截取鉴别材料代码行（前 N 页 + 后 N 页）。"""
    front_back_lines = front_back_pages * LINES_PER_PAGE
    total_lines = front_back_lines * 2

    if source_content_line_count < total_lines and len(lines) < total_lines:
        return lines

    if len(lines) < total_lines:
        return lines

    first_part_end = front_back_lines
    end_index = find_module_end_index(lines, minimum_index=total_lines)
    if end_index is None:
        end_index = find_graceful_end_index(lines, minimum_index=total_lines)

    back_start = end_index - front_back_lines
    if back_start < first_part_end:
        return lines[:total_lines]

    selected = lines[:first_part_end] + lines[back_start:end_index]
    return selected


def count_source_content_lines(lines: list[SourceLine]) -> int:
    return sum(1 for line in lines if line.counts_as_source)


def find_module_end_index(lines: list[SourceLine], minimum_index: int) -> int | None:
    for index in range(len(lines), minimum_index - 1, -1):
        line = lines[index - 1]
        if line.is_source_text and is_module_end_line(line.text):
            return index
    return None


def find_graceful_end_index(lines: list[SourceLine], minimum_index: int) -> int:
    """当未找到标准的大括号/end等结束符时（例如纯 Python 项目），寻找优雅的模块截断点。

    优先从末尾向前寻找顶格非空非注释代码行，或直接以最后一行结束，确保绝不会回退为全量代码。
    """
    for index in range(len(lines), minimum_index - 1, -1):
        line = lines[index - 1]
        if line.is_source_text and line.text.strip():
            # 顶格语句通常是一个模块或顶层函数/调用的结束边界
            if not line.text.startswith(" ") and not line.text.startswith("\t"):
                return index
    return len(lines)


def is_module_end_line(line: str) -> bool:
    return any(pattern.match(line) for pattern in MODULE_END_PATTERNS)


def is_valid_identification_selection(lines: list[SourceLine], expected_lines: int = IDENTIFICATION_TOTAL_LINES) -> bool:
    return len(lines) == expected_lines and lines[-1].is_source_text and is_module_end_line(lines[-1].text)


DISCLAIMER_NOTE = (
    "【提示】页数基于标准 A4 纸张（21 cm × 29.7 cm）及默认页边距（上下各 2 cm，左右各 2 cm）估算。"
    "生成的 Word 文档建议在 Word 中通过「审阅 → 字数统计 → 行数」进行最终复核，PDF 文档已按每页50行严格对齐。"
)


def write_code_docx(
    path: Path,
    lines: list[SourceLine],
    software_name: str,
    version: str,
    page_break_interval: int | None = None,
) -> None:
    doc = Document()
    setup_document(doc, software_name, version)

    for index, line in enumerate(lines, start=1):
        paragraph = doc.add_paragraph()
        paragraph.paragraph_format.space_before = Pt(0)
        paragraph.paragraph_format.space_after = Pt(0)
        paragraph.paragraph_format.line_spacing = Pt(14)
        run = paragraph.add_run(line.text if line.text else " ")
        apply_run_font(run)
        if page_break_interval and index % page_break_interval == 0 and index < len(lines):
            run.add_break(WD_BREAK.PAGE)

    path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(str(path))


def write_code_pdf(
    path: Path,
    lines: list[SourceLine],
    software_name: str,
    version: str,
    page_break_interval: int | None = LINES_PER_PAGE,
) -> None:
    """以精确符合软著申请规范的排版格式生成 PDF 文件。

    - 标准 A4 尺寸，上下左右各 20mm 边距。
    - 每页精确 50 行代码。
    - 包含标准页眉（软件名称+版本号、当前页码）与居中页脚（第 X 页 / 共 Y 页）。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    font_name = get_registered_cjk_font()

    c = canvas.Canvas(str(path), pagesize=A4)
    page_width, page_height = A4
    margin_left = 20 * mm
    margin_top = 20 * mm
    margin_bottom = 20 * mm
    content_width = page_width - 2 * margin_left
    content_height = page_height - margin_top - margin_bottom

    interval = page_break_interval or LINES_PER_PAGE
    total_pages = max(1, (len(lines) + interval - 1) // interval)

    for page_idx in range(total_pages):
        page_num = page_idx + 1

        # 页眉
        c.setFont(font_name, 9)
        c.drawString(margin_left, page_height - 12 * mm, f"{software_name} {version}")
        c.drawRightString(page_width - margin_left, page_height - 12 * mm, f"第 {page_num} 页")

        # 页眉底部分隔线
        c.setStrokeColorRGB(0.75, 0.75, 0.75)
        c.setLineWidth(0.5)
        c.line(margin_left, page_height - 15 * mm, page_width - margin_left, page_height - 15 * mm)

        # 50 行代码
        start_line = page_idx * interval
        end_line = min(start_line + interval, len(lines))
        page_lines = lines[start_line:end_line]

        line_height = content_height / LINES_PER_PAGE
        c.setFont(font_name, 9)

        for line_idx, line in enumerate(page_lines):
            y = page_height - margin_top - (line_idx + 0.8) * line_height
            text = line.text if line.text else " "
            c.drawString(margin_left, y, text)

        # 页脚
        c.setFont(font_name, 9)
        c.drawCentredString(page_width / 2.0, 10 * mm, f"第 {page_num} 页 / 共 {total_pages} 页")

        c.showPage()

    c.save()


def setup_document(doc: DocumentType, software_name: str, version: str) -> None:
    enable_field_updates(doc)

    normal = doc.styles["Normal"]
    normal.font.name = "Arial"
    normal.font.size = Pt(10)
    normal._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")

    section = doc.sections[0]
    section.start_type = WD_SECTION.NEW_PAGE
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)
    section.header_distance = Cm(1.2)
    section.footer_distance = Cm(1.2)

    setup_header(section, software_name, version)
    setup_footer(section)


def enable_field_updates(doc: DocumentType) -> None:
    settings = doc.settings._element
    update_fields = settings.find(qn("w:updateFields"))
    if update_fields is None:
        update_fields = OxmlElement("w:updateFields")
        settings.append(update_fields)
    update_fields.set(qn("w:val"), "true")


def setup_header(section: Section, software_name: str, version: str) -> None:
    header = section.header
    paragraph = header.paragraphs[0]
    clear_paragraph(paragraph)
    paragraph.paragraph_format.tab_stops.add_tab_stop(Cm(17), WD_TAB_ALIGNMENT.RIGHT)
    paragraph.paragraph_format.space_after = Pt(0)

    left_run = paragraph.add_run(f"{software_name} {version}")
    apply_run_font(left_run)
    tab_run = paragraph.add_run("\t")
    apply_run_font(tab_run)
    add_field(paragraph, "PAGE")


def setup_footer(section: Section) -> None:
    footer = section.footer
    paragraph = footer.paragraphs[0]
    clear_paragraph(paragraph)
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.paragraph_format.space_after = Pt(0)
    add_field(paragraph, "PAGE")
    slash_run = paragraph.add_run(" / ")
    apply_run_font(slash_run)
    add_field(paragraph, "NUMPAGES")


def clear_paragraph(paragraph: Paragraph) -> None:
    for child in list(paragraph._p):
        paragraph._p.remove(child)


def apply_run_font(run: Run) -> None:
    run.font.name = "Arial"
    run.font.size = Pt(10)
    if run._element.rPr is not None and run._element.rPr.rFonts is not None:
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "Arial")


def add_field(paragraph: Paragraph, instruction: str) -> None:
    run = paragraph.add_run()
    apply_run_font(run)

    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")

    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = f" {instruction} "

    separate = OxmlElement("w:fldChar")
    separate.set(qn("w:fldCharType"), "separate")

    text = OxmlElement("w:t")
    text.text = "1"

    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")

    run._r.append(begin)
    run._r.append(instr)
    run._r.append(separate)
    run._r.append(text)
    run._r.append(end)
