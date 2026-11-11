# `test_client_e2e.py` テスト仕様書

## 1. 概要

| 項目 | 内容 |
| --- | --- |
| 対象ファイル | `tests/e2e/test_client_e2e.py` |
| テスト種別 | E2E（ブラウザ操作＋PostgreSQLへの保存確認） |
| テストツール | pytest、Playwright（Chromium）、SQLAlchemy |
| 対象機能 | 管理画面でのクライアント登録、入力なしの送信、アクセス制御 |
| 対象URL | `/admin/`、`/top/`、`/login/` |
| テストケース数 | 5 |
| 実行結果 | **5ケースすべてPASS**（ユーザーによる実行結果） |

## 2. テストの目的

Flaskアプリケーションの管理画面について、ブラウザからの操作、HTTPリダイレクト、PostgreSQLへのレコード保存が一連の処理として正常に動作することを確認する。

主な検証対象は以下のとおり。

- 認証済みユーザーが管理画面を表示できること
- クライアント名を入力して登録すると、`clients` テーブルに新規レコードが保存されること
- 登録成功後に `/top/` へ遷移すること
- 何も入力せず送信した場合、登録せず `/admin/` に戻ること
- 未認証ユーザーは管理画面にアクセスできないこと

## 3. 対象実装と前提条件

### 3.1 Flaskルート

`admin/views.py` の `admin.index` を対象とする。Blueprintは `/admin/` に登録されている前提。

- `GET /admin/`：管理画面 `admin/index.html` を表示する
- `POST /admin/`：フォームの `client` に値があれば `Client(client_name=client)` を追加し、`session.commit()` 後に `top.index` へリダイレクトする
- 全入力が空の場合：`flash('何も入力されていません')` を実行し、`admin.index` にリダイレクトする
- `@login_required`：未ログインユーザーをログイン画面に誘導する

### 3.2 HTML要素

`admin/templates/admin/index.html` の次の要素を操作する。

| 用途 | セレクター |
| --- | --- |
| クライアント名入力 | `#client`（`input[name="client"]`） |
| 登録ボタン | `form.record input[type='submit']` |

管理画面は代理店・担当者・ツール・プロジェクト終了操作と共通のフォームを使う。クライアント登録テストでは `#client` のみ入力し、その他は空欄のまま送信する。

### 3.3 テスト環境

- `tests/e2e/conftest.py` の共通fixtureを使用する。
- `.env.test` の `DATABASE_URL`、`TEST_USERNAME`、`TEST_PASSWORD` を使用する。
- 専用Flaskサーバーを `http://127.0.0.1:5011` で起動する構成。
- DB名が `invoicee_test` であることを検証する。
- E2E開始時にテーブルと認証用ユーザーが準備されていること。
- `tests/conftest.py` に結合テスト用のautouse fixtureがある場合は、E2Eへの影響がないことを確認する。

## 4. テストケース一覧

| ID | pytest関数 | 操作・条件 | 期待結果 | 結果 |
| --- | --- | --- | --- | --- |
| CLIENT-E2E-001 | `test_client_page_display` | ログイン済みで `/admin/` にアクセス | URLが `/admin/`、クライアント入力欄と登録ボタンが表示される | PASS |
| CLIENT-E2E-002 | `test_client_registration` | 一意のクライアント名を入力して送信 | `/top/` に遷移し、DBに該当名の `Client` レコードが作成され、IDが設定される | PASS |
| CLIENT-E2E-003 | `test_client_registration_redirect` | クライアントを登録 | 登録後のURLが `/top/` になる | PASS |
| CLIENT-E2E-004 | `test_client_empty_submission` | 全入力欄を空欄のまま送信 | `/admin/` に戻り、`clients` の件数が増えない | PASS |
| CLIENT-E2E-005 | `test_client_page_requires_login` | 未ログインで `/admin/` にアクセス | `/login/`（クエリ文字列を含む場合あり）へリダイレクトされる | PASS |

## 5. ケース別詳細

### CLIENT-E2E-001：管理画面の表示

**前提**：`auth_page` fixtureによりログイン済み。

**操作**：`/admin/` にアクセスする。

**検証**：URLが `/admin/` であること、`#client` と `form.record input[type='submit']` が表示されること。

### CLIENT-E2E-002：クライアントの新規登録

**前提**：ログイン済み。`client_name` fixtureが `E2E_Client_` で始まる一意の名前を生成する。

**操作**：`/admin/` を開き、`#client` に名前を入力し、登録ボタンをクリックする。

