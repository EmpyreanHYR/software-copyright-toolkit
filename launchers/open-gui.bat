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
    popd >nul
    pause
    exit /b 1
  )

  powershell -NoProfile -ExecutionPolicy ByPass -Command "irm https://astral.sh/uv/install.ps1 | iex"
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
  echo Failed to prepare the uv environment.
  popd >nul
  pause
  exit /b 1
)

echo Starting GUI...
uv run sct-gui
set "EXIT_CODE=%ERRORLEVEL%"
popd >nul
if not "%EXIT_CODE%"=="0" pause
exit /b %EXIT_CODE%
