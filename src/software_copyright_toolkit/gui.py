"""Tkinter GUI 模块。

提供可视化的软著材料生成界面，业务逻辑委托给 controller 模块。
"""

from __future__ import annotations

import os
import queue
import random
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, cast

from software_copyright_toolkit.controller import (
    TaskConfig,
    format_success_message,
    run_generation,
    validate_task_config,
)
from software_copyright_toolkit.documents import DEFAULT_SEPARATOR, FRONT_BACK_PAGES
from software_copyright_toolkit.file_selector import ask_selected_files


class ToolkitApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Software Copyright Toolkit")
        self.geometry("740x630")
        self.minsize(680, 560)

        self.target_var = tk.StringVar()
        self.output_var = tk.StringVar(value=str(Path.cwd()))
        self.name_var = tk.StringVar()
        self.version_var = tk.StringVar(value="V1.0")
        self.separator_var = tk.StringVar(value=DEFAULT_SEPARATOR)
        self.seed_var = tk.StringVar(value="")
        self.pages_var = tk.StringVar(value=str(FRONT_BACK_PAGES))

        self.generate_report_var = tk.BooleanVar(value=True)
        self.generate_identification_var = tk.BooleanVar(value=True)
        self.generate_full_var = tk.BooleanVar(value=True)
        self.generate_docx_var = tk.BooleanVar(value=True)
        self.generate_pdf_var = tk.BooleanVar(value=True)

        self.status_var = tk.StringVar(value="请选择目标文件夹；生成材料时需要填写软件名称和版本号。")
        self.result_queue: queue.Queue[tuple[str, object]] = queue.Queue()

        self._selected_paths: set[Path] | None = None
        self._selection_summary_var = tk.StringVar(value="")

        self.output_dir_for_open: Path | None = None
        self.build_ui()
        self.after(150, self.poll_result_queue)

    def build_ui(self) -> None:
        self.columnconfigure(0, weight=1)
        root = ttk.Frame(self, padding=20)
        root.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(1, weight=1)

        title = ttk.Label(root, text="软著材料生成工具", font=("Arial", 16, "bold"))
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 14))

        # 1. 目标文件夹
        ttk.Label(root, text="目标文件夹").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(root, textvariable=self.target_var).grid(row=1, column=1, sticky="ew", padx=10)
        ttk.Button(root, text="选择", command=self.choose_target).grid(row=1, column=2, sticky="ew")

        # 2. 文件选择
        file_sel_row = ttk.Frame(root)
        file_sel_row.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(0, 5))
        file_sel_row.columnconfigure(1, weight=1)
        self._file_sel_button = ttk.Button(
            file_sel_row, text="选择文件...", command=self.choose_files, state="disabled"
        )
        self._file_sel_button.grid(row=0, column=0, sticky="w")
        ttk.Label(file_sel_row, textvariable=self._selection_summary_var, foreground="#2f5f8f").grid(
            row=0, column=1, sticky="w", padx=(10, 0)
        )

        # 3. 输出目录
        ttk.Label(root, text="输出目录").grid(row=3, column=0, sticky="w", pady=5)
        ttk.Entry(root, textvariable=self.output_var).grid(row=3, column=1, sticky="ew", padx=10)
        ttk.Button(root, text="选择", command=self.choose_output).grid(row=3, column=2, sticky="ew")

        # 4. 软件名称
        ttk.Label(root, text="软件名称").grid(row=4, column=0, sticky="w", pady=5)
        ttk.Entry(root, textvariable=self.name_var).grid(row=4, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        # 5. 版本号与单段页数
        ver_page_row = ttk.Frame(root)
        ver_page_row.grid(row=5, column=0, columnspan=3, sticky="ew", pady=5)
        ver_page_row.columnconfigure(1, weight=1)
        ver_page_row.columnconfigure(3, weight=1)

        ttk.Label(ver_page_row, text="版本号").grid(row=0, column=0, sticky="w")
        ttk.Entry(ver_page_row, textvariable=self.version_var).grid(row=0, column=1, sticky="ew", padx=(10, 20))

        ttk.Label(ver_page_row, text="单段页数").grid(row=0, column=2, sticky="w")
        page_box = ttk.Combobox(
            ver_page_row,
            textvariable=self.pages_var,
            values=["30", "60"],
            width=8,
            state="readonly",
        )
        page_box.grid(row=0, column=3, sticky="w", padx=(10, 0))
        ttk.Label(ver_page_row, text="页（默认前后各30页，共60页）", foreground="#666666").grid(
            row=0, column=4, sticky="w", padx=(6, 0)
        )

        # 6. 文件分隔符
        ttk.Label(root, text="文件分隔符").grid(row=6, column=0, sticky="w", pady=5)
        ttk.Entry(root, textvariable=self.separator_var).grid(row=6, column=1, columnspan=2, sticky="ew", padx=(10, 0))

        # 7. 随机种子打乱
        seed_row = ttk.Frame(root)
        seed_row.grid(row=7, column=0, columnspan=3, sticky="ew", pady=5)
        seed_row.columnconfigure(1, weight=1)

        ttk.Label(seed_row, text="随机种子").grid(row=0, column=0, sticky="w")
        ttk.Entry(seed_row, textvariable=self.seed_var).grid(row=0, column=1, sticky="ew", padx=(10, 10))
        ttk.Button(seed_row, text="随机生成", command=self.generate_random_seed).grid(row=0, column=2, sticky="ew")
        ttk.Label(seed_row, text="（固定打乱拼接顺序，不改动磁盘源码）", foreground="#666666").grid(
            row=0, column=3, sticky="w", padx=(10, 0)
        )

        # 8. 生成格式与内容选项
        ttk.Label(root, text="将生成").grid(row=8, column=0, sticky="nw", pady=(10, 4))
        options = ttk.Frame(root)
        options.grid(row=8, column=1, columnspan=2, sticky="w", padx=(10, 0), pady=(6, 0))

        # 内容行
        ttk.Checkbutton(options, text="程序鉴别材料（前后连续页）", variable=self.generate_identification_var).grid(
            row=0, column=0, sticky="w", pady=2, padx=(0, 15)
        )
        ttk.Checkbutton(options, text="全量代码", variable=self.generate_full_var).grid(
            row=0, column=1, sticky="w", pady=2, padx=(0, 15)
        )
        ttk.Checkbutton(options, text="代码统计 Markdown", variable=self.generate_report_var).grid(
            row=0, column=2, sticky="w", pady=2
        )

        # 格式行
        ttk.Label(options, text="导出格式：", foreground="#2f5f8f").grid(row=1, column=0, sticky="w", pady=(6, 2))
        fmt_frame = ttk.Frame(options)
        fmt_frame.grid(row=1, column=1, columnspan=2, sticky="w", pady=(6, 2))
        ttk.Checkbutton(fmt_frame, text="Word (.docx)", variable=self.generate_docx_var).grid(
            row=0, column=0, sticky="w", padx=(0, 20)
        )
        ttk.Checkbutton(fmt_frame, text="PDF (.pdf)", variable=self.generate_pdf_var).grid(row=0, column=1, sticky="w")

        # 9. 按钮
        actions = ttk.Frame(root)
        actions.grid(row=9, column=0, columnspan=3, sticky="ew", pady=(14, 10))
        actions.columnconfigure(0, weight=1)
        self.generate_button = ttk.Button(actions, text="生成材料", command=self.start_generation)
        self.generate_button.grid(row=0, column=0, sticky="ew")

        ttk.Separator(root).grid(row=10, column=0, columnspan=3, sticky="ew", pady=10)

        # 10. 状态栏
        status_row = ttk.Frame(root)
        status_row.grid(row=11, column=0, columnspan=3, sticky="ew")
        status_row.columnconfigure(0, weight=1)
        ttk.Label(status_row, textvariable=self.status_var, foreground="#2f5f8f").grid(row=0, column=0, sticky="w")
        self.open_dir_button = ttk.Button(
            status_row, text="打开输出目录", command=self.open_output_dir, state="disabled"
        )
        self.open_dir_button.grid(row=0, column=1, sticky="e", padx=(10, 0))

    def generate_random_seed(self) -> None:
        """随机生成一个整数种子。"""
        new_seed = random.randint(1000, 999999)
        self.seed_var.set(str(new_seed))

    def choose_target(self) -> None:
        folder = filedialog.askdirectory(title="选择要统计和整理的代码文件夹")
        if folder:
            self.target_var.set(folder)
            self._selected_paths = None
            self._selection_summary_var.set("")
            self._file_sel_button.configure(state="normal")
            if self.output_var.get() == str(Path.cwd()):
                self.output_var.set(str(Path(folder).resolve().parent))

    def choose_files(self) -> None:
        target = self.target_var.get().strip()
        if not target or not Path(target).is_dir():
            messagebox.showwarning("提示", "请先选择一个有效的目标文件夹。")
            return
        selected = ask_selected_files(self, Path(target).resolve())
        if selected is not None:
            self._selected_paths = selected
            if selected:
                self._selection_summary_var.set(f"已选择 {len(selected)} 个文件")
            else:
                self._selection_summary_var.set("未选择任何文件（将统计全部）")
                self._selected_paths = None

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

    def _build_config(self) -> TaskConfig:
        target = Path(self.target_var.get()).expanduser()
        output_dir = Path(self.output_var.get()).expanduser()
        selected = frozenset(self._selected_paths) if self._selected_paths else None

        seed_str = self.seed_var.get().strip()
        seed_val = int(seed_str) if seed_str.isdigit() else None

        pages_str = self.pages_var.get().strip()
        pages_val = int(pages_str) if pages_str.isdigit() else FRONT_BACK_PAGES

        return TaskConfig(
            target=target.resolve(),
            output_dir=output_dir.resolve(),
            software_name=self.name_var.get().strip(),
            version=self.version_var.get().strip(),
            separator=self.separator_var.get().strip() or DEFAULT_SEPARATOR,
            generate_report=self.generate_report_var.get(),
            generate_identification=self.generate_identification_var.get(),
            generate_full=self.generate_full_var.get(),
            generate_docx=self.generate_docx_var.get(),
            generate_pdf=self.generate_pdf_var.get(),
            selected_paths=selected,
            seed=seed_val,
            pages_per_section=pages_val,
        )

    def start_generation(self) -> None:
        config = self._build_config()
        errors = validate_task_config(config)
        if errors:
            messagebox.showwarning("需要补充信息", "\n".join(errors))
            return

        self.generate_button.configure(state="disabled")
        self.status_var.set("正在生成，请稍候...")
        thread = threading.Thread(
            target=self._generate_in_background,
            args=(config,),
            daemon=True,
        )
        thread.start()

    def _generate_in_background(self, config: TaskConfig) -> None:
        try:
            result = run_generation(config)
            self.result_queue.put(("success", (result, config)))
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
            result, config = cast("tuple[Any, Any]", payload)
            message = format_success_message(result, config)
            self.status_var.set(
                f"生成完成：统计 {result.stats_count} 个文件，有效代码 {result.effective_lines} 行。"
                if result.stats_count
                else f"生成完成：共生成 {len(result.generated_files)} 个文件。"
            )
            messagebox.showinfo("生成完成", message)
            self.output_dir_for_open = result.output_dir
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
