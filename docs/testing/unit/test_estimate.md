# 見積書Excel出力機能 単体テスト仕様書

## 1. テスト概要

| 項目 | 内容 |
|---|---|
| 対象モジュール | `estimate/views.py` |
| テストコード | `tests/unit/test_estimate.py` |
| テストフレームワーク | pytest |
| 対象ルート | `/estimate/`（GET・POST） |
| テスト方式 | Flaskテストクライアントと `unittest.mock` を利用した単体テスト |
| テストケース数 | **13件** |
| 目的 | 未見積もりJobの表示、Excel出力用データの構築、宛先情報の取得、見積済み更新、認証制御を検証する |

本仕様書は、修正後の `test_estimate.py` のアサーションに基づく。Excelファイルそのものは生成せず、`writeExcel()` をモック化して引数とレスポンスを検証する。

## 2. テスト環境・共通設定

- `client`：`tests/conftest.py` で提供されるFlaskテストクライアント。`estimate` Blueprintを `/estimate` に登録していること。
- `authenticated`：`flask_login.utils._get_user` をpatchし、`is_authenticated=True` とするfixture。
- `job_data`：Jobのモック。ID `1`、タイトル「Webサイト制作」、Tool種別ID `1`、価格 `100000`、作成日 `2026-11-09`、見積状態 `0` などを設定。
- `make_content()`：Contentと関連するWork・Taxのモックを生成する。既定値は作業内容「コーディング」、価格 `30000`、作成日 `2026-11-09`、税率 `10`。
- `setup_post_queries()`：POSTのSQLAlchemyクエリを実行順に5つモック化する。Web系JobではContentの `.all()`、紙媒体JobではToolの `.first()`、宛先情報では `.scalar()` の戻り値を設定する。
- `estimate.views.session`、`estimate.views.writeExcel`、必要に応じて `estimate.views.render_template` をpatchする。

### POST時のクエリ順序

| 順序 | 対象 | 検索結果の取得方法 | モックの戻り値 |
|---|---|---|---|
| 1 | Job | `join().filter().all()` | `[job]` |
| 2 | ContentまたはTool | `join().filter().all()` または `filter().first()` | ContentリストまたはTool |
| 3 | Agency名 | `join().filter().scalar()` | 代理店名または `None` |
| 4 | Account名 | `join().filter().scalar()` | 担当者名または `None` |
| 5 | Project名 | `join().filter().scalar()` | プロジェクト名または `None` |

## 3. テストケース一覧

| ID | テスト関数 | 検証内容 | 期待結果 |
|---|---|---|---|
| EST-001 | `test_estimate_get` | 未見積もりJob一覧の表示 | HTTP 200、Jobをテンプレートに渡し、`error=""` |
| EST-002 | `test_estimate_get_empty` | Jobが0件の場合 | HTTP 200、`jobs=[]`、`error="ジョブは0件です。"` |
| EST-003 | `test_estimate_post_web_job` | Web系JobのExcel出力データ | 作業内容・価格・作成日・税率を含む行と宛先3項目を `writeExcel()` に渡す |
| EST-004 | `test_estimate_post_print_job` | 紙媒体JobのExcel出力データ | Jobタイトル・価格・作成日・Toolの税率を含む行を渡し、commitを1回実行 |
| EST-005 | `test_estimate_post_multiple_contents` | Contentが複数あるJob | 作業内容ごとに2行を出力データに追加 |
| EST-006 | `test_estimate_post_no_contents` | Web系JobにContentがない場合 | Jobの基本情報を1行追加し、税率を `0.0` とする |
| EST-007 | `test_estimate_post_mark_estimated` | 見積済みフラグの更新 | `estimated=1`、commitが1回 |
| EST-008 | `test_estimate_post_recipient` | 宛先情報が取得できる場合 | 代理店・担当者・プロジェクト名を文字列として渡す |
| EST-009 | `test_estimate_post_recipient_none` | 宛先情報が取得できない場合 | 宛先3項目に `None` を渡し、HTTP 200 |
| EST-010 | `test_estimate_post_excel_response` | Excel出力関数のレスポンス | `writeExcel()` の戻り値を返し、`session.close()` が1回 |
| EST-011 | `test_estimate_post_multiple_jobs_current_behavior` | 複数Jobを選択した場合の現行動作 | 最初のJobで処理終了、Excel出力・commitが各1回、クエリ5回 |
| EST-012 | `test_estimate_login_required_get` | 未認証GET | HTTP 302、`/login/` に遷移、DB検索なし |
| EST-013 | `test_estimate_login_required_post` | 未認証POST | HTTP 302、`/login/` に遷移、DB検索・commit・Excel出力なし |

## 4. 主要テストケースの詳細

