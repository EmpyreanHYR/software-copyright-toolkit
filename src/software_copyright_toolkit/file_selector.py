"""文件树选择对话框。

提供可视化勾选界面，让用户在选定文件夹后进一步筛选要纳入统计的子文件夹和文件。
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from software_copyright_toolkit.scanner import iter_files

# 节点状态常量
_CHECKED = "checked"
_UNCHECKED = "unchecked"
_PARTIAL = "partial"

# 勾选符号
_ICON_CHECKED = "☑"
_ICON_UNCHECKED = "☐"
_ICON_PARTIAL = "☒"


class FileSelectorDialog(tk.Toplevel):
    """模态文件树选择对话框。

    用法::

        dialog = FileSelectorDialog(parent, root_folder)
        selected = dialog.result  # set[Path] | None (取消)

    功能：
    - 树形视图展示目录结构（自动跳过 .git/node_modules 等）
    - 每个节点前显示勾选框：☑ 绿色 / ☐ 灰色 / ☒ 黄色
    - 展开/折叠箭头与勾选操作分离，互不干扰
    - 父子联动：勾选父节点 → 所有子节点全选；取消同理
    - 子节点变化 → 父节点自动变为部分选或全选
    - 全选/取消全选/展开/折叠按钮
    - 显示已选文件数量
    """

    def __init__(
        self,
        parent: tk.Tk,
        root_folder: Path,
        *,
        title: str = "选择要统计的文件和文件夹",
    ) -> None:
        super().__init__(parent)
        self.title(title)
        self.geometry("800x600")
        self.minsize(600, 400)
        self.transient(parent)
        self.grab_set()

        self._root_folder = root_folder.resolve()
        self.result: set[Path] | None = None

        # iid → Path 映射
        self._iid_to_path: dict[str, Path] = {}
        # iid → 是否为文件夹
        self._iid_is_dir: dict[str, bool] = {}
        # iid → 检查状态
        self._checked: dict[str, str] = {}
        # 父子关系：child_iid → parent_iid
        self._parent_map: dict[str, str] = {}
        # 子节点列表：parent_iid → list[child_iid]
        self._children_map: dict[str, list[str]] = {}

        self._build_ui()
        self._populate_tree()
        self._update_status()

        # 居中显示
        self.update_idletasks()
        parent_x = parent.winfo_rootx()
        parent_y = parent.winfo_rooty()
        parent_w = parent.winfo_width()
        parent_h = parent.winfo_height()
        w = self.winfo_width()
        h = self.winfo_height()
        x = parent_x + (parent_w - w) // 2
        y = parent_y + (parent_h - h) // 2
        self.geometry(f"+{x}+{y}")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
        self.wait_window()

    def _build_ui(self) -> None:
        """构建 UI 布局。"""
        main = ttk.Frame(self, padding=10)
        main.pack(fill="both", expand=True)

        # 顶部说明
        info = ttk.Label(
            main,
            text=f"根目录: {self._root_folder}\n勾选要纳入统计的文件夹和文件，父子节点自动联动。",
            foreground="#2f5f8f",
        )
        info.pack(fill="x", pady=(0, 8))

        # 工具栏
        toolbar = ttk.Frame(main)
        toolbar.pack(fill="x", pady=(0, 4))
        ttk.Button(toolbar, text="全选", command=self._check_all).pack(side="left", padx=(0, 4))
        ttk.Button(toolbar, text="取消全选", command=self._uncheck_all).pack(side="left", padx=(0, 4))
        ttk.Button(toolbar, text="展开全部", command=self._expand_all).pack(side="left", padx=(0, 4))
        ttk.Button(toolbar, text="折叠全部", command=self._collapse_all).pack(side="left", padx=(0, 4))

        # 树形视图容器
        tree_frame = ttk.Frame(main)
        tree_frame.pack(fill="both", expand=True)

        self._tree = ttk.Treeview(tree_frame, selectmode="none", show="tree")
        # 滚动条
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self._tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self._tree.xview)
        self._tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # 替换默认绑定，手动控制展开/勾选行为
        self._tree.bind("<Button-1>", self._on_click)

        # 底部状态栏和按钮
        bottom = ttk.Frame(main)
        bottom.pack(fill="x", pady=(8, 0))

        self._status_var = tk.StringVar()
        ttk.Label(bottom, textvariable=self._status_var, foreground="#2f5f8f").pack(side="left")

        btn_frame = ttk.Frame(bottom)
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="确定", command=self._on_confirm).pack(side="left", padx=(0, 8))
        ttk.Button(btn_frame, text="取消", command=self._on_cancel).pack(side="left")

    def _populate_tree(self) -> None:
        """扫描目录并构建树。"""
        self._next_iid = 0
        self._path_to_iid_map: dict[Path, str] = {}

        # 根节点
        root_iid = self._new_iid(self._root_folder, is_dir=True)
        self._root_iid = root_iid
        self._checked[root_iid] = _CHECKED
        self._children_map[root_iid] = []
        self._tree.insert("", "end", iid=root_iid, text=self._node_text(self._root_folder.name, _CHECKED), open=True)

        # 先收集所有文件路径，然后构建目录树
        file_paths = sorted(
            (p.resolve() for p in iter_files(self._root_folder)),
            key=lambda p: str(p).lower(),
        )

        # 构建需要的目录集合（从根到文件的所有中间目录）
        needed_dirs: set[Path] = set()
        for fp in file_paths:
            parent = fp.parent
            while parent != self._root_folder and parent != parent.parent:
                needed_dirs.add(parent)
                parent = parent.parent

        # 按路径深度排序，确保父目录先插入
        sorted_dirs = sorted(needed_dirs, key=lambda p: (len(p.parts), str(p).lower()))

        for d in sorted_dirs:
            if d == self._root_folder:
                continue
            parent_dir = d.parent
            parent_iid = self._get_or_create_iid(parent_dir, is_dir=True)
            iid = self._new_iid(d, is_dir=True)
            self._checked[iid] = _CHECKED
            self._children_map.setdefault(iid, [])
            self._parent_map[iid] = parent_iid
            self._children_map.setdefault(parent_iid, []).append(iid)
            self._tree.insert(parent_iid, "end", iid=iid, text=self._node_text(d.name, _CHECKED), open=False)

        # 插入文件
        for fp in file_paths:
            parent_dir = fp.parent
            parent_iid = self._get_or_create_iid(parent_dir, is_dir=True)
            iid = self._new_iid(fp, is_dir=False)
            self._checked[iid] = _CHECKED
            self._parent_map[iid] = parent_iid
            self._children_map.setdefault(parent_iid, []).append(iid)
            self._tree.insert(parent_iid, "end", iid=iid, text=self._node_text(fp.name, _CHECKED))

    def _node_text(self, name: str, state: str) -> str:
        """生成带勾选符号的节点显示文本。"""
        if state == _CHECKED:
            return f"{_ICON_CHECKED} {name}"
        if state == _UNCHECKED:
            return f"{_ICON_UNCHECKED} {name}"
        return f"{_ICON_PARTIAL} {name}"

    def _new_iid(self, path: Path, *, is_dir: bool) -> str:
        """为路径分配一个新的数字 iid 并注册映射。"""
        iid = f"n{self._next_iid}"
        self._next_iid += 1
        resolved = path.resolve()
        self._iid_to_path[iid] = resolved
        self._iid_is_dir[iid] = is_dir
        self._path_to_iid_map[resolved] = iid
        return iid

    def _get_or_create_iid(self, path: Path, *, is_dir: bool) -> str:
        """获取已有路径的 iid，若不存在则创建。"""
        resolved = path.resolve()
        if resolved in self._path_to_iid_map:
            return self._path_to_iid_map[resolved]
        return self._new_iid(path, is_dir=is_dir)

    def _on_click(self, event: tk.Event) -> None:
        """处理点击事件 — 手动控制展开和勾选，互不干扰。"""
        item = self._tree.identify_row(event.y)
        if not item:
            return

        # 判断是否为展开/折叠指示器点击
        # 多重检测确保跨平台可靠性
        has_children = bool(self._tree.get_children(item))
        is_indicator_click = False

        if has_children:
            # 方法1：identify_element 直接判断
            element = self._tree.identify_element(event.x, event.y)
            if element == "indicator":
                is_indicator_click = True
            # 方法2：用 x 坐标与文本起始位置对比
            # 展开箭头在文本左侧，点击在文本 x 左侧 = 箭头区域
            elif self._tree.identify_region(event.x, event.y) == "tree":
                try:
                    bbox = self._tree.bbox(item, "#0")
                    if bbox:
                        text_x = int(bbox[0])
                        if event.x < text_x:
                            is_indicator_click = True
                except tk.TclError:
                    pass

        if is_indicator_click:
            current_open = self._tree.item(item, "open")
            self._tree.item(item, open=not current_open)
            return

        # 点击文字或其他区域 → 切换勾选状态
        current = self._checked.get(item, _CHECKED)
        new_state = _UNCHECKED if current == _CHECKED else _CHECKED
        self._set_checked_recursive(item, new_state)
        self._propagate_up(item)
        self._refresh_all_text()
        self._update_status()

    def _set_checked_recursive(self, iid: str, state: str) -> None:
        """递归设置节点及其所有子节点的状态。"""
        self._checked[iid] = state
        for child in self._children_map.get(iid, []):
            self._set_checked_recursive(child, state)

    def _propagate_up(self, iid: str) -> None:
        """向上更新父节点的状态（全选/部分选/未选）。"""
        parent = self._parent_map.get(iid)
        if parent is None:
            return
        children = self._children_map.get(parent, [])
        states = {self._checked.get(c, _CHECKED) for c in children}
        if states == {_CHECKED}:
            self._checked[parent] = _CHECKED
        elif states == {_UNCHECKED}:
            self._checked[parent] = _UNCHECKED
        else:
            self._checked[parent] = _PARTIAL
        self._propagate_up(parent)

    def _refresh_all_text(self) -> None:
        """刷新所有节点的显示文本和颜色标签。"""
        for iid, path in self._iid_to_path.items():
            state = self._checked.get(iid, _CHECKED)
            name = path.name
            self._tree.item(iid, text=self._node_text(name, state))
            if state == _CHECKED:
                self._tree.item(iid, tags=("checked",))
            elif state == _UNCHECKED:
                self._tree.item(iid, tags=("unchecked",))
            else:
                self._tree.item(iid, tags=("partial",))

        # 配置标签样式
        self._tree.tag_configure("checked", foreground="#1a7f37")
        self._tree.tag_configure("unchecked", foreground="#888888")
        self._tree.tag_configure("partial", foreground="#bf8700")

    def _update_status(self) -> None:
        """更新底部状态栏。"""
        total_files = sum(
            1 for iid, path in self._iid_to_path.items()
            if path.is_file()
        )
        selected_files = sum(
            1 for iid, path in self._iid_to_path.items()
            if path.is_file() and self._checked.get(iid) == _CHECKED
        )
        total_dirs = sum(
            1 for iid, path in self._iid_to_path.items()
            if path.is_dir()
        )
        selected_dirs = sum(
            1 for iid, path in self._iid_to_path.items()
            if path.is_dir() and self._checked.get(iid) == _CHECKED
        )
        self._status_var.set(
            f"已选 {selected_files}/{total_files} 个文件，"
            f"{selected_dirs}/{total_dirs} 个文件夹"
        )

    def _check_all(self) -> None:
        """全选。"""
        self._set_checked_recursive(self._root_iid, _CHECKED)
        self._refresh_all_text()
        self._update_status()

    def _uncheck_all(self) -> None:
        """取消全选。"""
        self._set_checked_recursive(self._root_iid, _UNCHECKED)
        self._refresh_all_text()
        self._update_status()

    def _expand_all(self) -> None:
        """展开所有节点。"""
        for iid in self._iid_to_path:
            self._tree.item(iid, open=True)

    def _collapse_all(self) -> None:
        """折叠所有节点（保留根节点展开）。"""
        for iid in self._iid_to_path:
            if iid != self._root_iid:
                self._tree.item(iid, open=False)

    def _collect_selected_paths(self) -> set[Path]:
        """收集所有被选中的文件路径。"""
        selected: set[Path] = set()
        for iid, path in self._iid_to_path.items():
            if path.is_file() and self._checked.get(iid) == _CHECKED:
                selected.add(path)
        return selected

    def _on_confirm(self) -> None:
        """确认选择。"""
        self.result = self._collect_selected_paths()
        self.destroy()

    def _on_cancel(self) -> None:
        """取消。"""
        self.result = None
        self.destroy()


def ask_selected_files(parent: tk.Tk, root_folder: Path) -> set[Path] | None:
    """便捷函数：打开文件选择对话框，返回选中的文件路径集合。

    Returns:
        选中的文件路径集合，或 None（用户取消）。
    """
    dialog = FileSelectorDialog(parent, root_folder)
    return dialog.result
