# 各機能の概要

| 観点          | 主に使うもの     | 意図            |
| ----------- | ---------- | ------------- |
| コード整形・静的ルール | ruff       | 開発中の崩れをその場で直す |
| 軽量な型確認      | pyright    | 編集時の早期フィードバック |
| 厳格な型確認      | mypy       | 統合前の最終型保証     |
| 単体の動作確認     | pytest     | 実装単位の正しさを確認   |
| 仕様・振る舞い確認   | pytest-bdd | 要件をシナリオとして検証  |
| 網羅率の可視化     | coverage   | テスト不足を見える化    |


## ローカルとリモートのCIの担当
コード品質に関するチェックはセキュリティチェックとは異なり、developブランチまでに解決していれば良いという方針とする

そのため、ローカルでは開発効率を重視して軽量で即時性の高い確認を行い、GitHub Actions ではコード品質に関わる確認を網羅的に実施する。

### 分担

| 区分                 | ツール              | 主な役割                         | 実行する目的                      |
| ------------------ | ---------------- | ---------------------------- | --------------------------- |
| ローカル               | ruff             | 構文チェック、lint、import 整列、format | 日常的な修正を素早く検証し、その場で整えるため     |
| ローカル               | pyright（Pylance） | 軽量な型チェック                     | エディタ上で早い段階から型の不整合に気づくため     |
| ローカル               | pytest           | 単体テスト                        | 実装直後の基本動作をすぐ確認するため          |
| CI（GitHub Actions） | mypy             | 厳格な型チェック                     | ローカルでは拾いきれない型不整合を最終確認するため   |
| CI（GitHub Actions） | pytest           | 単体テスト                        | ローカル環境との差異があっても動作保証を維持するため  |
| CI（GitHub Actions） | coverage         | テスト網羅率の可視化                   | 未テスト箇所を把握し、検証の抜け漏れを見える化するため |


## 補足
### ruff
`pyproject.toml`のlintの有効なルールは基本的に下記を参照した
> https://zenn.dev/ohashi_reon/articles/25e66c44caef08#%E6%BA%96%E6%8E%A8%E5%A5%A8

また、lint とformat ルールが競合する場合は下記参照
> https://docs.astral.sh/ruff/formatter/#conflicting-lint-rules

## mypy
後日記載

## pytest-bdd
pytest 上で BDD（Behavior-Driven Development）を実践するためのプラグインです。
.feature ファイルに Gherkin 形式で仕様を書き、Python 側で Given / When / Then の実装を結び付けます。別ランナー不要で pytest の資産（fixture、marker、hook、plugin 群）をそのまま使えるのが大きな強み

実務向けの採用パターン

- ユニットテスト: 普通の pytest
- API/受け入れシナリオ: pytest-bdd
- 画面E2Eが大規模: 必要なら Playwright/Selenium 系と組み合わせ
- 非開発者主導の大規模業務自動化: そのときだけ Robot Framework も検討


# ブラウザでcoverageを確認したい
GitHub Pages で確認出来る
> https://USER.github.io/REPO/coverage/

PR commentの方法もある

## 準備
- Public repo
- リポジトリの Settings → Pages を開く
- Build and deployment の Source を GitHub Actions にする
