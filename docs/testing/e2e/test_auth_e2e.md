# 認証E2Eテスト仕様書 — `test_auth_e2e.py`

## 1. 概要

| 項目 | 内容 |
|---|---|
| 対象 | Flaskアプリケーション `invoicee` の認証機能 |
| テストファイル | `tests/e2e/test_auth_e2e.py` |
| 共通fixture | `tests/e2e/conftest.py` |
| テストフレームワーク | pytest + Playwright（Chromiumなど） |
| データベース | PostgreSQL（`.env.test` に指定したテスト専用DB） |
| テストケース | 6件 |
| 確認状況 | ユーザーによる全件PASSの報告あり（共通fixture移動後） |

### 目的

ブラウザ上の入力・クリック・画面遷移を通して、ログイン、認証失敗、アクセス制御、ログアウト、セッション維持、新規ユーザー登録が実際のFlaskアプリケーションとPostgreSQLに対して正しく動作することを確認する。

## 2. テストケース一覧

| ID | 関数名 | 検証内容 | 期待結果 | 確認状況 |
|---|---|---|---|---|
| AUTH-E2E-001 | `test_login_success` | 正しいユーザー名とパスワードでログイン | `/top/` へ遷移 | PASS報告あり |
| AUTH-E2E-002 | `test_login_wrong_password` | 誤ったパスワードでログイン | `/login/` に留まり、保護ページへのアクセスはログイン画面に転送 | PASS報告あり |
| AUTH-E2E-003 | `test_protected_page_redirects_when_logged_out` | 未ログインで `/top/` にアクセス | `/login/` に転送 | PASS報告あり |
| AUTH-E2E-004 | `test_logout` | ログイン後に `/logout/` へアクセス | 再度 `/top/` にアクセスすると `/login/` へ転送 | PASS報告あり |
| AUTH-E2E-005 | `test_session_survives_reload` | ログイン後にブラウザを再読み込み | `/top/` を維持し、ページ本文が空でない | PASS報告あり |
| AUTH-E2E-006 | `test_register_and_login` | 新規ユーザーを登録し、その資格情報でログイン | `/top/` へ遷移し、テスト後に登録ユーザーを削除 | PASS報告あり |

> 確認状況は、共有されたテストコードとユーザーからの実行結果報告に基づく。CIログや最終版ファイルの実測結果を別途検証したものではない。

## 3. テストケース詳細

### AUTH-E2E-001 — ログイン成功

**前提条件:** `.env.test` の `TEST_USERNAME` / `TEST_PASSWORD` に対応するユーザーがテストDBに存在する。

**操作:** `/login/` を開き、ユーザー名・パスワードを入力して送信する。

**期待結果:** ブラウザのURLが `/top/` になる。

### AUTH-E2E-002 — ログイン失敗

**操作:** テストユーザー名と誤ったパスワードを入力し、ログインを送信する。続けて `/top/` を開く。

**期待結果:** ログイン後も `/login/` に留まり、保護ページへ直接アクセスしてもログイン画面へ転送される。

**範囲:** エラーメッセージの文言そのものは、共有されたテストコードでは検証していない。

### AUTH-E2E-003 — 未ログインアクセス制限

**操作:** 新しい未認証ブラウザページで `/top/` を開く。

**期待結果:** `/login/`（`next` クエリパラメータが付く場合を含む）へ転送される。

### AUTH-E2E-004 — ログアウト

**前提条件:** `auth_page` fixtureによりログイン済み。

**操作:** `/logout/` にアクセスし、その後 `/top/` を開く。

**期待結果:** ログイン画面に転送される。ログアウト後に保護ページへアクセスできない。

### AUTH-E2E-005 — セッション維持

**前提条件:** `auth_page` fixtureにより `/top/` にログイン済み。

**操作:** `page.reload()` で再読み込みする。

**期待結果:** URLが `/top/` のままで、`body` が空でない。

**範囲:** ブラウザ終了・再起動をまたぐセッション保持までは検証していない。

### AUTH-E2E-006 — 新規登録とログイン

**操作:** 一意なユーザー名（UUID由来）とテスト用パスワードを用いて `/register/` から登録し、いったん `/logout/` にアクセスしてから新規アカウントでログインする。

