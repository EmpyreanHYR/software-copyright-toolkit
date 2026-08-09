"""测试注释规则适配器。"""

import sys
from pathlib import Path

import pytest

from software_copyright_toolkit.adapters import (
    HTML_LIKE_EXTENSIONS,
    LINE_AND_BLOCK_ADAPTERS,
    LINE_COMMENT_ADAPTERS,
    NO_COMMENT_EXTENSIONS,
    PYTHON_EXTENSIONS,
    BlockCommentRule,
    LanguageRule,
    _load_toml_config,
    load_custom_adapters,
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

    def test_vue_has_multiple_block_rules(self):
        _, block_rules = LINE_AND_BLOCK_ADAPTERS[".vue"]
        assert len(block_rules) == 2  # /* */ and <!-- -->
        assert isinstance(block_rules[0], BlockCommentRule)


class TestBlockCommentRule:
    """测试 BlockCommentRule 数据类。"""

    def test_basic_creation(self):
        rule = BlockCommentRule("/*", "*/")
        assert rule.open_marker == "/*"
        assert rule.close_marker == "*/"
        assert rule.supports_nesting is False

    def test_nesting_flag(self):
        rule = BlockCommentRule("/*", "*/", supports_nesting=True)
        assert rule.supports_nesting is True

    def test_frozen(self):
        rule = BlockCommentRule("/*", "*/")
        with pytest.raises(AttributeError):
            rule.open_marker = "//"  # type: ignore[misc]

    def test_rust_supports_nesting(self):
        _, block_rules = LINE_AND_BLOCK_ADAPTERS[".rs"]
        assert len(block_rules) == 1
        assert block_rules[0].supports_nesting is True

    def test_c_does_not_support_nesting(self):
        _, block_rules = LINE_AND_BLOCK_ADAPTERS[".c"]
        assert len(block_rules) == 1
        assert block_rules[0].supports_nesting is False


class TestLanguageRule:
    """测试 LanguageRule 数据类。"""

    def test_basic_creation(self):
        rule = LanguageRule(line_prefixes=("//",), block_rules=(BlockCommentRule("/*", "*/"),))
        assert rule.line_prefixes == ("//",)
        assert len(rule.block_rules) == 1

    def test_defaults(self):
        rule = LanguageRule()
        assert rule.line_prefixes == ()
        assert rule.block_rules == ()


@pytest.mark.skipif(sys.version_info < (3, 11), reason="tomllib requires Python 3.11+")
class TestLoadTomlConfig:
    """测试 TOML 配置加载。"""

    def test_nonexistent_file(self, tmp_path):
        result = _load_toml_config(tmp_path / "nonexistent.toml")
        assert result == {}

    def test_simple_config(self, tmp_path):
        config_file = tmp_path / "languages.toml"
        config_file.write_text(
            '[languages]\n".mylang" = { line_comment = "//", block_comment = [["/*", "*/"]] }\n',
            encoding="utf-8",
        )
        result = _load_toml_config(config_file)
        assert ".mylang" in result
        assert result[".mylang"].line_prefixes == ("//",)
        assert len(result[".mylang"].block_rules) == 1
        assert result[".mylang"].block_rules[0].open_marker == "/*"

    def test_nesting_config(self, tmp_path):
        config_file = tmp_path / "languages.toml"
        config_file.write_text(
            '[languages]\n".mylang" = { block_comment = [["/*", "*/"]], block_comment_nesting = [true] }\n',
            encoding="utf-8",
        )
        result = _load_toml_config(config_file)
        assert result[".mylang"].block_rules[0].supports_nesting is True

    def test_multiple_extensions(self, tmp_path):
        config_file = tmp_path / "languages.toml"
        config_file.write_text(
            """
[languages.mylang]
extensions = [".ml1", ".ml2"]
line_comment = "//"
""",
            encoding="utf-8",
        )
        result = _load_toml_config(config_file)
        assert ".ml1" in result
        assert ".ml2" in result

    def test_multiple_line_prefixes(self, tmp_path):
        config_file = tmp_path / "languages.toml"
        config_file.write_text(
            '[languages]\n".mylang" = { line_comment = ["//", "#"] }\n',
            encoding="utf-8",
        )
        result = _load_toml_config(config_file)
        assert result[".mylang"].line_prefixes == ("//", "#")

    def test_invalid_spec_skipped(self, tmp_path):
        config_file = tmp_path / "languages.toml"
        config_file.write_text(
            '[languages]\n".mylang" = "invalid"\n',
            encoding="utf-8",
        )
        result = _load_toml_config(config_file)
        assert ".mylang" not in result


class TestLoadCustomAdapters:
    """测试自定义适配器加载。"""

    def test_loads_builtin(self):
        merged = load_custom_adapters()
        assert ".py" in merged
        assert ".sh" in merged
        assert ".rs" in merged

    @pytest.mark.skipif(sys.version_info < (3, 11), reason="tomllib requires Python 3.11+")
    def test_custom_overrides_builtin(self, tmp_path):
        config_file = tmp_path / "languages.toml"
        config_file.write_text(
            '[languages]\n".py" = { line_comment = "//" }\n',
            encoding="utf-8",
        )
        merged = load_custom_adapters(config_path=config_file)
        # 自定义配置应覆盖内置
        assert merged[".py"].line_prefixes == ("//",)

    def test_rust_nesting_preserved(self):
        merged = load_custom_adapters()
        assert merged[".rs"].block_rules[0].supports_nesting is True
