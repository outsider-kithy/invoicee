# webhook 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`webhook/views.py`
- テストコード：`tests/unit/test_webhook.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト（DBアクセスをモック化）
- 目的：GitHub APIへのアクセス、APIのレスポンスに応じて処理を適切に分岐

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| ADM-001 | test_invalid_payload_does_not_access_database | GitHub APIから400エラーが返ってきたら、データベースにアクセスしない |  |
| ADM-002 | test_database_failure_rolls_back | データベースに登録する処理が失敗したら、ロールバックする |  |

## 3. テストケース詳細

## 4. 検証範囲外

- PostgreSQLへの実際のINSERT・UPDATE
- トランザクションのロールバック

これらは結合テストで検証する。

## 5. テスト実行方法

```bash
python -m pytest tests/unit/test_webhook.py -v
```

## 6. 合格基準

- 2件のテストがすべてPASSEDになること。
- 未認証ユーザーによるデータ登録・更新が制限されること。