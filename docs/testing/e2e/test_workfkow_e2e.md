# ワークフロー E2Eテスト仕様書 — `test_workflow_e2e.py`

## 1. 概要

Flaskアプリケーション **invoicee** の主要な業務操作を、**ログインからログアウトまで同じブラウザセッション**で検証する。管理画面でのマスターデータ登録、ジョブ登録、トップ画面への反映、見積書Excel出力、見積状態更新、およびログアウト後のアクセス制限を一連の流れとして確認する。

- **テストファイル**：`tests/e2e/test_workflow_e2e.py`
- **テストケース**：`WORKFLOW-E2E-001`（`test_workflow_login_to_logout`）
- **実行結果**：PASS（ユーザー確認済み。`Tool.id=5` の初期化と `isfinished=0` への修正後）
- **使用技術**：Python、pytest、Playwright、SQLAlchemy、PostgreSQL、openpyxl
- **Viewport**：1440 × 900 px
- **対象DB**：`invoicee_test` のみ
- **主要fixture**：`page`、`e2e_server`、`e2e_config`、`workflow_engine`、`tmp_path`

## 2. テスト対象と範囲

| 対象 | 検証する処理 |
|---|---|
| `/login/` | ユーザー名・パスワードを入力しログインする |
| `/admin/` | クライアント・代理店・担当者を登録する |
| `projects` テーブル | ジョブ登録に必要なプロジェクトをテストDBへ直接作成する |
| `/record/` | プロジェクトとツールを選択してジョブを登録する |
| `/top/` | 登録したジョブが一覧に表示される |
| `/estimate/` | 対象ジョブを選択してExcel見積書をダウンロードする |
| `jobs` テーブル | 対象ジョブの `estimated` が `1` になる |
| `/logout/` | ログアウトし、保護ページへ再アクセスできなくなる |

**対象外**：`/project/` 画面からのプロジェクト登録操作、Web系ツール（ID 1〜4）の見積明細分岐、複数ジョブの一括出力、Excel全セルの網羅的な検証。これらは別のE2Eテストで扱うか、今後の拡張対象とする。

## 3. 前提条件

1. `.env.test` に `DATABASE_URL`、`TEST_USERNAME`、`TEST_PASSWORD` が設定され、既存の `e2e_server` fixtureからテスト用Flaskサーバーを起動できる。
2. 接続先データベース名は **`invoicee_test`**。`workflow_engine` が接続先を確認し、異なる場合はテストを失敗させる。
3. テストユーザーがログイン可能である。
4. `tools` テーブルに **ID 5以上の非Web系Tool** が存在する。今回、`tests/e2e/conftest.py` の `init_test_tools()` に次の初期データを追加した。

   ```python
   {"id": 5, "tool_type": "E2E_Workflow_Tool", "price": 10000}
   ```

5. `projects.isfinished` はDB上で整数型であり、未終了状態は **`0`** としてINSERTする。
6. 見積書テンプレートと出力先がテスト環境で利用できる。Excelダウンロードを検証するため、openpyxlがインストールされている。

## 4. テストケース一覧

| ID | pytest関数 | 検証内容 | 期待結果 | 結果 |
|---|---|---|---|---|
| WORKFLOW-E2E-001 | `test_workflow_login_to_logout` | ログイン → 管理データ登録 → プロジェクト準備 → ジョブ登録 → トップ表示 → 見積書出力 → ログアウト | 各操作が成功し、ExcelとDB状態が一致し、ログアウト後に保護ページへアクセスできない | PASS |

本テストは**1つのpytestケースに複数の業務ステップを含む**。以下のステップは独立したpytestケースではない。

## 5. 詳細手順と期待結果

| ステップ | 操作・確認 | 期待結果 |
|---|---|---|
| 1 | `/login/` にアクセスし、`.env.test` の資格情報でログイン | `/top/` に遷移する |
| 2 | `/admin/` の `#client` に一意なクライアント名を入力して登録 | `clients` に該当レコードが存在する |
| 3 | `/admin/` の `#agency` から代理店を登録 | `agencys` に該当レコードが存在する |
| 4 | `#account` に担当者名を入力し、`#agencyName` で作成した代理店を選択して登録 | `accounts` に該当レコードが存在する |
| 5 | テストDBで非Web系Tool（`id >= 5`）を取得し、プロジェクトをINSERT | `projects` に新規レコードが作成される（`isfinished=0`） |
| 6 | `/record/` の `#title`、`#project`、`#tool` を入力・選択して送信 | `jobs` に新規レコードが作成される |
| 7 | `/top/` にアクセスし `tr.jobs` を検索 | 登録したジョブタイトルを含む行が表示される |
| 8 | `/estimate/` で作成したジョブのラジオボタンを選択し送信 | Excelファイルがダウンロードされる |
| 9 | ダウンロードしたExcelの `シート1`・`A12` を確認 | `A12` が登録したジョブタイトルと一致する |
| 10 | `jobs.estimated` をDBから取得 | 値が `1`（見積済）になる |
| 11 | `/top/` から「ログアウト」をクリック | URLが `/login` に遷移する |
| 12 | ログアウト後に `/top/` へ再アクセス | `/top/` に留まらず、認証必須ルートの保護が機能する |

