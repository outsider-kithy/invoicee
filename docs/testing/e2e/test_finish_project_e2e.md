# プロジェクト終了処理 E2Eテスト仕様書

- **対象ファイル**: `tests/e2e/test_finish_project_e2e.py`
- **テスト基盤**: pytest / Playwright (Chromium) / Flask / SQLAlchemy / PostgreSQL
- **対象画面**: `/admin/`
- **対象処理**: `admin/views.py` の `finished_project` 分岐
- **実行結果**: 全8ケース **PASS**（ユーザー確認済み）

## 1. 目的と対象範囲

管理画面から未終了プロジェクトを選択して登録すると、`projects.isfinished` が `0` から `1` に更新されることを、ブラウザ操作とテストDBの両面から確認する。終了済みプロジェクトの画面上での非表示、他プロジェクトへの非干渉、異常入力時の挙動、未ログイン時のアクセス制御も対象とする。

本テストはプロジェクトの新規登録機能や、`Job` の作成・編集を対象としない。

## 2. アプリケーション仕様

### 2.1 Projectモデル

```python
class Project(Base):
    __tablename__ = 'projects'
    id = Column(Integer, primary_key=True, autoincrement=True)
    created = Column(Date, index=True, default=datetime.date.today())
    project_name = Column(String)
    client_id = Column(Integer, ForeignKey('clients.id'))
    agency_id = Column(Integer, ForeignKey('agencys.id'))
    account_id = Column(Integer, ForeignKey('accounts.id'))
    isfinished = Column(Integer)

    client = relationship('Client')
    agency = relationship('Agency')
    account = relationship('Account')
    job = relationship('Job', back_populates='project')
```

`isfinished = 0` を未終了、`isfinished = 1` を終了として扱う。`client_id`・`agency_id`・`account_id` は関連テーブルへの外部キーである。これらの列にはモデル上 `nullable=False` が指定されていないが、テストでは実データに近い状態を作るため、関連レコードを準備する。

### 2.2 管理画面での表示

GET `/admin/` では、次の条件で終了対象を取得する。

```python
projects = session.query(Project).filter(Project.isfinished == 0).all()
```

画面にはプロジェクト名を値とするラジオボタンが表示される。

```html
{% for project in projects %}
<div class="radio_box">
  <input type="radio" name="finished_project" value="{{ project['project_name'] }}">
  {{ project['project_name'] }}
</div>
{% endfor %}
```

### 2.3 終了処理

POST `/admin/` で `finished_project` が指定され、先行する `client`・`agency`・`account`・`tool` の入力がない場合、指定名のProjectを検索して `isfinished = 1` に変更し、コミット後 `/top/` にリダイレクトする。該当プロジェクトがない場合はフラッシュメッセージを設定して `/admin/` にリダイレクトする。全項目未入力でも `/admin/` にリダイレクトする。

**注意**: 検索条件は `project_name` であり、同名プロジェクトが複数存在する場合の対象特定は保証されない。テストではUUID由来の一意な名称を使用する。

## 3. テストケース一覧

| ID | テスト関数 | 確認内容 | 期待結果 | 結果 |
|---|---|---|---|---|
| FINISH-E2E-001 | `test_finish_project_page_display` | 終了対象の表示 | 未終了プロジェクトのラジオボタンが表示される | PASS |
| FINISH-E2E-002 | `test_finish_project_success` | 終了状態の更新 | `isfinished` が `0 → 1` | PASS |
| FINISH-E2E-003 | `test_finish_project_redirect` | 正常終了後の遷移 | `/top/` に遷移 | PASS |
| FINISH-E2E-004 | `test_finished_project_not_displayed` | 終了済み項目の非表示 | 管理画面再表示後、選択肢に存在しない | PASS |
| FINISH-E2E-005 | `test_finish_only_selected_project` | 他レコードへの影響 | 選択したAのみ終了し、Bは未終了 | PASS |
| FINISH-E2E-006 | `test_finish_project_empty_submission` | 未選択で送信 | `/admin/` に戻り、状態は `0` のまま | PASS |
| FINISH-E2E-007 | `test_finish_nonexistent_project` | 存在しない名前をPOST | 302で `/admin/` に戻り、既存Projectは変更されない | PASS |
| FINISH-E2E-008 | `test_finish_project_requires_login` | 未認証アクセス | `/login/` にリダイレクト | PASS |

## 4. テストケース詳細

### FINISH-E2E-001: 管理画面の表示

**前提**: ログイン済み。テスト用の未終了Projectが存在する。

**操作**: `/admin/` にアクセスする。

**検証**: URLが `/admin/` であり、対象Project名を `value` とする `input[name="finished_project"]` が表示される。

### FINISH-E2E-002: プロジェクト終了処理

**前提**: テストProjectの `isfinished == 0`。

**操作**: 管理画面で対象Projectのラジオボタンを選択して送信する。

**検証**: `/top/` に遷移し、DBの対象Projectの `isfinished == 1`。

### FINISH-E2E-003: 終了後のリダイレクト

**前提**: 未終了Projectが存在する。

**操作**: 対象Projectを選択して送信する。

**検証**: ブラウザのURLが `/top/` になる。

### FINISH-E2E-004: 終了済みプロジェクトの非表示

**前提**: 未終了Projectが存在する。

**操作**: 終了処理を行った後、`/admin/` を再表示する。

**検証**: 対象Project名を持つラジオボタンの件数が `0`。

