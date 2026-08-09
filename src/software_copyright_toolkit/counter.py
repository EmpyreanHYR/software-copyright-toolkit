"""代码行数统计算法模块。

提供针对不同编程语言的注释识别和行数统计功能。
支持嵌套块注释（如 Rust）。
"""

from __future__ import annotations

import io
import tokenize
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from software_copyright_toolkit.adapters import (
    HTML_LIKE_EXTENSIONS,
    LINE_AND_BLOCK_ADAPTERS,
    LINE_COMMENT_ADAPTERS,
    NO_COMMENT_EXTENSIONS,
    PYTHON_EXTENSIONS,
    BlockCommentRule,
    normalize_suffix,
)
from software_copyright_toolkit.scanner import iter_files, read_lines_lazy, read_text_lossless


@dataclass(frozen=True)
class FileStats:
    """单个文件的统计结果。"""

    path: Path
    total: int
    effective: int
    blank: int
    comment: int


@dataclass(frozen=True)
class SkippedFile:
    """被跳过的文件及其原因。"""

    path: Path
    reason: str


def count_python(path: Path, text: str) -> FileStats:
    """统计 Python 文件的代码行数（使用 tokenize 模块）。"""
    lines = text.splitlines()
    total = len(lines)
    blank_lines = {idx for idx, line in enumerate(lines, start=1) if not line.strip()}
    comment_lines: set[int] = set()

    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type == tokenize.COMMENT:
                comment_lines.add(token.start[0])
    except tokenize.TokenError:
        for idx, line in enumerate(lines, start=1):
            if line.lstrip().startswith("#"):
                comment_lines.add(idx)

    comment = len(comment_lines - blank_lines)
    blank = len(blank_lines)
    return FileStats(path=path, total=total, effective=max(total - blank - comment, 0), blank=blank, comment=comment)


def count_line_comments(path: Path, text: str, prefixes: tuple[str, ...]) -> FileStats:
    """统计仅含行注释的文件的代码行数。"""
    total = blank = comment = 0
    lower_prefixes = tuple(prefix.lower() for prefix in prefixes)

    for line in text.splitlines():
        total += 1
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped:
            blank += 1
        elif any(lowered.startswith(prefix) for prefix in lower_prefixes):
            comment += 1

    return FileStats(path=path, total=total, effective=max(total - blank - comment, 0), blank=blank, comment=comment)


def count_block_comments(
    path: Path,
    text: str,
    line_prefixes: tuple[str, ...],
    block_rules: tuple[BlockCommentRule, ...],
) -> FileStats:
    """统计含块注释的文件的代码行数。

    使用状态机逐行扫描：遇到块注释起始标记进入块注释模式，
    直到遇到结束标记退出。行注释仅在非块注释模式下检查。
    支持嵌套块注释（如 Rust 的 /* /* */ */ 语法）。
    """
    total = blank = comment = 0
    active_end: str | None = None
    nesting_depth: int = 0
    active_rule: BlockCommentRule | None = None

    for line in text.splitlines():
        total += 1
        stripped = line.strip()
        if not stripped:
            blank += 1
            continue

        if active_end is not None:
            comment += 1
            if active_rule and active_rule.supports_nesting:
                # 嵌套模式：计算嵌套深度
                remaining = stripped
                while remaining:
                    if remaining.startswith(active_rule.open_marker):
                        nesting_depth += 1
                        remaining = remaining[len(active_rule.open_marker) :]
                    elif remaining.startswith(active_rule.close_marker):
                        nesting_depth -= 1
                        remaining = remaining[len(active_rule.close_marker) :]
                        if nesting_depth == 0:
                            active_end = None
                            active_rule = None
                            break
                    else:
                        remaining = remaining[1:]
            else:
                # 非嵌套模式：第一个结束标记就关闭
                if active_end in stripped:
                    active_end = None
            continue

        matched_block = False
        for rule in block_rules:
            if stripped.startswith(rule.open_marker):
                matched_block = True
                comment += 1
                after_open = stripped[len(rule.open_marker) :]
                if rule.supports_nesting:
                    nesting_depth = 1
                    remaining = after_open
                    while remaining:
                        if remaining.startswith(rule.open_marker):
                            nesting_depth += 1
                            remaining = remaining[len(rule.open_marker) :]
                        elif remaining.startswith(rule.close_marker):
                            nesting_depth -= 1
                            remaining = remaining[len(rule.close_marker) :]
                            if nesting_depth == 0:
                                break
                        else:
                            remaining = remaining[1:]
                    if nesting_depth > 0:
                        active_end = rule.close_marker
                        active_rule = rule
                else:
                    if rule.close_marker not in after_open:
                        active_end = rule.close_marker
                        active_rule = None
                break
        if matched_block:
            continue

        if any(stripped.startswith(prefix) for prefix in line_prefixes):
            comment += 1
            continue

    return FileStats(path=path, total=total, effective=max(total - blank - comment, 0), blank=blank, comment=comment)


def count_python_streaming(path: Path, lines: Iterator[str]) -> FileStats:
    """流式统计 Python 文件的代码行数。"""
    # 流模式下仍需拼接完整文本以使用 tokenize
    text = "\n".join(lines)
    return count_python(path, text)


