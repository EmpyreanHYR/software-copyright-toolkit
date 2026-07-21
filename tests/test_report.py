"""测试报告生成。"""

from pathlib import Path

from software_copyright_toolkit.counter import FileStats, SkippedFile
from software_copyright_toolkit.report import make_report


class TestMakeReport:
    def test_basic_report(self):
        target = Path("/tmp/myproject")
        stats = [
            FileStats(path=Path("/tmp/myproject/main.py"), total=10, effective=7, blank=2, comment=1),
        ]
        skipped: list[SkippedFile] = []
        report = make_report(target, stats, skipped)

        assert "myproject 代码行数统计" in report
        assert "main.py" in report
        assert "已统计文件数: `1`" in report
        assert "全部文件有效代码总行数: `7`" in report

    def test_empty_stats(self):
        target = Path("/tmp/empty")
        report = make_report(target, [], [])
        assert "没有发现已适配的代码文件" in report
        assert "无。" in report  # 无未统计文件

    def test_with_skipped(self):
        target = Path("/tmp/proj")
        stats = [
            FileStats(path=Path("/tmp/proj/main.py"), total=10, effective=8, blank=1, comment=1),
        ]
        skipped = [
            SkippedFile(path=Path("/tmp/proj/data.bin"), reason="读取失败或非文本文件: 文件看起来是二进制文件"),
        ]
        report = make_report(target, stats, skipped)

        assert "未统计文件" in report
        assert "data.bin" in report
        assert "读取失败或非文本文件" in report

    def test_multiple_files_sorted(self):
        target = Path("/tmp/proj")
        stats = [
            FileStats(path=Path("/tmp/proj/z.py"), total=5, effective=5, blank=0, comment=0),
            FileStats(path=Path("/tmp/proj/a.py"), total=10, effective=8, blank=1, comment=1),
        ]
        report = make_report(target, stats, [])
        # 应该按路径排序：a.py 在 z.py 前面
        a_pos = report.index("a.py")
        z_pos = report.index("z.py")
        assert a_pos < z_pos

    def test_summary_values(self):
        target = Path("/tmp/proj")
        stats = [
            FileStats(path=Path("/tmp/proj/a.py"), total=10, effective=8, blank=1, comment=1),
            FileStats(path=Path("/tmp/proj/b.py"), total=20, effective=15, blank=3, comment=2),
        ]
        report = make_report(target, stats, [])
        assert "全部文件总行数: `30`" in report
        assert "全部文件有效代码总行数: `23`" in report
        assert "全部文件空行数: `4`" in report
        assert "全部文件注释行数: `3`" in report

    def test_windows_path_normalization(self):
        target = Path("C:/proj")
        stats = [
            FileStats(path=Path("C:/proj/sub/main.py"), total=5, effective=5, blank=0, comment=0),
        ]
        report = make_report(target, stats, [])
        # 相对路径应使用 / 而非 \
        assert "sub/main.py" in report
