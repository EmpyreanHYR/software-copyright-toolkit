"""测试注释规则适配器。"""

from pathlib import Path

from software_copyright_toolkit.adapters import (
    HTML_LIKE_EXTENSIONS,
    LINE_AND_BLOCK_ADAPTERS,
    LINE_COMMENT_ADAPTERS,
    NO_COMMENT_EXTENSIONS,
    PYTHON_EXTENSIONS,
    normalize_suffix,
)


class TestNormalizeSuffix:
    def test_regular_extension(self):
        assert normalize_suffix(Path("main.py")) == ".py"
        assert normalize_suffix(Path("App.tsx")) == ".tsx"

    def test_case_insensitive(self):
        assert normalize_suffix(Path("MAIN.PY")) == ".py"

    def test_dockerfile(self):
        assert normalize_suffix(Path("Dockerfile")) == ".dockerfile"
        assert normalize_suffix(Path("dockerfile")) == ".dockerfile"
        assert normalize_suffix(Path("Containerfile")) == ".dockerfile"

    def test_makefile(self):
        assert normalize_suffix(Path("Makefile")) == ".make"
        assert normalize_suffix(Path("makefile")) == ".make"
        assert normalize_suffix(Path("GNUmakefile")) == ".make"
        assert normalize_suffix(Path("GNUMakefile")) == ".make"

    def test_no_extension(self):
        assert normalize_suffix(Path("README")) == ""

    def test_unknown_special_name(self):
        assert normalize_suffix(Path("something")) == ""


class TestAdaptersCoverage:
    """确保常用语言在适配器中。"""

    def test_common_line_comment_languages(self):
        assert ".sh" in LINE_COMMENT_ADAPTERS
        assert ".sql" in LINE_COMMENT_ADAPTERS
        assert ".rb" in LINE_COMMENT_ADAPTERS
        assert ".toml" in LINE_COMMENT_ADAPTERS

    def test_common_block_comment_languages(self):
        assert ".c" in LINE_AND_BLOCK_ADAPTERS
        assert ".java" in LINE_AND_BLOCK_ADAPTERS
        assert ".go" in LINE_AND_BLOCK_ADAPTERS
        assert ".rs" in LINE_AND_BLOCK_ADAPTERS

    def test_html_like_extensions(self):
        assert ".html" in HTML_LIKE_EXTENSIONS
        assert ".xml" in HTML_LIKE_EXTENSIONS
        assert ".svg" in HTML_LIKE_EXTENSIONS

    def test_python_extensions(self):
        assert ".py" in PYTHON_EXTENSIONS
        assert ".pyw" in PYTHON_EXTENSIONS

    def test_no_comment_extensions(self):
        assert ".json" in NO_COMMENT_EXTENSIONS

    def test_vue_has_multiple_block_pairs(self):
        _, block_pairs = LINE_AND_BLOCK_ADAPTERS[".vue"]
        assert len(block_pairs) == 2  # /* */ and <!-- -->
