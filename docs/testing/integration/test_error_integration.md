# エラーハンドリング結合テスト仕様書

**対象ファイル:** `tests/integration/test_error_integration.py`  
**対象アプリケーション:** Flask / SQLAlchemy / PostgreSQL  
**関連コード:** `error/views.py`, `app.py`, `models.py`, `tests/conftest.py`  
**記録日:** 2026-11-10  
**実行結果:** 全10ケース PASS（ユーザー報告）

## 1. 目的

Flaskアプリケーションのエラーページ表示、PostgreSQLの整合性制約違反、SQLAlchemy Sessionのロールバックと復旧、およびアプリケーション全体に登録された `SQLAlchemyError` ハンドラの動作を結合テストで確認する。

特に、実DBで主キー重複による `IntegrityError` を発生させ、HTTP 500応答とエラーメッセージ、`session.rollback()` の実行、既存データの保全を検証する。

## 2. テスト環境・前提

- `pytest` と Flask `test_client` を使用する。
- テスト用PostgreSQLデータベースを使用し、既存の `tests/conftest.py` の `app`、`client`、`seed` fixtureを利用する。
- `seed` fixtureは、`id=1`、`client_name="Test Client"` の `Client` レコードを用意する前提。
- `models.session` はSQLAlchemyの `scoped_session`。テストでは `session.rollback()`、`session.remove()` を利用する。
- `app.config["TESTING"]` が有効な場合、例外伝播を抑えるテストでは `PROPAGATE_EXCEPTIONS=False` を設定する。
- `app.py` では `@app.teardown_appcontext` によりアプリケーションコンテキスト終了時に `session.remove()` を実行する。
- `app.py` の重複したimport・engine/Base定義等は見直し済み（ユーザー報告）。最終的なengine設定は実コードを正として確認する。

## 3. 対象となるエラーハンドリング

`error/views.py` は `/error/` にGET/POSTルートを提供し、両メソッドで「データベースエラーが発生しました。」というメッセージを含むHTMLをHTTP 500で返す。

また、次のハンドラがアプリケーション全体に登録されている。

```python
@error.app_errorhandler(SQLAlchemyError)
def handle_database_error(e):
    try:
        session.rollback()
    except Exception:
        current_app.logger.exception("Database rollback failed")

    current_app.logger.error(
        "Database Error",
        exc_info=(type(e), e, e.__traceback__)
    )

    return render_template(
        "error/index.html",
        error_message="データベースエラーが発生しました。"
    ), 500
```

**注意:** `/error/` への直接アクセスと、`SQLAlchemyError` 発生時の例外ハンドラ実行は別の経路。前者のテストだけでは後者の動作は保証できない。

## 4. テストケース一覧

| ID | テスト関数 | テスト対象 | 主な期待結果 | 結果 |
|---|---|---|---|---|
| ERR-INT-001 | `test_error_page_get` | `/error/` GET | HTTP 500、レスポンス本文あり | PASS |
| ERR-INT-002 | `test_error_page_post` | `/error/` POST | HTTP 500、レスポンス本文あり | PASS |
| ERR-INT-003 | `test_error_page_status` | HTMLレスポンス | HTTP 500、MIMEタイプ `text/html` | PASS |
| ERR-INT-004 | `test_integrity_error_rollback` | 主キー重複 | `IntegrityError` 発生、rollback後も既存Clientが維持される | PASS |
| ERR-INT-005 | `test_session_recovery_after_error` | Session復旧 | rollback後に新規Clientを正常に登録・取得できる | PASS |
| ERR-INT-006 | `test_transaction_atomicity` | トランザクション原子性 | 重複エラー時に同一トランザクション内の正常INSERTも取り消される | PASS |
| ERR-INT-007 | `test_error_handler_rollback` | Flask経由のDB例外 | テスト用ルートでのDB例外後、HTTP 500となりDB参照可能 | PASS |
| ERR-INT-008 | `test_error_page_after_db_failure` | DBエラー後の画面 | rollback後に `/error/` がHTTP 500を返し、DB参照可能 | PASS |
| ERR-INT-009 | `test_sqlalchemy_error_handler` | 独自例外ハンドラ | 実DBの `IntegrityError` を捕捉し、独自メッセージ付きHTTP 500を返す | PASS |
| ERR-INT-010 | `test_sqlalchemy_error_handler_rollback` | 独自ハンドラ内rollback | 実際のrollback処理を維持しつつ、`session.rollback()` が1回呼ばれる | PASS |

## 5. ケース別の確認ポイント

### ERR-INT-001〜003：エラーページ表示

`client.get('/error/')`、`client.post('/error/')` を実行し、500ステータス、本文の存在、HTMLのMIMEタイプを確認する。HTTP 500は本アプリの明示的な画面仕様であり、テスト失敗を意味しない。

