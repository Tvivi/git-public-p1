#!/usr/bin/env bash
set -eux

# コンテナで本ファイルが実行出来ない場合はホスト側で下記を実行しておくこと
# chmod +x .devcontainer/postCreate.sh


# 依存同期
if [ -f pyproject.toml ]; then
  uv sync
fi

gitleaks version
trivy --version
uv --version
uv run detect-secrets --version
