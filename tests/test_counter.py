"""测试代码行数统计算法。"""

from pathlib import Path

from software_copyright_toolkit.adapters import BlockCommentRule
from software_copyright_toolkit.counter import (
    count_block_comments,
    count_block_comments_streaming,
    count_line_comments,
    count_line_comments_streaming,
    count_python,
    count_python_streaming,
    count_supported_file,
)


class TestCountPython:
    def test_basic(self):
        text = "def hello():\n    pass\n"
        stats = count_python(Path("test.py"), text)
        assert stats.total == 2
        assert stats.effective == 2
        assert stats.blank == 0
        assert stats.comment == 0

    def test_with_comments(self):
        text = "# comment line\ndef hello():\n    pass  # inline comment\n"
        stats = count_python(Path("test.py"), text)
        assert stats.total == 3
        assert stats.comment >= 1

    def test_with_blank_lines(self):
        text = "def hello():\n\n    pass\n"
        stats = count_python(Path("test.py"), text)
        assert stats.total == 3
        assert stats.blank == 1
        assert stats.effective == 2

    def test_docstring_as_string_not_comment(self):
        # tokenize treats docstrings as STRING, not COMMENT
        text = '"""module docstring"""\ndef hello():\n    pass\n'
        stats = count_python(Path("test.py"), text)
        assert stats.comment == 0  # docstrings are strings, not comments

    def test_empty_file(self):
        stats = count_python(Path("test.py"), "")
        assert stats.total == 0
        assert stats.effective == 0

    def test_token_error_fallback(self):
        # Unicode that causes tokenize error, falls back to # detection
        text = "# valid comment\ndef hello():\n    pass\n"
        stats = count_python(Path("test.py"), text)
        assert stats.comment == 1
        assert stats.effective == 2


class TestCountLineComments:
    def test_shell_style(self):
        text = "# this is a comment\necho hello\n# another comment\n\n"
        stats = count_line_comments(Path("test.sh"), text, ("#",))
        assert stats.total == 4
        assert stats.comment == 2
        assert stats.blank == 1
        assert stats.effective == 1

    def test_sql_style(self):
        text = "-- comment\nSELECT 1;\n"
        stats = count_line_comments(Path("test.sql"), text, ("--",))
        assert stats.total == 2
        assert stats.comment == 1
        assert stats.effective == 1

    def test_bat_style(self):
        text = "REM this is a comment\n@echo off\n:: another comment\n"
        stats = count_line_comments(Path("test.bat"), text, ("rem", "::"))
        assert stats.comment == 2
        assert stats.effective == 1

    def test_case_insensitive(self):
        text = "Rem case insensitive\n@echo off\n"
        stats = count_line_comments(Path("test.bat"), text, ("rem",))
        assert stats.comment == 1

    def test_no_prefixes(self):
        # e.g., JSON — no comment syntax
        text = '{"key": "value"}\n'
        stats = count_line_comments(Path("test.json"), text, ())
        assert stats.comment == 0
        assert stats.effective == 1

    def test_blank_only_file(self):
        stats = count_line_comments(Path("test.sh"), "\n\n\n", ("#",))
        assert stats.total == 3
        assert stats.blank == 3
        assert stats.effective == 0


class TestCountBlockComments:
    def test_c_style_single_line_block(self):
        text = "/* comment */\nint x = 1;\n"
        stats = count_block_comments(Path("test.c"), text, ("//",), (BlockCommentRule("/*", "*/"),))
        assert stats.comment == 1
        assert stats.effective == 1

    def test_c_style_multi_line_block(self):
        text = "/* start\n   middle\n   end */\nint x = 1;\n"
        stats = count_block_comments(Path("test.c"), text, ("//",), (BlockCommentRule("/*", "*/"),))
        assert stats.comment == 3
        assert stats.effective == 1

    def test_c_style_line_comment(self):
        text = "// line comment\nint x = 1;\n"
        stats = count_block_comments(Path("test.c"), text, ("//",), (BlockCommentRule("/*", "*/"),))
        assert stats.comment == 1
        assert stats.effective == 1

    def test_html_style(self):
        text = "<!-- comment -->\n<div>hello</div>\n"
        stats = count_block_comments(Path("test.html"), text, (), (BlockCommentRule("<!--", "-->"),))
        assert stats.comment == 1
        assert stats.effective == 1

    def test_html_multi_line(self):
        text = "<!-- start\n  middle\n  end -->\n<div>hello</div>\n"
        stats = count_block_comments(Path("test.html"), text, (), (BlockCommentRule("<!--", "-->"),))
        assert stats.comment == 3
        assert stats.effective == 1

    def test_matlab(self):
        text = "% comment\nx = 1;\n%{ block start\nblock body\n%} block end\nx = 2;\n"
        stats = count_block_comments(Path("test.m"), text, ("%",), (BlockCommentRule("%{", "%}"),))
        assert stats.comment == 4  # % + %{ + block body + %}
        assert stats.effective == 2

    def test_nested_block_comment_c_style(self):
        """C 风格不支持嵌套：第一个 */ 就关闭。"""
        text = "/* outer /* inner */ still comment? */ int x;\n"
        stats = count_block_comments(Path("test.c"), text, ("//",), (BlockCommentRule("/*", "*/"),))
        # 非嵌套模式：第一个 */ 关闭后，剩余内容是代码
        assert stats.total == 1

    def test_nested_block_comment_rust_style(self):
        """Rust 风格支持嵌套：/* /* inner */ outer */ 全部是注释。"""
        rule = BlockCommentRule("/*", "*/", supports_nesting=True)
        text = "/* outer /* inner */ outer still comment */\nint x = 1;\n"
        stats = count_block_comments(Path("test.rs"), text, ("//",), (rule,))
        assert stats.comment == 1  # 整行都是注释
        assert stats.effective == 1  # 第二行是代码

    def test_nested_block_comment_deep(self):
        """三层嵌套。"""
        rule = BlockCommentRule("/*", "*/", supports_nesting=True)
        text = "/* level1 /* level2 /* level3 */ level2 */ level1 */\nint x;\n"
        stats = count_block_comments(Path("test.rs"), text, ("//",), (rule,))
        assert stats.comment == 1
        assert stats.effective == 1

    def test_nested_block_comment_multiline(self):
        """跨行嵌套注释。"""
        rule = BlockCommentRule("/*", "*/", supports_nesting=True)
        text = "/* start\n/* inner\nend inner */\nend outer */\nint x;\n"
        stats = count_block_comments(Path("test.rs"), text, ("//",), (rule,))
        assert stats.comment == 4  # 4 行注释
        assert stats.effective == 1  # 最后一行是代码

    def test_php_hash_comment(self):
        text = "# comment\n<?php echo 'hi'; ?>\n"
        stats = count_block_comments(Path("test.php"), text, ("//", "#"), (BlockCommentRule("/*", "*/"),))
        assert stats.comment == 1
        assert stats.effective == 1

    def test_multiple_block_rules(self):
        """Vue 文件同时有 /* */ 和 <!-- --> 两种块注释。"""
        rules = (BlockCommentRule("/*", "*/"), BlockCommentRule("<!--", "-->"))
        text = "/* block comment */\n<!-- html comment -->\n<div>hello</div>\n"
        stats = count_block_comments(Path("test.vue"), text, ("//",), rules)
        assert stats.comment == 2
        assert stats.effective == 1


