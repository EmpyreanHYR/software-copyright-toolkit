"""注释规则适配器和语言扩展映射。

集中管理所有语言的注释语法规则，方便后续扩展新语言。
"""

from __future__ import annotations

from pathlib import Path

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
# 每个条目: (行注释前缀, (块注释对, ...))
LINE_AND_BLOCK_ADAPTERS: dict[str, tuple[tuple[str, ...], tuple[tuple[str, str], ...]]] = {
    ".c": (("//",), (("/*", "*/"),)),
    ".cc": (("//",), (("/*", "*/"),)),
    ".cpp": (("//",), (("/*", "*/"),)),
    ".cs": (("//",), (("/*", "*/"),)),
    ".css": ((), (("/*", "*/"),)),
    ".dart": (("//",), (("/*", "*/"),)),
    ".go": (("//",), (("/*", "*/"),)),
    ".h": (("//",), (("/*", "*/"),)),
    ".hpp": (("//",), (("/*", "*/"),)),
    ".java": (("//",), (("/*", "*/"),)),
    ".js": (("//",), (("/*", "*/"),)),
    ".jsx": (("//",), (("/*", "*/"),)),
    ".kt": (("//",), (("/*", "*/"),)),
    ".less": (("//",), (("/*", "*/"),)),
    ".mm": (("//",), (("/*", "*/"),)),
    ".php": (("//", "#"), (("/*", "*/"),)),
    ".rs": (("//",), (("/*", "*/"),)),
    ".sass": (("//",), (("/*", "*/"),)),
    ".scss": (("//",), (("/*", "*/"),)),
    ".swift": (("//",), (("/*", "*/"),)),
    ".ts": (("//",), (("/*", "*/"),)),
    ".tsx": (("//",), (("/*", "*/"),)),
    ".vue": (("//",), (("/*", "*/"), ("<!--", "-->"))),
}

# --- 特殊处理的扩展集合 ---
HTML_LIKE_EXTENSIONS: set[str] = {".html", ".htm", ".xml", ".xhtml", ".svg"}
PYTHON_EXTENSIONS: set[str] = {".py", ".pyw"}
NO_COMMENT_EXTENSIONS: set[str] = {".json"}


def normalize_suffix(path: Path) -> str:
    """将特殊文件名映射为统一后缀，用于适配器查找。"""
    name = path.name.lower()
    if name in {"dockerfile", "containerfile"}:
        return ".dockerfile"
    if name in {"makefile", "gnumakefile"}:
        return ".make"
    return path.suffix.lower()
