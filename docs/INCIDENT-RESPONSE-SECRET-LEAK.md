# Secret / Security Scan 失敗時対応手順

## 目的
本手順は、ローカルまたは CI において secret 検知や security check が失敗した際に、機密情報流出・脆弱性混入・危険な設定の公開を防ぐための対応方法を定める。

対象:
- detect-secrets
- gitleaks
- Trivy
- その他 security.yml 内のCIのセキュリティ検査


## 基本方針

優先順位は以下の通りとする。

1. 拡散防止
2. 事実確認
3. 本物の secret なら失効・ローテーション
4. 影響範囲確認
5. 必要に応じて履歴除去
6. 再発防止

重要事項:
- secret 系の失敗は、コード修正より先に「本物かどうか」「失効が必要か」を判断する
- CI で失敗した場合、解消まで merge しない
- ローカルで失敗した場合、解消まで commit / push しない
- 誤検知でも、無言で無視せず、最小範囲で allowlist / baseline に登録する


# 1. 対応レベル

## レベルA: 誤検知
以下に該当するもの:
- ダミー値
- テスト用固定文字列
- ドキュメント用サンプル
- 実在しない鍵・トークン
- 実際には認証に使えない値

対応:
- 誤検知であることを確認する
- 必要最小限の allowlist / baseline 更新を行う
- 理由をコメントまたはレビューで残す

## レベルB: 実在する secret の可能性あり
以下に該当するもの:
- API key らしき文字列
- token / PAT / access key / private key
- 認証 JSON / `.env` 実値
- URL や設定値に埋め込まれた資格情報
- 実在か即断できないもの

対応:
- 本物として扱う
- commit / push / merge を停止する
- 失効・ローテーション要否を確認する

## レベルC: 実在する secret の漏えい
以下に該当するもの:
- 現在有効な認証情報
- 高権限 credential
- 本番環境で使われる資格情報
- 既に GitHub へ push 済み
- CI ログや artifact に露出済み

対応:
- インシデントとして扱う
- 即時に失効・ローテーションを行う
- 必要なら履歴除去と周知を実施する


# 2. ローカルで detect-secrets / gitleaks が失敗した場合

## 2.1 初動
1. commit を中止する
2. push しない
3. 検知ファイル・行番号・種別を確認する
4. その値が本物か誤検知かを判定する

## 2.2 本物または判断保留の場合
1. ファイルから secret を削除する
2. 環境変数参照へ置き換える
3. 実ファイルを `.gitignore` に追加する
4. `.env.example` などの雛形に置き換える
5. 再スキャンする

### 未 commit の場合
- 修正して再スキャン後、通過したら通常作業へ戻る

### 既に local commit 済みの場合
1. secret の失効・ローテーション要否を判断する
2. 必要なら直ちに失効・再発行する
3. ローカル履歴から secret を除去する
4. 再スキャンする
5. 通過後にのみ push する

#### 2.2.1 直前の未 push commit だけに混入していた場合

- ケース: 直前の commit に .env を誤って含めたが、まだ push していない。

``` bash
git reset --soft HEAD~1
```

その後、.env を削除して .gitignore を修正し、改めて commit する。

``` bash
printf ".env\n" >> .gitignore
git rm --cached .env
git add .gitignore
git commit -m "Remove secret file and ignore it"
```

#### 2.2.2 特定ファイルをローカル履歴から完全除去したい場合

- ケース: config/prod.env を過去 commit に入れてしまった。

``` bash
git filter-repo \
  --sensitive-data-removal \
  --invert-paths \
  --path config/prod.env
```

GitHub Docs では、機微データ除去に `git-filter-repo` を推奨しており、`--sensitive-data-removal` を使う版として 2.47 以降を案内している。

#### 2.2.3 特定文字列だけ履歴から置換したい場合

- ケース: 文字列そのものだけ消したい。

まず置換ルールファイルを用意する。次に実行する。

```
# replace-text.txt
literal:sample_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx==>***REMOVED***
literal:AKIAxxxxxxxxxxxxxxxx==>***REMOVED***
```

