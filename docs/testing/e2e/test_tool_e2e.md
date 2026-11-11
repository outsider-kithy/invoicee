# ツール登録 E2E テスト仕様書

- **対象ファイル**: `tests/e2e/test_tool_e2e.py`
- **対象機能**: 管理画面からのツール登録、価格保存、税率との関連付け、入力エラー、認証制御
- **テスト方式**: pytest + Playwright（Chromium）+ PostgreSQL
- **実行結果**: **8ケースすべてPASS**（ユーザー確認済み）
- **対象URL**: `/admin/`、登録成功時 `/top/`、未ログイン時 `/login/`

## 1. テストの目的

管理画面で入力したツール名・価格・税率が正しく処理され、`tools` テーブルに保存されることをブラウザ操作とDB照会の両面から検証する。税率未選択や空送信の異常系、および未認証ユーザーへのアクセス制限も確認する。

## 2. 対象仕様

### 2.1 DBモデル

```python
class Tool(Base):
    __tablename__ = 'tools'
    id = Column(Integer, primary_key=True, autoincrement=True)
    tool_type = Column(String)
    price = Column(Integer)
    tax_rate_id = Column(Integer, ForeignKey('taxes.id'))
    job = relationship('Job', back_populates='tool_type')
    tax_rate = relationship('Tax')

class Tax(Base):
    __tablename__ = 'taxes'
    id = Column(Integer, primary_key=True, autoincrement=True)
    rate = Column(Numeric(precision=4, scale=2))
```

`Tool.tax_rate_id` は `Tax.id` を参照する。価格は整数、税率は小数点以下2桁の `Numeric` 型。

### 2.2 画面と登録処理

管理画面のフォームは、`#tool`（ツール名）、`#price`（価格）、`select[name="tax"]`（税率）と `form.record input[type="submit"]`（登録ボタン）を使用する。

`admin/views.py` のツール登録分岐は、入力された税率に対応する `Tax` レコードを取得し、見つかれば `Tool(tool_type=..., price=..., tax_rate_id=...)` を保存して `/top/` にリダイレクトする。見つからない場合はフラッシュメッセージを設定して `/admin/` に戻る。

**不具合修正**: 当初、`request.form.get('tax')` の文字列をそのまま `Tax.rate` と比較していたため、正常系4ケースで `/top/` ではなく `/admin/` に戻っていた。税率を `Decimal` に変換して検索するよう `admin/views.py` を修正し、`test_tax` fixtureも修正した結果、8ケースすべてPASSした。

修正の要点（概念例）:

```python
from decimal import Decimal, InvalidOperation

try:
    tax_value = Decimal(tax)
except (InvalidOperation, TypeError):
    flash('税率が正しく指定されていません')
    return redirect(url_for('admin.index'))

tax_rate = session.query(Tax).filter(Tax.rate == tax_value).first()
```

※ 上記は修正箇所の要点を示すもので、`admin/views.py` 全体の掲載ではない。

## 3. テストケース一覧

| ID | テスト関数 | 検証内容 | 期待結果 | 結果 |
|---|---|---|---|---|
| TOOL-E2E-001 | `test_tool_page_display` | フォームの表示 | ツール名・価格・税率・送信ボタンが表示される | PASS |
| TOOL-E2E-002 | `test_tool_registration` | 新規登録 | DBに指定したツール名のレコードが作成され、IDが存在する | PASS |
| TOOL-E2E-003 | `test_tool_price` | 価格保存 | DBの `Tool.price` が入力値 `12000` と一致する | PASS |
| TOOL-E2E-004 | `test_tool_tax_relationship` | 税率の外部キー | `Tool.tax_rate_id` が選択した `Tax.id` と一致する | PASS |
| TOOL-E2E-005 | `test_tool_registration_redirect` | 登録後の遷移 | `/top/` に遷移する | PASS |
| TOOL-E2E-006 | `test_tool_without_tax` | 税率未選択 | `/admin/` に戻り、ツール件数は増加せず対象レコードもない | PASS |
| TOOL-E2E-007 | `test_tool_empty_submission` | 全項目未入力 | `/admin/` に戻り、ツール件数が変わらない | PASS |
| TOOL-E2E-008 | `test_tool_page_requires_login` | 未ログインアクセス | `/login/` にリダイレクトされる | PASS |

## 4. 各テストの手順と期待結果

### TOOL-E2E-001: フォームの表示

1. `auth_page` でログイン済みブラウザを取得する。
2. `/admin/` にアクセスする。
3. `#tool`、`#price`、`select[name="tax"]`、送信ボタンの可視性を確認する。

**期待結果**: すべての入力要素が表示され、URLが `/admin/` である。

### TOOL-E2E-002: ツールの新規登録

1. 一意の `tool_name` を生成する。
2. テスト用税率を準備する。
3. ツール名・価格 `12000`・税率を入力し送信する。
4. `/top/` への遷移を確認する。
5. DBからツール名で検索する。

**期待結果**: レコードが存在し、ツール名が一致し、`id` が採番されている。

