# test_other_integration.py 結合テスト仕様書

## 1. 概要

Flaskアプリケーションの主要画面、認証によるアクセス制御、ルーティング、404・405エラーページを検証する結合テストの仕様書です。

- 対象: `tests/integration/test_other_integration.py`
- 実行環境: pytest、Flaskテストクライアント、テスト用PostgreSQL
- 共通fixture: `app`、`client`、`authenticated_client`、`seed`（`tests/conftest.py`）
- 目的: HTTPレスポンス、リダイレクト、HTML描画、およびアプリケーション全体のルーティングを確認する

> **実行結果について:** 初期のテストでは `test_notfound_page_display` が302を返して失敗しましたが、`notfound/views.py` の `@login_required` を削除した後、当初のテストはすべてPASSしたと報告されています。追加提案した404・405テストの実行結果は未確認です。

## 2. テストケース一覧

| ID | テスト関数 | 確認内容 | 期待結果 | 状況 |
|---|---|---|---|---|
| OTH-INT-001 | `test_top_page_authenticated` | ログイン済みトップ画面 | HTTP 200、HTML本文あり | PASS（報告済み） |
| OTH-INT-002 | `test_top_page_requires_login` | 未ログインのトップ画面 | HTTP 302、ログイン画面へ転送 | PASS（報告済み） |
| OTH-INT-003 | `test_login_page_display` | ログイン画面 | HTTP 200、HTML本文あり | PASS（報告済み） |
| OTH-INT-004 | `test_register_page_display` | 登録画面 | HTTP 200、HTML本文あり | PASS（報告済み） |
| OTH-INT-005 | `test_estimate_page_display` | ログイン済み見積画面 | HTTP 200、HTML本文あり | PASS（報告済み） |
| OTH-INT-006 | `test_estimate_page_requires_login` | 未ログインの見積画面 | HTTP 302、ログイン画面へ転送 | PASS（報告済み） |
| OTH-INT-007 | `test_unknown_url_returns_404` | 存在しないURL | HTTP 404 | PASS（報告済み） |
| OTH-INT-008 | `test_notfound_page_display` | `/404/` への直接アクセス | HTTP 404、HTML本文あり | PASS（修正後、報告済み） |
| OTH-INT-009 | `test_registered_routes` | 主要ルートの登録 | 必須URLが `app.url_map` に存在 | PASS（報告済み） |
| OTH-INT-010 | `test_authenticated_pages_return_html` | `/top/` と `/estimate/` のHTML構造 | HTTP 200、`<html>` と `</html>` | PASS（2パラメータ、報告済み） |
| OTH-INT-011 | `test_custom_404_page` | 存在しないURLの独自404画面（GET） | HTTP 404、指定メッセージ | 提案済み・結果未確認 |
| OTH-INT-012 | `test_custom_404_page_post` | 存在しないURLの独自404画面（POST） | HTTP 404、指定メッセージ | 提案済み・結果未確認 |
| OTH-INT-013 | `test_custom_405_page` | 不許可HTTPメソッドの独自405画面 | HTTP 405、指定メッセージ、`Allow`ヘッダー | 提案済み・結果未確認 |

※ OTH-INT-010はパラメータ化されているため、当初の10関数はpytest上で11ケースとして実行されます。追加3関数をすべて実装した場合は計14ケースです。

## 3. 共通検証関数

### `assert_html_response(response)`

- `response.status_code == 200`
- `response.mimetype == "text/html"`
- `response.data` が空でない

### `assert_login_redirect(response)`

- `response.status_code == 302`
- `urlparse(response.location).path == "/login/"`

`urlparse`を用いることで、`next`クエリパラメータが付いていてもリダイレクト先のパスを確認できます。

## 4. 404・405エラーハンドリングの実装

### 404 Not Found

`notfound/views.py` の `@notfound.app_errorhandler(404)` により、アプリケーション全体で発生する404エラーを捕捉し、`notfound/index.html` とメッセージ「指定のページは見つかりませんでした。」をHTTP 404で返します。

`/404/` への直接アクセスは `@notfound.route("/", methods=("GET", "POST"))` が処理します。404画面は未ログインでも表示できる仕様のため、当該ルートには `@login_required` を設定しません。

### 405 Method Not Allowed

`@notfound.app_errorhandler(405)` により、既存ルートに許可されていないHTTPメソッドでアクセスした場合、独自エラーページをHTTP 405で返します。メッセージは「このHTTPメソッドは許可されていません。」です。

405レスポンスには、例外の `valid_methods` をもとにした `Allow` ヘッダーを設定します。GET・POST対応の `/login/` にPUTを送るテストでは、`Allow` にGETとPOSTが含まれ、PUTが含まれないことを確認します。

> 404と405は別のエラーです。存在しないURLへのリクエストは404、存在するURLに許可されていないメソッドを送った場合は405になります。

## 5. 追加テストのサンプルコード

```python
# OTH-INT-011: 独自404画面（GET）
def test_custom_404_page(client):
    response = client.get("/this-page-does-not-exist/")
    assert response.status_code == 404
    assert response.mimetype == "text/html"
    assert "指定のページは見つかりませんでした。" in response.get_data(as_text=True)


# OTH-INT-012: 独自404画面（POST）
def test_custom_404_page_post(client):
    response = client.post("/this-page-does-not-exist/")
    assert response.status_code == 404
    assert response.mimetype == "text/html"
    assert "指定のページは見つかりませんでした。" in response.get_data(as_text=True)


# OTH-INT-013: 独自405画面
def test_custom_405_page(client):
    response = client.put("/login/")
    assert response.status_code == 405
    assert response.mimetype == "text/html"
    assert "このHTTPメソッドは許可されていません。" in response.get_data(as_text=True)
    allow = response.headers.get("Allow", "")
    assert "GET" in allow
    assert "POST" in allow
    assert "PUT" not in allow
```

**前提:** `notfound/index.html` が `error_message` を実際にHTMLへ表示していること、`/login/` がGET・POSTを許可していること。

## 6. 実行コマンド

全ケース:

```bash
python -m pytest tests/integration/test_other_integration.py -v
```

404関連:

```bash
python -m pytest tests/integration/test_other_integration.py -k "404 or notfound" -v
```

405関連:

```bash
python -m pytest tests/integration/test_other_integration.py -k "custom_405" -v
```

## 7. 注意事項・今後の拡張

- `app.url_map` の検査はルート登録の確認であり、各ルートの正常動作までは保証しません。
- HTMLの開始・終了タグの確認は簡易的な構造検証です。DOM操作やJavaScriptの動作はPlaywrightのE2Eテストで確認します。
- 未ログイン時のリダイレクト先は `LoginManager.login_view` の設定に依存します。
- `notfound` Blueprintの `app_errorhandler` はアプリ全体に登録されます。Blueprintの登録前にハンドラを定義してください。
- 必要に応じて `record`、`update`、`detail`、`commitlog`、`webhook`、`project`、`logout` 等のルートを追加検証します。具体的なURLや必須引数は各 `views.py` の定義に合わせます。
- 404・405の追加テストを実行後、その結果を本書の状況欄に反映してください。
