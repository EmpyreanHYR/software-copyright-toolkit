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
        exit 1
    }

    powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
    $env:PATH = "$env:USERPROFILE\.local\bin;$env:USERPROFILE\.cargo\bin;$env:PATH"
    $uv = Get-Command uv -ErrorAction SilentlyContinue
    if (-not $uv) {
        Write-Host "uv was installed, but it is still not available in this terminal."
        Write-Host "Please reopen PowerShell and run this launcher again."
        exit 1
    }
}

Write-Host "Checking project environment and dependencies..."
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to prepare the uv environment."
    exit $LASTEXITCODE
}

Write-Host "Starting GUI..."
uv run sct-gui
exit $LASTEXITCODE
