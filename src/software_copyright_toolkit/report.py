"""Markdown 报告生成模块。

负责将统计结果格式化为 Markdown 报告字符串。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from software_copyright_toolkit.counter import FileStats, SkippedFile


def make_report(target: Path, stats: list[FileStats], skipped: list[SkippedFile]) -> str:
    """生成 Markdown 格式的代码行数统计报告。

    Args:
        target: 统计的目标文件夹。
        stats: 已统计的文件列表。
        skipped: 被跳过的文件列表。
    """
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
