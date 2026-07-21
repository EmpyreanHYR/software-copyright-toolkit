"""CLI 参数解析与入口调度模块。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from software_copyright_toolkit.counter import count_folder
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
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """CLI 主入口。

    Returns:
        int: 0 成功，2 参数/路径错误。
    """
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
    stats, skipped = count_folder(
        target,
        use_streaming=args.use_streaming,
    )
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
            separator_template=args.separator,
        )
        print(f"程序鉴别材料已生成: {documents.identification_docx}")
        print(f"全量代码 Word 已生成: {documents.full_docx}")
        print(f"程序鉴别材料 Word 可见行数: {documents.identification_line_count}")
        print(f"程序鉴别材料有效代码及注释行数: {documents.identification_content_line_count}")
        print(f"全量代码有效代码及注释行数: {documents.source_content_line_count}")
        from software_copyright_toolkit.documents import DISCLAIMER_NOTE

        print(f"\n{DISCLAIMER_NOTE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
