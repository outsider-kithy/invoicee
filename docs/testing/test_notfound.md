# `test_notfound.py` 単体テスト仕様書

## 1. 概要

- **テスト対象:** `notfound/views.py`
- **テストコード:** `tests/unit/test_notfound.py`
- **対象エンドポイント:** `/notfound/`（GET / POST）
- **テストフレームワーク:** pytest、Flaskテストクライアント、`unittest.mock.patch`
- **テストケース数:** 6件

`notfound` Blueprintが認証済みユーザーに対して404ページを返し、未認証ユーザーをログインページにリダイレクトすることを検証する。HTMLテンプレートの実レンダリングは対象外とし、`render_template()` をモック化して呼び出し引数を検証する。

## 2. 対象処理と期待仕様

`notfound/views.py` の `index()` は `@login_required` を付与した `/` ルートであり、Blueprintが `/notfound` プレフィックスで登録されていることを前提とする。

- **認証済み・GET:** `notfound/index.html` に `error_message="指定のページは見つかりませんでした。"` を渡し、HTTP 404を返す。
- **認証済み・POST:** GETと同じテンプレート・メッセージ・HTTP 404を返す。
- **未認証・GET / POST:** `@login_required` によりログイン画面へHTTP 302でリダイレクトし、`render_template()` は呼ばれない。

## 3. テストケース一覧

| ID | テスト関数 | 条件 | 主な期待結果 |
| --- | --- | --- | --- |
| NFD-001 | `test_notfound_get_status_code` | 認証済み、GET `/notfound/` | HTTP 404、レスポンス本文 `NOT FOUND PAGE` |
| NFD-002 | `test_notfound_get_template` | 認証済み、GET `/notfound/` | テンプレート名と日本語メッセージが正しい |
| NFD-003 | `test_notfound_post_status_code` | 認証済み、POST `/notfound/` | HTTP 404、レスポンス本文 `NOT FOUND PAGE` |
| NFD-004 | `test_notfound_post_template` | 認証済み、POST `/notfound/` | テンプレート名と日本語メッセージが正しい |
| NFD-005 | `test_notfound_login_required_get` | 未認証、GET `/notfound/` | HTTP 302、`/login/` にリダイレクト、テンプレート未呼び出し |
| NFD-006 | `test_notfound_login_required_post` | 未認証、POST `/notfound/` | HTTP 302、`/login/` にリダイレクト、テンプレート未呼び出し |

## 4. 各テストの検証内容

### NFD-001：GETのステータスコード

`authenticated` fixtureで認証状態を再現し、`render_template()` の戻り値を `NOT FOUND PAGE` に固定する。`client.get('/notfound/')` のHTTPステータスが404であり、レスポンス本文がモックの戻り値と一致することを確認する。

### NFD-002：GETのテンプレートとメッセージ

GETリクエスト後、`render_template()` が以下の引数で1回呼び出されたことを確認する。

```python
mock_render.assert_called_once_with(
    "notfound/index.html",
    error_message="指定のページは見つかりませんでした。"
)
```

### NFD-003：POSTのステータスコード

認証済みで `client.post('/notfound/')` を実行し、HTTP 404とレスポンス本文 `NOT FOUND PAGE` を確認する。

### NFD-004：POSTのテンプレートとメッセージ

POSTでもGETと同じ `notfound/index.html` とエラーメッセージが渡されることを `assert_called_once_with()` で確認する。

### NFD-005：未認証GETのアクセス制限

認証モックを設定せずGETを実行し、HTTP 302であること、`urlparse(response.location).path == '/login/'` であること、`render_template()` が呼ばれないことを確認する。

### NFD-006：未認証POSTのアクセス制限

認証モックを設定せずPOSTを実行し、GETと同様にHTTP 302、遷移先 `/login/`、`render_template()` 未呼び出しを確認する。

## 5. fixtureとモック

### `client`

既存の `tests/conftest.py` で提供されるFlaskテストクライアントを利用する。アプリケーションに `notfound` Blueprintが `/notfound` で登録されていることを前提とする。

### `authenticated`

`flask_login.utils._get_user` を `patch()` し、戻り値の `is_authenticated` を `True` にする。認証済みケースで使用する。

```python
@pytest.fixture
def authenticated():
    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value.is_authenticated = True
        yield mock_user
```

### `render_template` のモック

```python
with patch("notfound.views.render_template") as mock_render:
    mock_render.return_value = "NOT FOUND PAGE"
```

実際のJinja2テンプレートに依存せず、ビュー関数が選択したテンプレートと引数を確認する。未認証ケースでは `assert_not_called()` を使う。

## 6. 実行方法

プロジェクトルートで実行する。

```bash
python -m pytest tests/unit/test_notfound.py -v
```

想定結果：**6 passed**。実行環境や認証設定が変更された場合は結果を再確認すること。

## 7. 前提条件・対象外

- 未認証時のリダイレクト先 `/login/` は、Flask-Loginの `login_view` 設定に依存する。
- このテストは **`/notfound/` ルート** の動作を確認するもので、存在しない任意のURLに対するFlask全体の404エラーハンドリングは検証しない。
- HTMLテンプレートの実際の表示内容・レイアウト・Jinja2のレンダリング結果は検証しない。
- 認証状態はモックで再現するため、実ユーザーのログイン処理そのものは検証しない。
- `@login_required` により未認証アクセスは404ではなく302になる点に注意する。

## 8. 今後の拡張候補

アプリケーション全体で未知のURLを共通の404ページへ誘導する仕様を追加した場合は、`@app.errorhandler(404)` などの登録と、存在しないURLへのリクエストを使った結合テストを別途設ける。
