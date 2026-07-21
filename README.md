# Software Copyright Toolkit

**CLI/GUI 工具：统计代码行数并一键生成符合中国软著申请规范的程序鉴别材料 (Word)。**

统计指定文件夹内所有已适配代码文件的总行数、有效行数、空行数和注释行数，并在当前目录生成 Markdown 报告。同时支持生成软著申请所需的程序鉴别材料（前后 30 页合并 Word 文档）和全量代码 Word 文档。

## 功能概览

- 📊 **代码行数统计** — 自动识别 40+ 种编程语言的注释语法，精确统计有效代码行
- 📝 **Markdown 报告** — 生成包含汇总和每个文件明细的可读报告
- 📄 **程序鉴别材料** — 一键生成符合软著申请规范的 Word 文档
- 🖥️ **图形界面** — 直观的 GUI，无需记忆命令行参数
- 🔧 **高度可定制** — 自定义文件分隔符、输出目录等

> **截图占位**：此处可添加 GUI 界面截图或操作 GIF 动图，直观展示操作流程。
> (截图建议放在 `docs/screenshots/` 目录下，然后在下方用 `![GUI](docs/screenshots/gui.png)` 引用)

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
> 3. 使用备用方案：`pip install python-docx`，然后 `python -m software_copyright_toolkit.gui`

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

这会自动创建 `.venv` 虚拟环境，并安装本工具的命令入口。

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

如果希望在命令行中同时生成代码行数统计、程序鉴别材料 Word、全量代码 Word，可以执行：

Windows PowerShell:

```powershell
uv run sct-cli "D:\path\to\your\folder" --generate-docx --software-name "软件名称" --software-version "V1.0"
```

Linux / macOS:

```bash
uv run sct-cli "/path/to/your/folder" --generate-docx --software-name "软件名称" --software-version "V1.0"
```

指定输出目录：

```bash
uv run sct-cli "/path/to/your/folder" --output-dir "/path/to/reports" --generate-docx --software-name "软件名称" --software-version "V1.0"
```

命令行会生成：

- `目标文件夹名.md`
- `软件名称_版本号_程序鉴别材料_前后30页.docx`
- `软件名称_版本号_程序鉴别材料_全量代码.docx`

## 6. 打开图形界面

如果需要生成软著申请用的程序鉴别材料，运行：

```bash
uv run sct-gui
```

也可以使用启动脚本自动检查环境并打开 GUI：

推荐直接使用根目录启动器：

- **Windows**: 双击 `open-gui.bat`
- **macOS**: 双击 `open-gui.command`，或在终端中执行 `sh ./open-gui.command`
- **Linux**: 在终端中执行 `sh ./launchers/open-gui.sh`

也可以手动在终端运行：

Windows:

```powershell
.\launchers\open-gui.bat
```

PowerShell:

```powershell
.\launchers\open-gui.ps1
```

Linux:

```bash
sh ./launchers/open-gui.sh
```

macOS:

```bash
sh ./launchers/open-gui.command
```

启动脚本会自动定位项目目录，检查本机是否安装 `uv`。如果没有安装，会先询问是否安装；选择拒绝会直接退出并给出备用安装提示。检测到 `uv` 后，会使用清华源执行依赖同步：

```bash
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

如果清华源不可用，脚本会自动回退到默认源。

依赖环境准备完成后，会自动打开 GUI。

界面支持：

- 选择目标代码文件夹
- 选择输出目录
- 输入软件名称
- 输入版本号
- 自定义文件分隔符模板（例如改为 `// --- File: {path} ---`）
- 可选生成代码行数统计 Markdown
- 可选生成程序鉴别材料 Word
- 可选生成全量代码 Word

程序鉴别材料 Word 使用 Arial 字体、10 号字，左页眉为软件名称和版本号，右页眉为页码，页脚居中为"当前页 / 总页数"。

生成的 Word 文件包括：

- `软件名称_版本号_程序鉴别材料_前后30页.docx`
- `软件名称_版本号_程序鉴别材料_全量代码.docx`

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

这是本工具最核心的业务逻辑，请仔细阅读。

### 前后 30 页截取逻辑

> **当有效代码行数 + 注释行数 ≥ 3000 行时：**
>
> 1. 程序鉴别材料按每页 **50 个可见行位** 生成完整 **60 页**（前 30 页 + 后 30 页）。
> 2. 保留前 **1500 个可见行位**（前 30 页）。
> 3. 再从不与前 1500 个可见行位重叠的后方范围寻找一个**模块结束行**作为第 3000 个可见行位。
> 4. 取该结束行之前的 **1500 个可见行位** 作为后 30 页，中间代码会被删除。
> 5. 分页符附在每页最后一个可见行位末尾。
>
> **当有效代码行数 + 注释行数 < 3000 行时：**
>
> 程序鉴别材料直接使用全量源码内容，不进行截取。

