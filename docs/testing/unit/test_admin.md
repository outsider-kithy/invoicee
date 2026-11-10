# 管理画面 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`admin/views.py`
- テストコード：`tests/unit/test_admin.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト（DBアクセスをモック化）
- 目的：管理画面の表示、各種マスターデータの登録、プロジェクト終了処理、認証制御を検証する。

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| ADM-001 | test_admin_get | 管理画面表示 | HTTP 200、5種類の一覧を取得 |
| ADM-002 | test_admin_get_empty | 各テーブルが0件 | 空のリストを渡す |
| ADM-003 | test_admin_post_client | Client登録 | Clientを1件追加 |
| ADM-004 | test_admin_post_agency | Agency登録 | Agencyを1件追加 |
| ADM-005 | test_admin_post_account | Account登録 | Agency IDを紐づけて登録 |
| ADM-006 | test_admin_post_tool | Tool登録 | 価格と税率IDを設定して登録 |
| ADM-007 | test_admin_post_finish_project | Project終了 | isfinishedを1に更新 |
| ADM-008 | test_admin_post_empty | 全項目未入力 | エラーを表示し登録しない |
| ADM-009 | test_admin_post_priority | 複数項目を同時送信 | 最初の条件に一致する処理のみ実行 |
| ADM-010 | test_admin_post_redirect | 正常登録後の遷移 | /top/へリダイレクト |
| ADM-011 | test_admin_login_required_get | 未認証GET | ログイン画面へリダイレクト |
| ADM-012 | test_admin_login_required_post | 未認証POST | 登録せずログイン画面へリダイレクト |

## 3. テストケース詳細

### ADM-005：Accountの新規登録

**目的：**

担当者名と代理店名から、正しいAgency IDを持つAccountレコードが生成されることを確認する。

**入力データ：**

| 項目 | 値 |
|---|---|
| account | テスト担当者 |
| agencyName | テスト代理店 |

**期待結果：**

1. Agencyを名前で検索する。
2. Accountのaccount_nameが「テスト担当者」である。
3. Accountのagency_idが10である。
4. session.add()が1回呼ばれる。
5. 正常終了後に /top/ へリダイレクトされる。

### ADM-007：Projectの終了処理

**目的：**

選択されたProjectを終了状態に変更することを確認する。

**入力データ：**

| 項目 | 値 |
|---|---|
| finished_project | テストプロジェクト |

**期待結果：**

1. Projectを名前で検索する。
2. 対象Projectのisfinishedが1になる。
3. session.add()は呼ばれない。
4. session.commit()が呼ばれる。

## 4. 検証範囲外

- PostgreSQLへの実際のINSERT・UPDATE
- 外部キー制約
- マスターデータの重複登録防止
- トランザクションのロールバック
- HTMLテンプレートの描画結果

これらは結合テストで検証する。

## 5. テスト実行方法

```bash
python -m pytest tests/unit/test_admin.py -v
```

## 6. 合格基準

- 12件のテストがすべてPASSEDになること。
- 各種マスターデータが正しい属性で生成されること。
- Projectの終了状態が正しく更新されること。
- 未認証ユーザーによるデータ登録・更新が制限されること。