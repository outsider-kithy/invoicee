# ジョブ詳細画面 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`detail/views.py`
- テストコード：`tests/unit/test_detail.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト（DBアクセスとテンプレート描画をモック化）
- 目的：ジョブ詳細情報の取得、既存Contentの更新、新規Contentの追加、画面遷移、未認証アクセス制御を検証する。

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| DET-001 | test_detail_get | 詳細画面へのGETアクセス | HTTP 200、必要なデータをテンプレートに渡す |
| DET-002 | test_detail_get_empty | Contentが0件 | 空のリスト、合計金額None |
| DET-003 | test_detail_get_total_price | 合計金額の取得 | 30,000円をテンプレートに渡す |
| DET-004 | test_detail_post_update | 既存Contentの更新 | work_idとwork_contentが更新される |
| DET-005 | test_detail_post_add | 新規Contentの追加 | session.add()とcommit()が呼ばれる |
| DET-006 | test_detail_post_empty_content | 空欄の作業内容 | 新規Contentを追加しない |
| DET-007 | test_detail_post_unknown_work | 存在しないWork種別 | 新規Contentを追加しない |
| DET-008 | test_detail_post_redirect | POST処理後の画面遷移 | /update/へリダイレクト |
| DET-009 | test_detail_login_required | 未認証アクセス | ログイン画面へリダイレクト |

## 3. テストケース詳細

### DET-004：既存Contentの更新

**対象関数：** `test_detail_post_update(client, authenticated)`

**目的：**

既存のContentに対して、新しく選択されたWork種別と作業内容が正しく設定されることを確認する。

**入力データ：**

| 項目 | 値 |
|---|---|
| update_job_id | 1 |
| update_work[] | coding |
| update_content[] | 変更後 |

**期待結果：**

1. HTTPステータスコードが302である。
2. Contentのwork_idが2に更新される。
3. Contentのwork_contentが「変更後」に更新される。
4. 新しいContentは追加されない。

### DET-005：新規Contentの追加

**対象関数：** `test_detail_post_add(client, authenticated)`

**目的：**

新しい作業内容が入力された場合、正しいContentオブジェクトが作成され、データベースへの登録処理が呼び出されることを確認する。

**入力データ：**

| 項目 | 値 |
|---|---|
| update_job_id | 1 |
| new_work[] | design |
| new_content[] | デザイン制作 |

**期待結果：**

1. HTTPステータスコードが302である。
2. Contentオブジェクトが生成される。
3. job_id、work_id、work_contentが正しく設定される。
4. session.add()が1回呼ばれる。
5. session.commit()が1回呼ばれる。

## 4. 検証範囲外

- 実際のPostgreSQLへのINSERT・UPDATE
- SQLAlchemyのJOIN・SUMの実行結果
- トランザクションのロールバック
- HTMLテンプレートの表示内容

これらは結合テストで検証する。

## 5. テスト実行方法

```bash
python -m pytest tests/unit/test_detail.py -v
```

## 6. 合格基準

- 9件のテストがすべてPASSEDになること。
- 既存Contentの更新値が正しいこと。
- 新規Contentの登録処理が正しく呼び出されること。
- 空欄や存在しないWork種別が適切にスキップされること。
- 未認証ユーザーによるアクセスが制限されること。