### 可见行估算机制

> **默认最大显示宽度为 80**（英文半角字符宽度），中文/全角字符按 2 倍宽度处理。
>
> - 超长代码行会按显示宽度拆成多个 Word 可见行，避免代码超出页边距。
> - 续行会占用页内行位，但**不会重复计入**有效代码行 + 注释行。
> - 文件分隔行也会占用可见行位，以保证页数稳定。
>
> 为了保证 Word 正好 60 页，文件分隔行和超长代码拆出的续行都会计入 3000 个可见行位。因此程序鉴别材料中的有效代码行 + 注释行可能略少于 3000。

> **⚠️ 重要提示**：页数基于标准 A4 纸张（21 cm × 29.7 cm）及默认页边距（上下各 2 cm，左右各 2 cm）估算。生成后建议在 Word 中通过 **「审阅 → 字数统计 → 行数」** 进行最终复核。实际渲染效果可能因字体版本、打印机驱动等因素略有差异。

---

## 高级选项

### 自定义文件分隔符

默认文件分隔符为 `===== 文件: {path} =====`，其中 `{path}` 会被替换为文件相对路径。

你可以自定义分隔符样式以节省"可见行"额度，例如使用更隐蔽的注释形式：

**CLI:**

```bash
uv run sct-cli "/path/to/folder" --generate-docx \
  --software-name "MyApp" \
  --separator "// --- File: {path} ---"
```

**GUI:** 在界面的"文件分隔符"输入框中直接修改模板。

### 大文件流式读取

对于包含大型生成文件的项目，可以使用流式读取模式降低内存占用：

```bash
uv run count-code "/path/to/folder" --use-streaming
```

### 编码自动检测

安装可选依赖后自动启用增强编码检测（适合包含 GBK/Shift-JIS 等遗留编码的混合项目）：

```bash
uv sync --extra charset-normalizer
```

---

## 常见问题

### 终端提示无法识别 uv

重新打开终端后再执行：

```bash
uv --version
```

如果仍然无法识别，说明安装目录还没有加入 `PATH`。

Linux / macOS 通常可以尝试：

```bash
source ~/.bashrc
```

或：

```bash
source ~/.zshrc
```

Windows 可以重启 PowerShell 或重启电脑后再试。

### 统计结果里出现未统计文件

这是正常的容错机制。工具只会统计已经适配过注释规则的文件格式；如果遇到未知后缀，会在报告末尾列出，避免把未知格式当作代码乱算。

### 想重新生成报告

直接重新运行统计命令即可，同名 `.md` 报告会被覆盖更新。

### 安装 uv 时网络失败

启动脚本已内置超时处理和备用方案提示。如果安装脚本失败：

1. 检查网络连接和代理设置
2. 手动从 [astral.sh](https://docs.astral.sh/uv/getting-started/installation/) 下载安装
3. 使用备用方案（需要已安装 Python）：
   ```bash
   pip install python-docx
   python -m software_copyright_toolkit.gui
   ```

---

## 开发

### 设置开发环境

```bash
uv sync --extra dev
```

### 运行测试

```bash
uv run pytest tests/ -v
```

附带覆盖率报告：

```bash
uv run pytest tests/ -v --cov=software_copyright_toolkit --cov-report=term-missing
```

### 代码质量

```bash
# 格式化
uv run ruff format .

# 代码检查
uv run ruff check .

# 类型检查
uv run mypy src/
```

### 打包为独立可执行文件

```bash
uv run python build_installer.py --all
```

打包后的文件在 `dist/` 目录下：
- `sct-cli` / `sct-cli.exe` — 命令行工具
- `sct-gui` / `sct-gui.exe` — 图形界面工具

### 项目结构

```
src/software_copyright_toolkit/
├── __init__.py      # 公共 API 重导出
├── adapters.py      # 注释规则适配器和语言扩展映射
├── scanner.py       # 文件遍历、编码检测、文本读取
├── counter.py       # 代码行数统计算法
├── cli.py           # CLI 参数解析和入口调度
├── report.py        # Markdown 报告生成
├── documents.py     # Word 程序鉴别材料生成
└── gui.py           # Tkinter 图形界面
```
