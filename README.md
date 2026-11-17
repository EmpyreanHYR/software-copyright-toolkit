# Software Copyright Toolkit

**CLI/GUI 工具：统计代码行数并一键生成符合中国软著申请规范的程序鉴别材料 (Word / PDF)。**

统计指定文件夹内所有已适配代码文件的总行数、有效行数、空行数和注释行数，并在当前目录生成 Markdown 报告。同时支持一键生成软著申请所需的程序鉴别材料（前后连续页合并 Word/PDF 文档）和全量代码 Word/PDF 文档。

## 功能概览

- 📊 **代码行数统计** — 自动识别 40+ 种编程语言的注释语法，精确统计有效代码行
- 📝 **Markdown 报告** — 生成包含汇总和每个文件明细的可读报告
- 📄 **程序鉴别材料 (Word & PDF)** — 一键生成符合软著申请规范的 Word 及高精度 PDF 文档
- 📕 **原生 PDF 高精度排版** — 基于纯 Python 引擎（ReportLab），严格单页 50 行对齐、规范页眉页脚，不依赖 Office/WPS
- 🎲 **固定随机种子代码打乱** — 支持通过随机种子在内存中确定性打乱文件拼接顺序，100% 不修改磁盘源文件，功能完全正常
- 🖥️ **图形界面** — 直观的 GUI，无需记忆命令行参数，支持格式勾选、种子随机生成
- 📂 **文件选择器** — 可视化树形勾选界面，精确控制纳入统计的文件和文件夹
- 🔧 **高度可定制** — 自定义单段页数（30/60页）、文件分隔符、输出目录等
- 🧩 **插件化语言扩展** — 通过 TOML 配置文件添加自定义语言的注释规则
- 🦀 **嵌套块注释** — 支持 Rust 等语言的嵌套 `/* /* */ */` 语法

> **截图占位**：此处可添加 GUI 界面截图或操作 GIF 动图，直观展示操作流程。
> (截图建议放在 `docs/screenshots/` 目录下，然后在下方用 `![GUI](docs/screenshots/gui.png)` 引用)

---
## 🚀 完整软著申请解决方案

本仓库专注于提供高效的 **程序鉴别材料**（源代码）生成与统计工具。如果您还需要准备 **文档鉴别材料**（软件使用说明书 / 设计文档），强烈推荐搭配使用配套的高质量排版模板：