### EST-001：未見積もりJobの一覧表示

**入力：** `GET /estimate/`、Job検索結果 `[job]`。

**検証：** HTTP 200、`session.query(Job)` が1回、`join()` が3回、`render_template("estimate/index.html", jobs=[job], error="")` が1回呼ばれる。

### EST-002：Jobが0件の場合

**入力：** `GET /estimate/`、Job検索結果 `[]`。

**検証：** HTTP 200、テンプレートに `jobs=[]` および `error="ジョブは0件です。"` を渡す。

### EST-003：Web系Jobの出力

**入力：** Job「Webサイト制作」、Content「文言修正」、価格 `30000`、作成日 `2026-11-09`、税率 `0.1`。

**検証：** HTTP 200、レスポンス本文 `EXCEL RESULT`。`writeExcel()` が次の引数で1回呼ばれる。

```python
writeExcel(
    [["Webサイト制作", "文言修正", 30000, "2026-11-09", 0.1]],
    "テスト代理店",
    "テスト担当者",
    "テストプロジェクト",
)
```

### EST-004：紙媒体Jobの出力

**入力：** Job「パンフレット制作」、Tool種別ID `5`、価格 `50000`、Toolの税率 `10`。

**検証：** 出力データの先頭引数が `[["パンフレット制作", None, 50000, "2026-11-09", 10]]`、HTTP 200、commitが1回。

### EST-005：複数Contentの出力

**入力：** Content「デザイン」価格 `20000`、Content「コーディング」価格 `30000`。

**検証：** `writeExcel()` に渡す出力データは2行。1行目は「デザイン」・`20000`、2行目は「コーディング」・`30000`。

### EST-006：Contentが0件の場合

**入力：** Web系Job、Content検索結果 `[]`。

**検証：** HTTP 200、出力データが次の1行となり、commitが1回呼ばれる。

```python
[["Webサイト制作", None, 100000, "2026-11-09", 0.0]]
```

### EST-007：見積済み更新

**入力：** `POST /estimate/`、Job ID `1`。

**検証：** 対象Jobの `estimated` が `1` になり、`session.commit()` が1回呼ばれる。

### EST-008・EST-009：宛先情報

**通常時：** `writeExcel()` の第2〜4引数が順に「テスト代理店」「テスト担当者」「テストプロジェクト」であることを検証する。

**検索結果なし：** `setup_post_queries()` に `agency_name=None`、`account_name=None`、`project_name=None` を渡し、HTTP 200と `writeExcel()` の第2〜4引数がすべて `None` であることを検証する。実際のExcel生成関数が `None` を処理できるかどうかは本テストの対象外。

### EST-010：Excel出力レスポンス

**入力：** `writeExcel()` のモック戻り値 `TEST EXCEL RESPONSE`。

**検証：** HTTPレスポンス本文がその文字列と一致し、`writeExcel()` と `session.close()` が各1回呼ばれる。

### EST-011：複数Job選択時の現行動作

**入力：** `job=["1", "2"]`。

**検証：** HTTP 200、`writeExcel()` とcommitが各1回、`session.query()` が5回呼ばれる。現在の実装は最初のJobを処理した時点で `return` するため、2件目は処理しない。このテストは**現行動作の記録**であり、複数Jobの一括出力を保証するものではない。

### EST-012・EST-013：認証制御

**入力：** 未認証状態で `GET /estimate/` または `POST /estimate/`。

**検証：** HTTP 302、遷移先 `/login/`。GETはDB検索なし、POSTはDB検索・commit・`writeExcel()` 呼び出しなし。

## 5. テスト対象外・今後の検討事項

- 実際の `.xlsx` ファイルの生成、セル値、書式、シート構造。
- PostgreSQLに対する実際のSELECT・UPDATEとトランザクションの永続化。
- Excel出力失敗時のロールバックや、見積済みフラグとの整合性。
- 対象Jobが存在しない場合やPOSTでJobを選択しなかった場合の挙動。
- 複数Jobを1つの見積書にまとめる機能（現行実装では未対応）。
- `writeExcel()` が宛先情報の `None` を許容するかどうか。

## 6. 実行方法

```bash
python -m pytest tests/unit/test_estimate.py -v
```

## 7. 合格基準・確認結果

- 全13件のテストがPASSEDとなること。
- Excel出力関数に渡すデータと宛先情報が期待値に一致すること。
- 見積済みフラグの更新、DBセッションのcommit・closeが所定の回数呼ばれること。
- 未認証ユーザーがGET・POSTの処理を実行できないこと。

**確認結果：** ユーザーによる修正後の単体テスト実行で、全件パスしたとの報告あり。本文書作成時にpytestを再実行したものではない。
