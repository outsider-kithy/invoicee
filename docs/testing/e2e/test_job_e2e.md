# `test_job_e2e.py` E2Eテスト仕様書

## 1. 概要

- **対象機能**：ジョブ登録（`/record/`）
- **対象ファイル**：`tests/e2e/test_job_e2e.py`
- **対象実装**：`record/views.py`、`record/templates/record/index.html`、`models.py` の `Job`、`Project`、`Tool` など
- **テスト技術**：pytest、Playwright（Chromium）、SQLAlchemy、PostgreSQL
- **テストDB**：`invoicee_test`
- **実行結果**：**13ケースすべてPASS**（ユーザー確認済み）

### テスト目的

ジョブ登録画面の表示、フォームからの登録、DBへの保存、Project・Toolからの属性引き継ぎ、必須項目の検証、ログイン制限を、ブラウザ操作とDB照合によって確認する。

## 2. 対象機能の仕様

### GET `/record/`

- `@login_required` により認証済みユーザーだけがアクセス可能。
- `Project.isfinished == 0` のプロジェクトを取得し、`#project` の選択肢として表示する。
- `Tool` を取得し、`#tool` の選択肢として表示する。
- フォームにはジョブタイトル（`#title`、HTML `required`）、プロジェクト（`#project`）、ツール（`#tool`）、GitHubリポジトリ（`name="github_repository"`）を設置する。

### POST `/record/`

- `title`、`project`、`tool` が空の場合は `flash()` を設定して `/record/` にリダイレクトする。なお、現在の実装では複数の項目が空の場合、後の条件でエラーメッセージが上書きされる。
- 選択されたツール名に一致する `Tool` が存在しなければ、エラーを表示して `/record/` に戻る。
- 選択されたプロジェクト名に一致する `Project` が存在しなければ、エラーを表示して `/record/` に戻る。
- 正常時は `Job` を追加し、コミット後に `/top/` へリダイレクトする。

### Jobに保存される主な値

| Jobカラム | 設定元・初期値 |
|---|---|
| `title` | フォームの `title` |
| `tool_type_id` | 選択した `Tool.id` |
| `client_id` | 選択した `Project.client_id` |
| `agency_id` | 選択した `Project.agency_id` |
| `account_id` | 選択した `Project.account_id` |
| `project_id` | 選択した `Project.id` |
| `price` | 選択した `Tool.price` |
| `estimated` | `0` |
| `invoiced` | `0` |
| `github_repository` | フォームの `github_repository` |

## 3. テストケース一覧

| ID | テスト関数 | 検証内容 | 結果 |
|---|---|---|---|
| JOB-E2E-001 | `test_job_page_display` | 登録画面の入力要素を表示できる | PASS |
| JOB-E2E-002 | `test_job_registration` | 新規JobがDBに登録される | PASS |
| JOB-E2E-003 | `test_job_project_relationship` | `project_id` が選択したProjectと一致する | PASS |
| JOB-E2E-004 | `test_job_related_entities` | 顧客・代理店・担当者IDがProjectから引き継がれる | PASS |
| JOB-E2E-005 | `test_job_tool_and_price` | ツールIDと価格がToolから引き継がれる | PASS |
| JOB-E2E-006 | `test_job_initial_status` | `estimated` と `invoiced` がともに0 | PASS |
| JOB-E2E-007 | `test_job_github_repository` | GitHubリポジトリ文字列が保存される | PASS |
| JOB-E2E-008 | `test_job_registration_redirect` | 登録後に `/top/` へ遷移する | PASS |
| JOB-E2E-009 | `test_job_without_project` | プロジェクト未選択時は登録されない | PASS |
| JOB-E2E-010 | `test_job_without_tool` | ツール未選択時は登録されない | PASS |
| JOB-E2E-011 | `test_finished_project_not_selectable` | 終了済みProjectは選択肢に表示されない | PASS |
| JOB-E2E-012 | `test_job_page_requires_login` | 未ログイン時にログイン画面へ遷移する | PASS |
| JOB-E2E-013 | `test_job_title_required` | タイトル未入力時はHTMLバリデーションで送信されない | PASS |

## 4. 各テストの手順と期待結果

### JOB-E2E-001：登録画面の表示

**前提**：ログイン済み。

1. `/record/` を開く。
2. `#title`、`#project`、`#tool`、`input[name="github_repository"]` の表示を確認する。

**期待結果**：URLが `/record/` で、各フォーム要素が表示される。

### JOB-E2E-002：新規ジョブ登録

**前提**：テスト用Project・Toolと関連データが存在する。

1. 一意のジョブタイトルを入力する。
2. テスト用ProjectとToolを選択し、送信する。
3. DBから同じタイトルのJobを取得する。

**期待結果**：Jobが存在し、`id` と `title` が適切に設定される。送信後は `/top/` に遷移する。

### JOB-E2E-003：プロジェクトとの紐づけ

1. テスト用Projectを選んでJobを登録する。
2. DB上の `Job.project_id` を確認する。

**期待結果**：`Job.project_id == Project.id`。

### JOB-E2E-004：顧客・代理店・担当者との紐づけ

1. 関連するClient・Agency・Accountを持つProjectを用意する。
2. Jobを登録し、DBの3つの外部キーを確認する。

**期待結果**：`client_id`、`agency_id`、`account_id` がProjectの対応する値と一致する。

### JOB-E2E-005：ツールと価格の引き継ぎ

1. 価格 `12000` のテスト用Toolを選択してJobを登録する。
2. `Job.tool_type_id` と `Job.price` を確認する。

