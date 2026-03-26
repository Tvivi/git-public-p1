# 各機能の概要

| 機能                    | 何を検出するか                                           | 主な対象                                                        | 主な用途                                     | 補足                                                                                                                                               |
| --------------------- | ------------------------------------------------- | ----------------------------------------------------------- | ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **detect-secrets**    | ソースコードや設定ファイルに混入した **secret**（APIキー、トークン、パスワードなど） | Git管理下のファイル、指定ファイル群                                         | **ローカル pre-commit / CI で新規 secret 混入防止** | `baseline` を作って既知の検出結果を管理し、**差分運用**しやすいのが強みです。 ([GitHub][1])                                                                                     |
| **Gitleaks**          | ハードコードされた **secret**                              | Git履歴、repo全体、ファイル、stdin                                     | **履歴を含めた secret 漏洩監査**、CIでの一括スキャン        | `git` / `dir` / `stdin` など対象が広く、**Git履歴全体のチェック**に強いです。 ([GitHub][2])                                                                             |
| **Trivy config**      | **misconfiguration**（危険な設定、ベストプラクティス違反）           | Dockerfile、Terraform、Kubernetes YAML、CloudFormation、Helm など | **IaC / Docker / CI設定の安全性チェック**          | `trivy config` は設定ファイル専用で、**脆弱性そのものではなく設定の危険性**を見ます。 ([Trivy][3])                                                                                |
| **Trivy fs**          | **脆弱性、misconfiguration、secret、license**           | プロジェクトディレクトリ全体、lockファイル等                                    | **repo全体の横断スキャン**                        | `trivy fs` は filesystem を対象に広く見ます。公式では local project に対して vulnerabilities / misconfigurations / secrets / licenses をスキャンできるとされています。 ([Trivy][4]) |
| **pip-licenses**      | **依存ライブラリのライセンス情報**                               | pipで入った Python パッケージ                                        | **公開前のライセンス棚卸し**、配布可否確認                  | セキュリティツールではなく、**OSSライセンス確認**用です。 ([PyPI][5])                                                                                                     |
| **pip-audit**         | Python依存の **既知脆弱性**                               | Python環境、requirements、依存パッケージ                               | **Python専用の依存脆弱性監査**                     | PyPAの公式ツールで、**Python依存に既知脆弱性があるか**を見る用途に特化しています。 ([GitHub][6])                                                                                   |
| **Dependabot**        | 依存関係の **脆弱性通知** と **更新PR作成**                      | GitHub上の依存関係                                                | **依存更新の自動化**、脆弱性修正版への追従                  | GitHub公式では Dependabot を複数機能の総称として説明しており、**security updates** と **version updates** が中心です。 ([GitHub Docs][7])                                     |
| **Dependency Review** | PRで追加・更新された依存関係の **リスク**                          | Pull Request 上の dependency 差分                               | **PRレビュー時の危険な依存追加の検知**                   | 依存関係の **license / age / dependents / 脆弱性** などをレビューできます。 ([GitHub Docs][8])                                                                       |
| **CodeQL**            | コード中の **脆弱な実装・危険なパターン**                           | アプリケーションコード                                                 | **SAST / code scanning**                 | GitHubのコード解析エンジンで、結果は **code scanning alerts** として表示できます。 ([GitHub Docs][9])                                                                     |

[1]: https://github.com/Yelp/detect-secrets?utm_source=chatgpt.com "Yelp/detect-secrets: An enterprise friendly way ..."
[2]: https://github.com/gitleaks/gitleaks?utm_source=chatgpt.com "Find secrets with Gitleaks"
[3]: https://trivy.dev/docs/latest/references/configuration/cli/trivy_config/?utm_source=chatgpt.com "Config"
[4]: https://trivy.dev/docs/latest/target/filesystem/?utm_source=chatgpt.com "Filesystem"
[5]: https://pypi.org/project/pip-licenses/?utm_source=chatgpt.com "pip-licenses"
[6]: https://github.com/pypa/pip-audit/blob/main/README.md?utm_source=chatgpt.com "pip-audit/README.md at main"
[7]: https://docs.github.com/en/code-security/tutorials/secure-your-dependencies/dependabot-quickstart-guide?utm_source=chatgpt.com "Dependabot quickstart guide"
[8]: https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review?utm_source=chatgpt.com "About dependency review"
[9]: https://docs.github.com/code-security/code-scanning/introduction-to-code-scanning/about-code-scanning-with-codeql?utm_source=chatgpt.com "About code scanning with CodeQL"

