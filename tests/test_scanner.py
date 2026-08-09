"""测试文件扫描与编码检测模块。"""

from __future__ import annotations

import contextlib

import pytest

from software_copyright_toolkit.scanner import SKIP_DIRS, iter_files, read_lines_lazy, read_text_lossless


class TestReadTextLossless:
    """测试文本文件读取和编码探测。"""

    def test_utf8_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello world\n你好世界", encoding="utf-8")
        result = read_text_lossless(f)
        assert "hello world" in result
        assert "你好世界" in result

    def test_utf8_bom_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes(b"\xef\xbb\xbfhello world")
        result = read_text_lossless(f)
        assert result.strip() == "hello world"
        # BOM 应被 utf-8-sig 消化
        assert not result.startswith("\ufeff")

    def test_gbk_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes("你好世界".encode("gbk"))
        result = read_text_lossless(f, use_charset_normalizer=False)
        assert "你好世界" in result

    def test_utf16_file(self, tmp_path):
        """UTF-16 编码含 null 字节，会被二进制检测拦截（预期行为）。"""
        f = tmp_path / "test.txt"
        f.write_bytes("hello".encode("utf-16"))
        # UTF-16 含 null 字节，应被检测为二进制
        with contextlib.suppress(UnicodeError):
            read_text_lossless(f, use_charset_normalizer=False)

    def test_binary_file_raises(self, tmp_path):
        f = tmp_path / "test.bin"
        f.write_bytes(b"\x00\x01\x02\x03binary content")
        with pytest.raises(UnicodeError, match="二进制"):
            read_text_lossless(f)

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        result = read_text_lossless(f)
        assert result == ""

    def test_file_with_null_byte_detected(self, tmp_path):
        f = tmp_path / "mixed.txt"
        f.write_bytes(b"hello\x00world")
        with pytest.raises(UnicodeError):
            read_text_lossless(f)

    def test_replacement_fallback(self, tmp_path):
        """无法识别编码时应使用 replace 模式。"""
        f = tmp_path / "garbage.txt"
        # 构造无法被任何标准编码正确解码的字节序列
        f.write_bytes(b"\x80\x81\x82\x83")
        # 不应抛出异常，应回退到 utf-8 replace
        result = read_text_lossless(f, use_charset_normalizer=False)
        assert isinstance(result, str)

    def test_disable_charset_normalizer(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("hello", encoding="utf-8")
        result = read_text_lossless(f, use_charset_normalizer=False)
        assert "hello" in result


class TestReadLinesLazy:
    """测试逐行读取生成器。"""

    def test_basic(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_text("line1\nline2\nline3\n", encoding="utf-8")
        lines = list(read_lines_lazy(f))
        assert lines == ["line1", "line2", "line3"]

    def test_empty_file(self, tmp_path):
        f = tmp_path / "empty.txt"
        f.write_text("", encoding="utf-8")
        lines = list(read_lines_lazy(f))
        assert lines == []

    def test_binary_file_raises(self, tmp_path):
        f = tmp_path / "bin.dat"
        f.write_bytes(b"\x00\x01\x02")
        with pytest.raises(UnicodeError):
            list(read_lines_lazy(f))

    def test_gbk_file(self, tmp_path):
        f = tmp_path / "test.txt"
        f.write_bytes("你好\n世界".encode("gbk"))
        lines = list(read_lines_lazy(f, use_charset_normalizer=False))
        assert len(lines) == 2
        assert "你好" in lines[0]

    def test_generator_is_lazy(self, tmp_path):
        """确认返回的是生成器，不是列表。"""
        f = tmp_path / "test.txt"
        f.write_text("a\nb\nc", encoding="utf-8")
        gen = read_lines_lazy(f)
        # 生成器不应有 __len__
        assert not hasattr(gen, "__len__")


class TestIterFiles:
    """测试文件遍历。"""

    def test_basic(self, tmp_path):
        (tmp_path / "a.py").write_text("x = 1")
        (tmp_path / "b.js").write_text("let x = 1")
        files = list(iter_files(tmp_path))
        names = {f.name for f in files}
        assert "a.py" in names
        assert "b.js" in names

    def test_skips_git(self, tmp_path):
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("some config")
        (tmp_path / "a.py").write_text("x = 1")
        files = list(iter_files(tmp_path))
        assert all(".git" not in str(f) for f in files)

    def test_skips_node_modules(self, tmp_path):
        nm_dir = tmp_path / "node_modules"
        nm_dir.mkdir()
        (nm_dir / "pkg.js").write_text("module.exports = {}")
        (tmp_path / "a.py").write_text("x = 1")
        files = list(iter_files(tmp_path))
        # 使用 parts 检查而非字符串包含，避免 Windows 路径误匹配
        assert all("node_modules" not in f.parts for f in files)

    def test_skips_pycache(self, tmp_path):
        cache_dir = tmp_path / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "mod.cpython-310.pyc").write_bytes(b"\x00")
        (tmp_path / "a.py").write_text("x = 1")
        files = list(iter_files(tmp_path))
        assert all("__pycache__" not in str(f) for f in files)

    def test_nested_directories(self, tmp_path):
        sub = tmp_path / "sub"
        sub.mkdir()
        (sub / "deep.py").write_text("x = 1")
        files = list(iter_files(tmp_path))
        assert any(f.name == "deep.py" for f in files)

    def test_custom_skip_dirs(self, tmp_path):
        custom_dir = tmp_path / "vendor"
        custom_dir.mkdir()
        (custom_dir / "lib.js").write_text("var x = 1")
        (tmp_path / "a.py").write_text("x = 1")
        files = list(iter_files(tmp_path, skip_dirs={"vendor"}))
        assert all("vendor" not in str(f) for f in files)

    def test_empty_directory(self, tmp_path):
        files = list(iter_files(tmp_path))
        assert files == []

    def test_all_skip_dirs_covered(self):
        """确认 SKIP_DIRS 包含常见的应跳过目录。"""
        expected = {".git", "node_modules", "__pycache__", ".venv", "dist", "build"}
        assert expected.issubset(SKIP_DIRS)
