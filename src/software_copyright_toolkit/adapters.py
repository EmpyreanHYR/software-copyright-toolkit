"""注释规则适配器和语言扩展映射。

集中管理所有语言的注释语法规则，方便后续扩展新语言。
支持用户自定义语言配置文件（TOML 格式）。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import tomllib  # type: ignore[import-not-found]

# --- 行注释 + 块注释的语言 ---
# 每个条目: (行注释前缀, (块注释对, ...))


@dataclass(frozen=True)
class BlockCommentRule:
    """块注释规则，支持嵌套标记。"""

    open_marker: str
    close_marker: str
    supports_nesting: bool = False


@dataclass(frozen=True)
class LanguageRule:
    """完整的语言注释规则。"""

    line_prefixes: tuple[str, ...] = ()
    block_rules: tuple[BlockCommentRule, ...] = ()


# --- 仅行注释的语言 ---
LINE_COMMENT_ADAPTERS: dict[str, tuple[str, ...]] = {
    ".bat": ("rem", "::"),
    ".cmd": ("rem", "::"),
    ".cmake": ("#",),
    ".conf": ("#",),
    ".dockerfile": ("#",),
    ".env": ("#",),
    ".ini": ("#", ";"),
    ".m": ("%",),
    ".make": ("#",),
    ".mk": ("#",),
    ".ps1": ("#",),
    ".properties": ("#",),
    ".r": ("#",),
    ".rb": ("#",),
    ".sh": ("#",),
    ".sql": ("--",),
    ".toml": ("#",),
    ".yaml": ("#",),
    ".yml": ("#",),
}

# --- 行注释 + 块注释的语言 ---
# 每个条目: (行注释前缀, (块注释规则, ...))
LINE_AND_BLOCK_ADAPTERS: dict[str, tuple[tuple[str, ...], tuple[BlockCommentRule, ...]]] = {
    ".c": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".cc": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".cpp": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".cs": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".css": ((), (BlockCommentRule("/*", "*/"),)),
    ".dart": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".go": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".h": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".hpp": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".java": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".js": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".jsx": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".kt": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".less": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".mm": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".php": (("//", "#"), (BlockCommentRule("/*", "*/"),)),
    ".rs": (("//",), (BlockCommentRule("/*", "*/", supports_nesting=True),)),
    ".sass": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".scss": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".swift": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".ts": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".tsx": (("//",), (BlockCommentRule("/*", "*/"),)),
    ".vue": (("//",), (BlockCommentRule("/*", "*/"), BlockCommentRule("<!--", "-->"))),
}

# --- 特殊处理的扩展集合 ---
HTML_LIKE_EXTENSIONS: set[str] = {".html", ".htm", ".xml", ".xhtml", ".svg"}
PYTHON_EXTENSIONS: set[str] = {".py", ".pyw"}
NO_COMMENT_EXTENSIONS: set[str] = {".json"}

# --- 向后兼容：旧格式的块注释对元组 ---
# 供 counter.py 中需要旧格式的场景使用
LegacyBlockPairs = tuple[tuple[str, str], ...]


def get_legacy_block_pairs(rules: tuple[BlockCommentRule, ...]) -> LegacyBlockPairs:
    """将 BlockCommentRule 元组转换为旧格式的 (open, close) 元组。"""
    return tuple((r.open_marker, r.close_marker) for r in rules)


def normalize_suffix(path: Path) -> str:
    """将特殊文件名映射为统一后缀，用于适配器查找。"""
    name = path.name.lower()
    if name in {"dockerfile", "containerfile"}:
        return ".dockerfile"
    if name in {"makefile", "gnumakefile"}:
        return ".make"
    return path.suffix.lower()


# --- 用户自定义语言配置 ---


def _load_toml_config(config_path: Path) -> dict[str, LanguageRule]:
    """从 TOML 文件加载用户自定义语言配置。

    配置文件格式示例::

        [languages.mylang]
        extensions = [".mylang", ".ml2"]
        line_comment = "//"
        block_comment = [["/*", "*/"], ["<!--", "-->"]]
        block_comment_nesting = [false, false]

    或简写形式::

        [languages]
        ".mylang" = { line_comment = "//", block_comment = [["/*", "*/"]] }
    """
    if not config_path.is_file():
        return {}

    with config_path.open("rb") as f:
        data = tomllib.load(f)

    rules: dict[str, LanguageRule] = {}
    languages = data.get("languages", {})

    for ext_or_name, spec in languages.items():
        if not isinstance(spec, dict):
            continue

        # 确定扩展名列表
        extensions: list[str] = []
        if "extensions" in spec:
            extensions = spec["extensions"]
        elif ext_or_name.startswith("."):
            extensions = [ext_or_name]
        else:
            continue

        # 解析行注释前缀
        line_prefixes: tuple[str, ...] = ()
        if "line_comment" in spec:
            lc = spec["line_comment"]
            line_prefixes = (lc,) if isinstance(lc, str) else tuple(lc)

        # 解析块注释规则
        block_rules: tuple[BlockCommentRule, ...] = ()
        if "block_comment" in spec:
            bc_list = spec["block_comment"]
            nesting_list = spec.get("block_comment_nesting", [])
            rules_list: list[BlockCommentRule] = []
            for i, pair in enumerate(bc_list):
                if isinstance(pair, list) and len(pair) == 2:
                    supports_nesting = bool(nesting_list[i]) if i < len(nesting_list) else False
                    rules_list.append(BlockCommentRule(pair[0], pair[1], supports_nesting=supports_nesting))
            block_rules = tuple(rules_list)

        for ext in extensions:
            rules[ext] = LanguageRule(line_prefixes=line_prefixes, block_rules=block_rules)

    return rules


def load_custom_adapters(
    config_path: Path | None = None,
    *,
    extra_search_dirs: tuple[Path, ...] = (),
) -> dict[str, LanguageRule]:
    """加载用户自定义语言配置，与内置配置合并（用户优先）。

    搜索顺序（后者覆盖前者）：
    1. 内置适配器（已在模块级常量中）
    2. 用户主目录 ~/.sct/languages.toml
    3. 项目内 .sct.toml
    4. 指定的 config_path
    5. extra_search_dirs 中的 languages.toml

    Returns:
        合并后的语言规则字典，key 为文件后缀。
    """
    merged: dict[str, LanguageRule] = {}

    # 先将内置适配器转为 LanguageRule
    for ext, prefixes in LINE_COMMENT_ADAPTERS.items():
        merged[ext] = LanguageRule(line_prefixes=prefixes)

    for ext, (prefixes, block_rules) in LINE_AND_BLOCK_ADAPTERS.items():
        existing = merged.get(ext)
        if existing:
            merged[ext] = LanguageRule(
                line_prefixes=prefixes if prefixes else existing.line_prefixes,
                block_rules=block_rules,
            )
        else:
            merged[ext] = LanguageRule(line_prefixes=prefixes, block_rules=block_rules)

    # HTML 类语言
    for ext in HTML_LIKE_EXTENSIONS:
        merged[ext] = LanguageRule(block_rules=(BlockCommentRule("<!--", "-->"),))

    # Python 和 JSON
    for ext in PYTHON_EXTENSIONS:
        merged[ext] = LanguageRule()  # Python 使用 tokenize，不需要规则
    for ext in NO_COMMENT_EXTENSIONS:
        merged[ext] = LanguageRule()  # 无注释

    # 搜索用户配置文件
    search_paths: list[Path] = []
    home = Path.home()
    search_paths.append(home / ".sct" / "languages.toml")
    search_paths.append(Path.cwd() / ".sct.toml")
    search_paths.extend(d / "languages.toml" for d in extra_search_dirs)
    if config_path is not None:
        search_paths.append(config_path)

    for path in search_paths:
        custom = _load_toml_config(path)
        for ext, rule in custom.items():
            merged[ext] = rule

    return merged
