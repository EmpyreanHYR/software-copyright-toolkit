#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
PROJECT_DIR=$(CDPATH= cd -- "$SCRIPT_DIR/.." && pwd)
cd "$PROJECT_DIR"

find_uv() {
  command -v uv >/dev/null 2>&1
}

if ! find_uv; then
  printf '%s\n' 'uv is not installed or is not available in PATH.'
  printf '%s' 'Install uv now? [y/N] '
  read -r answer
  case "$answer" in
    y|Y|yes|YES)
      printf '%s\n' 'Downloading uv installer (timeout: 60s)...'
      if command -v curl >/dev/null 2>&1; then
        curl --connect-timeout 60 --max-time 120 -LsSf https://astral.sh/uv/install.sh | sh
      elif command -v wget >/dev/null 2>&1; then
        wget --timeout=60 -qO- https://astral.sh/uv/install.sh | sh
      else
        printf '%s\n' 'curl or wget is required to install uv.'
        printf '%s\n' 'Install one of them, or manually install uv: https://docs.astral.sh/uv/getting-started/installation/'
        printf '%s\n' 'Or use pip: pip install python-docx && python -m software_copyright_toolkit.gui'
        exit 1
      fi
      ;;
    *)
      printf '%s\n' 'Cancelled.'
      printf '%s\n' 'You can also install uv manually: https://docs.astral.sh/uv/getting-started/installation/'
      printf '%s\n' 'Or use pip to install dependencies directly:'
      printf '%s\n' '  pip install python-docx'
      printf '%s\n' '  python -m software_copyright_toolkit.gui'
      exit 1
      ;;
  esac
  export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
fi

if ! find_uv; then
  printf '%s\n' 'uv was installed, but it is still not available in this terminal.'
  printf '%s\n' 'Please reopen the terminal and run this launcher again.'
  exit 1
fi

printf '%s\n' 'Checking project environment and dependencies...'
if ! uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple; then
  printf '%s\n' 'uv sync failed with mirror. Trying without mirror...'
  if ! uv sync; then
    printf '%s\n' 'Failed to prepare the uv environment.'
    printf '%s\n' 'You can try manually:'
    printf '%s\n' '  pip install python-docx'
    printf '%s\n' '  python -m software_copyright_toolkit.gui'
    exit 1
  fi
fi

printf '%s\n' 'Starting GUI...'
uv run sct-gui
