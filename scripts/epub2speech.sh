#!/bin/bash

# epub2speech CLI 启动脚本
# 使用 poetry 环境中的 Python 来运行 CLI

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# 检查是否在项目根目录
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "错误: 无法找到项目根目录" >&2
    exit 1
fi

# 加载 .env 文件（如果存在）
if [ -f "$PROJECT_ROOT/.env" ]; then
    set -a
    source "$PROJECT_ROOT/.env"
    set +a
fi

# 使用 poetry 运行 CLI
cd "$PROJECT_ROOT"
poetry run python -m epub2speech.cli "$@"