**検証**：`/top/` への遷移後、SQLAlchemyで `Client.client_name` を条件に検索し、レコードが存在すること、名前が一致すること、`id` が `None` ではないこと。

**後処理**：`cleanup_client` fixtureが当該クライアント名のレコードを削除する。

### CLIENT-E2E-003：登録後のリダイレクト

**前提**：ログイン済み。一意のクライアント名を生成する。

**操作**：クライアント登録フォームを送信する。

**検証**：URLが `/top/` になること。

**後処理**：`cleanup_client` fixtureが登録データを削除する。

### CLIENT-E2E-004：未入力時のエラー処理

**前提**：ログイン済み。送信前にDBのクライアント件数を取得する。

**操作**：管理画面で何も入力せずに登録ボタンをクリックする。

**検証**：URLが `/admin/` に戻り、送信前後で `clients` テーブルの件数が変化しないこと。

**補足**：現行テストでは `flash()` の文言そのものは検証していない。`top/base.html` などのflash表示仕様を確認したうえで追加可能。

### CLIENT-E2E-005：未ログイン時のアクセス制限

**前提**：新しい未認証の `page` fixtureを使用する。

**操作**：`/admin/` にアクセスする。

**検証**：URLが `/login/` またはクエリ文字列付きの `/login/` になること。

## 6. 共通fixtureとヘルパー

| 名前 | 役割 |
| --- | --- |
| `e2e_config` | `.env.test` を読み込み、接続先などを検証する（`tests/e2e/conftest.py`） |
| `init_test_database` | テストテーブルとログイン用ユーザーを準備する（同上） |
| `e2e_server` | Flaskサーバーを起動し、テスト終了時に停止する（同上） |
| `auth_page` | ログイン済みのPlaywrightページを提供する（同上） |
| `client_name` | テストケースごとにUUIDを使った一意の顧客名を作る |
| `client_db` | `.env.test` のPostgreSQLに接続し、終了時にエンジンを破棄する |
| `cleanup_client` | テストで作成した顧客データのみ削除する |
| `register_client()` | 管理画面の表示、顧客名入力、登録ボタンクリックを共通化する |
| `get_client()` | DBから指定顧客名のレコードを取得する |
| `count_clients()` | `clients` テーブルの件数を取得する |

`cleanup_client` は `yield` 後の後処理で削除するため、通常のアサーション失敗時にもクリーンアップされる。ただし、プロセス強制終了などでは実行されない可能性がある。

## 7. 実行方法

認証済みユーザーの準備やテストDB初期化は共通fixtureが担当するため、通常は別途 `test_init_db.py` を実行する必要はない。

```bash
# 顧客管理E2Eテストのみ
python -m pytest tests/e2e/test_client_e2e.py -v

# ブラウザを表示
python -m pytest tests/e2e/test_client_e2e.py -v --headed

# E2Eテスト全体
python -m pytest tests/e2e/ -v
```

## 8. 安全性と運用上の注意

1. **DB分離**：`DATABASE_URL` はE2E専用DBを指すこと。DB名チェックに加え、本番DBへの権限を持たない専用DBユーザーを使うことが望ましい。
2. **データの独立性**：UUIDを含む顧客名でテスト間の衝突を避ける。
3. **後処理**：登録テストでは `cleanup_client` を指定し、作成した顧客だけを削除する。ほかのテーブルから外部キー参照される場合は削除順序に注意する。
4. **件数比較の前提**：空欄送信テストは、同時に別プロセスが `clients` を変更しないことを前提とする。
5. **URLとサーバー**：ポート5011に既存サーバーがいる場合は、意図しないプロセスへ接続しないよう注意する。
6. **既存テーブル**：`Base.metadata.create_all()` は既存テーブルのスキーマ変更を反映しない。スキーマ変更時は適切なマイグレーションを行う。

## 9. 現在の検証範囲と今後の候補

**今回検証済み**：管理画面表示、顧客新規登録とDB永続化、登録後の遷移、未入力送信時の非登録、未ログイン時のアクセス制限。

**未検証**：重複顧客名の扱い、文字数・特殊文字などの入力境界、flashメッセージの表示文言、顧客の更新・削除、同時登録、DB障害時のエラー表示。

また、管理画面の代理店・担当者・ツール・プロジェクト終了処理は別のE2Eテストとして追加する。

---

*この仕様書は、共有された `admin/views.py`・`admin/templates/admin/index.html`・`test_client_e2e.py` の内容と、5ケースすべてPASSしたという実行結果に基づく。*
