from __future__ import annotations

import argparse
import io
import sys
import tokenize
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable


SKIP_DIRS = {
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

HTML_LIKE_EXTENSIONS = {".html", ".htm", ".xml", ".xhtml", ".svg"}
PYTHON_EXTENSIONS = {".py", ".pyw"}
NO_COMMENT_EXTENSIONS = {".json"}


@dataclass(frozen=True)
class FileStats:
    path: Path
    total: int
    effective: int
    blank: int
    comment: int


@dataclass(frozen=True)
class SkippedFile:
    path: Path
    reason: str


def normalize_suffix(path: Path) -> str:
    name = path.name.lower()
    if name in {"dockerfile", "containerfile"}:
        return ".dockerfile"
    if name in {"makefile", "gnumakefile"}:
        return ".make"
    return path.suffix.lower()


def read_text_lossless(path: Path) -> str:
    raw = path.read_bytes()
    if b"\x00" in raw:
        raise UnicodeError("文件看起来是二进制文件")
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "utf-16"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def iter_files(root: Path) -> Iterable[Path]:
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        if any(part in SKIP_DIRS for part in item.parts):
            continue
        yield item


def count_python(path: Path, text: str) -> FileStats:
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
    block_pairs: tuple[tuple[str, str], ...],
) -> FileStats:
    total = blank = comment = 0
    active_end: str | None = None

    for line in text.splitlines():
        total += 1
        stripped = line.strip()
        if not stripped:
            blank += 1
            continue

        if active_end is not None:
            comment += 1
            if active_end in stripped:
                active_end = None
            continue

        matched_block = False
        for start, end in block_pairs:
            if stripped.startswith(start):
                matched_block = True
                comment += 1
                if end not in stripped[len(start) :]:
                    active_end = end
                break
        if matched_block:
            continue

        if any(stripped.startswith(prefix) for prefix in line_prefixes):
            comment += 1
            continue

    return FileStats(path=path, total=total, effective=max(total - blank - comment, 0), blank=blank, comment=comment)


def count_supported_file(path: Path, text: str) -> FileStats | None:
    suffix = normalize_suffix(path)
    if suffix in PYTHON_EXTENSIONS:
        return count_python(path, text)
    if suffix == ".m":
        return count_block_comments(path, text, ("%",), (("%{", "%}"),))
    if suffix in NO_COMMENT_EXTENSIONS:
        return count_line_comments(path, text, ())
    if suffix in HTML_LIKE_EXTENSIONS:
        return count_block_comments(path, text, (), (("<!--", "-->"),))
    if suffix in LINE_AND_BLOCK_ADAPTERS:
        line_prefixes, block_pairs = LINE_AND_BLOCK_ADAPTERS[suffix]
        return count_block_comments(path, text, line_prefixes, block_pairs)
    if suffix in LINE_COMMENT_ADAPTERS:
        return count_line_comments(path, text, LINE_COMMENT_ADAPTERS[suffix])
    return None


def make_report(target: Path, stats: list[FileStats], skipped: list[SkippedFile]) -> str:
    total_effective = sum(item.effective for item in stats)
    total_lines = sum(item.total for item in stats)
    total_blank = sum(item.blank for item in stats)
    total_comment = sum(item.comment for item in stats)

    rows = [
        f"# {target.name} 代码行数统计",
        "",
        "## 汇总",
        "",
        f"- 统计目录: `{target}`",
        f"- 已统计文件数: `{len(stats)}`",
        f"- 全部文件总行数: `{total_lines}`",
        f"- 全部文件有效代码总行数: `{total_effective}`",
        f"- 全部文件空行数: `{total_blank}`",
        f"- 全部文件注释行数: `{total_comment}`",
        f"- 生成时间: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        "",
        "## 文件明细",
        "",
        "| 文件 | 总行数 | 有效行数 | 空行数 | 注释行数 |",
        "| --- | ---: | ---: | ---: | ---: |",
    ]

    for item in sorted(stats, key=lambda value: str(value.path.relative_to(target)).lower()):
        rel = str(item.path.relative_to(target)).replace("\\", "/")
        rows.append(f"| `{rel}` | {item.total} | {item.effective} | {item.blank} | {item.comment} |")

    if not stats:
        rows.append("| _没有发现已适配的代码文件_ | 0 | 0 | 0 | 0 |")

    if skipped:
        rows.extend(["", "## 未统计文件", "", "| 文件 | 原因 |", "| --- | --- |"])
        for item in sorted(skipped, key=lambda value: str(value.path.relative_to(target)).lower()):
            rel = str(item.path.relative_to(target)).replace("\\", "/")
            rows.append(f"| `{rel}` | {item.reason} |")
    else:
        rows.extend(["", "## 未统计文件", "", "无。"])

    return "\n".join(rows) + "\n"


def count_folder(target: Path) -> tuple[list[FileStats], list[SkippedFile]]:
    stats: list[FileStats] = []
    skipped: list[SkippedFile] = []

    for path in iter_files(target):
        try:
            text = read_text_lossless(path)
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


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="统计代码行数，并可生成软著程序鉴别材料。")
    parser.add_argument("folder", type=Path, help="要统计的文件夹路径")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd(),
        help="报告输出目录，默认是当前命令所在目录",
    )
    parser.add_argument(
        "--generate-docx",
        action="store_true",
        help="同时生成软著程序鉴别材料 Word 和全量代码 Word",
    )
    parser.add_argument(
        "--software-name",
        help="软件名称，生成 Word 材料时必填",
    )
    parser.add_argument(
        "--software-version",
        "--version",
        dest="software_version",
        default="V1.0",
        help="软件版本号，默认 V1.0",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    args = parse_args(sys.argv[1:] if argv is None else argv)
    target = args.folder.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    if not target.exists():
        print(f"错误: 文件夹不存在: {target}", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"错误: 目标不是文件夹: {target}", file=sys.stderr)
        return 2
    if args.generate_docx and (not args.software_name or not args.software_name.strip()):
        print("错误: 生成 Word 材料时必须提供 --software-name。", file=sys.stderr)
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)
    stats, skipped = count_folder(target)
    report = make_report(target, stats, skipped)
    report_path = output_dir / f"{target.name}.md"
    report_path.write_text(report, encoding="utf-8")

    total_effective = sum(item.effective for item in stats)
    print(f"统计完成: {target}")
    print(f"报告已生成: {report_path}")
    print(f"已统计文件数: {len(stats)}")
    print(f"全部文件有效代码总行数: {total_effective}")
    if skipped:
        print(f"未统计文件数: {len(skipped)}，详情见报告末尾。")

    if args.generate_docx:
        from software_copyright_toolkit.documents import generate_identification_documents

        documents = generate_identification_documents(
            target=target,
            output_dir=output_dir,
            software_name=args.software_name.strip(),
            version=args.software_version.strip() or "V1.0",
        )
        print(f"程序鉴别材料已生成: {documents.identification_docx}")
        print(f"全量代码 Word 已生成: {documents.full_docx}")
        print(f"程序鉴别材料源行数: {documents.identification_line_count}")
        print(f"全量代码源行数: {documents.source_line_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
