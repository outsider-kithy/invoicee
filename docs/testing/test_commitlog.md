# コミットログページ 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`commitlog/views.py`
- テストコード：`tests/unit/test_commitlog.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト（DBアクセスをモック化）
- 目的：GitHub APIへのアクセス、APIのレスポンスに応じて処理を適切に分岐

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| ADM-001 | test_missing_job_returns_404 | jobIdがPOSTされなければ、404を返す | 404 |
| ADM-002 | test_missing_repository_returns_400 | GitHubのリポジトリ名がPOSTされなければ、404を返す | 404 |
| ADM-003 | test_github_api_response | GitHub APIへのリクエストを送る | 200, 400 |

## 3. テストケース詳細

## 4. 検証範囲外

- トランザクションのロールバック

これらは結合テストで検証する。

## 5. テスト実行方法

```bash
python -m pytest tests/unit/test_commitlog.py -v
```

## 6. 合格基準

- 3件のテストがすべてPASSEDになること。
- 未認証ユーザーによるデータ登録・更新が制限されること。