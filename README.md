# Software Copyright Toolkit

统计指定文件夹内所有已适配代码文件的总行数、有效行数、空行数和注释行数，并在当前目录生成与目标文件夹同名的 Markdown 报告。

本工具当前聚焦代码行数统计，后续可继续扩展为软著申请所需的程序鉴别文档整理工具。

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

运行完成后，会在当前目录生成与目标文件夹同名的 Markdown 报告：

Windows 示例：

```text
D:\Desktop\count-code\folder.md
```

Linux / macOS 示例：

```text
/home/your-name/count-code/folder.md
```

## 5. 指定报告输出目录

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