**期待結果**：ToolのIDと価格が正しく引き継がれる。

### JOB-E2E-006：初期ステータス

1. Jobを新規登録する。
2. DBの `estimated` と `invoiced` を確認する。

**期待結果**：両方とも `0`。

### JOB-E2E-007：GitHubリポジトリ

1. GitHubリポジトリ欄に `outsider-kithy/e2e-test-repository` を入力する。
2. Jobを登録し、DBの `github_repository` を確認する。

**期待結果**：入力文字列がそのまま保存される。

### JOB-E2E-008：登録後のリダイレクト

1. 必須項目を入力してJobを登録する。

**期待結果**：ブラウザURLが `/top/` になる。

### JOB-E2E-009：プロジェクト未選択

1. タイトルとツールを指定し、プロジェクトは選択せず送信する。
2. 指定タイトルのJob件数をDBで確認する。

**期待結果**：`/record/` に戻り、該当Job件数は `0`。

### JOB-E2E-010：ツール未選択

1. タイトルとプロジェクトを指定し、ツールは選択せず送信する。
2. 指定タイトルのJob件数をDBで確認する。

**期待結果**：`/record/` に戻り、該当Job件数は `0`。

### JOB-E2E-011：終了済みプロジェクトの非表示

1. テスト用Projectの `isfinished` を `1` に更新する。
2. `/record/` を開き、プロジェクト選択肢を確認する。

**期待結果**：終了済みProjectが選択肢に存在しない。

**範囲**：画面上の非表示を確認するテストであり、直接POSTによる登録禁止は検証していない。

### JOB-E2E-012：未ログイン時のアクセス制限

1. 未認証の `page` で `/record/` を開く。

**期待結果**：`/login/` へリダイレクトされる。

### JOB-E2E-013：タイトル必須入力

1. タイトルを空欄にしたまま、ProjectとToolを選択する。
2. 送信ボタンをクリックする。
3. タイトル欄の `validity.valueMissing` を確認する。

**期待結果**：ブラウザが送信をブロックし、URLは `/record/` のまま、`valueMissing == true` になる。

## 5. fixtureと共通関数

| 名称 | 役割 |
|---|---|
| `job_db(e2e_config)` | `.env.test` の接続先からエンジンを作成し、DB名が `invoicee_test` であることを検証する |
| `job_title()` | UUID由来の一意なジョブタイトルを生成する |
| `job_dependencies(job_db)` | Tax・Client・Agency・Account・Project・Toolを準備し、終了時に後片付けする |
| `register_job(...)` | ブラウザでフォームに入力して送信する |
| `get_job(db_engine, title)` | タイトルから登録Jobを取得する |
| `count_jobs_by_title(db_engine, title)` | 同名Jobの件数を確認する |
| `auth_page` | 共通 `conftest.py` のログイン済みPlaywrightページ |
| `e2e_server` | 共通 `conftest.py` のFlaskテストサーバー |

### テストデータ作成順序

1. 既存のTaxを取得（なければ作成）。
2. ClientとAgencyを作成。
3. Agencyに紐づくAccountを作成。
4. Client・Agency・Accountを参照するProjectを作成。
5. Taxを参照するToolを作成。
6. Jobはテスト本体でブラウザから登録する。

### クリーンアップ順序

`Job → Project → Tool → Account → Agency → Client → Tax（新規作成した場合のみ）`

関連する外部キー制約に配慮し、Jobを削除してから関連データを削除する。`Job.content` の関連レコードは今回のテストでは作成しない。将来Contentも生成するテストを追加した場合は、Job削除前のクリーンアップが必要になる可能性がある。

## 6. テスト実行方法

```bash
# ジョブ登録E2Eテストのみ
python -m pytest tests/e2e/test_job_e2e.py -v

# ブラウザを表示して実行
python -m pytest tests/e2e/test_job_e2e.py -v --headed

# 標準出力も表示
python -m pytest tests/e2e/test_job_e2e.py -v -s

# E2Eテスト全体
python -m pytest tests/e2e/ -v
```

## 7. 実行結果

ユーザーによる実行確認：**13件すべてPASS**。

本書は共有されたテストコードと実行結果の報告に基づく仕様書であり、実行ログや実行日時は別途採取していない。

## 8. 留意事項と追加テスト候補

- **直接POSTの異常系**：存在しないProject名やTool名をPOSTした際、登録されず `/record/` に戻ること。
- **終了済みProjectの直接POST**：現在のPOST処理はProject検索時に `isfinished == 0` を条件としていないため、終了済みProjectでも直接POSTできる可能性がある。禁止したい場合はサーバー側の検証を追加する。
- **GitHubリポジトリ空欄**：任意入力として空文字の登録が成功すること。
- **同名ジョブ**：同名タイトルを複数登録する場合の期待仕様の明確化。
- **タイトル未入力のサーバー側検証**：今回のJOB-E2E-013はHTML `required` によるブラウザ側検証。直接POSTした場合のFlask側検証は別途確認する。
- **選択肢の一意性**：現在のサーバー処理は名称から `.first()` でProject・Toolを取得するため、同名レコードがある場合の動作を確認する。
- **DB安全性**：`invoicee_test` の確認に加え、実行環境で本番DBと接続先が異なることを継続して検証する。

---

**総括**：ジョブ登録に関する画面表示、登録、関連ID・価格・初期値の保存、必須項目、認証制限の主要な13ケースを検証し、すべてPASSした。
