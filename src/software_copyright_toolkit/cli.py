"""CLI 参数解析与入口调度模块。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from software_copyright_toolkit.controller import (
    TaskConfig,
    run_generation,
    validate_task_config,
)
from software_copyright_toolkit.counter import count_folder
from software_copyright_toolkit.documents import DISCLAIMER_NOTE
from software_copyright_toolkit.report import make_report


def parse_args(argv: list[str]) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="统计代码行数，并可生成软著程序鉴别材料。",
    )
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
    parser.add_argument(
        "--separator",
        default="===== 文件: {path} =====",
        help=(
            "文件分隔符模板，{path} 会被替换为文件相对路径。"
            "例如 '// --- File: {path} ---'。"
            "默认: '===== 文件: {path} ====='"
        ),
    )
    parser.add_argument(
        "--use-streaming",
        action="store_true",
        help="使用流式读取模式统计代码（对大文件更友好，但速度略慢）",
    )
    parser.add_argument(
        "--lang-config",
        type=Path,
        default=None,
        help="自定义语言配置文件路径（TOML 格式）",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI 主入口。

    Returns:
        int: 0 成功，1 生成失败，2 参数/路径错误。
    """
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")

    args = parse_args(sys.argv[1:] if argv is None else argv)
    target = args.folder.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()

    # --- 输入验证 ---
    if not target.exists():
        print(f"错误: 文件夹不存在: {target}", file=sys.stderr)
        return 2
    if not target.is_dir():
        print(f"错误: 目标不是文件夹: {target}", file=sys.stderr)
        return 2
    if args.generate_docx and (not args.software_name or not args.software_name.strip()):
        print("错误: 生成 Word 材料时必须提供 --software-name。", file=sys.stderr)
        return 2

    # --- 快速预览 ---
    if not args.generate_docx:
        stats, skipped = count_folder(
            target,
            use_streaming=args.use_streaming,
        )
        total_effective = sum(item.effective for item in stats)
        report = make_report(target, stats, skipped)
        report_path = output_dir / f"{target.name}.md"
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path.write_text(report, encoding="utf-8")

        print(f"统计完成: {target}")
        print(f"报告已生成: {report_path}")
        print(f"已统计文件数: {len(stats)}")
        print(f"全部文件有效代码总行数: {total_effective}")
        if skipped:
            print(f"未统计文件数: {len(skipped)}，详情见报告末尾。")
        return 0

    # --- 使用 controller 执行 Word 生成 ---
    config = TaskConfig(
        target=target,
        output_dir=output_dir,
        software_name=args.software_name.strip(),
        version=args.software_version.strip() or "V1.0",
        separator=args.separator,
        generate_report=True,
        generate_identification=True,
        generate_full=True,
    )

    errors = validate_task_config(config)
    if errors:
        for err in errors:
            print(f"错误: {err}", file=sys.stderr)
        return 2

    try:
        result = run_generation(config)
    except ValueError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        return 1

    # 输出结果
    print(f"统计完成: {target}")
    print(f"已统计文件数: {result.stats_count}")
    print(f"全部文件有效代码总行数: {result.effective_lines}")
    if result.skipped_count:
        print(f"未统计文件数: {result.skipped_count}，详情见报告末尾。")

    if result.generated_files:
        for f in result.generated_files:
            print(f"已生成: {f}")
        print(f"程序鉴别材料 Word 可见行数: {result.identification_content_lines}")
        print(f"全量代码有效代码及注释行数: {result.source_content_lines}")

    # 输出警告
    if result.warnings:
        print("\n⚠ 警告:", file=sys.stderr)
        for w in result.warnings:
            print(f"  - {w}", file=sys.stderr)

    print(f"\n{DISCLAIMER_NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
