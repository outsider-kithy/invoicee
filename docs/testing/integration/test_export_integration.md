# 見積書生成 結合テスト仕様書

## 1. 概要

| 項目 | 内容 |
| --- | --- |
| テストファイル | `tests/integration/test_export_integration.py` |
| 対象機能 | Flaskアプリケーションの見積書（Excel）生成 |
| 対象エンドポイント | `POST /estimate/` |
| テストフレームワーク | pytest、Flask test client |
| データベース | PostgreSQL（テスト専用DB／テストごとの独立スキーマ） |
| Excel検証 | openpyxl、`io.BytesIO` |
| テスト件数 | 11件 |
| 現在の結果 | 全11件成功（2026年11月10日時点、ユーザー確認） |

本テストは、認証済みユーザーが見積書生成画面からJobを選択した際、実際のPostgreSQLデータを使用してExcelファイルを生成できること、生成されたExcelの内容が正しいこと、およびJobの見積済み状態が更新されることを検証する。

単体テストと異なり、原則としてDBアクセスおよびExcel生成処理そのものをモック化しない。

## 2. 対象範囲

- 認証済みユーザーによる見積書生成とExcelダウンロード
- 生成したXLSXファイルの読み込みとシート確認
- 宛先（代理店・担当者・プロジェクト）情報の出力
- Jobタイトルと明細内容の出力
- 金額・税率に関連するセル／数式の検証
- 生成後の `Job.estimated` 更新
- 未認証アクセスのリダイレクト
- 同じJobの再生成
- Web系Jobに紐づく複数Contentの出力
- 紙媒体Jobの出力
- 複数Jobを選択した場合の現行仕様

## 3. テスト環境・前提条件

### 3.1 fixture

| fixture | 役割 |
| --- | --- |
| `app` | テスト用Flaskアプリと独立したDBスキーマを用意する |
| `client` | 未認証状態のFlaskテストクライアント |
| `authenticated_client` | テストユーザーでログイン済みのFlaskテストクライアント |
| `seed` | Jobとその参照先などのテスト用データを投入し、`job_id`・`project_id` 等を提供する |
| `excel_env` | `tmp_path` を使用し、Excelテンプレートと出力先をテスト用に切り替える |

`seed["job_id"]` を対象JobのIDとして利用する。fixtureが返すキーやデータ構成は、実際の `conftest.py` に従う。

### 3.2 共通ヘルパー

- `export_estimate(client, job_id=1)`：`POST /estimate/` にフォーム項目 `job` を送信する。
- `load_excel_response(response)`：HTTPレスポンスのバイト列を `BytesIO` に渡し、`openpyxl.load_workbook()` でExcelブックとして開く。

Excelの生成には実際の `writeExcel()` を使用する。テンプレートや出力先を差し替える際は、アプリケーションが実際に参照している設定変数を使用すること。

## 4. テストケース一覧

| ID | テスト関数 | 主な検証内容 | 期待結果 |
| --- | --- | --- | --- |
| EXP-INT-001 | `test_export_success` | 見積書のダウンロード | HTTP 200、添付ファイルのレスポンス、`.xlsx` ファイル名 |
| EXP-INT-002 | `test_export_valid_excel` | XLSX形式の妥当性 | `openpyxl` で開け、`シート1` が存在する |
| EXP-INT-003 | `test_export_recipient` | 宛先情報 | 想定セルに宛先情報が出力される |
| EXP-INT-004 | `test_export_job_detail` | Jobタイトル | 明細範囲に対象Jobのタイトルが出力される |
| EXP-INT-005 | `test_export_amount_and_tax` | 金額・税関連の集計 | 対象集計セルに期待する値・数式が設定される |
| EXP-INT-006 | `test_export_updates_estimated` | 見積済みフラグ | DB再取得後に `Job.estimated == 1` |
| EXP-INT-007 | `test_export_requires_login` | 未認証アクセス | HTTP 302、`/login/` へリダイレクト |
| EXP-INT-008 | `test_export_twice` | 同一Jobの再生成 | 2回とも正常なExcelを返し、見積済み状態を維持 |
| EXP-INT-009 | `test_export_multiple_contents` | Web系Jobの複数明細 | 登録した2件のContentがExcelに出力される |
| EXP-INT-010 | `test_export_print_job` | 紙媒体Job | タイトル・金額が出力され、見積済みになる |
| EXP-INT-011 | `test_export_multiple_jobs` | 複数Jobの選択 | 現行実装では最初のJobのみ見積済みになる |

