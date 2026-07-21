"""文件扫描与编码检测模块。

负责文件遍历、编码自动探测和文本读取。
对大文件采用逐行生成器模式以降低内存占用。
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from pathlib import Path

# --- 默认跳过的目录 ---
SKIP_DIRS: set[str] = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    "target",
    "out",
    "coverage",
}

# 编码降级探测列表
_DEFAULT_ENCODINGS = ("utf-8-sig", "utf-8", "gb18030", "utf-16")


def _try_charset_normalizer(raw: bytes) -> str | None:
    """尝试使用 charset-normalizer 自动检测编码（可选依赖）。"""
    try:
        from charset_normalizer import from_bytes  # type: ignore[import-not-found]
    except ImportError:
        return None

    matches = from_bytes(raw)
    if matches:
        return str(matches.best().first() if hasattr(matches.best(), "first") else matches.best())
    return None


def read_text_lossless(path: Path, *, use_charset_normalizer: bool = True) -> str:
    """读取文本文件，自动探测编码。

    编码降级策略：
    1. 如果 use_charset_normalizer 为 True 且库已安装，优先使用 charset-normalizer 自动探测。
    2. 否则依次尝试 utf-8-sig → utf-8 → gb18030 → utf-16。
    3. 全部失败时回退到 utf-8 并使用 errors='replace'。

    Raises:
        UnicodeError: 检测到二进制文件（含 null 字节）。
        OSError: 文件读取失败。
    """
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise UnicodeError("文件看起来是二进制文件")

    if use_charset_normalizer:
        detected = _try_charset_normalizer(raw)
        if detected is not None:
            try:
                return raw.decode(detected)
            except (UnicodeDecodeError, LookupError):
                pass  # 降级到手动探测

    for encoding in _DEFAULT_ENCODINGS:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def read_lines_lazy(path: Path, *, use_charset_normalizer: bool = True) -> Iterator[str]:
    """逐行读取文本文件（生成器模式），适合大文件场景。

    与 read_text_lossless 使用相同的编码探测策略，但逐行 yield 而非
    一次性加载全部内容到内存。对于超大文件可显著降低内存峰值。
    """
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise UnicodeError("文件看起来是二进制文件")

    if use_charset_normalizer:
        detected = _try_charset_normalizer(raw)
        if detected is not None:
            try:
                text = raw.decode(detected)
                yield from text.splitlines()
                return
            except (UnicodeDecodeError, LookupError):
                pass

    for encoding in _DEFAULT_ENCODINGS:
        try:
            text = raw.decode(encoding)
            yield from text.splitlines()
            return
        except UnicodeDecodeError:
            continue

    text = raw.decode("utf-8", errors="replace")
    yield from text.splitlines()


def iter_files(root: Path, *, skip_dirs: set[str] | None = None) -> Iterable[Path]:
    """遍历目录下所有文件，跳过特定目录。

    Args:
        root: 根目录。
        skip_dirs: 要跳过的目录名集合。默认使用 SKIP_DIRS。
    """
    if skip_dirs is None:
        skip_dirs = SKIP_DIRS
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        if any(part in skip_dirs for part in item.parts):
            continue
        yield item
