"""业务逻辑控制器模块。

从 GUI 和 CLI 中抽取的共享业务逻辑，可独立测试，不依赖 UI 框架。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from software_copyright_toolkit.counter import count_folder
from software_copyright_toolkit.documents import (
    DISCLAIMER_NOTE,
    generate_identification_documents,
    sanitize_filename,
)
from software_copyright_toolkit.report import make_report

# 软著申请推荐的最少页数
MIN_RECOMMENDED_PAGES = 60
# 每页约 50 行
LINES_PER_PAGE = 50
# 推荐的最少行数
MIN_RECOMMENDED_LINES = MIN_RECOMMENDED_PAGES * LINES_PER_PAGE


@dataclass(frozen=True)
class TaskConfig:
    """任务配置，封装所有生成参数。"""

    target: Path
    output_dir: Path
    software_name: str
    version: str
    separator: str
    generate_report: bool
    generate_identification: bool
    generate_full: bool
    selected_paths: frozenset[Path] | None = None


@dataclass(frozen=True)
class AnalysisPreview:
    """分析预览信息，在生成前显示给用户。"""

    file_count: int
    total_lines: int
    effective_lines: int
    language_summary: dict[str, int]


@dataclass(frozen=True)
class GenerationResult:
    """生成结果。"""

    generated_files: list[Path]
    output_dir: Path
    stats_count: int
    skipped_count: int
    effective_lines: int
    source_content_lines: int
    identification_content_lines: int
    warnings: list[str]


def validate_task_config(config: TaskConfig) -> list[str]:
    """验证任务配置，返回错误信息列表（空列表表示通过）。"""
    errors: list[str] = []

    if not config.target.exists() or not config.target.is_dir():
        errors.append("目标文件夹不存在或不是有效目录。")
    if not config.generate_report and not config.generate_identification and not config.generate_full:
        errors.append("请至少选择一种要生成的文件。")
    if (config.generate_identification or config.generate_full) and not config.software_name:
        errors.append("生成 Word 材料时需要填写软件名称。")
    if (config.generate_identification or config.generate_full) and not config.version:
        errors.append("生成 Word 材料时需要填写版本号。")

    return errors


def preview_analysis(
    target: Path,
    *,
    use_charset_normalizer: bool = True,
) -> AnalysisPreview:
    """预览分析结果，不生成任何文件。

    用于在 GUI 中显示文件发现信息。
    """
    stats, _ = count_folder(target, use_charset_normalizer=use_charset_normalizer)
    total_lines = sum(s.total for s in stats)
    effective_lines = sum(s.effective for s in stats)

    # 统计语言分布
    language_summary: dict[str, int] = {}
    for s in stats:
        suffix = s.path.suffix.lower() or "(无后缀)"
        language_summary[suffix] = language_summary.get(suffix, 0) + 1

    return AnalysisPreview(
        file_count=len(stats),
        total_lines=total_lines,
        effective_lines=effective_lines,
        language_summary=language_summary,
    )


def estimate_pages(effective_lines: int) -> int:
    """估算代码行对应的页数。"""
    return max(1, (effective_lines + LINES_PER_PAGE - 1) // LINES_PER_PAGE)


def run_generation(config: TaskConfig) -> GenerationResult:
    """执行完整的生成流程。

    这是从 GUI 和 CLI 共享的核心业务逻辑。
    """
    config.output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: list[Path] = []
    stats_count = 0
    skipped_count = 0
    effective_lines = 0
    source_content_lines = 0
    identification_content_lines = 0
    result_warnings: list[str] = []

    if config.generate_report:
        stats, skipped = count_folder(config.target, include_paths=config.selected_paths)
        stats_count = len(stats)
        skipped_count = len(skipped)
        effective_lines = sum(item.effective for item in stats)
        report = make_report(config.target, stats, skipped)
        report_prefix = (
            f"{sanitize_filename(config.software_name)}_{sanitize_filename(config.version)}"
            if config.software_name and config.version
            else sanitize_filename(config.target.name)
        )
        report_path = config.output_dir / f"{report_prefix}_代码行数统计.md"
        report_path.write_text(report, encoding="utf-8")
        generated_files.append(report_path)

    if config.generate_identification or config.generate_full:
        documents = generate_identification_documents(
            config.target,
            config.output_dir,
            config.software_name,
            config.version,
            include_identification=config.generate_identification,
            include_full=config.generate_full,
            separator_template=config.separator,
            include_paths=config.selected_paths,
        )
        source_content_lines = documents.source_content_line_count
        identification_content_lines = documents.identification_content_line_count

        if documents.identification_docx is not None:
            generated_files.append(documents.identification_docx)
        if documents.full_docx is not None:
            generated_files.append(documents.full_docx)

        # 页数校验警告
        estimated_pages = estimate_pages(identification_content_lines)
        if estimated_pages < MIN_RECOMMENDED_PAGES and config.generate_identification:
            result_warnings.append(
                f"生成文档约 {estimated_pages} 页，软著申请通常要求不少于 {MIN_RECOMMENDED_PAGES} 页。"
                f"建议检查源代码目录或调整 --separator 参数。"
            )

    return GenerationResult(
        generated_files=generated_files,
        output_dir=config.output_dir,
        stats_count=stats_count,
        skipped_count=skipped_count,
        effective_lines=effective_lines,
        source_content_lines=source_content_lines,
        identification_content_lines=identification_content_lines,
        warnings=result_warnings,
    )


def format_success_message(result: GenerationResult, config: TaskConfig) -> str:
    """格式化成功消息。"""
    parts: list[str] = []

    if config.generate_report and (config.generate_identification or config.generate_full):
        parts.append(
            f"统计 {result.stats_count} 个文件，"
            f"有效代码 {result.effective_lines} 行，"
            f"鉴别材料代码/注释 {result.identification_content_lines} 行。"
        )
    elif config.generate_report:
        parts.append(f"统计 {result.stats_count} 个文件，有效代码 {result.effective_lines} 行。")
    else:
        parts.append(f"共生成 {len(result.generated_files)} 个文件。")

    if result.skipped_count:
        parts.append(f"未统计文件数：{result.skipped_count}，详情见 Markdown 报告。")

    file_list = "\n".join(str(path) for path in result.generated_files)
    parts.append(f"\n已生成：\n{file_list}")
    parts.append(f"\n{DISCLAIMER_NOTE}")

    if result.warnings:
        parts.append("\n⚠ 警告：")
        parts.extend(f"  - {w}" for w in result.warnings)

    return "\n".join(parts)
