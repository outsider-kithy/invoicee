# `test_helper.py` 単体テスト仕様書

## 1. 概要

| 項目 | 内容 |
| --- | --- |
| 対象モジュール | `helper.py` |
| 対象関数 | `writeExcel(exportJobList, agencyName, accountName, projectName)` |
| テストファイル | `tests/unit/test_helper.py` |
| ドキュメント配置先 | `docs/testing/test_helper.md` |
| テストフレームワーク | pytest |
| 主な依存ライブラリ | Flask、openpyxl |
| テスト件数 | 12件 |

`writeExcel()` は、Excelテンプレートの「シート1」に見積明細、宛先、発行日、消費税計算式などを書き込み、生成した `.xlsx` ファイルをFlaskのダウンロードレスポンスとして返す。

本テストは、実際の一時Excelファイルを生成し、返却されたレスポンスのバイナリを `openpyxl` で再読み込みして検証する。DB接続や本番用テンプレートへの依存はない。**Excelの計算式の文字列は検証するが、Excelによる計算結果そのものは検証しない。**

## 2. テスト環境と共通fixture

### `app`

既存の `tests/conftest.py` で提供されるFlaskアプリケーションfixture。`writeExcel()` 内の `flask.make_response()` を利用するため、各テストで `with app.app_context():` を使用する。

### `excel_env(tmp_path, monkeypatch)`

1. pytestの `tmp_path` にテスト専用の `template.xlsx` を生成する。
2. ワークシート名を `シート1` に設定する。
3. テスト専用の `output` ディレクトリを作成する。
4. `helper.TEMPLATE_FILE` をテスト用テンプレートのパスに差し替える。
5. `helper.OUTPUT_DIR` をテスト用出力ディレクトリのパスに差し替える。
6. 出力ディレクトリの `Path` を返す。

アプリケーション側は `OUTPUT_DIR` を出力先として使用し、未設定時は `/tmp` にフォールバックする。これにより、テンプレートのコピー、ワークブックの読み込み・保存、レスポンス用の読み込み、削除の各操作が同じファイルを参照する。

### `excel_reader`

`io.BytesIO(response.data)` を `openpyxl.load_workbook()` に渡して、レスポンス内のExcelバイナリをWorkbookとして読み込む。検証後は `workbook.close()` を実行する。

### `fixed_date`

`datetime.date.today()` を **2026-11-10** に固定する。発行日およびダウンロードファイル名を再現可能にする。

## 3. テストケース一覧

| ID | テスト関数 | 主な検証内容 |
| --- | --- | --- |
| HLP-001 | `test_write_excel_basic_info` | 発行日・代理店名・担当者名・プロジェクト名 |
| HLP-002 | `test_write_excel_with_content` | 作業内容ありの明細とセル位置 |
| HLP-003 | `test_write_excel_without_content` | 作業内容なしの明細とセル位置 |
| HLP-004 | `test_write_excel_multiple_contents` | 複数明細の行順と金額 |
| HLP-005 | `test_write_excel_tax_rates` | 0%・8%・10%の税率表示 |
| HLP-006 | `test_write_excel_currency_format` | 日本円の数値表示形式 |
| HLP-007 | `test_write_excel_formulas` | 小計・税率別金額・税額・総額の計算式 |
| HLP-008 | `test_write_excel_empty_jobs` | 明細0件時のセル状態 |
| HLP-009 | `test_write_excel_response_headers` | HTTPステータス、MIMEタイプ、添付ファイル名 |
| HLP-010 | `test_write_excel_response_content` | 返却バイナリが読み込み可能なExcelであること |
| HLP-011 | `test_write_excel_temporary_file_removed` | 出力用一時ファイルの削除 |
| HLP-012 | `test_write_excel_none_recipient` | 宛先が `None` の場合の現行挙動 |

## 4. テストケース詳細

### HLP-001: 基本情報の出力

**対象:** `test_write_excel_basic_info`

- **入力:** 明細 `[]`、代理店「テスト代理店」、担当者「テスト担当者」、プロジェクト「テストプロジェクト」
- **期待結果:** `E3 = "2026-11-10"`、`A3 = "テスト代理店"`、`A4 = "テスト担当者"`、`A11 = "テストプロジェクト"`
- **目的:** 見積書ヘッダーの基本情報が指定セルに設定されること。

### HLP-002: 作業内容ありの明細

**対象:** `test_write_excel_with_content`

- **入力:** `["Webサイト制作", "コーディング", 30000, "2026-11-09", 0.1]`
- **期待結果:** `A12 = "Webサイト制作"`、`A13 = "コーディング"`、`B13 = "2026-11-09"`、`D13 = "10%"`、`E13 = 30000`
- **目的:** 作業内容がある場合、タイトルは12行目、明細は13行目から出力されること。

### HLP-003: 作業内容なしの明細

**対象:** `test_write_excel_without_content`

- **入力:** `["パンフレット制作", None, 50000, "2026-11-09", 0.1]`
- **期待結果:** `A12 = "パンフレット制作"`、`B12 = "2026-11-09"`、`D12 = "10%"`、`E12 = 50000`
- **目的:** 作業内容がない場合、Jobのタイトルと金額が12行目に出力されること。

### HLP-004: 複数明細

**対象:** `test_write_excel_multiple_contents`

- **入力:** 「デザイン」20,000円、「コーディング」30,000円の2明細
- **期待結果:** `A13 = "デザイン"`、`E13 = 20000`、`A14 = "コーディング"`、`E14 = 30000`
- **目的:** 複数明細が入力順に別々の行へ書き込まれること。

### HLP-005: 税率表示

**対象:** `test_write_excel_tax_rates`

