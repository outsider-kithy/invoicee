# Client・Job DB操作 結合テスト仕様書

## 1. 概要

| 項目 | 内容 |
| --- | --- |
| 対象テスト | `tests/integration/test_job_integration.py` |
| テスト種別 | 結合テスト（SQLAlchemy × PostgreSQL） |
| テストフレームワーク | pytest |
| 対象モデル | `Client`, `Job` および関連モデル |
| テストケース数 | 12 |
| 配置先（推奨） | `docs/testing/test_job_integration.md` |

本テストは、Client・Jobに対する登録・取得・更新・削除がPostgreSQL上で正しく行われること、および主キー・外部キー制約とトランザクション管理が期待どおり動作することを確認する。

> **対象範囲**: ORMと実データベースの結合を検証する。FlaskのHTTPルート（例：`/admin/`）経由の登録処理、フォーム検証、認可、画面表示は本ファイルの対象外とする。

## 2. テスト環境・前提条件

- PostgreSQLに接続可能であること。
- プロジェクトルートの `.env.test` にテスト専用 `DATABASE_URL` が設定されていること。
- `tests/conftest.py` の `app` fixtureがテストごとに専用PostgreSQLスキーマを作成し、テスト終了後に削除すること。
- `models.session` は `scoped_session` として定義され、テスト用エンジンにバインドされること。
- `seed` fixtureが必要なClient、Job、Agency、Account、Project、Toolなどの関連レコードを用意すること。
- `seed` fixtureが明示的な主キーを持つレコードを挿入した後、シーケンスを適切に調整すること。
- テスト用エンジンは通常のトランザクション管理を使用し、`rollback()` を検証できること。

**安全上の注意**: テストはスキーマの作成・削除とDB書き込みを行う。`DATABASE_URL` が本番データベースを指していないことを必ず確認する。

## 3. テストケース一覧

| ID | テスト関数 | 検証内容 | 主な期待結果 |
| --- | --- | --- | --- |
| DB-INT-001 | `test_client_insert` | Client新規登録 | 登録後にDBから取得でき、名前が一致する |
| DB-INT-002 | `test_client_update` | Client更新 | 更新後の値がDBに保存される |
| DB-INT-003 | `test_client_auto_increment` | Client主キー自動採番 | 異なるIDが採番され、後続IDが大きい |
| DB-INT-004 | `test_client_duplicate_primary_key` | Client主キー重複 | `IntegrityError` が発生し、元レコードが維持される |
| DB-INT-005 | `test_job_insert` | Job新規登録 | 登録後にDBから取得でき、主要フィールドが一致する |
| DB-INT-006 | `test_job_update` | Job更新 | タイトル・価格・見積済みフラグが保存される |
| DB-INT-007 | `test_job_relationships` | Jobの関連モデル参照 | Client、Agency、Account、Project、Toolの関連情報を参照できる |
| DB-INT-008 | `test_job_auto_increment` | Job主キー自動採番 | 異なるIDが採番され、後続IDが大きい |
| DB-INT-009 | `test_job_invalid_foreign_key` | 不正な外部キー | `IntegrityError` が発生し、不正なJobが保存されない |
| DB-INT-010 | `test_job_delete` | Job削除 | 削除後の主キー検索結果が `None` になる |
| DB-INT-011 | `test_transaction_rollback` | トランザクション取消 | `flush()` 後の未コミット登録が `rollback()` で取り消される |
| DB-INT-012 | `test_session_recovery_after_integrity_error` | DBエラー後の復旧 | `rollback()` 後に正常なClientを登録できる |

## 4. テストケース詳細

### DB-INT-001：Client新規登録

1. `Client(client_name="New Client")` を生成する。
2. `session.add()` と `session.commit()` で登録する。
3. 採番されたIDを保持して `session.remove()` を実行する。
4. `session.get(Client, id)` で再取得する。

**期待結果**: レコードが存在し、`client_name` が `New Client` である。

### DB-INT-002：Client更新

1. `seed` で作成した `Client(id=1)` を取得する。
2. `client_name` を `Updated Client` に変更してコミットする。
3. Sessionを切り替え、同じIDで再取得する。

**期待結果**: 更新後の名前が取得できる。

### DB-INT-003：Client主キー自動採番

1. IDを明示せずにClientを2件追加する。
2. コミット後、両方のIDを確認する。

**期待結果**: IDがどちらも `None` ではなく、互いに異なり、後続のIDが先行IDより大きい。

### DB-INT-004：Client主キー重複

1. `id=100` のClient Aを登録してコミットする。
2. **`session.remove()` でSessionを切り替える。**
3. 同じ `id=100` のClient Bを登録しようとする。
4. `pytest.raises(IntegrityError)` でコミット失敗を確認する。
5. `session.rollback()` 後にID 100を再取得する。

**期待結果**: 重複INSERTが拒否され、Client Aが保持される。

