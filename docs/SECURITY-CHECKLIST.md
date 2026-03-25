# 🔐 GitHub公開前チェックリスト（必須10項目）

公開前に **必ず確認すること**
すべてチェックできたら公開OK


## 1. シークレット漏えいチェック
- [ ] `.env` ファイルが含まれていない
- [ ] APIキー / トークン / パスワードが含まれていない
- [ ] SSH鍵（`id_rsa`, `id_ed25519` 等）が含まれていない
- [ ] `docker-compose.yml` / `devcontainer.json` に秘密情報がない
- [ ] README に秘密情報を書いていない

`.gitignore`, `detect-secrets`, `gitleaks` で担保


## 2. Git履歴の確認（超重要）
- [ ] 過去コミットに `.env` や鍵を含めていない
- [ ] 機密情報を commit した履歴がない
- [ ] 削除済みファイルが履歴に残っていない
- [ ] Actionsログに秘密が出ていない

`.gitignore`, `detect-secrets`, `gitleaks` で担保

## 3. `.gitignore` の見直し
- [ ] `.env` が除外されている
- [ ] `.venv/`, `node_modules/` が除外されている
- [ ] `coverage/`, `.pytest_cache/` が除外されている
- [ ] `.mypy_cache/`, `.ruff_cache/` が除外されている
- [ ] `dist/`, `build/` が除外されている

全て確認済み

## 4. 不要ファイル削除
- [ ] ローカル用メモ・検証ファイルを削除
- [ ] スクリーンショットを削除（必要なものだけ残す）
- [ ] 一時ファイル・ログを削除
- [ ] `.devcontainer` の個人設定を整理

`.devcontainer` でホスト側の情報をマウントしないように修正済み

## 5. ライセンス設定
- [ ] `LICENSE` ファイルを追加
- [ ] README に利用条件を記載
- [ ] 依存ライブラリのライセンスを確認
- [ ] 配布物（画像・フォント等）の再配布可否を確認

`LICENSE`, `pip-licenses`, `README` で担保

## 6. GitHub Security機能の有効化
- [ ] Dependabot alerts ON
- [ ] Dependabot security updates ON
- [ ] Secret scanning ON
- [ ] Push protection ON（可能なら）

Push protection以外は導入予定

## 7. CIセキュリティチェック導入
- [ ] Dependency Review を導入
- [ ] CodeQL（Code Scanning）を導入
- [ ] pytest / lint / type check を導入

全て導入済み

## 8. GitHub Actions の安全性
- [ ] 不要な `secrets` を削除
- [ ] `permissions` を最小化
    - [ ] write-all を使っていない
    - [ ] contents: write を本当に必要か確認
    - [ ] workflowごとに最小権限になっている
- [ ] 長期トークン（PAT）を使っていない or 最小権限
    - [ ] `secrets.PAT` を使っていない
    - [ ] 使う場合は fine-grained
    - [ ] 権限が最小（contents: read など）
- [ ] OIDC(OpenID Connect=トークンを保存しない認証方式)利用可能なら採用
    - [ ] クラウド認証に secrets を使っていない
    - [ ] OIDC に置き換え可能か検討
    - [ ] id-token: write を設定している

全て守っている

## 9. 個人情報・内部情報チェック
- [ ] README に個人情報がない
- [ ] メールアドレスを公開していない（必要なら専用）
- [ ] 内部URL / IP / パスが含まれていない
- [ ] Git remote URL に private repo 情報がない

全てgit追跡ファイルから排除済み

## 10. 安全に再現できるか
- [ ] `git clone` → セットアップが正常にできる
- [ ] secrets なしでも最低限動く
- [ ] 本番環境に接続しない
- [ ] サンプル設定（`.env.example`）がある


# ✅ 最終確認

- [ ] main ブランチは直接 push 禁止（Ruleset / Branch protection）
- [ ] PR + CI + Review フローが成立している
- [ ] 第三者が見ても安全な状態



# 🚀 公開OK

すべてチェック済みなら

👉 **GitHubに公開してOK**