## 5. 各テストの詳細

### EXP-INT-001：見積書ダウンロード成功

1. `seed` のJob IDを指定して認証済みクライアントからPOSTする。
2. HTTPステータスが200で、レスポンス本文にデータが存在することを確認する。
3. `Content-Disposition` が添付ファイルを示し、ファイル名に `.xlsx` が含まれることを確認する。

### EXP-INT-002：Excelファイルの妥当性

1. 見積書を生成する。
2. レスポンスのバイト列をExcelブックとして開く。
3. `シート1` が存在することを確認し、ブックを閉じる。

### EXP-INT-003：宛先情報

1. 見積書を生成して `シート1` を開く。
2. 宛先情報の出力対象セル（既存テストでは `E3`・`A3`・`A4`）が空でないことを確認する。
3. 必要に応じてAgency・Account・Projectの実際のDB値と照合する。

### EXP-INT-004：Jobタイトル

1. DBから対象Jobの `title` を取得する。
2. 見積書を生成する。
3. Excelの明細範囲（12〜39行）にタイトルが含まれることを確認する。

### EXP-INT-005：金額・税関連の集計

1. 見積書を生成する。
2. 集計セル（既存テストでは `E40`・`E41`・`E42`）の設定値または数式を確認する。
3. `openpyxl` はExcel数式を再計算しないため、数式そのものの検証と計算済み結果の検証を区別する。

### EXP-INT-006：見積済みフラグの更新

1. `Job.estimated` を0にしてコミットする。
2. 見積書を生成する。
3. `session.remove()` 後にDBからJobを再取得する。
4. `Job.estimated == 1` を確認する。

### EXP-INT-007：未認証アクセス

1. 未ログインの `client` から見積書生成をPOSTする。
2. HTTP 302を確認する。
3. リダイレクト先パスが `/login/` であることを確認する。

### EXP-INT-008：同一Jobの再生成

1. 同じJob IDで見積書生成を2回実行する。
2. 両レスポンスがHTTP 200であることを確認する。
3. 両Excelファイルを読み込み、`シート1` が存在することを確認する。
4. DB上で `Job.estimated == 1` が維持されていることを確認する。

### EXP-INT-009：Web系Jobの複数Content

1. Web系Job（`tool_type_id` が1〜4）を用意する。
2. Workを参照する2件のContent（`デザイン制作`・`コーディング`）を登録しコミットする。
3. 見積書を生成して `シート1` を開く。
4. **A列・12〜39行**から値を取得し、両方の明細が存在することを確認する。
5. DB上で `Job.estimated == 1` を確認する。

**確認済みの修正点：** 当初のテストはB列（`column=2`）を参照していたため失敗した。実際の出力に合わせてA列（`column=1`）へ修正し、テスト成功。

```python
# Contentの明細が出力されるA列を検証
details = [
    worksheet.cell(row=row, column=1).value
    for row in range(12, 40)
]
assert "デザイン制作" in details
assert "コーディング" in details
```

### EXP-INT-010：紙媒体Job

1. Jobを紙媒体用（`tool_type_id = 5`）に変更する。
2. タイトルを `パンフレット制作`、価格を50000、`estimated` を0にしてコミットする。
3. 見積書を生成する。
4. A列・12〜39行にタイトルが含まれることを確認する。
5. **E列・12〜39行**に金額50000が含まれることを確認する。
6. DB上で `Job.estimated == 1` を確認する。