### TOOL-E2E-003: 価格の保存

1. テスト用税率を選択してツールを登録する。
2. DBから登録済みツールを取得する。
3. `Tool.price` を `Decimal(str(tool.price))` 等で比較する。

**期待結果**: 保存された価格が `12000` と一致する。

### TOOL-E2E-004: 税率との紐づけ

1. `test_tax` で税率の `id` と `rate` を取得する。
2. その税率を選択してツールを登録する。
3. DBから `Tool.tax_rate_id` を取得する。

**期待結果**: `Tool.tax_rate_id == test_tax['id']` が成立する。

### TOOL-E2E-005: 登録後の遷移

1. 必須情報を入力して登録する。
2. 登録直後のURLを確認する。

**期待結果**: `/top/` に遷移する。

### TOOL-E2E-006: 税率未選択

1. 登録前のツール件数を記録する。
2. ツール名と価格のみ入力し、税率を選択せず送信する。
3. 遷移先と登録後の件数を確認する。

**期待結果**: `/admin/` に戻り、ツール件数は変わらず、指定したツールは存在しない。

### TOOL-E2E-007: 全項目未入力

1. 登録前のツール件数を記録する。
2. フォームを空欄のまま送信する。
3. 遷移先と登録後の件数を確認する。

**期待結果**: `/admin/` に戻り、ツール件数が変わらない。

### TOOL-E2E-008: 未ログイン時のアクセス

1. 未認証の `page` fixtureで `/admin/` にアクセスする。
2. URLを検証する。

**期待結果**: `/login/` にリダイレクトされる（クエリ文字列は許容）。

## 5. Fixtureと共通関数

| 名称 | 用途 |
|---|---|
| `e2e_config` | `.env.test` のテスト用DB接続情報・認証情報を提供（共通fixture） |
| `e2e_server` | Flaskテストサーバーを起動（共通fixture） |
| `auth_page` | ログイン済みのPlaywrightページを提供（共通fixture） |
| `tool_name` | UUID由来の一意のツール名を生成 |
| `tool_db` | テスト用DBへのSQLAlchemy Engineを提供し、終了時に破棄 |
| `test_tax` | 使用可能な税率を取得し、必要に応じて作成・後処理 |
| `cleanup_tool` | テストで作成したツール名に一致するレコードを削除 |
| `register_tool()` | フォーム入力・送信を共通化 |
| `get_tool()` | ツール名でDBを検索 |
| `count_tools()` | ツール総数を取得 |

### 税率fixtureの取り扱い

`test_tax` は既存税率があれば再利用し、なければ `Decimal('0.10')` を使って税率を作成する方式。修正版では、新規作成した税率だけを後処理で削除する。既存マスターデータは削除しない。

**削除順序**: ツールを先に削除し、後からテストで新規作成した税率を削除する。`tools.tax_rate_id` の外部キー制約に注意する。

## 6. テスト環境とデータ保護

- `.env.test` で指定した `DATABASE_URL` を使用する。
- `tool_db` fixtureで接続先DB名が `invoicee_test` であることを検証する。
- テストごとに一意のツール名を使用し、既存ツールと衝突しないようにする。
- 登録したツールのみ削除し、既存のツールや税率を変更・削除しない。
- テストサーバー側も同じテストDBを参照していることを確認する。

## 7. 実行コマンド

```bash
# ツール登録E2Eテストのみ
python -m pytest tests/e2e/test_tool_e2e.py -v

# ブラウザ表示あり
python -m pytest tests/e2e/test_tool_e2e.py -v --headed

# 1ケースだけ実行
python -m pytest tests/e2e/test_tool_e2e.py::test_tool_registration -v -s

# E2Eテスト全体
python -m pytest tests/e2e/ -v
```

## 8. 不具合と修正履歴

| 項目 | 内容 |
|---|---|
| 初回実行 | 正常登録系4ケース（002〜005）が失敗 |
| 失敗内容 | 期待URL `/top/` に対して実際の遷移先は `/admin/` |
| 調査 | `register_tool()` の送信後URLを確認し、正常系で管理画面に戻ることを特定 |
| 関連する仕様 | `Tax.rate` は `Numeric(4,2)`、フォームからの税率は文字列 |
| 修正 | `admin/views.py` で税率を `Decimal` として扱い、`test_tax` fixtureを修正 |
| 再実行結果 | **8ケースすべてPASS** |

## 9. 今後の追加候補

- 存在しない税率を直接POSTした場合のエラー表示とDB未変更の確認
- 価格が空文字・非数値・負数の場合のバリデーション確認（現行実装の期待仕様を決めてから追加）
- 同名ツールの重複登録を許容するかどうかの仕様確認
- 税率の選択肢表示と `Tax.rate` の一致確認
- 登録処理中にDBエラーが発生した場合のロールバック・エラー画面の検証

---

**結論**: 税率の `Decimal` 化とfixtureの修正後、ツール登録E2Eテスト全8ケースのPASSを確認した。正常系・異常系・認証制御と、価格・税率外部キーの永続化を検証できている。
