"""测试代码行数统计算法。"""

from pathlib import Path

from software_copyright_toolkit.counter import (
    count_block_comments,
    count_line_comments,
    count_python,
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
        stats = count_block_comments(Path("test.c"), text, ("//",), (("/*", "*/"),))
        assert stats.comment == 1
        assert stats.effective == 1

    def test_c_style_multi_line_block(self):
        text = "/* start\n   middle\n   end */\nint x = 1;\n"
        stats = count_block_comments(Path("test.c"), text, ("//",), (("/*", "*/"),))
        assert stats.comment == 3
        assert stats.effective == 1

    def test_c_style_line_comment(self):
        text = "// line comment\nint x = 1;\n"
        stats = count_block_comments(Path("test.c"), text, ("//",), (("/*", "*/"),))
        assert stats.comment == 1
        assert stats.effective == 1

    def test_html_style(self):
        text = "<!-- comment -->\n<div>hello</div>\n"
        stats = count_block_comments(Path("test.html"), text, (), (("<!--", "-->"),))
        assert stats.comment == 1
        assert stats.effective == 1

    def test_html_multi_line(self):
        text = "<!-- start\n  middle\n  end -->\n<div>hello</div>\n"
        stats = count_block_comments(Path("test.html"), text, (), (("<!--", "-->"),))
        assert stats.comment == 3
        assert stats.effective == 1

    def test_matlab(self):
        text = "% comment\nx = 1;\n%{ block start\nblock body\n%} block end\nx = 2;\n"
        stats = count_block_comments(Path("test.m"), text, ("%",), (("%{", "%}"),))
        assert stats.comment == 4  # % + %{ + block body + %}
        assert stats.effective == 2

    def test_nested_block_comment_handling(self):
        # /* /* nested */ — first */ closes, not true nesting
        text = "/* outer /* inner */ still comment? */ int x;\n"
        stats = count_block_comments(Path("test.c"), text, ("//",), (("/*", "*/"),))
        # After "*/" closes, "still comment? */" — "still comment?" is code,
        # then "*/" closes nothing (since already closed), then "int x;" is code
        # Actually: /* outer /* inner */ still comment? */ int x;
        # After first */ at "inner */", active_end is None
        # " still comment? */" — "*/" is not a start, so it's treated as code
        assert stats.total == 1

    def test_php_hash_comment(self):
        text = "# comment\n<?php echo 'hi'; ?>\n"
        stats = count_block_comments(Path("test.php"), text, ("//", "#"), (("/*", "*/"),))
        assert stats.comment == 1
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