- **入力:** 税率 `0`、`Decimal("0.08")`、`Decimal("0.10")` の3明細（作業内容なし）
- **期待結果:** `D12 = "0%"`、`D13 = "8%"`、`D14 = "10%"`
- **目的:** 税率を百分率の文字列に変換して出力すること。
- **留意点:** `Decimal` に浮動小数点値を直接渡すと精度の影響を受け得る。必要に応じてアプリケーション側で `Decimal(str(rate))` を使用する。

### HLP-006: 日本円の表示形式

**対象:** `test_write_excel_currency_format`

- **入力:** 作業内容なし、金額50,000円の明細
- **期待結果:** `E12`、`E40`、`E42`、`B7` の `number_format` が `helper.currentJPY`（`"¥"#,##0`）と一致すること。
- **目的:** 金額セルと主要な集計セルに日本円の表示形式が設定されること。

### HLP-007: 計算式

**対象:** `test_write_excel_formulas`

以下のセルに、指定の数式文字列が設定されることを確認する。

| セル | 期待する数式 | 用途 |
| --- | --- | --- |
| E40 | `=SUM(E12:E39)` | 小計 |
| B41 | `=SUMIF(D12:D39,"8%",E12:E39)` | 8%対象額 |
| C41 | `=B41*0.08` | 8%税額 |
| B42 | `=SUMIF(D12:D39,"10%",E12:E39)` | 10%対象額 |
| C42 | `=B42*0.10` | 10%税額 |
| B43 | `=SUMIF(D12:D39,"0%",E12:E39)` | 0%対象額 |
| C43 | `=B43*0` | 0%税額 |
| C44 | `=SUM(C41:C43)` | 消費税合計 |
| E41 | `=SUM(C41:C43)` | 消費税合計 |
| E42 | `=SUM(E40:E41)` | 税込総額 |
| B7 | `=SUM(E40:E41)` | 上部表示の税込総額 |

**目的:** 計算式が意図したセルと参照範囲に設定されていること。openpyxlはExcelの数式を計算しないため、金額計算の実結果までは確認しない。

### HLP-008: 明細0件

**対象:** `test_write_excel_empty_jobs`

- **入力:** 明細 `[]`
- **期待結果:** `A12` と `E12` が `None`、`E40 = "=SUM(E12:E39)"`
- **目的:** 明細が空でもエラーなくExcelが生成され、集計式が設定されること。

### HLP-009: レスポンスヘッダー

**対象:** `test_write_excel_response_headers`

- **期待結果:** HTTPステータス `200`
- **MIMEタイプ:** `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- **Content-Disposition:** `attachment; filename=2026-11-10-estimate.xlsx`
- **目的:** ブラウザでExcelファイルとしてダウンロードできるレスポンス設定を確認すること。

### HLP-010: Excelバイナリ

**対象:** `test_write_excel_response_content`

- **期待結果:** `response.data` が空ではなく、先頭2バイトがZIP形式を示す `b"PK"` であること。
- **追加確認:** `io.BytesIO(response.data)` からWorkbookを開けて、`シート1` が存在すること。
- **目的:** レスポンスに有効な `.xlsx` ファイルが格納されていること。

### HLP-011: 一時ファイルの削除

**対象:** `test_write_excel_temporary_file_removed`

- **対象ファイル:** `excel_env / "2026-11-10-estimate.xlsx"`
- **期待結果:** `writeExcel()` 完了後に `output_file.exists()` が `False` となること。
- **目的:** レスポンス生成後に作業用Excelファイルが削除されること。

### HLP-012: 宛先情報がNone

**対象:** `test_write_excel_none_recipient`

- **入力:** 代理店・担当者・プロジェクトをすべて `None` とする。
- **期待結果:** `A3 = "None"`、`A4 = "None"`、`A11 = "None"`
- **目的:** 現行の `str(None)` による文字列化の挙動を明示的に検証すること。
- **留意点:** 空欄に変更する仕様改修を行った場合は、この期待値も更新する。

## 5. 実行方法

プロジェクトのルートディレクトリで実行する。

```bash
python -m pytest tests/unit/test_helper.py -v
```

特定のテストのみ実行する場合：

```bash
python -m pytest tests/unit/test_helper.py -v -k currency_format
```

**期待結果:** 12件すべてが `PASSED`。

## 6. テストの範囲と注意点

- **実ファイルを用いた検証:** Excelのセル値・書式・数式・レスポンスを、テスト専用テンプレートと一時出力先で検証する。純粋なモックテストではなく、ファイルI/Oを含む軽量なコンポーネントテストである。
- **本番環境からの分離:** 本番の `TEMPLATE_FILE`、`OUTPUT_DIR` を使用しない。`monkeypatch` による設定値の差し替えは各テスト後に復元される。
- **日付の固定:** 発行日とファイル名が実行日に依存しないようにする。
- **未検証事項:** Excelアプリでの実際の見た目・印刷結果、Excelエンジンによる数式再計算、異常系（テンプレート欠落・保存失敗・権限不足）、複数リクエスト同時実行時のファイル名衝突、明細が集計対象の39行目を超えるケースは対象外。
- **運用上の注意:** 現行の出力ファイル名は日付のみで決まるため、同時実行時に衝突する可能性がある。必要に応じて `tempfile` などによる一意な一時ファイル名を採用する。

## 7. 関連ファイル

- `helper.py` — Excel見積書の生成処理
- `estimate/views.py` — `writeExcel()` の呼び出し元
- `tests/unit/test_helper.py` — 本仕様書の対象テスト
- `tests/conftest.py` — Flaskアプリケーションfixture
- `docs/testing/test_estimate.md` — 見積書出力ルートの単体テスト仕様書
