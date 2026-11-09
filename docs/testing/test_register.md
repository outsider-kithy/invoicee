# ユーザー登録機能 単体テスト仕様書

## 1. テスト概要

- 対象モジュール：`register/views.py`
- テストコード：`tests/unit/test_register.py`
- テストフレームワーク：pytest
- テスト方式：単体テスト（DBアクセスはモック化）
- 目的：ユーザー登録時の入力検証、パスワードのハッシュ化、DB登録処理、画面遷移が正しく動作することを確認する。

## 2. テストケース一覧

| ID | テスト関数 | テスト内容 | 期待結果 |
|---|---|---|---|
| REG-001 | test_register_get | GETで登録ページへアクセス | HTTP 200 |
| REG-002 | test_register_empty_username | ユーザー名が未入力 | エラーメッセージ表示、DB登録なし |
| REG-003 | test_register_empty_password | パスワードが未入力 | エラーメッセージ表示、DB登録なし |
| REG-004 | test_register_empty_confirmation | 確認用パスワードが未入力 | エラーメッセージ表示、DB登録なし |
| REG-005 | test_register_password_mismatch | パスワードが一致しない | エラーメッセージ表示、DB登録なし |
| REG-006 | test_register_success | 正しい情報でユーザー登録 | DB登録処理実行、ログイン画面へリダイレクト |
| REG-007 | test_register_password_hashed | パスワードのハッシュ化 | 平文ではなく検証可能なハッシュが設定される |

## 3. テストケース詳細

### REG-001：GETで登録ページへアクセス

**対象関数：** `test_register_get(client)`

**目的：**

/registerルートにGETメソッドでアクセスした際に、正しくユーザー登録画面が表示されるかを確認する

**前提条件：**

- Flaskテストクライアントが利用可能

**期待結果：**

1. HTTPステータスコードが200である。

### REG-002：ユーザー名が未入力

**対象関数：** `test_register_empty_username`

**目的：**

usernameフィールドが空の状態でPOSTされた時に、エラーメッセージ「名前を入力してください」が正しく表示され、DB処理は行わず、/registerルートにリダイレクトされるかを検証する

**前提条件：**

- Flaskテストクライアントが利用可能
- SQLAlchemyのsessionをモック化
- 実際のデータベースには接続しない

**入力データ：**

| 項目 | 値 |
|---|---|
| username |  |
| password | password123 |
| confirmation | password123 |

**期待結果：**

1. HTTPステータスコードが302である。
2. リダイレクト先が `/register/` である。

### REG-003：パスワードが未入力

**対象関数：** `test_register_empty_password(client)`

**目的：**

passwordフィールドが空の状態でPOSTされた時に、エラーメッセージ「パスワードを入力してください」が正しく表示され、DB処理は行わず、/registerルートにリダイレクトされるかを検証する

**前提条件：**

- Flaskテストクライアントが利用可能
- SQLAlchemyのsessionをモック化
- 実際のデータベースには接続しない

**入力データ：**

| 項目 | 値 |
|---|---|
| username | testuser |
| password |  |
| confirmation | password123 |

**期待結果：**

1. HTTPステータスコードが302である。
2. リダイレクト先が `/register/` である。

### REG-00４：確認用パスワードが未入力

**対象関数：** `test_register_empty_confirmation(client)`

**目的：**

confirmationフィールドが空の状態でPOSTされた時に、エラーメッセージ「パスワードをもう一度入手してください」が正しく表示され、DB処理は行わず、/registerルートにリダイレクトされるかを検証する

**前提条件：**

- Flaskテストクライアントが利用可能
- SQLAlchemyのsessionをモック化
- 実際のデータベースには接続しない

**入力データ：**

| 項目 | 値 |
|---|---|
| username | testuser |
| password | password123 |
| confirmation |  |

**期待結果：**

1. HTTPステータスコードが302である。
2. リダイレクト先が `/register/` である。

### REG-005：パスワードが一致しない

**対象関数：** `test_register_password_mismatch(client)`

**目的：**

passwordフィールドとconfirmationフィールドに入力された値が一致しない場合、エラーメッセージ「入力されたパスワードが一致しません」が正しく表示され、DB処理は行わず、/registerルートにリダイレクトされるかを検証する

**前提条件：**

- Flaskテストクライアントが利用可能
- SQLAlchemyのsessionをモック化
- 実際のデータベースには接続しない

**入力データ：**

| 項目 | 値 |
|---|---|
| username | testuser |
| password | password123 |
| confirmation | different_password |

**期待結果：**

1. HTTPステータスコードが302である。
2. リダイレクト先が `/register/` である。

### REG-006：ユーザー登録成功

**対象関数：** `test_register_success(client)`

**目的：**

正しいユーザー名とパスワードを送信した場合、ユーザー登録処理が実行され、ログイン画面にリダイレクトされることを確認する。

**前提条件：**

- Flaskテストクライアントが利用可能
- SQLAlchemyのsessionをモック化
- 実際のデータベースには接続しない

**入力データ：**

| 項目 | 値 |
|---|---|
| username | testuser |
| password | password123 |
| confirmation | password123 |

**期待結果：**

1. HTTPステータスコードが302である。
2. リダイレクト先が `/login/` である。
3. `session.add()` が1回呼ばれる。
4. `session.commit()` が1回呼ばれる。
5. 登録対象のUserオブジェクトのusernameが `testuser` である。

**検証範囲外：**

- 実際のデータベースへのINSERT
- データベースのUNIQUE制約
- commit失敗時のロールバック

これらは結合テストで検証する。

### REG-007：パスワードのハッシュ化

**対象関数：** `test_register_password_hashed(client)`

**目的：**

正しいユーザー名とパスワードを送信した場合、ユーザー登録処理の際に、passwordに入力した値が正しくハッシュ化されているか、また、ハッシュ化されたパスワードを正しく検証できるかを確認する。

**前提条件：**

- Flaskテストクライアントが利用可能
- SQLAlchemyのsessionをモック化
- 実際のデータベースには接続しない

**入力データ：**

| 項目 | 値 |
|---|---|
| username | testuser |
| password | password123 |
| confirmation | password123 |

**期待結果：**

1. HTTPステータスコードが302である。
2. リダイレクト先が `/login/` である。
3. `session.add()` に渡されたUserオブジェクトのpasswordの値がハッシュ化されている。
5. 登録対象のUserオブジェクトのpasswordのハッシュ値がpasswordフィールドに入力された値と一致する


## 4. テスト実行方法

```bash
python -m pytest tests/unit/test_register.py -v
```

## 5. 合格基準

- 定義された7件のテストがすべてPASSEDになること。
- テスト実行中に予期しない例外が発生しないこと。
- テスト実行によって本番データベースが変更されないこと。