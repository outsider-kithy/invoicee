# 担当者登録 E2Eテスト仕様書

- **対象ファイル**：`tests/e2e/test_account_e2e.py`
- **対象機能**：管理画面での担当者（Account）登録、および代理店（Agency）との関連付け
- **テスト環境**：Flask / PostgreSQL / pytest / Playwright（Chromium）
- **実行結果**：全7ケース PASS（ユーザー確認済み）

## 1. 目的

実際のブラウザから管理画面（`/admin/`）を操作し、担当者登録フォームの表示、担当者のDB保存、代理店への外部キー紐づけ、登録後の画面遷移、異常入力時の挙動、およびログイン必須制御を検証する。

## 2. 対象の実装仕様

`admin/templates/admin/index.html` には `form.record` 内に担当者名入力欄 `#account`、代理店選択欄 `#agencyName`、送信ボタン `input[type='submit']` がある。代理店の選択肢はDBの `Agency` レコードから生成される。

`admin/views.py` の `/admin/` ルートは `@login_required` で保護されている。POSTで `account` が指定された場合、送信された `agencyName` に一致する代理店を検索し、見つかれば `Account(account_name=account, agency_id=accountAgency.id)` を保存して `/top/` にリダイレクトする。代理店が見つからなければ `flash("指定された代理店が存在しません")` を設定して `/admin/` に戻る。全項目が空の場合も `flash("何も入力されていません")` を設定して `/admin/` に戻る。

## 3. テストケース一覧

| ID | テスト関数 | 確認内容 | 期待結果 | 結果 |
|---|---|---|---|---|
| ACCOUNT-E2E-001 | `test_account_page_display` | 管理画面を開く | `#account`、`#agencyName`、送信ボタンが表示される | PASS |
| ACCOUNT-E2E-002 | `test_account_registration` | 代理店を選択して担当者を登録 | `accounts` に担当者が保存され、IDと名前を確認できる | PASS |
| ACCOUNT-E2E-003 | `test_account_agency_relationship` | 登録した担当者の関連付けを確認 | `Account.agency_id` がテスト用代理店のIDと一致する | PASS |
| ACCOUNT-E2E-004 | `test_account_registration_redirect` | 正常登録後の遷移 | `/top/` に遷移する | PASS |
| ACCOUNT-E2E-005 | `test_account_without_agency` | 代理店を未選択で担当者名を送信 | `/admin/` に戻り、担当者が登録されない | PASS |
| ACCOUNT-E2E-006 | `test_account_empty_submission` | 全項目未入力で送信 | `/admin/` に戻り、担当者件数が増えない | PASS |
| ACCOUNT-E2E-007 | `test_account_page_requires_login` | 未ログインで管理画面にアクセス | `/login/` にリダイレクトされる | PASS |

## 4. 各ケースの手順と判定基準

### ACCOUNT-E2E-001：担当者登録フォームの表示

1. `auth_page` でログインした状態から `/admin/` を開く。
2. URLが `/admin/` であることを確認する。
3. 担当者名入力欄 `#account`、代理店選択欄 `#agencyName`、登録ボタンの可視性を確認する。

**判定**：すべての要素が表示される。

### ACCOUNT-E2E-002：担当者の新規登録

1. テスト専用代理店をDBに作成する。
2. 一意の担当者名を生成する。
3. `/admin/` の `#account` に担当者名を入力し、`#agencyName` で代理店を選択して送信する。
4. `/top/` への遷移を確認する。
5. テストDBの `Account` を検索し、名前とIDを確認する。

**判定**：登録された担当者が存在し、名前が一致し、IDが設定されている。

### ACCOUNT-E2E-003：代理店との紐づけ

1. テスト専用代理店を作成する。
2. 管理画面からその代理店を指定して担当者を登録する。
3. DBから登録した担当者を取得する。
4. `Account.agency_id` とテスト用代理店IDを比較する。

**判定**：両IDが一致する。

### ACCOUNT-E2E-004：登録後のリダイレクト

1. テスト専用代理店を作成する。
2. 代理店を選択して担当者を登録する。
3. 登録後のブラウザURLを確認する。

**判定**：`/top/` に遷移する。

### ACCOUNT-E2E-005：代理店未選択時のエラー

1. 担当者レコード数を取得する。
2. 担当者名だけを入力し、代理店を選択せず送信する。
3. 遷移先URLと送信後の担当者件数を確認する。
4. 入力した担当者名のレコードが存在しないことを確認する。

**判定**：`/admin/` に戻り、件数は変わらず、該当担当者が存在しない。

### ACCOUNT-E2E-006：全項目未入力での送信

1. 担当者レコード数を取得する。
2. `/admin/` のフォームを空のまま送信する。
3. 遷移先URLと担当者件数を確認する。

**判定**：`/admin/` に戻り、件数が増えない。

### ACCOUNT-E2E-007：未ログイン時のアクセス制限

1. 未認証の `page` fixtureで `/admin/` にアクセスする。
2. 遷移先URLを確認する。

**判定**：`/login/` にリダイレクトされる（クエリパラメータの有無は許容）。

## 5. fixtureと共通関数

| 名称 | 役割 |
|---|---|
| `e2e_config` | `.env.test` からテスト用設定を読み込む（`tests/e2e/conftest.py`） |
| `init_test_database` | テーブル・テストユーザーを準備する（同上） |
| `e2e_server` | FlaskのE2E用サーバーを起動・終了する（同上） |
| `auth_page` | ログイン済みPlaywrightページを提供する（同上） |
| `account_name` | テストごとに一意の担当者名を生成する |
| `account_db` | `.env.test` のPostgreSQLへ接続し、DB名 `invoicee_test` を確認する |
| `test_agency` | テスト専用代理店を作成し、終了時に関連担当者・代理店を削除する |
| `cleanup_account` | テストで作成した担当者を名前で削除する |
| `register_account` | 管理画面から担当者名と代理店を入力・送信する |
| `get_account` | DBから担当者を取得する |
| `count_accounts` | DB内の担当者件数を取得する |

## 6. テストデータの管理

- 担当者名は `E2E_Account_` にランダム文字列を付けて生成する。
- 代理店名も `E2E_Agency_` にランダム文字列を付けて生成する。
- 正常系では専用代理店を先に作成し、担当者をその代理店に紐づける。
- テスト終了後は外部キー制約を考慮し、**担当者を削除してから代理店を削除**する。
- `account_db` はDB名が `invoicee_test` であることを検査する。より安全に運用するには、テスト専用のDBユーザーと接続先の厳格な管理も必要。

## 7. 実行方法

担当者E2Eテストのみ：

```bash
python -m pytest tests/e2e/test_account_e2e.py -v
```

ブラウザ表示あり：

```bash
python -m pytest tests/e2e/test_account_e2e.py -v --headed
```

E2Eテスト全体：

```bash
python -m pytest tests/e2e/ -v
```

## 8. 現在の検証範囲と今後の課題

- 今回の異常系では、画面遷移とDBへの未登録を検証している。`flash()` の具体的な文言が画面に表示されるかは、共通テンプレートの実装に応じて別途追加できる。
- 存在しない代理店名を直接送信するケース、代理店を切り替えて登録するケース、重複担当者名の扱いなどは今後の追加候補。
- テスト用代理店の削除時に、その代理店に紐づく担当者をまとめて削除する実装であるため、他テストとデータを共有しない運用を前提とする。

---

**実行状況**：ACCOUNT-E2E-001〜007、全7ケース PASS（ユーザー報告）。