### ERR-INT-004：主キー重複とrollback

既存の `Client(id=1)` と同じ主キーのClientを登録して `session.commit()` を行い、`IntegrityError` を期待する。その後 `session.rollback()` と `session.remove()` を行い、元のClient名が変わっていないことを確認する。

### ERR-INT-005：エラー後のSession復旧

主キー重複による `IntegrityError` の後、rollbackを行って別のClientを追加・commitする。新しいSessionから登録結果を確認し、DB操作が再開できることを検証する。

### ERR-INT-006：トランザクションの原子性

正常なClientと主キーが重複するClientを同一トランザクションで登録し、commit失敗後にrollbackする。Client総数が変化せず、正常な方のClientも残っていないことを確認する。

このテストは**通常のトランザクション動作**を前提とする。使用中のテスト用engineがDBAPIレベルの `AUTOCOMMIT` でないことを確認する。

### ERR-INT-007：Flask経由のDB例外

テスト専用POSTルートで重複INSERTを発生させ、FlaskがHTTP 500を返し、リクエスト終了後もDBを参照できることを確認する。**このケース単体では独自ハンドラ内のrollback実行を直接証明しない。**

### ERR-INT-008：DBエラー後の画面表示

直接発生させたDB例外をrollbackした後、`/error/` にGETアクセスしてHTTP 500のHTML応答を確認する。既存Clientが参照可能であることも確認する。

### ERR-INT-009：独自SQLAlchemyErrorハンドラ

テスト専用POSTルートで実DBの `IntegrityError` を発生させる。`@error.app_errorhandler(SQLAlchemyError)` の応答としてHTTP 500と「データベースエラーが発生しました。」を確認し、既存Clientの内容が保持されていることを検証する。

### ERR-INT-010：独自ハンドラによるrollback

`patch.object(session, 'rollback', wraps=session.rollback)` を使い、実際のrollbackを実行しながら呼び出しを監視する。テスト専用POSTルートでDB例外を発生させ、HTTP 500と `rollback()` の呼び出し1回を確認する。

## 6. 実行コマンド

全ケースを実行：

```bash
python -m pytest tests/integration/test_error_integration.py -v
```

独自ハンドラの2ケースのみ実行：

```bash
python -m pytest tests/integration/test_error_integration.py \
    -k "test_sqlalchemy_error_handler" -v
```

特定ケースを実行：

```bash
python -m pytest \
    tests/integration/test_error_integration.py::test_transaction_atomicity -v
```

## 7. テスト設計上の注意

1. **本番DBでは実行しない。** 主キー重複を意図的に発生させるため、隔離されたテスト用DB・スキーマを使用する。
2. **Flask `TESTING` と例外伝播:** テスト用ルートから500応答を確認するケースでは、必要に応じて `PROPAGATE_EXCEPTIONS=False` を設定する。fixtureのスコープによっては設定値をテスト後に復元する。
3. **`session.remove()` とrollbackは役割が異なる。** `rollback()` は失敗トランザクションの解消、`remove()` はscoped_sessionのSession破棄に使用する。
4. **DBエラーとHTTP 500を区別する。** `/error/` の直接表示だけでは、SQLAlchemy例外ハンドラの動作を検証できない。ERR-INT-009/010で補完する。
5. **テスト用ルートの登録時期:** Flaskでは最初のリクエスト処理後にルートを追加できない。各テストは新しい `app` fixtureでルートを登録する構成を前提とする。
6. **AUTOCOMMIT:** `Session.rollback()` の存在だけでDBの原子性は保証されない。テスト用engineのトランザクション設定を確認する。
7. **エラーのログ出力:** `handle_database_error()` は例外情報を `current_app.logger.error()` で記録する。ログ本文・例外情報のアサーションは今回の10ケースには含まれない。

## 8. 今後の拡張候補

- `caplog` を使い、DBエラーのログ出力と例外情報の記録を確認する。
- rollback自体が失敗した場合に、`Database rollback failed` が記録され、エラーページの返却処理が継続されることを単体テストで検証する。
- 認証必須の業務ルートで実際にDB例外を発生させ、画面・DB状態・ログをまとめて検証する。
- 例外ハンドラに依存するケースと、SQLAlchemy/PostgreSQLのトランザクション動作を検証するケースを分類し、テスト重複を整理する。

## 9. 実施結果まとめ

**全10ケースPASS（2026-11-10、ユーザー報告）。** エラーページのGET/POST、DB制約違反、rollback後のSession復旧、トランザクションの原子性、Flask経由の500応答、独自 `SQLAlchemyError` ハンドラの応答、およびハンドラによるrollback呼び出しを確認した。

この文書は会話で共有されたテストコードと実行結果を基に整理した仕様書であり、現在のリポジトリ内のファイルを直接照合した監査結果ではない。
