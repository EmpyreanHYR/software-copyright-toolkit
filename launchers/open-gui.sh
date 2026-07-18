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
      if command -v curl >/dev/null 2>&1; then
        curl -LsSf https://astral.sh/uv/install.sh | sh
      elif command -v wget >/dev/null 2>&1; then
        wget -qO- https://astral.sh/uv/install.sh | sh
      else
        printf '%s\n' 'curl or wget is required to install uv.'
        exit 1
      fi
      export PATH="$HOME/.local/bin:$HOME/.cargo/bin:$PATH"
      ;;
    *)
      printf '%s\n' 'Cancelled.'
      exit 1
      ;;
  esac
fi

if ! find_uv; then
  printf '%s\n' 'uv was installed, but it is still not available in this terminal.'
  printf '%s\n' 'Please reopen the terminal and run this launcher again.'
  exit 1
fi

printf '%s\n' 'Checking project environment and dependencies...'
uv sync --index-url https://pypi.tuna.tsinghua.edu.cn/simple

printf '%s\n' 'Starting GUI...'
uv run sct-gui