``` bash
git filter-repo \
  --sensitive-data-removal \
  --replace-text replace-text.txt
```

ファイル丸ごと削除ではなく、特定 secret 文字列だけ消したいときの例。
GitHub は `sensitive data removal` の手順として `git-filter-repo` を案内している。

## 2.3 誤検知の場合
対応順は以下を推奨する。

1. 行単位の allowlist
2. ファイル単位の除外
3. ルール全体の緩和

注意:
- 広い除外を先に入れない
- allowlist / baseline 更新の理由を残す
- 誤検知対応だけの変更でもレビュー対象にする


### 2.3.1 detect-secrets の具体例

- ケース: テスト用のダミー秘密鍵文字列が検知されたが、実在しない。

乱用は禁物だが、理由コメント付きで`# pragma: allowlist secret` を使う

`TEST_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----dummy-----END PRIVATE KEY-----"  # pragma: allowlist secret`

- ケース: 既に .secrets.baseline を使っていて、誤検知として監査したい。

``` bash
uv run detect-secrets scan > .secrets.baseline
uv run detect-secrets audit .secrets.baseline
```

レビュー画面。 y で誤検知として登録されて .secrets.baseline に`"is_secret": false`が付加される

``` bash
sample code
...
---------
Should this string be committed to the repository? (y)es, (n)o, (s)kip, (q)uit: y
Saving progress...
```

運用上は、audit で誤検知として確認したものだけを baseline に残し、baseline の丸ごと再生成で雑に上書きしない。
detect-secrets は baseline と audit を前提にした運用を想定している。


### 2.3.2 gitleaks の具体例

- ケース: tests/fixtures/ 配下にある明らかなダミー文字列だけ除外したい。

``` yml
[allowlist]
description = "test fixtures only"
paths = [
  '''tests/fixtures/.*'''
]
```

ケース: README のサンプル token 風文字列だけ除外したい。

``` yml
[allowlist]
description = "documentation sample token"
regexes = [
  '''ghp_example_only_not_real_token'''
]
```

実運用では、パス単位か限定 regex の allowlist を優先し、リポジトリ全体に効く広い除外は避ける。
これは secret scanning の目的である「本物の露出防止」を損ないにくい運用のため

# 3. CI で detect-secrets / gitleaks が失敗した場合

## 3.1 初動
1. PR を merge しない
2. 対象ブランチへの追加 push を慎重に判断する
3. ログ・サマリー・レポートから検知箇所を特定する
4. 本物か誤検知かを判定する

## 3.2 誤検知の場合
1. 検知箇所が実在 secret でないことを確認する
2. 最小範囲で allowlist / baseline / 設定を更新する
3. 再実行して通過確認する
4. レビューで「なぜ誤検知と判断したか」を共有する

## 3.3 本物の secret の場合
1. インシデント扱いとする
2. secret の失効・ローテーションを行う
3. 影響範囲を確認する
4. 必要なら履歴除去を行う
5. 再スキャン通過後に PR を作り直す、または force-push で修正する


# 4. 本物の secret 漏えい時の詳細対応

## 4.1 直後の対応
以下を優先する。

1. 拡散防止
2. secret の失効・ローテーション
3. 影響範囲確認
4. リポジトリ清掃
5. 再発防止

## 4.2 拡散防止
- PR merge を止める
- Slack / Issue / コメントに secret を貼らない
- 追加の commit / push を止める
- CI ログや artifact を確認する
- 必要なら関連 workflow を一時停止する

## 4.3 secret の失効・ローテーション
対象例:
- GitHub PAT
- AWS / GCP / Azure credential
- npm / PyPI token
- SSH private key
- deploy key
- `.env` 内の本番用値
- サービスアカウント鍵

実施項目:
1. 現在の secret を無効化する
2. 新しい secret を発行する
3. 参照先を新しい値へ差し替える
4. CI secrets / secret manager / 本番設定 / staging 設定も更新する
5. 動作確認を行う

## 4.4 影響範囲確認
以下を確認する。