**確認済みの修正点：** 当初のテストはC列（`column=3`）を参照していたため失敗した。Excel出力ログに `E12: 50000` が表示されていたためE列（`column=5`）へ修正し、テスト成功。

```python
# 金額が出力されるE列を検証
amounts = [
    worksheet.cell(row=row, column=5).value
    for row in range(12, 40)
]
assert 50000 in amounts
```

※ 本ケースで明示的に検証しているのはタイトル・価格・見積済み状態であり、Toolの税率そのものとExcel上の税率セルの一致検証は今後の拡張候補とする。

### EXP-INT-011：複数Job選択時の現行動作

1. 1件目のJobを未見積状態にする。
2. 2件目のJobを作成し、未見積状態でコミットする。
3. フォームの `job` に2件のIDを順に指定してPOSTする。
4. HTTP 200で正常なExcelを取得できることを確認する。
5. DBから両Jobを再取得する。
6. **現行仕様として**1件目のみ `estimated == 1`、2件目は `estimated == 0` であることを確認する。

このケースは現在の処理フローを固定する回帰テストである。将来、複数Jobの一括出力に対応した場合は、アプリケーションの仕様変更に合わせて期待値を更新する。

## 6. Excelセル配置（今回のテストで確認済みの範囲）

| 範囲・セル | 用途 | 備考 |
| --- | --- | --- |
| A12:A39 | Jobタイトル／Content明細 | 複数Contentと紙媒体Jobのテストで使用 |
| E12:E39 | 明細金額 | 紙媒体Jobで50000の出力を確認 |
| B列（明細範囲） | 日付など | 複数Contentテストの失敗時に日付値を確認 |
| E40:E42 | 集計関連 | 既存の集計テストで使用 |
| E3、A3、A4 | 宛先関連 | 既存の宛先テストで使用 |

セル配置はExcelテンプレートおよび `writeExcel()` の実装に依存する。テンプレートを変更した場合は、テスト側のセル指定と仕様書を合わせて更新する。

## 7. 実行方法

全11件の実行：

```bash
python -m pytest tests/integration/test_export_integration.py -v
```

追加3件のみ実行：

```bash
python -m pytest tests/integration/test_export_integration.py \
  -k "multiple_contents or print_job or multiple_jobs" -v
```

単一ケースの実行例：

```bash
python -m pytest tests/integration/test_export_integration.py::test_export_multiple_contents -v
```

## 8. テスト設計上の注意点

1. **DBの分離**：テスト専用DBと独立スキーマを使い、本番データを操作しない。
2. **実処理を検証**：DBアクセスとExcel生成処理を原則モック化しない。
3. **Excelの一時ファイル**：`tmp_path` に出力し、テスト間でファイルが干渉しないようにする。
4. **Sessionの再取得**：更新後の永続化を検証するときは `session.remove()` してからDBを再照会する。
5. **数式の扱い**：`openpyxl` は数式を計算しない。式の存在や内容と、Excelで計算した結果は別の検証対象である。
6. **列位置の維持**：明細名はA列、金額はE列という確認済み配置を用いる。
7. **複数Jobの仕様**：現状は最初のJobのみ処理されるため、仕様変更時は回帰テストも更新する。
8. **テストの再現性**：Work・Tool・Taxなどの参照データはfixtureで明示的に用意し、取得順や既存データの偶然に依存しないようにする。

## 9. 今後の拡張候補

- 複数Contentの明細名・金額・税率が**同じ行**で対応していることの検証
- 紙媒体JobのTool税率とExcel上の税率セルの一致検証
- 複数Jobの一括出力に対応した際の期待結果の更新
- 明細0件、無効なJob ID、空の選択、出力エラー時の動作検証
- Excelの合計金額や消費税額を独立した計算結果と比較する検証

---

**状態：全11ケース成功。** 本書は2026年11月10日時点の会話で確認できたテスト構成と結果を記録したもの。テストコード全体の最新内容と差異がある場合は、実際のコードを正として本書を更新する。
