# `test_error.py` 単体テスト仕様書

## 1. 概要

- **対象モジュール**：`error/views.py`
- **テストコード**：`tests/unit/test_error.py`
- **対象Blueprint**：`error`（URLプレフィックス：`/error`）
- **テストフレームワーク**：pytest、Flaskテストクライアント、`unittest.mock`
- **テストケース数**：7件

### 目的

`GET /error/` のエラーページ表示、許可されないHTTPメソッドの拒否、SQLAlchemy例外発生時のロールバック・ログ出力・500応答を確認する。実データベースへの接続は行わず、DBセッションやテンプレート描画をモック化する。

## 2. テスト対象の動作

### `index()`

- `GET /error/` で `error/index.html` を描画する。
- `error_message` に `データベースエラーが発生しました。` を渡す。
- HTTPステータスコード `500` を返す。
- POSTはルートに許可されていないため `405 Method Not Allowed` になる。

### `handle_database_error(e)`

- `SQLAlchemyError` を受け取ったら `session.rollback()` を試みる。
- ロールバック失敗時は `current_app.logger.exception("Database rollback failed")` を記録し、処理を継続する。
- `current_app.logger.error("Database Error", exc_info=(type(e), e, e.__traceback__))` を呼び出す。
- `error/index.html` に共通エラーメッセージを渡し、HTTPステータス `500` を返す。

## 3. テストケース一覧

| ID | テスト関数 | 操作・条件 | 期待結果 |
|---|---|---|---|
| ERR-001 | `test_error_get_status_code` | `GET /error/` | HTTP 500、本文 `ERROR PAGE` |
| ERR-002 | `test_error_get_template` | `GET /error/` | 指定テンプレートとエラーメッセージで描画 |
| ERR-003 | `test_error_post_not_allowed` | `POST /error/` | HTTP 405、テンプレート描画なし |
| ERR-004 | `test_database_error_rollback` | `SQLAlchemyError` を直接ハンドラへ渡す | `session.rollback()` が1回呼ばれる |
| ERR-005 | `test_database_error_response` | `SQLAlchemyError` を直接ハンドラへ渡す | 戻り値が `("ERROR PAGE", 500)`、指定テンプレートを描画 |
| ERR-006 | `test_database_error_logging` | トレースバック付きの `SQLAlchemyError` | `logger.error` に例外情報を渡す |
| ERR-007 | `test_database_error_rollback_failure` | `rollback()` が `RuntimeError` を送出 | 失敗ログと元のDBエラーログを記録し、500応答を返す |

## 4. 各テストの仕様

### ERR-001：エラーページのステータス

`render_template` を `"ERROR PAGE"` にモック化し、`client.get("/error/")` を実行する。`response.status_code == 500` と `response.get_data(as_text=True) == "ERROR PAGE"` を確認する。

### ERR-002：テンプレートとメッセージ

GETリクエスト後、`render_template` が次の引数で1回呼ばれたことを検証する。

```python
mock_render.assert_called_once_with(
    "error/index.html",
    error_message="データベースエラーが発生しました。"
)
```

### ERR-003：POSTの拒否

`client.post("/error/")` の結果が405であり、`render_template` が呼ばれていないことを確認する。

### ERR-004：DB例外発生時のロールバック

`SQLAlchemyError("DB connection failed")` を作成し、`app.app_context()` 内で `handle_database_error(error)` を直接呼び出す。`session.rollback()` の呼び出し回数が1回であることを確認する。

### ERR-005：DB例外発生時の応答

例外ハンドラの戻り値を `response, status_code` に分解し、`status_code == 500`、`response == "ERROR PAGE"` を確認する。テンプレート名と共通エラーメッセージも検証する。

### ERR-006：DB例外のログ記録

実際に `SQLAlchemyError` を `raise` して捕捉し、トレースバックを持つ例外オブジェクトを用意する。`logger.error` が以下の引数で1回呼ばれることを確認する。

```python
mock_log_error.assert_called_once_with(
    "Database Error",
    exc_info=(type(db_error), db_error, db_error.__traceback__)
)
```

### ERR-007：ロールバック失敗時の継続処理

`mock_session.rollback.side_effect = RuntimeError("Rollback failed")` を設定する。ロールバックが1回試行され、`logger.exception("Database rollback failed")` と元のDBエラーに対する `logger.error(...)` がそれぞれ1回呼ばれ、最終的に `("ERROR PAGE", 500)` が返ることを確認する。

## 5. fixture・モックの構成

| 対象 | 用途 |
|---|---|
| `client` | `GET /error/`、`POST /error/` のHTTPテスト |
| `app` | `app.app_context()` の生成とアプリケーションロガーの参照 |
| `patch("error.views.render_template")` | 実テンプレートを描画せず戻り値・呼び出し引数を検証 |
| `patch("error.views.session")` | 実DBへのアクセスを防ぎ、ロールバックを検証 |
| `patch.object(app.logger, "error")` | DB例外のログ記録を検証 |
| `patch.object(app.logger, "exception")` | ロールバック失敗ログを検証 |

`handle_database_error()` は `current_app.logger` を使用するため、直接呼び出すテストでは **`app.app_context()` が必要**。HTTPクライアントを使用するテストでは、Flaskがリクエストコンテキストを管理する。

## 6. テストの実行方法

```bash
python -m pytest tests/unit/test_error.py -v
```

特定のケースのみ実行する例：

```bash
python -m pytest tests/unit/test_error.py -v -k rollback_failure
```

**期待結果**：7件すべてが `PASSED`。これはテスト仕様上の期待値であり、このドキュメント作成時に実行結果を確認したものではない。

## 7. テスト範囲と制約

- `handle_database_error()` のテストは関数を直接呼び出しているため、Flaskが実際のルート処理中に発生した `SQLAlchemyError` を自動的にハンドラへ振り分けることまでは検証しない。
- 実際のPostgreSQL接続、トランザクション状態、テンプレートのHTML表示内容は検証しない。
- `ERR-005` の `response` はモック化した `render_template` の戻り値であり、実際のFlask `Response` オブジェクトではない。
- 実運用での例外ハンドラ登録とエラー画面表示は、別途 `tests/integration/test_error_integration.py` などで確認する。

## 8. 今後の拡張候補

- テスト用ルートで `SQLAlchemyError` を発生させ、`@error.app_errorhandler(SQLAlchemyError)` の登録・呼び出しを結合テストで確認する。
- エラー画面にSQL文や接続情報などの内部情報が表示されないことを確認する。
- 必要に応じて、ロールバック成功・失敗後のDBセッションの扱いを結合テストで確認する。
