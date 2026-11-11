# test_error_e2e.py — E2Eテスト仕様書

## 1. 概要

Flaskアプリケーションのエラー処理（`/error/`、`/404/`、存在しないURL、許可されないHTTPメソッド、およびSQLAlchemy例外）を、pytestとPlaywrightでブラウザ／HTTPレベルから検証する。

- 対象: `tests/e2e/test_error_e2e.py`
- 関連実装: `error/views.py`、`notfound/views.py`、各 `templates/.../index.html`、`app.py`
- 実行環境: テスト用Flaskサーバー（既存の `e2e_server` fixture）、Playwright、pytest
- 実行結果: **12件 PASS**（ユーザーによる実行確認、2026-11-11）
- DBレコードの追加・削除: 原則不要。SQLAlchemyErrorの再現はテスト専用ルートを使用する。

## 2. 対象ルートと期待仕様

| 対象 | メソッド・条件 | 期待HTTPステータス | 表示内容 |
|---|---|---:|---|
| `/error/` | GET / POST | 500 | 「データベースエラー」「データベースエラーが発生しました。」 |
| `/404/` | GET / POST | 404 | 「404エラー」「指定のページは見つかりませんでした。」 |
| 存在しないURL | GET | 404 | 404エラーページ。元のURLを維持 |
| `/error/` | PUT | 405 | 「このHTTPメソッドは許可されていません。」、`Allow` ヘッダー |
| テスト専用DB例外ルート | SQLAlchemyError発生 | 500 | 共通DBエラーページ |

`app.py` は `error` Blueprint を `/error`、`notfound` Blueprint を `/404` で登録している。`notfound.app_errorhandler(404)` および `(405)` はアプリ全体のHTTPエラーを処理する。`error.app_errorhandler(SQLAlchemyError)` は例外時に `session.rollback()` を試み、エラーをログに記録して500レスポンスを返す。

## 3. テストケース一覧

| ID | テスト関数 | 検証内容 | 結果 |
|---|---|---|---|
| ERROR-E2E-001 | `test_error_page_get` | `/error/` GETで500と見出しを表示 | PASS |
| ERROR-E2E-002 | `test_error_page_post` | `/error/` POSTで500 | PASS |
| ERROR-E2E-003 | `test_error_message_display` | DBエラーメッセージが正しい | PASS |
| ERROR-E2E-004 | `test_notfound_page_get` | `/404/` GETで404と見出しを表示 | PASS |
| ERROR-E2E-005 | `test_notfound_page_post` | `/404/` POSTで404とメッセージ | PASS |
| ERROR-E2E-006 | `test_unknown_url_notfound` | 存在しないURLで404画面 | PASS |
| ERROR-E2E-007 | `test_notfound_url_preserved` | 404処理でURLが変更されない | PASS |
| ERROR-E2E-008 | `test_method_not_allowed` | `/error/` PUTで405 | PASS |
| ERROR-E2E-009 | `test_method_not_allowed_message` | 405用メッセージを表示 | PASS |
| ERROR-E2E-010 | `test_method_not_allowed_allow_header` | `Allow` にGETとPOSTを含む | PASS |
| ERROR-E2E-011 | `test_recovery_after_error` | 500ページ表示後に `/top/` が200 | PASS |
| ERROR-E2E-012 | `test_database_exception_handler` | SQLAlchemyErrorから500画面を返す | PASS |

## 4. テストケース詳細

### ERROR-E2E-001 — 500エラーページ（GET）
- **手順:** Playwrightで `/error/` にGETアクセスする。
- **期待:** HTTP 500、URLが `/error/`、見出し「データベースエラー」が表示される。

### ERROR-E2E-002 — 500エラーページ（POST）
- **手順:** PlaywrightのAPIリクエストで `/error/` にPOSTする。
- **期待:** HTTP 500を返す。

### ERROR-E2E-003 — DBエラーメッセージ
- **手順:** `/error/` を表示し `p.error` のテキストを確認する。
- **期待:** 「データベースエラーが発生しました。」と完全一致する。