**補足（SAWarning対策）**: 1件目を保持したSessionに同一主キーの別インスタンスを追加すると、SQLAlchemyのIdentity Mapの競合により `SAWarning` が発生する。コミット直後に `session.remove()` を実行すると、ORM上の競合を避けつつ、PostgreSQL側の主キー制約を検証できる。

### DB-INT-005：Job新規登録

1. `seed` による関連データを用意する。
2. 既存のClient・Agency・Account・Project・Toolを参照するJobを追加する。
3. コミット後にIDを保持し、Sessionを切り替えて再取得する。

**期待結果**: Jobが存在し、タイトル、価格、見積済み・請求済みフラグが登録値と一致する。

### DB-INT-006：Job更新

1. `Job(id=1)` を取得する。
2. タイトル、価格、見積済みフラグを変更してコミットする。
3. Sessionを切り替えて再取得する。

**期待結果**: 変更した各フィールドがDBに保存される。

### DB-INT-007：Jobリレーション

1. `seed` によりJobと関連モデルを作成する。
2. Jobから定義済みのリレーション属性を参照する。

**期待結果**: Client、Agency、Account、Project、Toolの関連情報が想定するテストデータと一致する。

### DB-INT-008：Job主キー自動採番

1. `seed` で既存Jobを用意する。
2. IDを明示しないJobを2件追加してコミットする。

**期待結果**: それぞれに異なるIDが採番され、後続IDが大きい。

### DB-INT-009：不正な外部キー

1. 存在しない `client_id=99999` を参照するJobを生成する。
2. INSERTをコミットする。
3. `IntegrityError` を確認し、ロールバックする。
4. タイトルで不正なJobが存在しないことを確認する。

**期待結果**: 外部キー制約によりINSERTが拒否される。

### DB-INT-010：Job削除

1. `Job(id=1)` を取得して削除する。
2. コミット後にSessionを切り替える。
3. 同じ主キーで再取得する。

**期待結果**: `session.get(Job, 1)` が `None` を返す。

### DB-INT-011：ロールバック

1. 新しいClientを追加し、`session.flush()` でINSERTを発行する。
2. 採番IDを保持し、`session.rollback()` を実行する。
3. Sessionを切り替え、同じIDを検索する。

**期待結果**: ロールバックされたレコードは存在しない。

### DB-INT-012：IntegrityError後のSession復旧

1. 既存Clientと重複する主キーで登録を試みる。
2. `IntegrityError` を確認して `session.rollback()` を実行する。
3. 別の新しいClientを追加してコミットする。
4. IDを保持してSessionを切り替え、DBから再取得する。

**期待結果**: エラー後でも新規レコードの登録・取得が正常に行える。

## 5. 実行方法

対象ファイルのみ実行：

```bash
python -m pytest tests/integration/test_job_integration.py -v
```

警告も確認する場合：

```bash
python -m pytest tests/integration/test_job_integration.py -v -W default
```

単一ケースの実行例：

```bash
python -m pytest tests/integration/test_job_integration.py::test_client_duplicate_primary_key -v
```

**成功基準**: 12ケースすべてがPASSし、意図しないWarningやErrorが発生しないこと。

## 6. 実装・保守上の注意

### `session.remove()` と再取得

`scoped_session` の `session.remove()` は現在のSessionを閉じて破棄する。コミット後にSessionを切り替えて再取得することで、元のSessionのIdentity Mapに依存せずDBへの保存結果を確認できる。

```python
session.commit()
client_id = client.id
session.remove()
saved_client = session.get(Client, client_id)
```

`session.remove()` 後はORMインスタンスがSessionから切り離されるため、必要なIDは先に保存する。

### `IntegrityError` 発生時の処理

コミット失敗後は `session.rollback()` を実行してSessionを復旧させる。`pytest.raises(IntegrityError)` は意図した制約違反だけを対象にする。

### シーケンスと自動採番

手動IDで初期データを作成した場合、PostgreSQLのシーケンス値が追いついていないと次回のINSERTで主キー重複が起こり得る。`seed` fixtureでシーケンスを調整し、自動採番テストで整合性を検証する。

### テストの独立性

各テストが専用スキーマを使用する前提で、他のテストが作成・変更したデータに依存しない。テストの追加・変更時もこの独立性を維持する。

## 7. 対象外・今後の拡張

本ファイルでは、次の項目は検証しない。

- `/admin/` などFlaskのルートを経由したClient登録・Job更新
- ログイン状態や権限によるDB操作の許可・拒否
- フォームのバリデーションとエラーメッセージ表示
- 同時実行時の競合や高負荷時の挙動

これらは、ルート経由の結合テストまたはE2Eテストで別途検証する。

## 8. 実施結果

- 実施状況：**12ケースすべてPASS**（ユーザー確認済み）
- `test_client_duplicate_primary_key` の `SAWarning`：`session.remove()` の追加により解消（ユーザー確認済み）
- 実行日時・環境バージョン：必要に応じてテスト記録へ追記する。
