# Software Copyright Toolkit

统计指定文件夹内所有已适配代码文件的总行数、有效行数、空行数和注释行数，并在当前目录生成与目标文件夹同名的 Markdown 报告。

本工具用于代码行数统计，以及生成软著申请常用的程序鉴别材料。

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

`count-code` 和 `sct-cli` 是同一个命令入口。后续如果打包为命令行 exe，可以使用 `sct-cli` 作为更通用的名称。

运行完成后，会在当前目录生成与目标文件夹同名的 Markdown 报告：

Windows 示例：

```text
D:\Desktop\count-code\folder.md
```

Linux / macOS 示例：

```text
/home/your-name/count-code/folder.md
```

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

- Windows: 双击 `open-gui.bat`
- macOS: 双击 `open-gui.command`，或在终端中执行 `sh ./open-gui.command`
- Linux: 在终端中执行 `sh ./launchers/open-gui.sh`

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

启动脚本会自动定位项目目录，检查本机是否安装 `uv`。如果没有安装，会先询问是否安装；选择拒绝会直接退出。检测到 `uv` 后，会使用清华源执行依赖同步：

```bash
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

依赖环境准备完成后，会自动打开 GUI。

界面支持：

- 选择目标代码文件夹
- 选择输出目录
- 输入软件名称
- 输入版本号
- 可选生成代码行数统计 Markdown
- 可选生成程序鉴别材料 Word
- 可选生成全量代码 Word

程序鉴别材料 Word 使用 Arial 字体、10 号字，左页眉为软件名称和版本号，右页眉为页码，页脚居中为当前页 / 总页数。

生成的 Word 文件包括：

- `软件名称_版本号_程序鉴别材料_前后30页.docx`
- `软件名称_版本号_程序鉴别材料_全量代码.docx`

程序鉴别材料生成规则：

- 保留 `===== 文件: xxx =====` 文件分隔行。
- 去除源码空行，不生成空白分页段落。
- 文件分隔行会占用 Word 中的可见行位，以保证页数稳定。
- 超长代码行会先拆成多个 Word 可见行，避免代码超出页边距；拆出的续行会占用页内行位，但不会重复计入有效代码行 + 注释行。

当有效代码行数 + 注释行数不少于 3000 行时：

- 程序鉴别材料按每页 50 个可见行位生成完整 60 页。
- 保留前 1500 个可见行位。
- 再从不与前 1500 个可见行位重叠的后方范围寻找一个模块结束行作为第 3000 个可见行位。
- 取该结束行之前的 1500 个可见行位作为后 30 页，中间代码会被删除。
- 分页符附在每页最后一个可见行位末尾。

为了保证 Word 正好 60 页，文件分隔行和超长代码拆出的续行都会计入 3000 个可见行位。因此程序鉴别材料中的有效代码行 + 注释行可能略少于 3000。

如果有效代码行数 + 注释行数不足 3000 行，程序鉴别材料会直接使用全量源码内容。模块结束行包括常见的 `}`、`]`、`)`、`end` 等。

## 7. 指定报告输出目录

默认报告输出到当前命令所在目录。也可以用 `--output-dir` 指定输出目录：

Windows PowerShell:

```powershell
uv run count-code "D:\path\to\your\folder" --output-dir "D:\path\to\reports"
```

Linux / macOS:

```bash
uv run count-code "/path/to/your/folder" --output-dir "/path/to/reports"
```

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

- Python: `.py`, `.pyw`
- JavaScript / TypeScript: `.js`, `.jsx`, `.ts`, `.tsx`
- Web: `.html`, `.htm`, `.css`, `.scss`, `.sass`, `.less`, `.vue`
- Go: `.go`
- MATLAB: `.m`
- R: `.r`, `.R`
- C / C++ / C# / Java / Rust / Swift / Kotlin / Dart: `.c`, `.cpp`, `.h`, `.hpp`, `.cs`, `.java`, `.rs`, `.swift`, `.kt`, `.dart`
- Shell / PowerShell / Batch: `.sh`, `.ps1`, `.bat`, `.cmd`
- 配置和数据文件: `.json`, `.yaml`, `.yml`, `.toml`, `.ini`, `.env`, `.conf`, `.properties`
- 其他: `.sql`, `.php`, `.rb`, `.xml`, `.svg`, `Dockerfile`, `Makefile`

其中 `.json` 按无注释格式处理。

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

直接重新运行统计命令即可，同名 `.md` 报告会被覆盖更新：

```powershell
uv run count-code "D:\path\to\your\folder"
```

Linux / macOS:

```bash
uv run count-code "/path/to/your/folder"
```