# 公開前チェックでの役割分担
機密情報流出の恐れがある `detect-secrets, Gitleaks`のみ**ローカルでもチェック**するが、それ以外はCIやGitHubで実施で良い
検出されるのは脆弱性なので、developブランチまでに解決していれば良い


| 観点                                       | 担当                   |
| ---------------------------------------- | ------------------------ |
| secret を誤って入れていないか                       | detect-secrets, Gitleaks |
| Dockerfile / Terraform / YAML の設定が危険でないか | Trivy config             |
| repo全体に脆弱性や問題がないか                        | Trivy fs                 |
| Python依存に既知脆弱性がないか                       | pip-audit                |
| 依存ライブラリのライセンスに問題がないか                     | pip-licenses             |
| GitHub上で依存更新を自動化したい                      | Dependabot               |
| PRで危険な依存追加を止めたい                          | Dependency Review        |
| コード実装そのものの脆弱性を見たい                        | CodeQL                   |



## detect-secrets
初回コミット時にscan結果を`.secrets.baseline`に保管し、誤検知判定を行う。以降はbaseline（既知の検出結果一覧） を用いて差分で「新しく混入した secret」を検出しやすい

scanした際にリークが含まれると下記のようになる

```
  "results": {
    "SampleFilename": [
      {
        "type": "GitHub Token",
        "filename": "SampleFilename",
        "hashed_secret": "リーク対象のhash値", # pragma: allowlist secret
        "is_verified": false,
        "line_number": 136, # リークが起きたファイルの行
        "is_secret": false # audit で無視を選ぶと出現する
      }
    ]
  },
```

!!! ローカルとCIのscanコマンドは合わせているが、何故かCIでのみ`detect-secrets`がエラーを吐くことがあった。
その際は意図せずCI環境のworkplaceが汚されたことで、ローカルとCIでREADME.mdが一致しないことが原因で起きた

## gitleaks
`detect-secrets`とかなり似通っているが、過去のGit 履歴まで含めてスキャン出来るのが違う
CIでエラーが出るとエラーが出たコミットを解消しない限り、ずっとエラーが出続ける

!!! 上記の`.secrets.baseline`のhashがエラー対象と言われることもあったので、扱いは慎重に


### 将来的には初回だけローカルで実施かも
gitleaksで既存の負債いったん固定出来る。以降は`--baseline-path`を付ければ負債を除外？してくれる
でも`.gitleaks.toml`だけで十分な気もする

``` bash
gitleaks git \
  --config .gitleaks.toml \
  --report-format json \
  --report-path .gitleaks-baseline.json \
  .
```

``` bash
gitleaks git \
    --config .gitleaks.toml \
    --baseline-path .gitleaks-baseline.json \
    --report-format json \
```

## trivy config
追記すべきことはない

