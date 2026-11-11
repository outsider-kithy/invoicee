# `test_export_e2e.py` E2Eテスト仕様書

## 1. 概要

| 項目 | 内容 |
|---|---|
| テスト対象 | 見積書Excel出力機能（`/estimate/`） |
| テストファイル | `tests/e2e/test_export_e2e.py` |
| フレームワーク | pytest / Playwright / SQLAlchemy / openpyxl |
| テストDB | PostgreSQL `invoicee_test` |
| テスト件数 | **21件（紙媒体・共通13件、Web系8件）** |
| 実行結果 | **21件すべてPASS**（ユーザー報告） |

本テストは、未見積もりのJobを画面に表示し、対象を選択してExcel見積書をダウンロードする一連の処理を検証する。Excelファイルの形式・セル内容・数式と、出力後の`Job.estimated`更新を確認する。`/estimate/`は見積書出力ルートであり、請求済みフラグ`invoiced`の更新を行うものではない。

## 2. 対象の実装と処理フロー

- `estimate/views.py` の `index()`：GETでは `Job.estimated == 0` のJobを一覧表示。POSTでは `job` フォーム値から対象Jobを取得し、見積書データを構築する。
- `estimate/templates/estimate/index.html`：Jobのラジオボタン（`name="job"`、`required`）と出力ボタン（`form.estimate`）。
- `helper.py` の `writeExcel()`：テンプレートをコピーして `シート1` にデータと計算式を設定し、XLSXレスポンスを返す。
- POST成功時に対象Jobの `estimated` を `1` に更新する。
- Web系の判定は `tool_type_id` が **1〜4**。作業内容があれば `Content`・`Work`・`Tax` から明細を生成する。それ以外のTool IDは紙媒体向け処理。

**注意：** POST内で最初のJobを処理した時点で `return exportFile` するため、複数IDを直接POSTした場合に全件処理される仕様ではない。画面はラジオボタンで単一選択。

## 3. テストケース一覧

### 3.1 共通・紙媒体向け（13件）

| ID | テスト関数 | 検証内容 | 結果 |
|---|---|---|---|
| EXPORT-E2E-001 | `test_estimate_page_display` | `/estimate/`、フォーム、出力ボタンが表示される | PASS |
| EXPORT-E2E-002 | `test_unestimated_job_display` | 未見積もりJobが一覧に表示される | PASS |
| EXPORT-E2E-003 | `test_excel_download` | `.xlsx` をダウンロードでき、ファイルが空でない | PASS |
| EXPORT-E2E-004 | `test_excel_file_valid` | `openpyxl` で開け、`シート1` が存在する | PASS |
| EXPORT-E2E-005 | `test_excel_customer_information` | 代理店・担当者・プロジェクト名が正しい | PASS |
| EXPORT-E2E-006 | `test_excel_job_information` | Jobタイトル・価格・作成日・発行日が正しい | PASS |
| EXPORT-E2E-007 | `test_excel_tax_and_formulas` | 税率と主要なExcel数式が正しい | PASS |
| EXPORT-E2E-008 | `test_job_estimated_status` | 出力したJobの `estimated` が `1` になる | PASS |
| EXPORT-E2E-009 | `test_exported_job_not_displayed` | 出力済みJobが未見積もり一覧から消える | PASS |
| EXPORT-E2E-010 | `test_no_unestimated_jobs` | 未見積もりJobが0件のときメッセージ表示 | PASS |
| EXPORT-E2E-011 | `test_export_only_selected_job` | 選択したJobだけが見積もり済みになる | PASS |
| EXPORT-E2E-012 | `test_export_requires_selection` | Job未選択ではHTMLの`required`で送信されない | PASS |
| EXPORT-E2E-013 | `test_estimate_requires_login` | 未ログイン時にログイン画面へ誘導される | PASS |

### 3.2 Web系ジョブ向け（8件）

| ID | テスト関数 | 検証内容 | 結果 |
|---|---|---|---|
| EXPORT-E2E-014 | `test_web_excel_download` | Web系JobのXLSXをダウンロードできる | PASS |
| EXPORT-E2E-015 | `test_web_excel_job_title` | Jobタイトルが `A12` に出力される | PASS |
| EXPORT-E2E-016 | `test_web_excel_content_text` | Contentの作業内容が `A13`・`A14` に出力される | PASS |
| EXPORT-E2E-017 | `test_web_excel_work_price` | Workの価格が `E13`・`E14` に出力される | PASS |
| EXPORT-E2E-018 | `test_web_excel_content_date_and_tax` | 作業日・税率が明細行に出力される | PASS |
| EXPORT-E2E-019 | `test_web_excel_multiple_contents` | 複数Contentの内容・価格・税率の組み合わせが一致 | PASS |
| EXPORT-E2E-020 | `test_web_excel_without_contents` | ContentなしではJobタイトル・価格を12行目に出力 | PASS |
| EXPORT-E2E-021 | `test_web_job_estimated_status` | Web系Jobの `estimated` が `1` になる | PASS |

