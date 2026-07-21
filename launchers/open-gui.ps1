$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Resolve-Path (Join-Path $ScriptDir "..")
Set-Location $ProjectDir

$uv = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uv) {
    Write-Host "uv is not installed or is not available in PATH."
    $answer = Read-Host "Install uv now? [Y/N]"
    if ($answer -notin @("Y", "y")) {
        Write-Host "Cancelled."
        Write-Host ""
        Write-Host "You can also install uv manually: https://docs.astral.sh/uv/getting-started/installation/"
        Write-Host "Or use pip to install dependencies directly:"
        Write-Host "  pip install python-docx"
        Write-Host "  python -m software_copyright_toolkit.gui"
        exit 1
    }

    Write-Host "Downloading uv installer (timeout: 60s)..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $req = [System.Net.WebRequest]::Create("https://astral.sh/uv/install.ps1")
        $req.Timeout = 60000
        $resp = $req.GetResponse()
        $stream = $resp.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($stream)
        $script = $reader.ReadToEnd()
        Invoke-Expression $script
    } catch {
        Write-Host "Failed to download uv installer (network error or timeout)."
        Write-Host "Please install uv manually: https://docs.astral.sh/uv/getting-started/installation/"
        Write-Host "Or use pip: pip install python-docx; python -m software_copyright_toolkit.gui"
        exit 1
    }

    $env:PATH = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:PATH"
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Write-Host "uv was installed, but it is still not available in this terminal."
        Write-Host "Please reopen PowerShell and run this launcher again."
        exit 1
    }
}

Write-Host "Checking project environment and dependencies..."
try {
    uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
    if ($LASTEXITCODE -ne 0) {
        Write-Host "uv sync failed with mirror. Trying without mirror..."
        uv sync
        if ($LASTEXITCODE -ne 0) {
            throw "uv sync failed"
        }
    }
} catch {
    Write-Host "Failed to prepare the uv environment."
    Write-Host "You can try manually:"
    Write-Host "  pip install python-docx"
    Write-Host "  python -m software_copyright_toolkit.gui"
    exit 1
}

Write-Host "Starting GUI..."
uv run sct-gui
exit $LASTEXITCODE
