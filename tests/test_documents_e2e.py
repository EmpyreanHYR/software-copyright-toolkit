"""测试 Word 程序鉴别材料生成的端到端逻辑。"""

from __future__ import annotations

import pytest
from docx import Document

from software_copyright_toolkit.documents import (
    GeneratedDocuments,
    SourceLine,
    collect_source_lines,
    generate_identification_documents,
    write_code_docx,
)


class TestWriteCodeDocx:
    """端到端测试：生成 .docx 文件并验证内容。"""

    def test_basic_generation(self, tmp_path):
        """生成基本的 Word 文档并验证文件存在。"""
        lines = [SourceLine(f"line {i}", counts_as_source=True, is_source_text=True) for i in range(10)]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0")
        assert out.exists()
        assert out.stat().st_size > 0

    def test_docx_content_lines(self, tmp_path):
        """验证生成的 Word 文档包含正确的行数。"""
        lines = [
            SourceLine("line 1", counts_as_source=True, is_source_text=True),
            SourceLine("line 2", counts_as_source=True, is_source_text=True),
            SourceLine("line 3", counts_as_source=True, is_source_text=True),
        ]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0")

        doc = Document(str(out))
        # 文档中的段落数应等于代码行数（不包括页眉页脚）
        text_paragraphs = [p for p in doc.paragraphs if p.text.strip()]
        assert len(text_paragraphs) == 3

    def test_docx_font_settings(self, tmp_path):
        """验证字体设置为 Arial 10pt。"""
        lines = [SourceLine("hello", counts_as_source=True, is_source_text=True)]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0")

        doc = Document(str(out))
        normal_style = doc.styles["Normal"]
        assert normal_style.font.name == "Arial"
        assert normal_style.font.size.pt == 10

    def test_docx_page_settings(self, tmp_path):
        """验证页面设置为 A4 纸张。"""
        lines = [SourceLine("hello", counts_as_source=True, is_source_text=True)]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0")

        doc = Document(str(out))
        section = doc.sections[0]
        # A4: 21cm x 29.7cm
        assert abs(section.page_width.cm - 21) < 0.1
        assert abs(section.page_height.cm - 29.7) < 0.1
        # 页边距 2cm
        assert abs(section.top_margin.cm - 2) < 0.1
        assert abs(section.bottom_margin.cm - 2) < 0.1
        assert abs(section.left_margin.cm - 2) < 0.1
        assert abs(section.right_margin.cm - 2) < 0.1

    def test_docx_header_contains_software_name(self, tmp_path):
        """验证页眉包含软件名称。"""
        lines = [SourceLine("hello", counts_as_source=True, is_source_text=True)]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="MyApp", version="V2.0")

        doc = Document(str(out))
        header_text = doc.sections[0].header.paragraphs[0].text
        assert "MyApp" in header_text
        assert "V2.0" in header_text

    def test_docx_footer_exists(self, tmp_path):
        """验证页脚存在。"""
        lines = [SourceLine("hello", counts_as_source=True, is_source_text=True)]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0")

        doc = Document(str(out))
        footer = doc.sections[0].footer
        # 页脚应该有段落
        assert len(footer.paragraphs) > 0

    def test_docx_with_page_breaks(self, tmp_path):
        """验证分页符功能。"""
        lines = [SourceLine(f"line {i}", counts_as_source=True, is_source_text=True) for i in range(100)]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0", page_break_interval=50)

        assert out.exists()
        doc = Document(str(out))
        # 100 行代码 + 分页后的段落
        assert len(doc.paragraphs) >= 100

    def test_docx_without_page_breaks(self, tmp_path):
        """不使用分页符时文档仍正常生成。"""
        lines = [SourceLine(f"line {i}", counts_as_source=True, is_source_text=True) for i in range(10)]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0")

        doc = Document(str(out))
        assert len(doc.paragraphs) == 10

    def test_docx_empty_line_handled(self, tmp_path):
        """空行应被替换为空格以保持段落。"""
        lines = [
            SourceLine("code", counts_as_source=True, is_source_text=True),
            SourceLine("", counts_as_source=True, is_source_text=True),
            SourceLine("more code", counts_as_source=True, is_source_text=True),
        ]
        out = tmp_path / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0")

        doc = Document(str(out))
        # 空行应被替换为空格
        assert len(doc.paragraphs) == 3

    def test_docx_creates_parent_dirs(self, tmp_path):
        """应自动创建父目录。"""
        lines = [SourceLine("hello", counts_as_source=True, is_source_text=True)]
        out = tmp_path / "deep" / "nested" / "test.docx"
        write_code_docx(out, lines, software_name="TestApp", version="V1.0")
        assert out.exists()


