# 認証機能 結合テスト仕様書

## 1. 概要

- **対象ファイル**: `tests/integration/test_auth_integration.py`
- **目的**: Flask の認証ルートと SQLAlchemy／PostgreSQL の連携を、実際の HTTP リクエストとテスト用データベースを使って検証する。
- **対象機能**: ログイン、ログアウト、ログイン必須ページへのアクセス、セッション維持、ユーザー登録、パスワードのハッシュ化、ユーザー名の重複登録防止。
- **実行フレームワーク**: pytest、Flask test client、SQLAlchemy、PostgreSQL。

## 2. テスト環境と前提条件

`tests/conftest.py` の `app`、`client`、`seed` fixture を利用する。`app` はテスト用 PostgreSQL にテストごとの専用スキーマを作成し、モデルのテーブルを準備する。`client` は Flask のテストクライアントを提供する。`seed` は既存ユーザー `tester`（パスワード `test-password`）などの初期データを登録する。

`.env.test` の `DATABASE_URL` が**テスト専用データベース**を指していることを実行前に確認する。本番データベースでは実行しない。テスト終了時には専用スキーマを削除する構成を前提とする。

認証処理のリクエスト先は `/login/`、`/logout/`、`/register/`、保護対象ページは `/top/` とする。登録フォームの確認用パスワードのフィールド名は **`confirmation`** であり、`password_confirm` ではない。

## 3. テストケース一覧

以下は、これまでに作成・実行したテストの仕様を整理したもの。`test_login_empty_fields` はパラメータ化により3ケースとして数える。

| ID | テスト関数 | 検証内容 | 主な期待結果 |
| --- | --- | --- | --- |
| AUTH-INT-001 | `test_login_success` | 正しい認証情報でログイン | HTTP 302、`/top/` にリダイレクト |
| AUTH-INT-002 | `test_login_wrong_password` | 誤ったパスワードでログイン | ログイン失敗、保護ページに進めない |
| AUTH-INT-003 | `test_login_unknown_user` | 未登録ユーザーでログイン | ログイン失敗 |
| AUTH-INT-004〜006 | `test_login_empty_fields` | ユーザー名・パスワードの未入力（3パターン） | 入力エラー、認証されない |
| AUTH-INT-007 | `test_protected_route_without_login` | 未ログインで `/top/` にアクセス | HTTP 302、`/login/` にリダイレクト |
| AUTH-INT-008 | `test_protected_route_after_login` | ログイン後に `/top/` にアクセス | HTTP 200 |
| AUTH-INT-009 | `test_login_session_persistence` | ログイン後のセッション継続 | 続くリクエストでも認証状態が維持される |
| AUTH-INT-010 | `test_login_password_hash` | 保存済みパスワードのハッシュ確認 | 平文と異なり、ハッシュ照合が成功 |
| AUTH-INT-011 | `test_logout_success` | ログイン後のログアウト | ログアウト後は `/top/` にアクセス不可 |
| AUTH-INT-012 | `test_logout_without_login` | 未ログイン状態でログアウト操作 | 認証状態にならず、保護ページへアクセス不可 |
| AUTH-INT-013 | `test_register_success` | 新規ユーザー登録 | DBに新規ユーザーが保存される |
| AUTH-INT-014 | `test_register_password_hash` | 登録時のパスワード保存形式 | 平文ではなくハッシュで保存される |
| AUTH-INT-015 | `test_register_and_login` | 登録直後に同じ認証情報でログイン | HTTP 302で `/top/` に遷移し、保護ページがHTTP 200 |
| AUTH-INT-016 | `test_register_duplicate_username` | 既存ユーザー名での再登録 | 同名ユーザーが増えず、重複エラーを表示 |

**ケース数**: 16ケース（テスト関数は14個、うち1個が3パターン）。

> **補足**: 重複登録エラー後に別ユーザーを登録できることを検証する `test_register_after_duplicate` を追加している場合は、17ケース目として別途追記する。実際のファイルに含まれているかは未確認。