## 4. テストケース詳細

### EXPORT-E2E-001〜004：画面とダウンロード

**目的：** 認証済みユーザーが見積書出力画面を開き、未見積もりJobを選択して有効なXLSXを取得できること。

**手順：** `auth_page` で `/estimate/` を開く。テスト用Jobのラジオボタンを選択して出力ボタンをクリックし、Playwrightの `expect_download()` でファイルを取得。`tmp_path` に保存して `openpyxl.load_workbook()` で開く。

**期待結果：** フォームとJobが表示され、`.xlsx` が保存され、`シート1` が存在する。

### EXPORT-E2E-005〜007：Excelセル・数式

**目的：** データベースの値が指定セルに反映され、税率と数式が設定されること。

**手順：** ダウンロード済みブックを `data_only=False` で読み込み、セルを照合する。

**期待結果：** 下表のセルが想定値と一致する。数式の**計算結果**ではなく**式の文字列**を検証する。

### EXPORT-E2E-008〜009：ステータス更新と一覧除外

**目的：** 見積書出力後、Jobが再度未見積もり一覧に表示されないこと。

**手順：** XLSX出力後にSQLAlchemyで `Job.estimated` を取得し、画面を再読み込みする。

**期待結果：** `estimated == 1`、対象Jobのラジオボタンは0件。

### EXPORT-E2E-010〜013：例外的な状態とアクセス制限

**目的：** Jobなし、複数Job、未選択、未ログインのケースを検証する。

**手順と期待結果：**

- 未見積もりJobが0件：`ジョブは0件です。` が表示される。元のテストコードでは他の未見積もりJobがある場合 `pytest.skip()` する仕様のため、実行結果はDBの状態に依存する。
- 複数Job：選択した1件のみ `estimated == 1`、もう1件は `0` のまま。
- 未選択：`required` によりブラウザ側で送信が阻止され、画面遷移しない。
- 未ログイン：`@login_required` によりログイン画面へリダイレクトされる。

### EXPORT-E2E-014〜019：Web系明細の出力

**目的：** `tool_type_id` 1〜4のJobに対し、Contentに紐づくWorkの作業内容・価格・作業日・税率が明細行に出力されること。

**手順：** Web系Toolを参照するJob、2件のWork、2件のContentを用意し、見積書をダウンロードする。明細行を比較する。

**期待結果：** `A12` にJobタイトル、`A13:A14` に作業内容、`B13:B14` に作業日、`D13:D14` に税率、`E13:E14` に価格が出力される。Contentのクエリに `order_by()` がないため、明細の照合では順序に依存しない集合比較を採用する。

### EXPORT-E2E-020：Web系Contentなし

**目的：** Web系JobにContentが存在しない場合もExcelを出力できること。

**手順：** Contentを作成せずにWeb系Jobを登録して出力する。

**期待結果：** `A12` にJobタイトル、`E12` にJob価格、`D12` に現行実装上の `0%` が出力される。

### EXPORT-E2E-021：Web系見積もり済み更新

**目的：** Web系明細を含むExcel出力後にJobの見積もり状態が更新されること。

**期待結果：** 対象Jobの `estimated == 1`。

## 5. Excelセル対応表

| セル・範囲 | 内容 | 確認内容 |
|---|---|---|
| `A3` | 代理店名 | `Agency.agency_name` |
| `A4` | 担当者名 | `Account.account_name` |
| `E3` | 発行日 | 当日の日付文字列 |
| `B7` | 税込合計 | `=SUM(E40:E41)` |
| `A11` | プロジェクト名 | `Project.project_name` |
| `A12` | Jobタイトル | 紙媒体・Web系ともに出力 |
| `B12` / `E12` / `D12` | 紙媒体の日付・価格・税率 | Job・Tool由来の値 |
| `A13:A14` | Web系作業内容 | `Content.work_content` |
| `B13:B14` | Web系作業日 | `Content.created` |
| `D13:D14` | Web系税率 | `Work.tax_rate.rate` を百分率文字列に変換 |
| `E13:E14` | Web系価格 | `Work.price` |
| `E40` | 小計 | `=SUM(E12:E39)` |
| `B41` / `C41` | 8%対象額・税額 | `SUMIF` と税額計算式 |
| `B42` / `C42` | 10%対象額・税額 | `SUMIF` と税額計算式 |
| `B43` / `C43` | 0%対象額・税額 | `SUMIF` と税額計算式 |
| `C44` / `E41` | 消費税合計 | `=SUM(C41:C43)` |
| `E42` | 税込合計 | `=SUM(E40:E41)` |

