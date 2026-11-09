# 更新画面 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`update/views.py`
- テストコード：`tests/unit/test_update.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト（DBアクセスをモック化）
- 目的：更新画面の表示、ジョブ選択、リダイレクト、未認証アクセス制御を検証する。

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| UPD-001 | test_update_get | 更新画面の表示 | HTTP 200、ジョブ・作業一覧を取得 |
| UPD-002 | test_update_get_empty | ジョブ・作業が0件 | 空のリストをテンプレートに渡す |
| UPD-003 | test_update_post_success | ジョブを選択してPOST | 詳細画面へリダイレクト |
| UPD-004 | test_update_post_empty_job | ジョブ未選択でPOST | エラーメッセージを設定 |
| UPD-005 | test_update_session_close | POST時のセッション管理 | session.close()が1回実行される |
| UPD-006 | test_update_login_required | 未認証アクセス | ログイン画面へリダイレクト |

## 3. テストケース詳細

### UPD-003：ジョブ選択成功

**対象関数：** `test_update_post_success(client)`

**目的：**

選択されたジョブIDが詳細画面へ正しく渡されることを確認する。

**入力データ：**

| 項目 | 値 |
|---|---|
| jobId | 123 |

**期待結果：**

1. HTTPステータスコードが302である。
2. リダイレクト先が `/detail/` である。
3. `selectedJobId=123` が渡される。
4. `session.close()` が1回実行される。

## 4. テスト実行方法

```bash
python -m pytest tests/unit/test_update.py -v
```

## 5. 合格基準

- 6件のテストがすべてPASSEDになること。
- ジョブ一覧・作業一覧が正しくテンプレートに渡されること。
- ジョブ選択後に正しい詳細画面へ遷移すること。
- 未認証ユーザーによるアクセスが制限されること。