## 4. 主なテストの確認事項

### 4.1 ログイン

- 正しいユーザー名・パスワードで `/login/` にPOSTすると、`/top/` へリダイレクトされる。
- 誤パスワード・未登録ユーザー・未入力ではログインできない。
- 未認証状態で `/top/` にアクセスすると `/login/` にリダイレクトされる。
- ログイン後は、別リクエストでもセッションが維持される。

### 4.2 ログアウト

- ログイン後に `/logout/` へアクセスすると認証状態が解除される。
- ログアウト後に `/top/` へアクセスするとログイン画面にリダイレクトされる。
- 未ログイン状態でのログアウト操作後も、保護ページにはアクセスできない。

### 4.3 ユーザー登録

- `/register/` に `username`、`password`、`confirmation` を送信するとユーザーが作成される。
- 登録済みユーザーのパスワードは `check_password_hash()` で照合でき、平文では保存されない。
- 登録後、そのユーザー名・パスワードでログインできる。
- 同じユーザー名を登録しようとしてもDBのレコード数は増えず、アプリケーション側で重複を検出する。

## 5. テスト用ヘルパーの例

```python
from urllib.parse import urlparse
from sqlalchemy import select, func
from models import User, session

TEST_USERNAME = "tester"
TEST_PASSWORD = "test-password"


def login(client, username=TEST_USERNAME, password=TEST_PASSWORD):
    return client.post(
        "/login/",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def register(client, username, password, password_confirm=None):
    if password_confirm is None:
        password_confirm = password
    return client.post(
        "/register/",
        data={
            "username": username,
            "password": password,
            "confirmation": password_confirm,
        },
        follow_redirects=False,
    )


def get_user_by_username(username):
    return session.scalar(select(User).where(User.username == username))


def count_users_by_username(username):
    return session.scalar(
        select(func.count()).select_from(User).where(User.username == username)
    )
```

このコードは仕様を示す参考例であり、実際のテストファイルの完全な複製ではない。

## 6. 実行方法

プロジェクトのルートディレクトリから実行する。

```bash
python -m pytest tests/integration/test_auth_integration.py -v
```

警告も確認する場合:

```bash
python -m pytest tests/integration/test_auth_integration.py -v -ra
```

**期待結果**: 現在の16ケースがすべて `PASSED`。追加ケースを実装した場合は、その分だけ合計件数が増える。

## 7. 注意点・保守方針

1. **フォームのフィールド名**: 登録処理の確認パスワードは `confirmation` を使用する。名称を間違えると、DBへの登録処理まで到達しない。
2. **DBの分離**: `DATABASE_URL` はテスト専用DBを指定し、テストごとのスキーマ分離を維持する。
3. **主キー取得と検索**: 主キーで取得する場合は `session.get(User, id)`、ユーザー名で検索する場合は `session.scalar(select(User).where(...))` を使用する。
4. **重複登録の確認**: 件数だけでなく、レスポンスのエラー表示も検証する。登録フォームのテンプレートがメッセージを描画していることが前提となる。
5. **IntegrityError発生時**: アプリケーション側で `session.rollback()` を行い、後続のDB操作に影響しないようにする。
6. **テストの独立性**: テスト実行順序に依存しないよう、必要なデータはfixtureまたは各テストで準備する。

## 8. 今後の拡張候補

- 重複登録エラーの後に別ユーザーを正常登録できることの検証。
- ユーザー名・パスワードの境界値、空白入力、極端に長い入力の検証。
- 不正なセッションやログアウト後の再アクセスに関する追加検証。
- 同時登録時のUNIQUE制約違反を適切に処理できることの検証。

---

**関連ファイル**: `tests/conftest.py`、`tests/integration/test_auth_integration.py`、`register/views.py`、ログイン／ログアウトの各Blueprint、`models.py`。
