# ジョブ登録機能 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`record/views.py`
- テストコード：`tests/unit/test_record.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト（DBアクセスをモック化）
- 目的：ジョブ登録画面の表示、入力検証、Jobレコードの作成、画面遷移、認証制御を検証する。

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| REC-001 | test_record_get | 登録画面の表示 | HTTP 200、ProjectとTool一覧を取得 |
| REC-002 | test_record_get_empty | 一覧データが0件 | 空のリストをテンプレートに渡す |
| REC-003 | test_record_post_success | Jobの正常登録 | 正しい属性のJobを追加しcommitする |
| REC-004 | test_record_post_empty_title | タイトル未入力 | エラーを表示し登録画面へ戻る |
| REC-005 | test_record_post_empty_project | プロジェクト未選択 | エラーを表示し登録しない |
| REC-006 | test_record_post_empty_tool | ツール未選択 | エラーを表示し登録しない |
| REC-007 | test_record_post_optional_github | GitHub URLが空欄 | 空文字列でJobを登録する |
| REC-008 | test_record_post_multiple_projects | 同名Projectが複数存在 | 現行実装では複数Jobが登録される |
| REC-009 | test_record_post_unknown_tool | toolが存在しない場合 | エラーを表示し登録しない |
| REC-010 | test_record_post_unknown_project | projectが存在しない場合 | エラーを表示し登録しない |
| REC-011 | test_record_login_required | 未認証アクセス | ログイン画面へリダイレクト |

## 3. テストケース詳細

### REC-003：Jobの正常登録

**目的：**

入力されたタイトル、プロジェクト、ツール、GitHub URLからJobレコードが正しく生成されることを確認する。

**入力データ：**

| 項目 | 値 |
|---|---|
| title | コーポレートサイト制作 |
| project | テストプロジェクト |
| tool | HTML |
| github_repository | https://github.com/example/test |

**期待結果：**

1. HTTPステータスコードが302である。
2. `/top/` にリダイレクトされる。
3. `session.add()` が1回実行される。
4. `session.commit()` が1回実行される。
5. Jobの各属性が正しく設定される。
6. estimated、invoicedがそれぞれ0である。

### REC-004：タイトル未入力

**目的：**

タイトルが入力されていない場合に、Jobが登録されないことを確認する。

**期待結果：**

1. エラーメッセージが設定される。
2. `/record/` にリダイレクトされる。
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
python -m pytest tests/unit/test_record.py -v
```

## 6. 合格基準

- 9件のテストがすべてPASSEDになること。
- Jobの各属性が正しく設定されること。
- 入力エラー時にJobが登録されないこと。
- 未認証ユーザーのアクセスが制限されること。
