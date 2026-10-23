#!/bin/zsh
set -e
cd -- "$(dirname -- "$0")"
if [[ ! -x .venv/bin/python ]]; then
  if ! command -v uv >/dev/null 2>&1; then
    print '尚未安装 uv。请先按 README 的环境准备说明安装，再双击启动。'
    read '?按回车关闭窗口。'
    exit 1
  fi
  uv sync --frozen --extra dev
fi
exec .venv/bin/python -m tps_evidence.server --port 8502 --open