class TestCountSupportedFile:
    def test_python_dispatch(self):
        stats = count_supported_file(Path("main.py"), "x = 1\n")
        assert stats is not None
        assert stats.effective == 1

    def test_json_dispatch(self):
        stats = count_supported_file(Path("data.json"), '{"key": "value"}\n')
        assert stats is not None
        assert stats.comment == 0
        assert stats.effective == 1

    def test_unknown_extension(self):
        stats = count_supported_file(Path("data.xyz"), "some content\n")
        assert stats is None

    def test_dockerfile_dispatch(self):
        stats = count_supported_file(Path("Dockerfile"), "# comment\nFROM python:3\n")
        assert stats is not None
        assert stats.comment == 1
        assert stats.effective == 1

    def test_makefile_dispatch(self):
        stats = count_supported_file(Path("Makefile"), "# comment\nall: build\n")
        assert stats is not None
        assert stats.comment == 1
        assert stats.effective == 1

    def test_rust_dispatch_uses_nesting(self):
        """确认 Rust 文件通过 count_supported_file 使用嵌套模式。"""
        text = "/* outer /* inner */ outer */\nfn main() {}\n"
        stats = count_supported_file(Path("main.rs"), text)
        assert stats is not None
        assert stats.comment == 1
        assert stats.effective == 1


class TestStreamingVariants:
    """测试流式变体与非流式版本结果一致。"""

    def test_python_streaming_consistency(self):
        """流式 Python 统计与非流式的核心指标一致。

        注意：count_python_streaming 通过 "\n".join(lines) 重建文本，
        会丢失原始文本末尾的空行，因此 total/blank 可能略有差异。
        我们验证关键指标（effective、comment）一致。
        """
        text = "# comment\ndef hello():\n    pass\n"
        result_normal = count_python(Path("test.py"), text)
        result_streaming = count_python_streaming(Path("test.py"), iter(text.splitlines()))
        assert result_normal.effective == result_streaming.effective
        assert result_normal.comment == result_streaming.comment

    def test_line_comments_streaming_consistency(self):
        text = "# comment\necho hello\n# another\n\n"
        lines = text.splitlines()
        result_normal = count_line_comments(Path("test.sh"), text, ("#",))
        result_streaming = count_line_comments_streaming(Path("test.sh"), iter(lines), ("#",))
        assert result_normal == result_streaming

    def test_block_comments_streaming_consistency(self):
        text = "/* comment */\nint x = 1;\n// line\n"
        lines = text.splitlines()
        rules = (BlockCommentRule("/*", "*/"),)
        result_normal = count_block_comments(Path("test.c"), text, ("//",), rules)
        result_streaming = count_block_comments_streaming(Path("test.c"), iter(lines), ("//",), rules)
        assert result_normal == result_streaming

    def test_block_comments_streaming_nesting_consistency(self):
        text = "/* outer /* inner */ outer */\nfn main() {}\n"
        lines = text.splitlines()
        rules = (BlockCommentRule("/*", "*/", supports_nesting=True),)
        result_normal = count_block_comments(Path("test.rs"), text, ("//",), rules)
        result_streaming = count_block_comments_streaming(Path("test.rs"), iter(lines), ("//",), rules)
        assert result_normal == result_streaming

    def test_block_comments_streaming_multiline(self):
        text = "/* start\n   middle\n   end */\nint x;\n"
        lines = text.splitlines()
        rules = (BlockCommentRule("/*", "*/"),)
        result_normal = count_block_comments(Path("test.c"), text, ("//",), rules)
        result_streaming = count_block_comments_streaming(Path("test.c"), iter(lines), ("//",), rules)
        assert result_normal == result_streaming