## 6. テストデータと後処理

テストの各実行で `uuid4().hex[:10]` を使った識別子を作成し、次の一意な名称を付与する。

- `E2E_CLIENT_<suffix>`
- `E2E_AGENCY_<suffix>`
- `E2E_ACCOUNT_<suffix>`
- `E2E_PROJECT_<suffix>`
- `E2E_JOB_<suffix>`

作成したレコードのIDを `ids` 辞書で保持し、`try/finally` によりテスト終了時に外部キーの依存関係を考慮して削除する。

**削除順序**：`contents` → `jobs` → `projects` → `accounts` → `agencys` → `clients`。

Tool（ID 5）は共通初期データとして保持し、このテストでは削除しない。Excelはpytestの `tmp_path` 配下に保存する。

**注意**：`finally` による後処理は、テスト中の通常のアサーション失敗には対応するが、プロセスの強制終了やDB障害時の完全な後処理を保証するものではない。また、IDの取得前に登録が成功してしまった場合などは、孤立したテストデータが残る可能性がある。

## 7. 主な実装上のポイント

### 7.1 認証済みfixtureを使用しない

`auth_page` ではなく通常の `page` を使用し、ログインフォームへの入力から開始する。これにより、認証開始から終了までの同一セッションを検証できる。

### 7.2 管理画面とジョブ登録はブラウザ操作

管理画面では `#client`、`#agency`、`#account`、`#agencyName` を使用する。ジョブ登録では `#title`、`#project`、`#tool` を使用する。登録結果はDBのSELECTでも確認する。

### 7.3 プロジェクトのみDBへ直接作成

`/project/` のフォーム操作は本テストに含めず、プロジェクトの前提データを直接INSERTする。`isfinished` は整数カラムのため、`FALSE` ではなく `0` を指定する。

```sql
INSERT INTO projects
    (project_name, client_id, agency_id, account_id, created, isfinished)
VALUES
    (:name, :client, :agency, :account, CURRENT_DATE, 0)
RETURNING id;
```

### 7.4 見積書はファイルとDBの両面で確認

Playwrightの `expect_download()` でダウンロードを捕捉し、openpyxlで `シート1` の `A12` を確認する。同時に、DBの `jobs.estimated` が `1` へ更新されたことを確認する。

### 7.5 ログアウト後のアクセス制限

`/logout/` によって `/login` へ遷移することと、再度 `/top/` にアクセスしてもトップ画面に留まらないことを確認する。現行テストは再アクセス後の**厳密なリダイレクト先URLまでは検証していない**。

## 8. 実行方法

プロジェクトルートで実行する。

```bash
python -m pytest tests/e2e/test_workflow_e2e.py -v
```

Chromiumの画面を表示して確認する場合（pytest-playwrightが対応している環境）：

```bash
python -m pytest tests/e2e/test_workflow_e2e.py -v --headed
```

## 9. 発生したエラーと対応履歴

| 発生箇所 | エラー | 原因 | 対応 |
|---|---|---|---|
| Tool取得 | `AssertionError: Seed a non-Web Tool (id >= 5) in invoicee_test` | テストDBにID 5以上のToolが存在しなかった | `init_test_tools()` にID 5の `E2E_Workflow_Tool` を追加 |
| Project INSERT | `psycopg.errors.DatatypeMismatch`（`isfinished`） | 整数型カラムにBOOLEANの `FALSE` を指定していた | INSERT値を整数の `0` に変更 |

上記修正後、**WORKFLOW-E2E-001 はPASS**（ユーザー確認済み）。

## 10. 制約・今後の改善候補

- プロジェクト登録も `/project/` 画面経由に切り替え、完全なUI操作フローとする。
- 担当者の存在確認だけでなく、作成した代理店への紐付けをDBで明示的に検証する。
- ログアウト後の `/top/` アクセスについて、期待するログインURLとHTTPステータスを厳密に検証する。
- 見積書の金額・税率・取引先情報も業務フロー全体の観点で検証する。
- 登録直後の画面遷移や成功メッセージも確認し、DB検証だけでは分からないUI上の失敗を検出する。
- テストの途中失敗時に残存したデータを回収できるよう、識別子を使った追加クリーンアップを検討する。
- 共通の見積出力ファイル名を使う実装では、並列テスト実行による競合に注意する。

---

**記録**：本仕様書は共有された `test_workflow_e2e.py` の構造と、その後の `isfinished=0` 修正・テストPASS報告に基づく。手元の元ファイルには修正前の `FALSE` が残っていたため、仕様書では実際にPASSした修正後の挙動を記載している。
