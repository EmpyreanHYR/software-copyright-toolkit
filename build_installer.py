"""PyInstaller 打包脚本。

使用 PyInstaller 将 CLI 和 GUI 打包为独立可执行文件。

用法:
    python build_installer.py          # 打包当前平台
    python build_installer.py --all    # 打包所有 CLI + GUI
    python build_installer.py --cli    # 仅打包 CLI
    python build_installer.py --gui    # 仅打包 GUI
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

# 确保 Windows 下 print 中文不崩溃
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"


def _suffix_name(base: str, suffix: str | None) -> str:
    """构造带版本后缀的文件名。"""
    if suffix:
        return f"{base}-{suffix}"
    return base


def build_cli(suffix: str | None = None) -> Path:
    """打包 CLI 为单文件 exe。"""
    name = _suffix_name("sct-cli", suffix)
    print(f"Building CLI ({name})...")
    subprocess.run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--onefile",
            "--name",
            name,
            "--distpath",
            str(DIST),
            "--workpath",
            str(ROOT / "build" / "pyinstaller"),
            "--specpath",
            str(ROOT / "build" / "pyinstaller"),
            str(ROOT / "src" / "software_copyright_toolkit" / "cli.py"),
        ],
        check=True,
    )
    exe_ext = ".exe" if sys.platform == "win32" else ""
    return DIST / f"{name}{exe_ext}"


def build_gui(suffix: str | None = None) -> Path:
    """打包 GUI 为单文件 exe（Windows 下无控制台窗口）。"""
    name = _suffix_name("sct-gui", suffix)
    print(f"Building GUI ({name})...")
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        name,
        "--distpath",
        str(DIST),
        "--workpath",
        str(ROOT / "build" / "pyinstaller"),
        "--specpath",
        str(ROOT / "build" / "pyinstaller"),
    ]
    if sys.platform == "win32":
        args.append("--noconsole")
    args.append(str(ROOT / "src" / "software_copyright_toolkit" / "gui.py"))
    subprocess.run(args, check=True)
    exe_ext = ".exe" if sys.platform == "win32" else ""
    return DIST / f"{name}{exe_ext}"


def clean() -> None:
    """清理构建产物。"""
    for path in (ROOT / "build" / "pyinstaller", DIST):
        if path.exists():
            shutil.rmtree(path)
    for spec in ROOT.glob("*.spec"):
        spec.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="PyInstaller 打包脚本")
    parser.add_argument("--all", action="store_true", help="打包 CLI 和 GUI")
    parser.add_argument("--cli", action="store_true", help="仅打包 CLI")
    parser.add_argument("--gui", action="store_true", help="仅打包 GUI")
    parser.add_argument("--clean", action="store_true", help="清理构建产物")
    parser.add_argument("--suffix", help="版本后缀，如 v1.0.0，生成 sct-cli-v1.0.0.exe")
    args = parser.parse_args()

    if args.clean:
        clean()
        print("构建产物已清理。")
        return

    if not any([args.all, args.cli, args.gui]):
        args.all = True  # 默认全部

    DIST.mkdir(parents=True, exist_ok=True)

    if args.all or args.cli:
        cli_path = build_cli(suffix=args.suffix)
        print(f"CLI 已打包: {cli_path}")

    if args.all or args.gui:
        gui_path = build_gui(suffix=args.suffix)
        print(f"GUI 已打包: {gui_path}")

    print("\n打包完成！可执行文件位于 dist/ 目录。")


if __name__ == "__main__":
    main()
