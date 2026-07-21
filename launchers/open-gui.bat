@echo off
setlocal EnableExtensions

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
pushd "%PROJECT_DIR%" >nul 2>nul
if errorlevel 1 (
  echo Failed to enter project directory.
  pause
  exit /b 1
)

where uv >nul 2>nul
if errorlevel 1 (
  echo uv is not installed or is not available in PATH.
  set /p INSTALL_UV=Install uv now? [Y/N] 
  if /i not "%INSTALL_UV%"=="Y" (
    echo Cancelled.
    echo.
    echo You can also install uv manually: https://docs.astral.sh/uv/getting-started/installation/
    echo Or use pip to install dependencies directly:
    echo   pip install python-docx
    echo   python -m software_copyright_toolkit.gui
    popd >nul
    pause
    exit /b 1
  )

  echo Downloading uv installer (timeout: 60s)...
  powershell -NoProfile -ExecutionPolicy ByPass -Command ^
    "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; " ^
    "try { " ^
    "  $req = [System.Net.WebRequest]::Create('https://astral.sh/uv/install.ps1'); " ^
    "  $req.Timeout = 60000; " ^
    "  $resp = $req.GetResponse(); " ^
    "  $stream = $resp.GetResponseStream(); " ^
    "  $reader = New-Object System.IO.StreamReader($stream); " ^
    "  $script = $reader.ReadToEnd(); " ^
    "  Invoke-Expression $script; " ^
    "} catch { " ^
    "  Write-Host 'Failed to download uv installer (network error or timeout).'; " ^
    "  Write-Host 'Please install uv manually: https://docs.astral.sh/uv/getting-started/installation/'; " ^
    "  Write-Host 'Or use pip: pip install python-docx && python -m software_copyright_toolkit.gui'; " ^
    "  exit 1; " ^
    "}"
  set "PATH=%USERPROFILE%\.local\bin;%USERPROFILE%\.cargo\bin;%PATH%"

  where uv >nul 2>nul
  if errorlevel 1 (
    echo uv was installed, but it is still not available in this terminal.
    echo Please close this window, reopen a terminal, and run this launcher again.
    popd >nul
    pause
    exit /b 1
  )
)

echo Checking project environment and dependencies...
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple
if errorlevel 1 (
  echo uv sync failed. Trying without mirror...
  uv sync
  if errorlevel 1 (
    echo Failed to prepare the uv environment.
    echo You can try manually:
    echo   pip install python-docx
    echo   python -m software_copyright_toolkit.gui
    popd >nul
    pause
    exit /b 1
  )
)

echo Starting GUI...
uv run sct-gui
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