- どの commit から混入したか
- どの branch / tag に含まれるか
- PR diff に露出したか
- Actions logs / artifacts / step summary に出ていないか
- fork / clone 済みの可能性があるか
- 外部サービスで利用痕跡がないか

最低限の確認先:
- Git history
- PR diff
- CI logs
- artifact
- 対象サービスの監査ログ
- token 利用履歴


# 5. 履歴除去の判断

## 5.1 履歴除去が必要になりやすいケース
- GitHub へ push 済み
- 高権限 secret
- 長期有効 credential
- private key
- fork / clone 済みの可能性が高い
- 組織ルール上「履歴残存不可」

### 5.1 典型例 1: push 済みの .env を全履歴から消す
``` bash
git clone --mirror git@github.com:OWNER/REPO.git repo-mirror.git
cd repo-mirror.git

git filter-repo \
  --sensitive-data-removal \
  --invert-paths \
  --path .env \
  --path app/.env

git push --force --mirror
```

用途: .env のようなファイルが branch や tag をまたいで残っている場合。
GitHub は、機微データ削除後に push しただけでは終わらず、必要に応じて追加対応やサポート連携が必要な場合があると案内している。

### 5.2 典型例 2: 特定 branch だけでなく tags も含めて洗浄したい
``` bash
git filter-repo \
  --sensitive-data-removal \
  --replace-text replace-text.txt

git push --force --all
git push --force --tags
```

用途: token がリリース tag にも乗っている可能性がある場合。
履歴改変後は、チーム側で古い clone から再 push すると再汚染するので、再 clone か hard reset を徹底。

### 5.3 典型例 3: GitHub に push 済みで secret scanning alert も出ている
1. 先に secret を revoke / rotate
1. 履歴除去
1. 再 push
1. GitHub 上で alert を手動で close する

GitHub は、secret scanning alert は対象 token を単に削除しただけでは自動で閉じず、手動で close する必要があると案内している

## 5.2 履歴除去を慎重判断できるケース
- 既に失効済み
- 低権限または短命 token
- 実害が起きにくい
- private repo 限定で拡散範囲が小さい

注意:
- 失効済みでも、組織ルールによっては履歴除去が必要
- 判断に迷う場合は厳しめに扱う


# 6. 履歴除去手順

## 6.1 事前準備
1. 作業担当者を決める
2. 一時的に merge / push を止める
3. チームへ履歴改変予定を周知する
4. バックアップを取得する

## 6.2 対象明確化
- 除去対象ファイル
- 除去対象文字列
- 対象 branch / tag
- 再作成が必要な PR

## 6.3 実施後の必須確認
1. 再スキャン
2. force-push
3. tags の更新要否確認
4. GitHub 上の表示確認
5. チームへ再同期方法を案内

## 6.4 チームへの案内事項
- 古い clone を再利用しない
- 必要に応じて再 clone する
- 少なくとも hard reset / fetch で同期する
- 古い branch を再 push しない


# 7. CI ログ / artifact / summary に secret が出た場合

## 7.1 対応
1. secret を失効・ローテーションする
2. workflow logs を削除またはアクセス制御する
3. artifacts を削除する
4. 生成された markdown / summary / JSON レポートを確認する
5. 再発防止としてログ出力内容を見直す

### 7.1.1 GitHub Web から workflow logs を削除する
- ケース: GitHub Actions ログに secret の一部が出てしまった。

手順:
1. GitHub リポジトリの Actions を開く
1. 対象 workflow を開く
1. 対象 run を開く
1. 右上のハンバーガーメニューから Delete all logs を選ぶ

GitHub は、workflow run のログを Web UI またはプログラム的に削除でき、実行には write 権限が必要としている

### 7.1.2 REST API で workflow logs を削除する例
- ケース: run ID が分かっており、CLI から即削除したい。

``` bash
gh api \
  -X DELETE \
  repos/OWNER/REPO/actions/runs/RUN_ID/logs
```

GitHub REST API には workflow run logs の削除 endpoint がある