### ERROR-E2E-004 — 404ページ（GET）
- **手順:** `/404/` にGETアクセスする。
- **期待:** HTTP 404、URLが `/404/`、見出し「404エラー」が表示される。

### ERROR-E2E-005 — 404ページ（POST）
- **手順:** `/404/` にPOSTする。
- **期待:** HTTP 404で「指定のページは見つかりませんでした。」を含む。

### ERROR-E2E-006 — 未定義URLの404処理
- **手順:** UUID付きの存在しないパスにGETアクセスする。
- **期待:** HTTP 404、見出し「404エラー」、`p.error` に指定メッセージを表示する。

### ERROR-E2E-007 — 404時のURL維持
- **手順:** 別の未定義パスにGETアクセスする。
- **期待:** HTTP 404のまま、ブラウザのURLが元の未定義パスである（`/404/` へリダイレクトしない）。

### ERROR-E2E-008 — 許可されないHTTPメソッド
- **手順:** GET/POSTのみ許可される `/error/` にPUTする。
- **期待:** HTTP 405を返す。

### ERROR-E2E-009 — 405メッセージ
- **手順:** `/error/` にPUTし、レスポンス本文を確認する。
- **期待:** 「このHTTPメソッドは許可されていません。」を含む。

### ERROR-E2E-010 — Allowヘッダー
- **手順:** `/error/` にPUTし、レスポンスヘッダー `Allow` を取得する。
- **期待:** 少なくとも `GET` と `POST` を含む（`HEAD` や `OPTIONS` が含まれてもよい）。

### ERROR-E2E-011 — エラー後の通常画面への復帰
- **手順:** ログイン済みブラウザで `/error/` を表示した後、`/top/` にアクセスする。
- **期待:** 最初は500、その後 `/top/` はHTTP 200で表示される。
- **注:** これは500ページからの画面遷移の確認であり、DBトランザクション復旧の直接検証ではない。

### ERROR-E2E-012 — SQLAlchemyErrorハンドラー
- **手順:** テスト環境でのみ有効な例外発生用ルート（例: `/__test__/database-error`）にアクセスし、`SQLAlchemyError` を発生させる。
- **期待:** HTTP 500、`p.error` に「データベースエラーが発生しました。」を表示する。
- **注:** 実際のDB障害を発生させるのではなく、テスト専用ルートから例外を送出する。`rollback()` の呼び出し回数やログ出力の内容は、このE2Eテスト単独では厳密に検証していない。

## 5. Fixture・テストデータ・安全対策

- `e2e_server`: 既存のテスト用Flaskサーバーを起動するfixture。
- `auth_page`: ログイン済みPlaywrightページ。`/top/` への復帰確認で使用。
- `page`: 未認証状態の独立したPlaywrightページ。GET表示やHTTPリクエスト検証で使用。
- `uuid.uuid4()`: 未定義URLを一意にして既存ルートとの衝突を避ける。
- **SQLAlchemyError再現用ルートは本番に登録しない。** テスト設定でのみ登録し、外部公開しない。
- エラー画面のGET/POSTテストはDBに変更を加えないため、専用のデータ作成・クリーンアップfixtureは不要。

## 6. 実行方法

```bash
# エラー処理のE2Eテストのみ
python -m pytest tests/e2e/test_error_e2e.py -v

# ブラウザを表示して実行
python -m pytest tests/e2e/test_error_e2e.py -v --headed

# E2Eテスト全体
python -m pytest tests/e2e/ -v
```

**確認済み結果:** 12ケースすべてPASS。実行時間やpytestのログ全文は本書には含めない。

## 7. 今後の追加候補

1. SQLAlchemyError発生時の `session.rollback()` とログ記録を単体／結合テストで検証する。
2. DB例外発生後に実際のDBクエリが正常に実行できることを検証する。
3. `/error/` および `/404/` のレスポンスに意図したキャッシュ制御や機密情報非表示が適用されているかを確認する。
4. `Allow` ヘッダーの内容とHTTPメソッドの許可設定の整合性を継続的に確認する。

---

作成日: 2026-11-11