``` bash
(calc-app) vscode ➜ /workspace (main) $ trivy config --format json -o artifacts/repo/trivy-config.json .
2026-03-21T08:09:09Z    INFO    [misconfig] Misconfiguration scanning is enabled
2026-03-21T08:09:09Z    INFO    [checks-client] Need to update the checks bundle
2026-03-21T08:09:09Z    INFO    [checks-client] Downloading the checks bundle...
234.65 KiB / 234.65 KiB [---------------------------------------------------------------------------] 100.00% 196.26 KiB p/s 1.4s
2026-03-21T08:09:50Z    INFO    Detected config files   num=1
(calc-app) vscode ➜ /workspace (main) $ trivy fs --format json -o artifacts/repo/trivy-fs.json .
2026-03-21T08:10:47Z    INFO    [vulndb] Need to update DB
2026-03-21T08:10:47Z    INFO    [vulndb] Downloading vulnerability DB...
2026-03-21T08:10:47Z    INFO    [vulndb] Downloading artifact...        repo="mirror.gcr.io/aquasec/trivy-db:2"
88.14 MiB / 88.14 MiB [----------------------------------------------------------------------------] 100.00% 444.29 KiB p/s 3m23s
2026-03-21T08:14:14Z    INFO    [vulndb] Artifact successfully downloaded       repo="mirror.gcr.io/aquasec/trivy-db:2"
2026-03-21T08:14:14Z    INFO    [vuln] Vulnerability scanning is enabled
2026-03-21T08:14:14Z    INFO    [secret] Secret scanning is enabled
2026-03-21T08:14:14Z    INFO    [secret] If your scanning is slow, please try '--scanners vuln' to disable secret scanning
2026-03-21T08:14:15Z    INFO    [secret] Please see https://trivy.dev/docs/v0.69/guide/scanner/secret#recommendation for faster secret detection
2026-03-21T08:15:01Z    INFO    Suppressing dependencies for development and testing. To display them, try the '--include-dev-deps' flag.
2026-03-21T08:15:01Z    INFO    Number of language-specific files       num=1
2026-03-21T08:15:01Z    INFO    [uv] Detecting vulnerabilities...
(calc-app) vscode ➜ /workspace (main) $ uv run python scripts/security/trivy_summary.py --scan-type config --input artifacts/repo/trivy-config.json --summary-file artifacts/repo/trivy-config-summary.md
(calc-app) vscode ➜ /workspace (main) $ uv run python scripts/security/trivy_summary.py --scan-type fs --input artifacts/repo/trivy-fs.json --summary-file artifacts/repo/trivy-fs-summary.md
```

## trivy fs
追記すべきことはない

## pip-licenses
ライセンス情報を一覧化するだけで脆弱性を見つけるものではない。

MIT / BSD / Apache / GPL などの ライセンス確認・配布可否確認 が目的で公開前に「この依存関係を含めて配布して問題ないか」を確認する用途に向いている。

## pip-audit
Pythonの依存パッケージの依存関係に、既知の脆弱性(CVE)が含まれていないかを検査するツール。

PyPA Advisory Database などの脆弱性情報を使って、requirements / lock / 現在の環境を監査できる。

```
Found 1 vulnerable package(s) ❌

pygments@2.19.2: CVE-2026-4539
Fix version(s): none suggested

💡 Fix hints
Update vulnerable packages directly: uv add <package>@latest
Or refresh lock file broadly: uv lock --upgrade
Inspect dependency tree: uv tree
Re-run locally: uv run pip-audit
```


## Dependabot
GitHub の依存関係管理機能群。下記3つで構成される

- Dependabot alerts: 脆弱な依存関係の通知
- Dependabot security updates: 修正版へ更新する PR の自動作成
- Dependabot version updates: 脆弱性有無に関係なく通常更新の PRを`dependabot.yml`に従って定期的に作る

検出だけでなく、修正PR作成まで面倒を見てくれるのが強み

### GitHubでの設定

- Dependency graph を有効化
    これがないと GitHub が依存関係を把握しづらく、Dependabot alerts / security updates の前提が崩れます。security updates は dependency graph と Dependabot alerts が有効なリポジトリで動作します。
- Dependabot alerts を有効化
    脆弱性が見つかったときに Security タブや dependency graph に alert が出ます。alert ごとに影響ファイル、脆弱性情報、修正版の有無などを確認できます。
- Dependabot security updates を有効化
    脆弱性修正 PR の自動作成に必要です。
    ただし、修正 PR が作られやすいのは manifest / lock file に明示された依存関係 です。間接依存だけで lock file に十分な情報がない場合などは、alert は出ても PR が出ないことがあります。
