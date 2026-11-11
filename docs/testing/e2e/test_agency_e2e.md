# 代理店管理 E2E テスト仕様書

- **対象ファイル**：`tests/e2e/test_agency_e2e.py`
- **関連ファイル**：`tests/e2e/conftest.py`、`admin/views.py`、`admin/templates/admin/index.html`
- **テスト基盤**：pytest、pytest-playwright（Chromium）、Flask、SQLAlchemy、PostgreSQL
- **実行結果**：全6ケース PASS（ユーザー確認）

## 1. 目的

管理画面 `/admin/` における代理店登録について、ブラウザからのフォーム操作、PostgreSQLへの保存、登録後の遷移、未入力時の処理、認証制御、および登録済み代理店の選択肢への反映を検証する。

## 2. テスト対象の仕様

`admin/index.html` の代理店入力欄は `input#agency[name="agency"]`。送信ボタンは `form.record input[type="submit"]`。代理店選択欄は `select#agencyName` で、`agencys` の各レコードを `<option value="代理店名">代理店名</option>` として表示する。

`admin/views.py` の `/admin/` は `@login_required` で保護される。POSTで `client` が空、`agency` に値がある場合は `Agency(agency_name=agency)` を追加して `session.commit()` し、`top.index`（`/top/`）へリダイレクトする。全対象項目が未入力の場合は `flash('何も入力されていません')` の後、`admin.index`（`/admin/`）へリダイレクトする。

> 管理画面はクライアント・代理店・担当者・ツール・プロジェクト終了を同一フォームで処理する。代理店登録のテストでは `#agency` のみ入力する。

## 3. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 | 結果 |
|---|---|---|---|---|
| AGENCY-E2E-001 | `test_agency_page_display` | 管理画面の表示 | `/admin/` に遷移し、`#agency` と送信ボタンが表示される | PASS |
| AGENCY-E2E-002 | `test_agency_registration` | 代理店の新規登録 | 登録後 `/top/` に遷移し、DBに代理店名・IDを持つレコードが存在する | PASS |
| AGENCY-E2E-003 | `test_agency_registration_redirect` | 登録後の画面遷移 | `/top/` にリダイレクトされる | PASS |
| AGENCY-E2E-004 | `test_agency_empty_submission` | 全項目未入力で送信 | `/admin/` に戻り、代理店レコード数が増えない | PASS |
| AGENCY-E2E-005 | `test_agency_page_requires_login` | 未ログイン時のアクセス制限 | `/login/` にリダイレクトされる（クエリ文字列を許容） | PASS |
| AGENCY-E2E-006 | `test_agency_appears_in_select` | 登録済み代理店の選択肢への反映 | 再表示した `/admin/` の `#agencyName` に該当する `option` が1件ある | PASS |

## 4. ケース別手順と検証

### AGENCY-E2E-001：管理画面の表示

1. `auth_page` でログイン済みページを取得する。
2. `/admin/` を開く。
3. URLが `/admin/` であることを確認する。
4. `#agency` と `form.record input[type='submit']` が表示されることを確認する。

### AGENCY-E2E-002：代理店の新規登録

1. テストごとに一意の `E2E_Agency_...` 形式の代理店名を生成する。
2. `/admin/` を開き、`#agency` に代理店名を入力する。
3. 共通送信ボタンをクリックする。
4. `/top/` への遷移を確認する。
5. テストDBから `Agency.agency_name` を条件に検索する。
6. レコードが存在し、代理店名が一致し、`id` が設定されていることを確認する。
7. テスト終了後、作成した代理店レコードを削除する。

### AGENCY-E2E-003：登録後の画面遷移

1. 一意の代理店名を入力して送信する。
2. URLが `/top/` になることを確認する。
3. テスト終了後、作成した代理店レコードを削除する。

### AGENCY-E2E-004：未入力時のエラー

1. テストDBの代理店レコード数を取得する。
2. `/admin/` を開き、入力欄をすべて空のまま送信する。
3. URLが `/admin/` に戻ることを確認する。
4. 送信後の代理店レコード数が送信前と一致することを確認する。

**検証範囲**：現行テストはflashメッセージ本文の表示までは検証していない。

### AGENCY-E2E-005：未ログイン時のアクセス制限

1. 未認証の `page` で `/admin/` を開く。
2. URLが `/login/` にリダイレクトされることを確認する。リダイレクト先のクエリ文字列は許容する。

### AGENCY-E2E-006：登録済み代理店の選択肢への反映

1. 一意の代理店名を登録する。
2. `/top/` への遷移を確認する。
3. `/admin/` を再表示する。
4. `#agencyName option[value="代理店名"]` が1件存在することを確認する。
5. テスト終了後、作成した代理店レコードを削除する。

## 5. 共通fixture・補助関数

| 名称 | 役割 |
|---|---|
| `e2e_config` | `.env.test` からテストDB接続情報とテスト認証情報を取得する |
| `init_test_database` | テスト用テーブルとログインユーザーを準備する |
| `e2e_server` | Flaskテストサーバーを起動・終了する |
| `auth_page` | ログイン済みのPlaywrightページを提供する |
| `agency_name` | テストごとに一意の代理店名を生成する |
| `agency_db` | `.env.test` のDBに接続し、DB名 `invoicee_test` を確認する |
| `cleanup_agency` | テスト後に該当代理店名のレコードを削除する |
| `register_agency()` | 代理店入力欄への入力とフォーム送信を共通化する |
| `get_agency()` | DBから代理店レコードを取得する |
| `count_agencies()` | DBの代理店レコード数を取得する |

`e2e_config`・`init_test_database`・`e2e_server`・`auth_page` は `tests/e2e/conftest.py` から利用する。`agency_name` など代理店固有のfixtureと補助関数は `test_agency_e2e.py` 内に定義する。

## 6. テストデータと安全対策

- 接続先は `.env.test` の `DATABASE_URL` を使用し、テスト用DB名 `invoicee_test` を確認する。
- テスト用DBと通常環境の接続先が一致しないことを共通fixtureで確認する。
- テストデータは `E2E_Agency_` とランダム文字列を組み合わせ、既存データとの衝突を避ける。
- 代理店登録を伴うテストは、fixtureの後処理で対象代理店名のレコードのみ削除する。
- `Account` などの関連レコードが作成されるケースでは外部キー制約に注意し、関連データを適切な順序で削除する。
- DB名のチェックのみでは同名の別環境DBへの接続を完全には防げないため、専用のDB権限を使用することが望ましい。

## 7. 実行方法

代理店E2Eテストのみ：

```bash
python -m pytest tests/e2e/test_agency_e2e.py -v
```

ブラウザを表示して実行：

```bash
python -m pytest tests/e2e/test_agency_e2e.py -v --headed
```

E2Eテスト全体：

```bash
python -m pytest tests/e2e/ -v
```

## 8. 今後の追加候補

- 代理店名の重複登録時の動作（重複禁止仕様がある場合）。
- 空白のみの代理店名に対する入力検証。
- flashメッセージ本文の表示確認。
- 代理店に紐づく担当者（`Account`）の登録と外部キー整合性の検証。
- 複数の管理項目を同時入力した際の優先順位（`if client` → `elif agency`）の確認。

---

**記録**：`test_agency_e2e.py` の6ケースすべてがPASSしたことをユーザーが確認済み。