class TestCollectSourceLines:
    """测试源代码行收集。"""

    def test_basic(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1\ny = 2\n\n", encoding="utf-8")
        lines, skipped = collect_source_lines(tmp_path)
        # 应包含分隔行 + 代码行（空行被过滤）
        assert len(lines) >= 2
        assert len(skipped) == 0

    def test_skips_unsupported(self, tmp_path):
        (tmp_path / "data.xyz").write_text("content", encoding="utf-8")
        lines, skipped = collect_source_lines(tmp_path)
        assert len(lines) == 0
        assert len(skipped) == 1

    def test_separator_format(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1", encoding="utf-8")
        lines, _ = collect_source_lines(tmp_path)
        # 第一行应该是分隔行
        assert lines[0].counts_as_source is False
        assert lines[0].is_source_text is False
        assert "main.py" in lines[0].text

    def test_custom_separator(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1", encoding="utf-8")
        lines, _ = collect_source_lines(tmp_path, separator_template="// --- {path} ---")
        assert "// ---" in lines[0].text


class TestGenerateIdentificationDocuments:
    """测试完整的鉴别材料生成流程。"""

    def test_generates_both_docs(self, tmp_path):
        """生成前后30页和全量代码两个文档。"""
        # 创建足够的代码文件
        for i in range(5):
            (tmp_path / f"mod{i}.py").write_text(
                "\n".join(f"    x_{i}_{j} = {j}" for j in range(100)),
                encoding="utf-8",
            )
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        result = generate_identification_documents(
            tmp_path,
            out_dir,
            software_name="TestApp",
            version="V1.0",
        )
        assert isinstance(result, GeneratedDocuments)
        assert result.identification_docx is not None
        assert result.full_docx is not None
        assert result.identification_docx.exists()
        assert result.full_docx.exists()

    def test_generates_only_identification(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1\n" * 10, encoding="utf-8")
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        result = generate_identification_documents(
            tmp_path,
            out_dir,
            software_name="TestApp",
            version="V1.0",
            include_identification=True,
            include_full=False,
        )
        assert result.identification_docx is not None
        assert result.full_docx is None

    def test_generates_only_full(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1\n" * 10, encoding="utf-8")
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        result = generate_identification_documents(
            tmp_path,
            out_dir,
            software_name="TestApp",
            version="V1.0",
            include_identification=False,
            include_full=True,
        )
        assert result.identification_docx is None
        assert result.full_docx is not None

    def test_no_source_files_raises(self, tmp_path):
        """没有源代码文件时应抛出 ValueError。"""
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        with pytest.raises(ValueError, match="没有可用"):
            generate_identification_documents(
                tmp_path,
                out_dir,
                software_name="TestApp",
                version="V1.0",
            )

    def test_no_selection_raises(self, tmp_path):
        (tmp_path / "main.py").write_text("x = 1", encoding="utf-8")
        out_dir = tmp_path / "output"
        out_dir.mkdir()
        with pytest.raises(ValueError, match="至少选择"):
            generate_identification_documents(
                tmp_path,
                out_dir,
                software_name="TestApp",
                version="V1.0",
                include_identification=False,
                include_full=False,
            )

    def test_filename_sanitization(self, tmp_path):
        """文件名中的特殊字符应被清理。"""
        (tmp_path / "main.py").write_text("x = 1", encoding="utf-8")
        out_dir = tmp_path / "output"
        out_dir.mkdir()

        result = generate_identification_documents(
            tmp_path,
            out_dir,
            software_name="My<App>V2",
            version="V1.0",
            include_identification=False,
            include_full=True,
        )
        assert result.full_docx is not None
        # 文件名不应包含 < >
        assert "<" not in result.full_docx.name
        assert ">" not in result.full_docx.name
