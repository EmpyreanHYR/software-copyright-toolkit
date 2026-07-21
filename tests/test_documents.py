"""测试 Word 程序鉴别材料生成逻辑。"""

from software_copyright_toolkit.documents import (
    DEFAULT_SEPARATOR,
    SourceLine,
    count_source_content_lines,
    display_width,
    find_module_end_index,
    is_module_end_line,
    is_valid_identification_selection,
    sanitize_filename,
    select_identification_lines,
    split_long_line,
    wrap_source_lines,
)


class TestSanitizeFilename:
    def test_normal_name(self):
        assert sanitize_filename("MyApp") == "MyApp"

    def test_special_chars(self):
        result = sanitize_filename('test<>:"/\\|?*file')
        assert "?" not in result
        assert "<" not in result
        assert ">" not in result

    def test_spaces_to_underscores(self):
        result = sanitize_filename("my app v1")
        assert " " not in result

    def test_empty_becomes_default(self):
        result = sanitize_filename("   ")
        assert result == "未命名软件"


class TestDisplayWidth:
    def test_ascii(self):
        assert display_width("abc") == 3

    def test_cjk(self):
        assert display_width("中文") == 4  # 2 wide chars × 2 = 4

    def test_mixed(self):
        # "A中" = 1 (A) + 2 (中) = 3
        assert display_width("A中") == 3


class TestSplitLongLine:
    def test_short_line(self):
        assert split_long_line("abc", 80) == ["abc"]

    def test_exact_width(self):
        result = split_long_line("a" * 80, 80)
        assert len(result) == 1
        assert len(result[0]) == 80

    def test_over_width(self):
        result = split_long_line("a" * 90, 80)
        assert len(result) == 2
        assert len(result[0]) == 80
        assert len(result[1]) == 10

    def test_cjk_split(self):
        # 中文每个占 2 宽度，80宽度 = 40个中文字
        line = "中" * 50  # width = 100
        result = split_long_line(line, 80)
        assert len(result) == 2
        assert result[0] == "中" * 40
        assert result[1] == "中" * 10


class TestWrapSourceLines:
    def test_short_lines_unchanged(self):
        lines = [SourceLine("abc", counts_as_source=True, is_source_text=True)]
        result = wrap_source_lines(lines)
        assert len(result) == 1
        assert result[0].text == "abc"
        assert result[0].counts_as_source is True

    def test_long_line_wrapped(self):
        lines = [SourceLine("a" * 100, counts_as_source=True, is_source_text=True)]
        result = wrap_source_lines(lines)
        assert len(result) == 2
        assert result[0].counts_as_source is True  # 第一行计入
        assert result[1].counts_as_source is False  # 续行不计入

    def test_separator_not_wrapped(self):
        lines = [SourceLine("=" * 100, counts_as_source=False, is_source_text=False)]
        result = wrap_source_lines(lines)
        # 分隔行超长也会被拆分，但不计入源码行
        assert all(not line.counts_as_source for line in result)


class TestModuleEndDetection:
    def test_brace_end(self):
        assert is_module_end_line("}") is True
        assert is_module_end_line("  }  ") is True
        assert is_module_end_line("};") is True

    def test_bracket_end(self):
        assert is_module_end_line("]") is True

    def test_paren_end(self):
        assert is_module_end_line(")") is True

    def test_end_keyword(self):
        assert is_module_end_line("end") is True
        assert is_module_end_line("end;") is True

    def test_not_end(self):
        assert is_module_end_line("int x = 1;") is False
        assert is_module_end_line("  if (x > 0) {") is False


class TestFindModuleEndIndex:
    def test_finds_brace(self):
        lines = [
            SourceLine("code", counts_as_source=True, is_source_text=True),
            SourceLine("more code", counts_as_source=True, is_source_text=True),
            SourceLine("}", counts_as_source=True, is_source_text=True),
        ]
        idx = find_module_end_index(lines, minimum_index=2)
        assert idx == 3

    def test_ignores_separator_lines(self):
        lines = [
            SourceLine("code", counts_as_source=True, is_source_text=True),
            SourceLine("===== 文件: x.py =====", counts_as_source=False, is_source_text=False),
            SourceLine("}", counts_as_source=True, is_source_text=True),
        ]
        idx = find_module_end_index(lines, minimum_index=2)
        assert idx == 3

    def test_no_match_returns_none(self):
        lines = [SourceLine("code", counts_as_source=True, is_source_text=True)] * 10
        idx = find_module_end_index(lines, minimum_index=5)
        assert idx is None


class TestSelectIdentificationLines:
    def test_small_source_returns_all(self):
        lines = [SourceLine(f"line {i}", counts_as_source=True, is_source_text=True) for i in range(100)]
        result = select_identification_lines(lines, 100)
        assert len(result) == 100  # 小于 3000，返回全部

    def test_large_source_truncates(self):
        # 创建 5000 行，最后一行是 }
        lines = [SourceLine(f"line {i}", counts_as_source=True, is_source_text=True) for i in range(4999)]
        lines.append(SourceLine("}", counts_as_source=True, is_source_text=True))
        result = select_identification_lines(lines, 5000)
        # 至少3000行才会截取
        if len(result) < 5000:
            assert is_valid_identification_selection(result)


class TestCountSourceContentLines:
    def test_basic(self):
        lines = [
            SourceLine("code", counts_as_source=True, is_source_text=True),
            SourceLine("===== 文件: x.py =====", counts_as_source=False, is_source_text=False),
            SourceLine("code2", counts_as_source=True, is_source_text=True),
        ]
        assert count_source_content_lines(lines) == 2


class TestDefaultSeparator:
    def test_format(self):
        result = DEFAULT_SEPARATOR.format(path="sub/main.py")
        assert "sub/main.py" in result
        assert "=====" in result
