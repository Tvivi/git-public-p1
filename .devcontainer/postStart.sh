#!/usr/bin/env bash
set -eu

# コンテナで本ファイルが実行出来ない場合はホスト側で下記を実行しておくこと
# chmod +x .devcontainer/postStart.sh

# Dev Containers の既定動作でホスト側 Git 設定がコンテナ側ホームに取り込まれる場合がある
# ホストの設定や認証情報をコンテナに持ち込ませない
echo "== Reset Git global config =="

# 1. system gitconfig を空にする
# VS Code Dev Containers が /etc/gitconfig に注入した credential.helper を消す
if [ -f /etc/gitconfig ]; then
    sudo tee /etc/gitconfig >/dev/null <<'EOF'
EOF
fi

# 2. global gitconfig を最小構成で再作成
rm -f /home/vscode/.gitconfig

cat > /home/vscode/.gitconfig <<'EOF'
[credential]
	helper =
[init]
	defaultBranch = main
[core]
	autocrlf = input
[pull]
	rebase = false
[safe]
	directory = /workspace
EOF

# 3. 念のため個人情報系を削除
git config --global --unset-all user.name || true
git config --global --unset-all user.email || true

# 4. 状態確認
echo "== credential.helper origins =="
git config --show-origin --get-all credential.helper || true

echo "== global gitconfig =="
cat /home/vscode/.gitconfig || true

echo "== Done =="
