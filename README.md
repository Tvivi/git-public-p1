# AI生成コードに関する免責
This repository is a personal learning project and not intended for commercial use.
All code is either original, AI-assisted, or based on publicly available learning resources.

Some parts of the code may have been generated or assisted by AI tools such as ChatGPT.
The author does not intentionally copy or reproduce copyrighted source code from third-party projects.

However, because AI-generated content may resemble existing implementations,
there is a possibility that portions of the code may be similar to publicly available examples or tutorials.

If you believe that any code in this repository unintentionally reproduces copyrighted material,
please open an issue or contact the repository owner.
The relevant code will be reviewed and removed or replaced if necessary.

# 学習用途について
This project is intended for educational purposes only.

The code in this repository:

- may contain simplified implementations
- may not follow production security practices
- should not be used directly in production systems without review

# ライセンス
Unless otherwise specified, the source code in this repository is licensed under the terms described in the LICENSE file.

# ブランチ戦略
- main
    デプロイ用本番環境
- develop
    テストを通した開発ブランチ
- feature**
    基本的にここで開発。ISSUEと連動予定

# タグ付けルール
後日決める

# 開発環境整備
コンテナ作成前に下記は実行しておくこと。バージョンが揃えられなくなる

``` bash
# コンテナビルド用
copy .env.sample .env
# CI用。git commit して良い
copy .env.sample tool-versions.env
```

## 各種バージョンチェック
``` bash
vscode ➜ /workspace (main) $ gitleaks version
8.28.0
vscode ➜ /workspace (main) $ trivy --version
Version: 0.69.3
vscode ➜ /workspace (main) $ uv --version
uv 0.10.11
vscode ➜ /workspace (main) $ uv run python --version
Python 3.12.0
vscode ➜ /workspace (main) $ uv run detect-secrets --version
1.5.0
```

## CodeXCLI
``` bash
# codexはあくまでpython環境のおまけなのでDockerFileでインストールしない
npm i -g @openai/codex
codex --version
```

## MCP
`xxx.json`をgit追跡対象外にして将来的に入れるか？

## git
ホストの情報が漏れ出ていないか念のため確認

``` bash
vscode ➜ /workspace $ git config -l
credential.helper=
init.defaultbranch=main
core.autocrlf=input
pull.rebase=false
safe.directory=/workspace
vscode ➜ /workspace $
```

初回のリモート接続

``` bash
git init -b main
git remote add origin git@github.com:<User>/<project>
git remote -v
git push -u origin main
```

# セキュリティ
詳細は`docs\SECURITY.md`参照

## 初回だけローカルで実施
### detect-secrets
`poethepoet`で実行するとコンテナが落ちたことがある。
初回はgit追跡ファイルが多いのでその分処理が重くなって死んでしまうのかも？

!!! 場合によってはChromeなどは閉じておいた方が良い

``` bash
$ poe secrets-init
```

ただし、先に`git init`していないとエラーが出る

``` bash
$ uv run detect-secrets scan > .secrets.baseline
fatal: not a git repository (or any parent up to mount point /)
Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).
```

### trivy
CIも用意しているが、最初のコミットはコンテナで実行するとDockerfileなどの不備をgit履歴に載せる前に止められる

!!! 実行負荷が大きいので、場合によってはChromeなどは閉じておいた方が良い

``` bash
$ mkdir -p artifacts/repo
$ poe trivy-init
```

```
### 🔍 Trivy config findings (HIGH/CRITICAL)

- No HIGH/CRITICAL findings (trivyignore applied)

### 🔍 Trivy fs findings (HIGH/CRITICAL)

- No HIGH/CRITICAL findings (trivyignore applied)
```

## 初回も含めてコミット前に毎回実施すること
脆弱性とは異なり、機密情報流出はpush前にローカルで止めるのが原則

``` bash
$ poe min-git-scan
```

# コード品質保証
詳細は`docs\CODE-QUALITY-CHECK.md`参照

## 初回も含めてコミット前に毎回実施すること
型チェック(`mypy`)はローカルでは重たいのでCIが担当する

``` bash
$ poe check
```

## pre-commit
導入した方が良いが機密情報流出対策としてコンテナ内部でcommitしない方針なので、採用していない。
上述の「コミット前に毎回実施すること」、特にセキュリティ側を必ず開発者が実施すること


## 将来的にやりたいこと
- `security.yml`のリファクタリング？
- `python-licenses.yml`などのCIのHTML変換用のscript書く？
- scriptsとそのテストコードをruff,mypyを通す
- 何故かVSCodeのポートが勝手に開くことの対策

```
[150528 ms] Port forwarding 56603 > 43861 > 43861 stderr: Connection established
[155002 ms] Port forwarding 50985 > 43861 > 43861 stderr: Remote close
[155310 ms] Port forwarding 50985 > 43861 > 43861 terminated with code 0 and signal null.
[156178 ms] [07:48:19] [127.0.0.1][7c7a9ea6][ExtensionHostConnection] <596> [reconnection-grace-time] Extension host: read VSCODE_RECONNECTION_GRACE_TIME=10800000ms (10800s)
```