**期待結果:** 新規アカウントで `/top/` へ遷移する。

**後処理:** `finally` 節で `.env.test` のDBに接続し、当該ユーザー名のレコードのみを削除する。

**注意:** 登録処理自体の画面遷移は明示的には検証しておらず、後続のログイン成功によって登録を間接的に確認する。

## 4. 共通fixture（`tests/e2e/conftest.py`）

| fixture | scope | 役割 |
|---|---|---|
| `e2e_config` | session | `.env.test` の読み込み、必須設定の確認、本番設定との接続先比較 |
| `init_test_database` | session | テスト専用DBの確認、テーブル作成、テストユーザーの作成・パスワード更新 |
| `e2e_server` | session | テストDB環境変数を渡したFlaskサーバーの起動・終了 |
| `auth_page` | function | Playwrightページでログインし、認証済みページを各テストに渡す |
| `page` | function | pytest-playwrightによるテストごとのブラウザページ |

実行時の依存関係は概ね次のとおり。

```text
e2e_config
    └── init_test_database
          └── e2e_server
                ├── page → 未認証操作のテスト
                └── auth_page → 認証済み操作のテスト
```

`login()` はfixtureではなく共通ヘルパー関数として利用できる。`conftest.py` に置いた通常の関数は、fixtureと異なりテストファイルへ自動注入されない点に注意する。

## 5. 環境設定と安全対策

ルートディレクトリの `.env.test` に少なくとも以下を設定する。

```dotenv
DATABASE_URL=postgresql+psycopg://<test-user>:<password>@localhost:5432/invoicee_test
TEST_USERNAME=<test-username>
TEST_PASSWORD=<test-password>
```

- DB名が `invoicee_test` であることを初期化前に検証する。
- `.env` と `.env.test` の `DATABASE_URL` が同一であれば実行を停止する。
- 初期化と登録ユーザー削除には、`.env.test` の接続先を明示的に用いる。
- Flaskサーバーは別プロセスで起動するため、そのプロセスにも `.env.test` の環境変数を渡す。
- **DB名だけの検証では十分な隔離にならない。** テスト専用のDBロールを使用し、本番DBへの権限を付与しない。
- テストユーザーの初期化は既存レコードを削除せず、必要に応じてパスワードを更新する。テストユーザーは終了後も残る構成。

## 6. 実行方法

認証E2Eテストのみ実行する。

```bash
python -m pytest tests/e2e/test_auth_e2e.py -v
```

ブラウザを表示する。

```bash
python -m pytest tests/e2e/test_auth_e2e.py -v --headed
```

E2Eテスト全体を実行する。

```bash
python -m pytest tests/e2e/ -v
```

個別ケースを実行する。

```bash
python -m pytest tests/e2e/test_auth_e2e.py -k 'test_logout' -v
```

## 7. 運用上の注意と今後の改善

1. **サーバーのポート競合:** 例では `127.0.0.1:5011` を使用する。既存プロセスが同じポートを使用していないか確認する。将来的には空きポートの自動割り当てを検討する。
2. **親ディレクトリのfixture:** `tests/conftest.py` に `autouse=True` のfixtureがある場合、E2Eにも適用されるためDB初期化やスキーマ操作の競合に注意する。
3. **テストデータの独立性:** 新規登録ユーザーはUUIDで一意化し、テスト後に削除する。途中失敗時も `finally` によって削除を試みる。
4. **エラー表示の検証:** ログイン失敗時のメッセージ内容や入力値の扱いは、必要に応じて追加する。
5. **登録成功の検証:** 登録後の画面遷移、成功メッセージ、重複ユーザー登録の拒否などを追加できる。
6. **セッションの検証:** ブラウザ再起動、Cookie期限切れ、複数タブの動作などは今回の範囲外。
7. **依存パッケージ:** 過去に `pytest-base-url` 更新によってpytestの非推奨警告が解消したため、依存関係のバージョンを管理する。

## 8. 位置付け

本ファイルはブラウザ操作を伴う認証機能のE2E仕様書であり、Flaskテストクライアントによる `test_auth_integration.py` の検証を補完する。DB例外・トランザクション・404/405ハンドラ等の詳細検証は、それぞれの結合テストまたは別のE2Eテストで扱う。
