"""测试文件路径过滤逻辑。"""

from __future__ import annotations

from software_copyright_toolkit.counter import count_folder
from software_copyright_toolkit.documents import collect_source_lines


class TestCountFolderIncludePaths:
    """测试 count_folder 的 include_paths 过滤。"""

    def test_no_filter_returns_all(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("y = 2\n", encoding="utf-8")
        stats, _ = count_folder(tmp_path)
        assert len(stats) == 2

    def test_filter_returns_subset(self, tmp_path):
        a = (tmp_path / "a.py").resolve()
        b = (tmp_path / "b.py").resolve()
        a.write_text("x = 1\n", encoding="utf-8")
        b.write_text("y = 2\n", encoding="utf-8")
        stats, _ = count_folder(tmp_path, include_paths={a})
        assert len(stats) == 1
        assert stats[0].path.resolve() == a

    def test_filter_empty_set_returns_nothing(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
        stats, _ = count_folder(tmp_path, include_paths=set())
        assert len(stats) == 0

    def test_filter_nonexistent_path_skips(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
        fake = tmp_path / "nonexistent.py"
        stats, _ = count_folder(tmp_path, include_paths={fake.resolve()})
        assert len(stats) == 0

    def test_filter_with_subdirectories(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        a = (tmp_path / "a.py").resolve()
        b = (sub / "b.py").resolve()
        a.write_text("x = 1\n", encoding="utf-8")
        b.write_text("y = 2\n", encoding="utf-8")
        stats, _ = count_folder(tmp_path, include_paths={b})
        assert len(stats) == 1
        assert stats[0].path.resolve() == b


class TestCollectSourceLinesIncludePaths:
    """测试 collect_source_lines 的 include_paths 过滤。"""

    def test_no_filter_returns_all(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1\n", encoding="utf-8")
        (tmp_path / "b.py").write_text("y = 2\n", encoding="utf-8")
        lines, skipped = collect_source_lines(tmp_path)
        # 每个文件有 1 行分隔 + 1 行代码 = 2 行，共 4 行
        assert len(lines) == 4

    def test_filter_returns_subset(self, tmp_path):
        a = (tmp_path / "a.py").resolve()
        b = (tmp_path / "b.py").resolve()
        a.write_text("x = 1\n", encoding="utf-8")
        b.write_text("y = 2\n", encoding="utf-8")
        lines, _ = collect_source_lines(tmp_path, include_paths={a})
        # 只有 a.py: 1 行分隔 + 1 行代码
        assert len(lines) == 2
        assert "a.py" in lines[0].text
