"""Software Copyright Toolkit — 代码行数统计与软著程序鉴别材料生成工具。

公共 API 重导出，保持向后兼容。
"""

from software_copyright_toolkit.adapters import (
    HTML_LIKE_EXTENSIONS,
    LINE_AND_BLOCK_ADAPTERS,
    LINE_COMMENT_ADAPTERS,
    NO_COMMENT_EXTENSIONS,
    PYTHON_EXTENSIONS,
    normalize_suffix,
)
from software_copyright_toolkit.cli import main, parse_args
from software_copyright_toolkit.counter import (
    FileStats,
    SkippedFile,
    count_block_comments,
    count_folder,
    count_line_comments,
    count_python,
    count_supported_file,
)
from software_copyright_toolkit.report import make_report
from software_copyright_toolkit.scanner import (
    SKIP_DIRS,
    iter_files,
    read_lines_lazy,
    read_text_lossless,
)

__all__ = [
    # adapters
    "HTML_LIKE_EXTENSIONS",
    "LINE_AND_BLOCK_ADAPTERS",
    "LINE_COMMENT_ADAPTERS",
    "NO_COMMENT_EXTENSIONS",
    "PYTHON_EXTENSIONS",
    "normalize_suffix",
    # cli
    "main",
    "parse_args",
    # counter
    "FileStats",
    "SkippedFile",
    "count_block_comments",
    "count_folder",
    "count_line_comments",
    "count_python",
    "count_supported_file",
    # report
    "make_report",
    # scanner
    "SKIP_DIRS",
    "iter_files",
    "read_lines_lazy",
    "read_text_lossless",
]
