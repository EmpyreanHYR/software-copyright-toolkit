"""测试 PDF 导出、随机种子打乱与多页码截取功能。"""

from __future__ import annotations

from pathlib import Path

from software_copyright_toolkit.controller import TaskConfig, run_generation, validate_task_config
from software_copyright_toolkit.documents import (
    FRONT_BACK_PAGES,
    SourceLine,
    collect_source_lines,
    generate_identification_documents,
    select_identification_lines,
    write_code_pdf,
)


class TestCollectSourceLinesSeed:
    """测试通过随机种子打乱文件拼接顺序，并确保源文件未受修改。"""

    def test_seed_determinism_and_non_destructive(self, tmp_path: Path):
        # 创建 6 个测试源码文件
        file_contents = {}
        for char in ["a", "b", "c", "d", "e", "f"]:
            p = tmp_path / f"mod_{char}.py"
            content = f"# module {char}\nx_{char} = 1\n"
            p.write_text(content, encoding="utf-8")
            file_contents[p] = content

        # 默认不打乱：按文件名字母序排列
        default_lines, _ = collect_source_lines(tmp_path)
        default_separators = [line.text for line in default_lines if not line.counts_as_source]
        assert "mod_a.py" in default_separators[0]
        assert "mod_b.py" in default_separators[1]

        # 给定 seed=42 打乱
        lines_seed1, _ = collect_source_lines(tmp_path, seed=42)
        seps_seed1 = [line.text for line in lines_seed1 if not line.counts_as_source]

        # 再次使用相同的 seed=42
        lines_seed2, _ = collect_source_lines(tmp_path, seed=42)
        seps_seed2 = [line.text for line in lines_seed2 if not line.counts_as_source]

        # 相同种子结果严格一致
        assert seps_seed1 == seps_seed2

        # 换用不同的 seed=999
        lines_seed3, _ = collect_source_lines(tmp_path, seed=999)
        seps_seed3 = [line.text for line in lines_seed3 if not line.counts_as_source]

        # 验证不同种子产生不同的拼接顺序
        assert seps_seed1 != seps_seed3

        # 极其重要：验证磁盘上的所有源文件未被改动
        for p, original in file_contents.items():
            assert p.read_text(encoding="utf-8") == original


class TestWriteCodePdf:
    """测试 PDF 排版与生成。"""

    def test_pdf_generation_basic(self, tmp_path: Path):
        lines = [
            SourceLine(f"print('Hello world {i}')", counts_as_source=True, is_source_text=True) for i in range(120)
        ]
        pdf_path = tmp_path / "output.pdf"

        write_code_pdf(pdf_path, lines, software_name="测试系统", version="V1.0.0")

        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 1000

    def test_pdf_with_cjk_content(self, tmp_path: Path):
        lines = [
            SourceLine("# 中文注释与函数声明", counts_as_source=True, is_source_text=True),
            SourceLine("def 业务处理流程():", counts_as_source=True, is_source_text=True),
            SourceLine("    return '版权保护中心标准规范'", counts_as_source=True, is_source_text=True),
        ]
        pdf_path = tmp_path / "cjk_test.pdf"

        write_code_pdf(pdf_path, lines, software_name="中文软件软著", version="V2.0")

        assert pdf_path.exists()
        assert pdf_path.stat().st_size > 500


class TestGenerateIdentificationDocumentsPdf:
    """测试 generate_identification_documents 的 PDF 导出与页数扩展。"""

    def test_generates_pdf_and_docx(self, tmp_path: Path):
        code_dir = tmp_path / "src"
        code_dir.mkdir()
        (code_dir / "main.py").write_text("x = 1\ny = 2\n", encoding="utf-8")

        out_dir = tmp_path / "out"
        out_dir.mkdir()

        res = generate_identification_documents(
            target=code_dir,
            output_dir=out_dir,
            software_name="TestApp",
            version="V1.0",
            generate_docx=True,
            generate_pdf=True,
        )

        assert res.identification_docx is not None and res.identification_docx.exists()
        assert res.full_docx is not None and res.full_docx.exists()
        assert res.identification_pdf is not None and res.identification_pdf.exists()
        assert res.full_pdf is not None and res.full_pdf.exists()

    def test_custom_pages_and_name_tag(self, tmp_path: Path):
        code_dir = tmp_path / "src"
        code_dir.mkdir()
        (code_dir / "main.py").write_text("x = 1\n", encoding="utf-8")

        out_dir = tmp_path / "out"
        out_dir.mkdir()

        # 指定单段 60 页（前后各 60 页）
        res = generate_identification_documents(
            target=code_dir,
            output_dir=out_dir,
            software_name="CustomApp",
            version="V1.0",
            generate_docx=True,
            generate_pdf=True,
            front_back_pages=60,
        )

        assert "前后60页" in str(res.identification_docx)
        assert "前后60页" in str(res.identification_pdf)


class TestSelectIdentificationLinesPythonFallback:
    """测试 Python 等无大括号语言超大源文件截取前后各 N 页。"""

    def test_python_without_braces_truncates_safely(self):
        # 构造 4000 行纯 Python 代码（无大括号）
        lines = [
            SourceLine(f"    var_{i} = calculate_value({i})", counts_as_source=True, is_source_text=True)
            for i in range(4000)
        ]
        # 默认前后各30页 = 3000行
        selected = select_identification_lines(lines, source_content_line_count=4000, front_back_pages=30)

        # 修复前因找不到大括号会直接返回 4000 行；修复后应严格截取为 3000 行
        assert len(selected) == 3000
        # 前 1500 行
        assert selected[0].text == lines[0].text
        assert selected[1499].text == lines[1499].text
        # 后 1500 行来自末尾
        assert selected[-1].text == lines[-1].text


class TestControllerIntegration:
    """测试 Controller 对 PDF、种子和页数配置的集成。"""

    def test_controller_pdf_flow(self, tmp_path: Path):
        code_dir = tmp_path / "proj"
        code_dir.mkdir()
        for i in range(3):
            (code_dir / f"file_{i}.py").write_text(f"def foo_{i}(): pass\n", encoding="utf-8")

        out_dir = tmp_path / "dist"
        cfg = TaskConfig(
            target=code_dir,
            output_dir=out_dir,
            software_name="Toolbox",
            version="V1.0",
            separator="===== 文件: {path} =====",
            generate_report=True,
            generate_identification=True,
            generate_full=True,
            generate_docx=False,
            generate_pdf=True,
            seed=42,
            pages_per_section=FRONT_BACK_PAGES,
        )

        errors = validate_task_config(cfg)
        assert errors == []

        res = run_generation(cfg)
        # 应生成 md 报告 + 2 个 pdf（鉴别材料与全量代码）
        assert len(res.generated_files) == 3
        pdf_files = [f for f in res.generated_files if f.suffix == ".pdf"]
        assert len(pdf_files) == 2
