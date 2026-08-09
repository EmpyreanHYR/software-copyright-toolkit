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
  echo.
  echo Please install uv first:
  echo   https://docs.astral.sh/uv/getting-started/installation/
  echo.
  echo Or use pip to install dependencies directly:
  echo   pip install python-docx
  echo   python -m software_copyright_toolkit.gui
  echo.
  popd >nul
  pause
  exit /b 1
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
if not "%EXIT_CODE%"=="0" (
  echo GUI exited with code: %EXIT_CODE%
)
pause
exit /b %EXIT_CODE%