### 7.1.3 アクセス制御の実務例
ログ単体の細かい ACL を後付けで掛けるより、実務ではリポジトリ自体の閲覧者を絞るのが即効性があります。
特に private repository では、不要な collaborator / team のアクセスを一時的に外す、
または incident 対応が終わるまで閲覧可能メンバーを最小化する運用が現実的です。
workflow run 情報の閲覧は GitHub アカウントでのアクセス権に依存します。

### 7.1.4 workflow logs を削除への再発防止例
ログへ値そのものを出さない。

``` yaml
- name: Bad example
  run: echo "TOKEN=${{ secrets.MY_TOKEN }}"

- name: Better example
  run: echo "authentication configured"
```

GitHub は Actions の secure use guidance で、workflow 記述時の秘密情報の扱いに注意するよう案内している。

### 7.1.5 GitHub Web から artifact を個別削除する
- ケース: security-report.md artifact に secret が含まれていた。

手順:
1. GitHub リポジトリの Actions を開く
1. 対象 workflow を開く
1. 対象 run を開く
1. artifact 一覧から対象 artifact を削除する

GitHub は artifact の個別削除をサポートしており、削除後は復元できないと案内している

### 7.1.6 workflow run ごと削除して artifact もまとめて消す
- ケース: その run 全体が危険で、ログも artifact も全部消したい。

``` bash
gh run delete RUN_ID
```

GitHub CLI には `gh run delete` があり、GitHub Docs では workflow run を削除すると、その run に紐づく artifact も一緒に削除されると説明されている

### 7.1.7 REST API で artifact を削除する例
- ケース: artifact ID が分かっていて、スクリプトから消したい。
``` bash
gh api \
  -X DELETE \
  repos/OWNER/REPO/actions/artifacts/ARTIFACT_ID
```

GitHub REST API には artifact の削除 endpoint がある

### 7.1.8 retention を短くして被害面積を減らす例
- ケース: security 系 artifact は長期保存しない。

運用例:
1. security report artifact の保存日数を短くする
1. 組織または repository の Actions retention を短めに設定する

GitHub は artifact と log の保持期間を設定でき、既定では 90日保持されると案内している


## 7.2 再発防止
- 生の secret 値を出力しない
- エラー文に secret を含めない
- report にはファイル名・行番号・種別のみ出す
- 必要ならマスク処理を入れる


# 8. Trivy が失敗した場合

Trivy は主に以下を検知する。
- 脆弱性
- 設定不備
- 一部 secret / license

そのため、detect-secrets / gitleaks とは運用を分ける。

## 8.1 Trivy config failure
対象例:
- Dockerfile の危険な書き方
- GitHub Actions の危険設定
- IaC 設定不備
- Kubernetes / Terraform / CloudFormation の危険設定

対応:
1. レポートの rule ID を確認する
2. 危険設定の内容を理解する
3. 修正可能なら直す
4. 正当な理由がある場合のみ ignore を検討する
5. ignore 時は理由をコメントまたは設定ファイルに残す

## 8.2 Trivy fs failure
対象例:
- 依存パッケージの HIGH / CRITICAL 脆弱性
- ベースイメージ由来の脆弱性
- OS パッケージ脆弱性

対応:
1. 該当パッケージと severity を確認する
2. 修正版への更新可否を確認する
3. 直接依存か間接依存かを確認する
4. 修正版がない場合は一時保留の妥当性を判断する
5. 例外化する場合は期限と理由を残す

## 8.3 Trivy 失敗時の判断
- secret 漏えいと異なり、通常は即失効対応ではない
- ただし公開前に直すべき問題かどうかは severity と到達性で判断する
- HIGH / CRITICAL は原則修正優先とする


# 9. 誤検知対応ルール

## 9.1 基本原則
- 無言で握りつぶさない
- 広すぎる除外を入れない
- なぜ誤検知なのか説明可能にする

## 9.2 推奨順
1. 行単位
2. ファイル単位
3. ルール単位

## 9.3 コメント例
```py
TEST_PRIVATE_KEY = "-----BEGIN PRIVATE KEY-----dummy-----END PRIVATE KEY-----"  # pragma: allowlist secret