### FINISH-E2E-005: 複数プロジェクトの独立性

**前提**: 未終了のProject A・Bを作成する。

**操作**: Aだけを終了する。

**検証**: DB上でAの `isfinished == 1`、Bの `isfinished == 0`。

### FINISH-E2E-006: プロジェクト未選択

**前提**: 未終了Projectが存在する。

**操作**: 管理画面の入力項目を空のまま送信する。

**検証**: `/admin/` に戻り、対象Projectの `isfinished == 0` が維持される。

### FINISH-E2E-007: 存在しないプロジェクト名

**前提**: ログイン済み。テストProjectが存在する。

**操作**: PlaywrightのAPIリクエストで、存在しないUUID付きの名前を `finished_project` としてPOSTする（`max_redirects=0`）。

**検証**: HTTP 302、`Location` が `/admin/` を指し、既存Projectの `isfinished == 0`。

**補足**: これはブラウザ上のラジオボタン選択ではなく、ログインCookieを共有するAPIリクエストによる異常系の検証。

### FINISH-E2E-008: 未ログインアクセス

**前提**: 未ログインの新しいPage。

**操作**: `/admin/` にアクセスする。

**検証**: `/login/` にリダイレクトされる。

## 5. fixtureと共通関数

| 名称 | 役割 |
|---|---|
| `e2e_config` | `.env.test` からテストDB接続情報・認証情報を取得（共通fixture） |
| `e2e_server` | Flaskテストサーバーを起動（共通fixture） |
| `auth_page` | ログイン済みPlaywright Pageを提供（共通fixture） |
| `project_db` | `invoicee_test` のみ接続を許可するSQLAlchemy Engine |
| `project_name` | UUIDを使った一意のプロジェクト名 |
| `project_dependencies` | テスト用Client・Agency・Accountを作成・後処理 |
| `test_project` | 未終了Projectを1件作成・後処理 |
| `two_test_projects` | 独立性検証用のProjectを2件作成・後処理 |
| `create_test_project()` | 外部キーを指定してProjectをDBに作成 |
| `finish_project()` | 管理画面でラジオボタンを選択しフォーム送信 |
| `get_project()` | IDからProjectを取得 |
| `get_project_status()` | Projectの `isfinished` を取得 |
| `submit_empty_form()` | 未入力で管理フォームを送信 |

### 5.1 関連データの生成順

1. `Client` と `Agency` を作成して `flush()` し、IDを取得する。
2. `Account(agency_id=agency.id)` を作成する。
3. `Project(client_id=..., agency_id=..., account_id=..., isfinished=0)` を作成する。

### 5.2 クリーンアップ順

1. `test_project` または `two_test_projects` が作成したProjectを削除する。
2. `project_dependencies` が作成したAccountを削除する。
3. Agencyを削除する。
4. Clientを削除する。

fixtureの依存関係により、Projectの削除が関連レコードの削除より先に行われる。テストが失敗した場合も `yield` 後の終了処理が実行される構成とする。関連するJobなどが別途生成された場合は、外部キー制約に応じて削除順を見直す。

## 6. セレクター・アサーション

```python
# 終了対象のラジオボタン
page.locator(
    'input[name="finished_project"]'
    f'[value="{project_name}"]'
).check()

# 登録ボタン
page.locator("form.record input[type='submit']").click()

# 正常終了後のURL
expect(page).to_have_url(f"{e2e_server}/top/")

# 終了状態のDB確認
assert get_project_status(project_db, project_id) == 1
```

`finish_project()` では不要な `.filter(has=None)` 等を使わず、上記の属性セレクターで直接対象を選択する。

## 7. 実行方法

```bash
# プロジェクト終了テストのみ
python -m pytest tests/e2e/test_finish_project_e2e.py -v

# ブラウザを表示して実行
python -m pytest tests/e2e/test_finish_project_e2e.py -v --headed

# E2Eテスト全体
python -m pytest tests/e2e/ -v
```

**実行結果**: `test_finish_project_e2e.py` の全8ケースがPASS（ユーザー報告）。実行ログ・実行日時・所要時間は本書に添付していない。

## 8. 安全対策・制約

- `.env.test` の接続先はテスト専用DB `invoicee_test` とし、`project_db` fixtureでDB名を検証する。
- 生成データにはUUID付きの名前を使用し、既存レコードと衝突しにくくする。
- 削除は生成したIDに限定し、既存の業務データを削除しない。
- `Project.created` の `default=datetime.date.today()` はモデル定義時に評価されるため、日付の自動設定を厳密に必要とする場合は `default=datetime.date.today` への変更を別途検討する。
- `FINISH-E2E-007` はログイン済みのAPIリクエストを前提とする。CSRF対策が導入されている場合はトークン対応が必要になる。
- `Project` を参照する `Job` などが作成されるテストに拡張する際は、関連レコードを先に削除する。

## 9. 今後の追加候補

- 同名プロジェクトが複数存在する場合の挙動と、IDベースの選択への改善。
- 終了済みプロジェクトを再度POSTした場合の挙動。
- `client` 等の別入力項目と `finished_project` が同時送信された場合の優先順位。
- 例外発生時のロールバックとエラー画面への遷移。
- `isfinished` の値が `NULL` または想定外の値の場合の表示条件。

---

本書は、共有されたFlask実装・モデル定義・提案したテスト構成、および全8ケースPASSの報告に基づいて作成した。
