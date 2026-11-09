# プロジェクト登録機能 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`project/views.py`
- テストコード：`tests/unit/test_project.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト（DBアクセスをモック化）
- 目的：プロジェクト登録画面の表示、入力検証、Projectレコードの作成、画面遷移、認証制御を検証する。

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| PRJ-001 | test_project_get | 登録画面の表示 | HTTP 200、Client・Agency・Account一覧を取得 |
| PRJ-002 | test_project_get_empty | 一覧データが0件 | 空のリストをテンプレートに渡す |
| PRJ-003 | test_project_post_success | Projectの正常登録 | 正しい属性のProjectを追加しcommitする |
| PRJ-004 | test_project_post_empty_name | プロジェクト名未入力 | エラーを表示して登録画面へ戻る |
| PRJ-005 | test_project_post_empty_client | クライアント名未選択 | エラーを表示して登録しない |
| PRJ-006 | test_project_post_empty_agency | 代理店が存在しない | エラーを表示して登録しない |
| PRJ-007 | test_project_post_empty_account | 担当者名未入力 | エラーを表示して登録しない |
| PRJ-008 | test_project_post_optional_agency_id | 代理店IDが空文字列 | エラーを表示して登録しない |
| PRJ-009 | test_project_post_redirect | 登録後の画面遷移 | /top/へリダイレクト |
| PRJ-010 | test_project_login_required | 未認証アクセス | ログイン画面へリダイレクト |

## 3. テストケース詳細

### PRJ-003：Projectの正常登録

**目的：**

入力されたプロジェクト名、クライアント、代理店、担当者の情報からProjectレコードが正しく生成されることを確認する。

**入力データ：**

| 項目 | 値 |
|---|---|
| project | テストプロジェクト |
| projectClientName | テストクライアント |
| projectAgencyId | 2 |
| projectAccountName | テスト担当者 |

**期待結果：**

1. HTTPステータスコードが302である。
2. `/top/` にリダイレクトされる。
3. `session.add()` が1回実行される。
4. `session.commit()` が1回実行される。
5. Projectの各属性が正しく設定される。
6. isfinishedが0である。

### PRJ-004：プロジェクト名未入力

**目的：**

プロジェクト名が入力されていない場合に、Projectが登録されないことを確認する。

**期待結果：**

1. エラーメッセージが設定される。
2. `/project/` にリダイレクトされる。
3. `session.add()` が呼ばれない。
4. `session.commit()` が呼ばれない。

## 4. 検証範囲外

- PostgreSQLへの実際のINSERT
- 外部キー制約の検証
- データベース上の重複登録防止
- トランザクションのロールバック
- HTMLテンプレートの描画結果

これらは結合テストで検証する。

## 5. テスト実行方法

```bash
python -m pytest tests/unit/test_project.py -v
```

## 6. 合格基準

- 10件のテストがすべてPASSEDになること。
- Projectの各属性が正しく設定されること。
- 入力エラー時にProjectが登録されないこと。
- 未認証ユーザーのアクセスが制限されること。