[![Software Copyright LaTeX Template](https://img.shields.io/badge/配套模板-软件著作权%20LaTeX%20模板-orange?style=for-the-badge&logo=latex)](https://github.com/EmpyreanHYR/copyright-of-computer-software_latex_template)

### 为什么推荐它？
| 特性 | 说明 |
| :--- | :--- |
| 📐 **严格符合规范** | 页面布局、字体、字号及页眉页脚严格遵循中国版权保护中心软著申请的格式要求 |
| 🎨 **专业级排版** | 基于 LaTeX 引擎，彻底告别 Word 排版错乱、图片压缩模糊、目录更新繁琐等痛点 |
| 📝 **开箱即用** | 提供结构清晰的示例文件，只需替换软件名称、界面截图和简单描述即可快速编译出 PDF |
| 🔄 **灵活可扩展** | 完美支持“软件使用说明书”与“软件设计文档”等多种软著必要文档的模板切换与定制 |

> **💡 最佳实践工作流**：  
> 1. 使用本 [software-copyright-toolkit](https://github.com/EmpyreanHYR/software-copyright-toolkit) 一键统计代码并生成符合规范的“源代码前后 30 页” Word/PDF 文档。  
> 2. 使用配套 [LaTeX 模板](https://github.com/EmpyreanHYR/copyright-of-computer-software_latex_template) 填写并编译生成专业的软件使用说明书 PDF。  
> 3. 合并导出，轻松、专业地完成软著登记全套材料准备！

---

## 目录

- [1. 安装 uv](#1-安装-uv)
- [2. 进入项目目录](#2-进入项目目录)
- [3. 初始化环境](#3-初始化环境)
- [4. 统计文件夹](#4-统计文件夹)
- [5. 命令行生成软著材料](#5-命令行生成软著材料)
- [6. 打开图形界面](#6-打开图形界面)
- [7. 指定报告输出目录](#7-指定报告输出目录)
- [报告内容](#报告内容)
- [统计规则](#统计规则)
- [已适配的常见格式](#已适配的常见格式)
- [程序鉴别材料生成规则](#程序鉴别材料生成规则)
- [高级选项](#高级选项)
- [常见问题](#常见问题)
- [开发](#开发)

---

## 1. 安装 uv

如果电脑还没有安装 `uv`，先按自己的系统安装。

### Windows PowerShell

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Linux / macOS

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

如果系统没有 `curl`，也可以用：

```bash
wget -qO- https://astral.sh/uv/install.sh | sh
```

安装完成后，重新打开终端，检查是否安装成功：

```bash
uv --version
```

能看到版本号就说明安装成功。

> **⚠️ 网络问题？** 如果 `astral.sh` 无法访问（常见于国内部分网络环境），可以：
> 1. 使用代理或 VPN
> 2. 手动安装 uv：参考 [官方安装指南](https://docs.astral.sh/uv/getting-started/installation/)
> 3. 使用备用方案：`pip install python-docx reportlab`，然后 `python -m software_copyright_toolkit.gui`

## 2. 进入项目目录

进入本工具所在目录：

Windows PowerShell:

```powershell
cd D:\Desktop\count-code
```

Linux / macOS:

```bash
cd ~/count-code
```

## 3. 初始化环境

第一次使用前执行：

```bash
uv sync
```

这会自动创建 `.venv` 虚拟环境，并安装本工具的命令入口及所需依赖。

如果需要增强的编码自动检测能力（推荐用于包含多种编码的遗留项目），可以安装可选依赖：

```bash
uv sync --extra charset-normalizer
```

## 4. 统计文件夹

统计指定文件夹：

Windows PowerShell:

```powershell
uv run count-code "D:\path\to\your\folder"
```

Linux / macOS:

```bash
uv run count-code "/path/to/your/folder"
```

`count-code` 和 `sct-cli` 是同一个命令入口。

运行完成后，会在当前目录生成与目标文件夹同名的 Markdown 报告。

## 5. 命令行生成软著材料

如果希望在命令行中同时生成代码行数统计、程序鉴别材料（Word/PDF）、全量代码（Word/PDF），可以执行：

### 导出 Word + PDF 格式材料

```bash
uv run sct-cli "/path/to/your/folder" \
  --software-name "软件名称" \
  --software-version "V1.0" \
  --generate-docx \
  --generate-pdf
```

### 使用随机种子打乱文件拼接顺序（固定可复现）

```bash
uv run sct-cli "/path/to/your/folder" \
  --software-name "软件名称" \
  --software-version "V1.0" \
  --generate-pdf \
  --seed 42
```

> **提示**：`--seed` 仅在内存中打乱文件先后组织顺序，**绝对不修改磁盘上的源代码**，项目功能 100% 正常。

### 自定义鉴别材料单段页数（如前后各 60 页）

```bash
uv run sct-cli "/path/to/your/folder" \
  --software-name "软件名称" \
  --software-version "V1.0" \
  --generate-pdf \
  --pages 60
```

### 指定输出目录

```bash
uv run sct-cli "/path/to/your/folder" \
  --output-dir "/path/to/reports" \
  --software-name "软件名称" \
  --software-version "V1.0" \
  --generate-docx \
  --generate-pdf
```

命令行输出文件包含：

- `软件名称_版本号_代码行数统计.md`
- `软件名称_版本号_程序鉴别材料_前后30页.docx` (若开启 `--generate-docx`)
- `软件名称_版本号_程序鉴别材料_全量代码.docx` (若开启 `--generate-docx`)
- `软件名称_版本号_程序鉴别材料_前后30页.pdf` (若开启 `--generate-pdf`)
- `软件名称_版本号_程序鉴别材料_全量代码.pdf` (若开启 `--generate-pdf`)

### CLI 参数速查表

| 参数 | 说明 | 默认值 |
| :--- | :--- | :--- |
| `folder` | 要统计或处理的目标源代码文件夹路径 | （必填） |
| `--output-dir` | 输出目录 | 当前目录 |
| `--software-name` | 软件名称（生成 Word/PDF 材料时必填） | 无 |
| `--software-version` / `--version` | 软件版本号 | `V1.0` |
| `--generate-docx` | 导出 Word (`.docx`) 格式材料 | `False` |
| `--generate-pdf` | 导出 PDF (`.pdf`) 格式材料 | `False` |
| `--seed` | 整数随机种子，用于固定打乱文件拼接顺序 | 无（默认字典序） |
| `--pages` | 鉴别材料单段页数（30 即前后各 30 页共 60 页；60 即前后各 60 页） | `30` |
| `--separator` | 文件分隔符模板，`{path}` 为相对路径 | `===== 文件: {path} =====` |
| `--use-streaming` | 流式读取模式，适合超大文件降低内存占用 | `False` |

---

## 6. 打开图形界面

如果需要直观地进行文件勾选、参数设置与生成材料，运行：

```bash
uv run sct-gui
```

也可以使用启动脚本自动检查环境并打开 GUI：

推荐直接使用根目录启动器：

- **Windows**: 双击 `open-gui.bat`
- **macOS**: 双击 `open-gui.command`，或在终端中执行 `sh ./open-gui.command`
- **Linux**: 在终端中执行 `sh ./launchers/open-gui.sh`

也可以手动在终端运行：

Windows PowerShell:

```powershell
.\launchers\open-gui.bat
```

Linux:

```bash
sh ./launchers/open-gui.sh
```

macOS:

```bash
sh ./launchers/open-gui.command
```

### 图形界面功能一览

- 📂 **选择目标文件夹** — 自动记忆与智能匹配输出目录
- 🌲 **文件选择器** — 点击「选择文件...」打开树形勾选界面，精细控制纳入统计的子文件夹和文件
- 🏷️ **软件名称与版本号** — 自动填入页眉、封面与文件名前缀
- 📄 **单段页数设置** — 下拉选择 `30` 页（默认前后各 30 页，共 60 页）或 `60` 页
- 🎲 **随机种子打乱** — 支持手动输入种子或点击「随机生成」，以固定种子打乱文件排版顺序（不修改磁盘源码）
- 🔧 **自定义文件分隔符** — 自定义各源码文件之间的隔离行标记
- 📑 **输出格式多选** — 支持独立或同时勾选导出 **Word (.docx)** 与 **PDF (.pdf)**
- 📋 **材料内容多选** — 自由勾选生成“程序鉴别材料”、“全量代码”、“代码行数统计 Markdown”

---

## 报告内容

Markdown 报告包含：

- 汇总信息
- 每个文件的总行数
- 每个文件的有效行数
- 每个文件的空行数
- 每个文件的注释行数
- 全部文件有效代码总行数
- 未统计文件及原因

## 统计规则

- 有效行数 = 总行数 - 空行数 - 注释行数。
- 未适配的文件后缀不会被胡乱统计为代码，会在报告末尾列出。
- 默认跳过常见缓存、依赖和构建目录，例如 `.git`、`.venv`、`node_modules`、`dist`、`build`。

## 已适配的常见格式

- **Python**: `.py`, `.pyw`（使用 `tokenize` 模块精确解析）
- **JavaScript / TypeScript**: `.js`, `.jsx`, `.ts`, `.tsx`
- **Web**: `.html`, `.htm`, `.css`, `.scss`, `.sass`, `.less`, `.vue`
- **Go**: `.go`
- **MATLAB**: `.m`
- **R**: `.r`, `.R`
- **C / C++ / C# / Java / Rust / Swift / Kotlin / Dart**: `.c`, `.cpp`, `.h`, `.hpp`, `.cs`, `.java`, `.rs`, `.swift`, `.kt`, `.dart`
- **Shell / PowerShell / Batch**: `.sh`, `.ps1`, `.bat`, `.cmd`
- **配置和数据文件**: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.env`, `.conf`, `.properties`
- **其他**: `.sql`, `.php`, `.rb`, `.xml`, `.svg`, `Dockerfile`, `Makefile`

其中 `.json` 按无注释格式处理。

---

## 程序鉴别材料生成规则

### 前后连续页截取逻辑

根据中国版权保护中心（CPCC）《计算机软件著作权登记办法》规范：

> 源程序鉴别材料应当由源程序的前、后各连续的 30 页组成，共 60 页。整个程序不到 60 页的，应当提交全部源程序。

1. **当代码总可见行数 ≥ 规范行数（3000 行 / 60 页）时：**
   - 提取前半部分：严格保留前 **1500 行**（第 1~30 页）。
   - 提取后半部分：从代码后方匹配模块结束标记（如 `}`、`end` 或 Python 模块边界）作为结束点，向前截取 **1500 行**（第 31~60 页），中间代码安全省略。
2. **当代码总可见行数 < 规范行数时：**
   - 程序鉴别材料直接包含全部源代码，不进行多余截断。

### 可见行与排版机制

- **最大显示宽度限制**：默认单行宽度为 80（英文字符），全角中文字符按 2 倍宽度计算，超长行自动折行。
- **PDF 高精度排版优势**：
  - 标准 A4 尺寸，上下左右各 20mm 边距；
  - 严格单页 50 行物理对齐，字号与行距严整；
  - 页眉：左侧「软件名称 版本号」，右侧「第 X 页」，带 0.5pt 分隔线；
  - 页脚：居中「第 X 页 / 共 Y 页」；
  - 自动识别并加载系统等宽中文字体（SimSun、微软雅黑等），杜绝乱码。

---

## 高级选项

### 随机种子打乱（代码顺序混淆）

- **原理**：在文件级别打乱拼接顺序。用户本地工程源码文件**不作任何变动**，项目运行、开发、测试不受影响。
- **可复现性**：使用确定性随机数生成算法，相同 seed 每次生成的输出文件完全一致；更换 seed 即获得一套全新文件次序。

### 自定义语言配置（插件化扩展）

如果内置的 40+ 种语言不能满足需求，可以通过 TOML 配置文件添加自定义语言的注释规则。

在以下任一位置创建配置文件，工具会自动加载：

- `~/.sct/languages.toml` — 用户全局配置
- 项目根目录 `.sct.toml` — 项目级配置

配置文件格式：

```toml
[languages]
# 简写：扩展名 = 配置
".mylang" = { line_comment = "//", block_comment = [["/*", "*/"]] }

# 完整格式：支持多扩展名、嵌套块注释
[languages.mylang2]
extensions = [".ml2", ".ml3"]
line_comment = ["//", "#"]
block_comment = [["/*", "*/"], ["<!--", "-->"]]
block_comment_nesting = [true, false]
```

### 嵌套块注释支持

Rust 等语言支持嵌套块注释语法 `/* /* inner */ outer */`。工具会自动识别 Rust（`.rs`）的嵌套注释，无需额外配置。

---

## 常见问题

### 终端提示无法识别 uv

重新打开终端后再执行：

```bash
uv --version
```

如果仍然无法识别，说明安装目录还没有加入 `PATH`。

### 导出 PDF 时中文字体如何处理？

工具内置了全平台中文字体自适应探测引擎：
- **Windows**: 优先加载 `SimSun`（宋体）或 `msyh`（微软雅黑）；
- **macOS**: 优先加载 `PingFang` 或 `Songti`；
- **Linux**: 优先加载 `NotoSansCJK` 或 `wqy-zenhei`。
无需用户额外下载或配置字体文件。

---

## 开发

### 设置开发环境

```bash
uv sync --extra dev
```

### 运行测试

```bash
uv run pytest
```

### 打包为独立可执行文件

```bash
uv run python build_installer.py --all
```

### 项目结构

```
src/software_copyright_toolkit/
├── __init__.py      # 公共 API 重导出
├── adapters.py      # 注释规则适配器和语言扩展映射（支持 TOML 自定义）
├── scanner.py       # 文件遍历、编码检测、文本读取
├── counter.py       # 代码行数统计算法（支持嵌套块注释）
├── cli.py           # CLI 参数解析和入口调度
├── controller.py    # 业务逻辑控制器（GUI/CLI 共享）
├── report.py        # Markdown 报告生成
├── documents.py     # Word & PDF 程序鉴别材料生成（ReportLab 引擎）
├── file_selector.py # 文件树选择对话框组件
└── gui.py           # Tkinter 图形界面
```
