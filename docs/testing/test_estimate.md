# 見積書Excel出力機能 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`estimate/views.py`
- テストコード：`tests/unit/test_estimate.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト
- モック対象：SQLAlchemy session、writeExcel、render_template
- 目的：見積対象Jobの取得、Excel出力用データの生成、見積済み更新、認証制御を検証する。

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| EST-001 | test_estimate_get | 未見積もりJob一覧 | HTTP 200、Job一覧を取得 |
| EST-002 | test_estimate_get_empty | 対象Jobが0件 | 空のリストを渡す |
| EST-003 | test_estimate_post_web_job | Web系Job出力 | Contentの内容・金額・税率を渡す |
| EST-004 | test_estimate_post_print_job | 紙媒体Job出力 | Jobタイトル・価格・税率を渡す |
| EST-005 | test_estimate_post_multiple_contents | 複数Content | 複数行の出力データを生成 |
| EST-006 | test_estimate_post_no_contents | Contentなし | 現行実装では空の出力データになる |
| EST-007 | test_estimate_post_mark_estimated | 見積済み更新 | estimatedが1になる |
| EST-008 | test_estimate_post_recipient | 宛先情報 | 代理店・担当者・プロジェクト名を取得 |
| EST-009 | test_estimate_post_excel_response | Excelレスポンス | writeExcelの戻り値を返す |
| EST-010 | test_estimate_post_multiple_jobs_current_behavior | 複数Job選択 | 現行実装では最初のJobのみ処理 |
| EST-011 | test_estimate_login_required_get | 未認証GET | ログイン画面へリダイレクト |
| EST-012 | test_estimate_login_required_post | 未認証POST | Excelを出力せずログイン画面へ遷移 |

## 3. 主要テストケース

### EST-003：Web系JobのExcel出力

**目的：** Jobに紐づくContent情報が正しくExcel出力用データに変換されることを確認する。

**期待結果：**

1. Jobを取得する。
2. Contentから作業内容、価格、作成日、税率を取得する。
3. writeExcel()に正しいデータを渡す。
4. Excel出力関数の戻り値をHTTPレスポンスとして返す。

### EST-007：見積済み更新

**目的：** 見積書の出力対象となったJobが見積済み状態に更新されることを確認する。

**期待結果：**

1. Job.estimatedが1になる。
2. session.commit()が呼び出される。

### EST-010：複数Job選択時の現行動作

**目的：** 複数のJobを指定した場合の現行実装の動作を確認する。

**期待結果：**

1. 最初のJobの出力処理が行われる。
2. writeExcel()が1回呼び出される。
3. 最初のJobを処理した時点でレスポンスが返される。

**備考：** 複数Jobの一括出力に対応する場合は、テスト内容を変更する。

## 4. 検証範囲外

- 実際のExcelファイル生成
- Excelのセル内容・書式
- PostgreSQLへの更新反映
- ファイル生成時の例外処理
- ダウンロード時のHTTPヘッダー
- 複数Jobを一括出力する際の正常動作

これらは別途、結合テストやExcel生成関数の単体テストで検証する。

## 5. テスト実行方法

```bash
python -m pytest tests/unit/test_estimate.py -v
```

## 6. 合格基準

- 12件のテストがすべてPASSEDになること。
- Excel出力用データが正しく生成されること。
- Jobの見積済み状態が更新されること。
- 未認証ユーザーのExcel出力が制限されること。