- version updates を使うなら `.github/dependabot.yml` を追加
    version updates は設定ファイルをコミットして有効化します。GitHub が初期ファイルを作ることもありますが、通常は自分で管理するのが実務向きです。
- Python だけでなく GitHub Actions も更新対象にするとよい
    Dependabot は github-actions エコシステムも扱えます。workflow の action バージョン固定をしているなら、これも自動更新対象にすると保守性が上がります

## Dependency Review
Pull Request に含まれる依存関係の変更を見て、新しく追加・更新される依存関係のリスクをレビューする
既存リポジトリ全体を定期監査するというより、PR単位で「この変更で危険な依存が入っていないか」 を確認するための仕組み。
pip-audit は 現在のPython依存を監査するが、Dependency Review は PRに含まれる依存変更をレビューするので見るタイミングが違う

公開前やマージ前のゲートとして有効。

Dependency Reviewはpython_licenses-check.ymlに取り込む予定。
dependency-review-config.yml

### GitHubでの設定

1. リポジトリ種別を確認
    public ならそのまま、private なら GitHub Code Security か GHAS を有効化。
2. Dependency graph を有効化
    `Settings → Advanced Security`から依存関係が GitHub に認識される状態にする。
3. GitHub Actions を有効化
    workflow を動かせるようにする。
4. Workflow を追加
    `.github/workflows/dependency-review.yml` を置く。
5. Branch protection / Ruleset で必須化
    PR の merge 前ゲートとして使う。

## CodeQL
「脆弱性の型」を深く追えるGitHub の code scanning で使える静的解析。たとえば「外部入力がサニタイズされず危険な API に届く」ような問題を、ソースからシンクまでの流れとして検出できる

単なる AST ルールではなく、データフローや制御フローを追跡するクエリを書ける点で、フレームワークや独自ライブラリ向けにモデルを拡張することもできる（`.yml`で対応）

単純な lint(Ruff) では見つからない危険パターンも検知できる

### 誤検知の抑制
下記２つの方法が考えられる

- suppression comment(`# codeql[query-id]`)を使う
    query-idはcode-scanningページののRule IDに記載がある
- GitHub の Security タブでこの alert を Dismiss → false positive にする
    false positive にした履歴は Closedタブで見れる
- ファイルを CodeQL 対象から外す(`codeql.yml`限定)

### GitHubでの設定

- リポジトリが public か / private なら GitHub Code Security があるかを確認。
    - public で使うことを想定
- GitHub Actions が有効か確認。
    - CIが使えていれば問題なし
- リポジトリ設定の Advanced Security 画面に入れる権限があるか確認。
    - public で`Settings → Advanced Security` もしくは `Settings → Code security and analysis` に入れるはず
- default setup で始めるか、advanced setup でワークフロー管理するか決める。
    - 最初はdefault setup で始めるとGitHubが良しなにやってくれる
    - advanced setup でにすると`.yml`で独自設定を作れるようになる
- advanced setup なら、Actions 権限とワークフローポリシーを確認。
    - Code scanning の結果をアップロードするワークフローでは、通常 `security-events: write` などの権限設定が関係
- コンパイル言語やコンテナ利用時は、ビルド方法・実行環境を先に整理する。

## ruleset
後日記載

## SARIF = Static Analysis Results Interchange Format

的解析ツールの結果を保存・交換するための JSON ベース標準形式です。GitHub はこの SARIF を受け取って、Security タブや Code scanning alerts に結果を表示できます

今のところSARIF をtrivyなどに採用するつもりはない

### サードパーティーにSARIFを用いて連携させるべきかの判断基準
#### GitHub Code Scanning 向き
次の条件を満たすものです。

- 問題が 特定ファイル・特定行 にひも付く
- PR や Security タブで アラートとして追跡したい
- 修正対象がコードや IaC ファイルそのもの

#### Step Summary 向き
次のようなものです。

- 結果が 依存パッケージ一覧 ベース
- 漏洩候補一覧 や 監査レポート として読むほうが自然
- 誤検知レビューや運用判断が多く、GitHub の code scanning アラート化が必須ではない