def count_line_comments_streaming(path: Path, lines: Iterator[str], prefixes: tuple[str, ...]) -> FileStats:
    """流式统计仅含行注释的文件的代码行数。"""
    total = blank = comment = 0
    lower_prefixes = tuple(prefix.lower() for prefix in prefixes)

    for line in lines:
        total += 1
        stripped = line.strip()
        lowered = stripped.lower()
        if not stripped:
            blank += 1
        elif any(lowered.startswith(prefix) for prefix in lower_prefixes):
            comment += 1

    return FileStats(path=path, total=total, effective=max(total - blank - comment, 0), blank=blank, comment=comment)


def count_block_comments_streaming(
    path: Path,
    lines: Iterator[str],
    line_prefixes: tuple[str, ...],
    block_rules: tuple[BlockCommentRule, ...],
) -> FileStats:
    """流式统计含块注释的文件的代码行数。"""
    total = blank = comment = 0
    active_end: str | None = None
    nesting_depth: int = 0
    active_rule: BlockCommentRule | None = None

    for line in lines:
        total += 1
        stripped = line.strip()
        if not stripped:
            blank += 1
            continue

        if active_end is not None:
            comment += 1
            if active_rule and active_rule.supports_nesting:
                remaining = stripped
                while remaining:
                    if remaining.startswith(active_rule.open_marker):
                        nesting_depth += 1
                        remaining = remaining[len(active_rule.open_marker) :]
                    elif remaining.startswith(active_rule.close_marker):
                        nesting_depth -= 1
                        remaining = remaining[len(active_rule.close_marker) :]
                        if nesting_depth == 0:
                            active_end = None
                            active_rule = None
                            break
                    else:
                        remaining = remaining[1:]
            else:
                if active_end in stripped:
                    active_end = None
            continue

        matched_block = False
        for rule in block_rules:
            if stripped.startswith(rule.open_marker):
                matched_block = True
                comment += 1
                after_open = stripped[len(rule.open_marker) :]
                if rule.supports_nesting:
                    nesting_depth = 1
                    remaining = after_open
                    while remaining:
                        if remaining.startswith(rule.open_marker):
                            nesting_depth += 1
                            remaining = remaining[len(rule.open_marker) :]
                        elif remaining.startswith(rule.close_marker):
                            nesting_depth -= 1
                            remaining = remaining[len(rule.close_marker) :]
                            if nesting_depth == 0:
                                break
                        else:
                            remaining = remaining[1:]
                    if nesting_depth > 0:
                        active_end = rule.close_marker
                        active_rule = rule
                else:
                    if rule.close_marker not in after_open:
                        active_end = rule.close_marker
                        active_rule = None
                break
        if matched_block:
            continue

        if any(stripped.startswith(prefix) for prefix in line_prefixes):
            comment += 1
            continue

    return FileStats(path=path, total=total, effective=max(total - blank - comment, 0), blank=blank, comment=comment)


def count_supported_file(path: Path, text: str) -> FileStats | None:
    """根据文件后缀选择对应的统计策略。"""
    suffix = normalize_suffix(path)
    if suffix in PYTHON_EXTENSIONS:
        return count_python(path, text)
    if suffix == ".m":
        return count_block_comments(path, text, ("%",), (BlockCommentRule("%{", "%}"),))
    if suffix in NO_COMMENT_EXTENSIONS:
        return count_line_comments(path, text, ())
    if suffix in HTML_LIKE_EXTENSIONS:
        return count_block_comments(path, text, (), (BlockCommentRule("<!--", "-->"),))
    if suffix in LINE_AND_BLOCK_ADAPTERS:
        line_prefixes, block_rules = LINE_AND_BLOCK_ADAPTERS[suffix]
        return count_block_comments(path, text, line_prefixes, block_rules)
    if suffix in LINE_COMMENT_ADAPTERS:
        return count_line_comments(path, text, LINE_COMMENT_ADAPTERS[suffix])
    return None


def count_folder(
    target: Path,
    *,
    use_streaming: bool = False,
    use_charset_normalizer: bool = True,
    include_paths: frozenset[Path] | set[Path] | None = None,
) -> tuple[list[FileStats], list[SkippedFile]]:
    """遍历文件夹，统计所有已适配文件的代码行数。

    Args:
        target: 目标文件夹。
        use_streaming: 是否使用流式读取模式（对大文件更友好）。
        use_charset_normalizer: 是否尝试 charset-normalizer 自动编码探测。
        include_paths: 仅统计指定的文件路径集合。为 None 时统计全部文件。
    """
    stats: list[FileStats] = []
    skipped: list[SkippedFile] = []

    for path in iter_files(target):
        # 如果指定了 include_paths，仅处理包含在内的文件
        if include_paths is not None and path.resolve() not in include_paths:
            continue
        try:
            if use_streaming:
                lines = list(read_lines_lazy(path, use_charset_normalizer=use_charset_normalizer))
                text = "\n".join(lines)
            else:
                text = read_text_lossless(path, use_charset_normalizer=use_charset_normalizer)
        except (OSError, UnicodeError) as exc:
            skipped.append(SkippedFile(path, f"读取失败或非文本文件: {exc}"))
            continue

        result = count_supported_file(path, text)
        if result is None:
            suffix = normalize_suffix(path) or "(无后缀)"
            skipped.append(SkippedFile(path, f"未适配的文件后缀: {suffix}"))
            continue
        stats.append(result)

    return stats, skipped
