from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, cast

from software_copyright_toolkit.counter import count_folder
from software_copyright_toolkit.documents import (
    DEFAULT_SEPARATOR,
    DISCLAIMER_NOTE,
    generate_identification_documents,
    sanitize_filename,
)
from software_copyright_toolkit.report import make_report


class ToolkitApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Software Copyright Toolkit")
        self.geometry("720x510")
        self.minsize(680, 490)

        self.target_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd()))
        self.name_var = tk.StringVar()
        self.version_var = tk.StringVar(value="V1.0")
        self.separator_var = tk.StringVar(value=DEFAULT_SEPARATOR)
        self.generate_report_var = tk.BooleanVar(value=True)
        self.generate_identification_var = tk.BooleanVar(value=True)
        self.generate_full_var = tk.BooleanVar(value=True)
        self.status_var = tk.StringVar(value="请选择目标文件夹；生成 Word 时需要填写软件名称和版本号。")
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self.output_dir_for_open: Path | None = None
        self.build_ui()
        self.after(150, self.poll_result_queue)

    def build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        root = ttk.Frame(self, padding=20)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(1, weight=1)

        title = ttk.Label(root, text="软著材料生成工具", font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 18))

        ttk.Label(root, text="目标文件夹").grid(row=1, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.target_var).grid(row=1, column=1, sticky="ew", padx=10)
        ttk.Button(root, text="选择", command=self.choose_target).grid(row=1, column=2, sticky="ew")

        ttk.Label(root, text="输出目录").grid(row=2, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.output_var).grid(row=2, column=1, sticky="ew", padx=10)
        ttk.Button(root, text="选择", command=self.choose_output).grid(row=2, column=2, sticky="ew")

        ttk.Label(root, text="软件名称").grid(row=3, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.name_var).grid(row=3, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        ttk.Label(root, text="版本号").grid(row=4, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.version_var).grid(row=4, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        ttk.Label(root, text="文件分隔符").grid(row=5, column=0, sticky="w", pady=6)
        ttk.Entry(root, textvariable=self.separator_var).grid(row=5, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        actions = ttk.Frame(root)
        actions.grid(row=6, column=0, columnspan=3, sticky="ew", pady=(18, 12))
        actions.columnconfigure(0, weight=1)
        self.generate_button = ttk.Button(actions, text="生成材料", command=self.start_generation)
        self.generate_button.grid(row=0, column=0, sticky="ew")

        ttk.Label(root, text="将生成").grid(row=7, column=0, sticky="nw", pady=(12, 4))
        options = ttk.Frame(root)
        options.grid(row=7, column=1, columnspan=2, sticky="w", padx=(10, 0), pady=(8, 0))
        ttk.Checkbutton(options, text="代码行数统计 Markdown", variable=self.generate_report_var).grid(
            row=0, column=0, sticky="w", pady=2
        )
        ttk.Checkbutton(
            options, text="程序鉴别材料 Word（前后30页合并）", variable=self.generate_identification_var
        ).grid(row=1, column=0, sticky="w", pady=2)
        ttk.Checkbutton(options, text="全量代码 Word", variable=self.generate_full_var).grid(
            row=2, column=0, sticky="w", pady=2
        )

        ttk.Separator(root).grid(row=8, column=0, columnspan=3, sticky="ew", pady=16)

        status_row = ttk.Frame(root)
        status_row.grid(row=9, column=0, columnspan=3, sticky="ew")
        status_row.columnconfigure(0, weight=1)
        ttk.Label(status_row, textvariable=self.status_var, foreground="#2f5f8f").grid(row=0, column=0, sticky="w")
        self.open_dir_button = ttk.Button(
            status_row, text="打开输出目录", command=self.open_output_dir, state="disabled"
        )
        self.open_dir_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

    def choose_target(self) -> None:
        folder = filedialog.askdirectory(title="选择要统计和整理的代码文件夹")
        if folder:
            self.target_var.set(folder)
            if self.output_var.get() == str(Path.cwd()):
                self.output_var.set(str(Path(folder).resolve().parent))

    def choose_output(self) -> None:
        folder = filedialog.askdirectory(title="选择输出目录")
        if folder:
            self.output_var.set(folder)

    def open_output_dir(self) -> None:
        if self.output_dir_for_open is None or not self.output_dir_for_open.exists():
            return
        path_str = str(self.output_dir_for_open.resolve())
        if sys.platform == "win32":
            os.startfile(path_str)
        elif sys.platform == "darwin":
            subprocess.run(["open", path_str], check=False)
        else:
            subprocess.run(["xdg-open", path_str], check=False)

    def start_generation(self) -> None:
        try:
            target, output_dir, software_name, version, separator, selections = self.validate_inputs()
        except ValueError as exc:
            messagebox.showwarning("需要补充信息", str(exc))
            return

        self.generate_button.configure(state="disabled")
        self.status_var.set("正在生成，请稍候...")
        thread = threading.Thread(
            target=self.generate_files,
            args=(target, output_dir, software_name, version, separator, selections),
            daemon=True,
        )
        thread.start()

    def validate_inputs(self) -> tuple[Path, Path, str, str, str, dict[str, bool]]:
        target = Path(self.target_var.get()).expanduser()
        output_dir = Path(self.output_var.get()).expanduser()
        software_name = self.name_var.get().strip()
        version = self.version_var.get().strip()
        separator = self.separator_var.get().strip() or DEFAULT_SEPARATOR
        selections = {
            "report": self.generate_report_var.get(),
            "identification": self.generate_identification_var.get(),
            "full": self.generate_full_var.get(),
        }

        if not target.exists() or not target.is_dir():
            raise ValueError("请选择有效的目标文件夹。")
        if not any(selections.values()):
            raise ValueError("请至少选择一种要生成的文件。")
        if (selections["identification"] or selections["full"]) and not software_name:
            raise ValueError("请输入软件名称。")
        if (selections["identification"] or selections["full"]) and not version:
            raise ValueError("请输入版本号。")

        return target.resolve(), output_dir.resolve(), software_name, version, separator, selections

    def generate_files(
        self,
        target: Path,
        output_dir: Path,
        software_name: str,
        version: str,
        separator: str,
        selections: dict[str, bool],
    ) -> None:
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            generated_files: list[Path] = []
            stats_count = skipped_count = effective = 0
            source_lines = identification_lines = 0

            if selections["report"]:
                stats, skipped = count_folder(target)
                stats_count = len(stats)
                skipped_count = len(skipped)
                effective = sum(item.effective for item in stats)
                report = make_report(target, stats, skipped)
                report_prefix = (
                    f"{sanitize_filename(software_name)}_{sanitize_filename(version)}"
                    if software_name and version
                    else sanitize_filename(target.name)
                )
                report_path = output_dir / f"{report_prefix}_代码行数统计.md"
                report_path.write_text(report, encoding="utf-8")
                generated_files.append(report_path)

            if selections["identification"] or selections["full"]:
                documents = generate_identification_documents(
                    target,
                    output_dir,
                    software_name,
                    version,
                    include_identification=selections["identification"],
                    include_full=selections["full"],
                    separator_template=separator,
                )
                source_lines = documents.source_content_line_count
                identification_lines = documents.identification_content_line_count
                if documents.identification_docx is not None:
                    generated_files.append(documents.identification_docx)
                if documents.full_docx is not None:
                    generated_files.append(documents.full_docx)

            payload = {
                "files": generated_files,
                "output_dir": output_dir,
                "selections": selections,
                "stats_count": stats_count,
                "skipped_count": skipped_count,
                "effective": effective,
                "source_lines": source_lines,
                "identification_lines": identification_lines,
            }
            self.result_queue.put(("success", payload))
        except Exception as exc:
            self.result_queue.put(("error", exc))

    def poll_result_queue(self) -> None:
        try:
            kind, payload = self.result_queue.get_nowait()
        except queue.Empty:
            self.after(150, self.poll_result_queue)
            return

        self.generate_button.configure(state="normal")
        if kind == "success":
            data = cast("dict[str, Any]", payload)
            if data["selections"]["report"] and (data["selections"]["identification"] or data["selections"]["full"]):
                self.status_var.set(
                    f"生成完成：统计 {data['stats_count']} 个文件，"
                    f"有效代码 {data['effective']} 行，鉴别材料代码/注释 {data['identification_lines']} 行。"
                )
            elif data["selections"]["report"]:
                self.status_var.set(f"生成完成：统计 {data['stats_count']} 个文件，有效代码 {data['effective']} 行。")
            else:
                self.status_var.set(f"生成完成：共生成 {len(data['files'])} 个文件。")
            file_list = "\n".join(str(path) for path in data["files"])
            skipped_note = (
                f"\n\n未统计文件数：{data['skipped_count']}，详情见 Markdown 报告。" if data["skipped_count"] else ""
            )
            messagebox.showinfo(
                "生成完成",
                f"已生成：\n{file_list}{skipped_note}\n\n{DISCLAIMER_NOTE}",
            )
            self.output_dir_for_open = data.get("output_dir")
            if self.output_dir_for_open:
                self.open_dir_button.configure(state="normal")
        else:
            self.status_var.set("生成失败。")
            messagebox.showerror("生成失败", str(payload))

        self.after(150, self.poll_result_queue)


def main() -> None:
    app = ToolkitApp()
    app.mainloop()


if __name__ == "__main__":
    main()