## 6. fixture・ヘルパーの役割

| 名称 | 役割 |
|---|---|
| `export_db` | `invoicee_test` に接続し、終了時にエンジン破棄 |
| `export_dependencies` | Tax、Client、Agency、Account、Project、紙媒体向けToolの準備と削除 |
| `export_job` | 未見積もりJobを1件作成 |
| `download_estimate()` | ラジオボタン選択、クリック、XLSX保存 |
| `exported_excel` / `exported_sheet` | 紙媒体向けダウンロードファイル・ワークシート |
| `web_export_job` | Web系Tool（ID 1〜4）、Job、Work、Contentの準備と削除 |
| `web_exported_excel` / `web_exported_sheet` | Web系ダウンロードファイル・ワークシート |
| `get_estimated()` | DBからJobの見積もり状態を取得 |
| `job_radio()` | 対象Jobのラジオボタンを特定 |

既存の共通fixture `e2e_config`、`init_test_database`、`e2e_server`、`auth_page` を利用する。Web系ToolのID 1〜4は `tests/e2e/conftest.py` のDB初期化で投入し、各テストから参照する。

## 7. テストデータのライフサイクル

1. セッション開始時にテストDBのテーブルとWeb系Toolマスターデータを準備する。
2. 各テストのfixtureでClient、Agency、Account、Project、Jobなどを作成する。
3. Web系テストでは追加でWork・Contentを作成する。
4. ブラウザからExcelをダウンロードし、ファイルとDBを検証する。
5. テスト終了時に **Content → Work → Job → Project → Tool → Account → Agency → Client → Tax** のように外部キーを考慮してテスト作成分を削除する。共通マスターデータは原則残す。

**安全上の注意：** `export_dependencies` の削除条件はテスト専用IDに限定する。DB名が `invoicee_test` であることを検証し、本番DBでは実行しない。`test_web_excel_without_contents` のJobも失敗時に確実に削除できるよう、将来的には専用fixture化するとよい。

## 8. 実行コマンド

```bash
# 全21件
python -m pytest tests/e2e/test_export_e2e.py -v

# Web系テストを抽出（関数名にwebを含むもの）
python -m pytest tests/e2e/test_export_e2e.py -v -k "web"

# ブラウザを表示
python -m pytest tests/e2e/test_export_e2e.py -v --headed

# E2Eテスト全体
python -m pytest tests/e2e/ -v
```

## 9. 環境設定・制約

- `.env.test` にはテスト用 `DATABASE_URL`、認証用変数、`TEMPLATE_FILE`、`OUTPUT_DIR` を設定する。
- テンプレートは `シート1` を含む有効な `.xlsx` ファイルであること。
- `helper.py` は `OUTPUT_DIR` に日付ベースのファイル名（`YYYY-MM-DD-estimate.xlsx`）で一時保存し、レスポンス生成後に削除する。同日の並列実行では競合する可能性があるため、逐次実行を推奨する。
- `openpyxl` はExcelの数式を計算しない。検証対象は式の設定であり、Excelアプリケーションによる再計算後の金額ではない。
- Web系ToolはID 1〜4で判定される。テストDB初期化で固定IDを用意した後は、PostgreSQLの採番シーケンスの整合性も保つ。
- 実装はJobの `estimated` をExcel生成前にコミットしている。Excel生成が失敗しても見積もり済みになる可能性があるため、別途異常系テストが必要。

## 10. 今後の改善候補

- **Excel生成失敗時の整合性：** テンプレート欠落・保存エラー時に `estimated` が変更されないことを保証する。
- **Web系明細の順序：** `Content.created` とIDでソートし、出力順を仕様として固定する。
- **税率混在：** 8%、10%、0%のWorkを混在させて税率別集計式を検証する。
- **大量明細：** 12〜39行を超えるContentの扱いを定義し、合計範囲から漏れないことを検証する。
- **不正POST：** 存在しないJob ID、既に見積もり済みのJob ID、未選択POSTのサーバー側挙動を検証する。
- **同時出力：** 出力ファイル名の衝突を防止するため、一時ファイル名を一意化する。

---

**実行結果：21件すべてPASS（ユーザー報告）。** 本書は共有された実装と、会話内で提案したテスト構成に基づく仕様書である。
