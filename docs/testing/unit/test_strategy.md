# pytestによるinvoiceeのテスト戦略

- 単体テスト（Unit Test）：Flaskのルーティングやバリデーションを検証し、DBアクセスや外部APIをモック化する。

- 結合テスト（Integration Test）：テスト用PostgreSQLを使用し、SQLAlchemyのINSERT・SELECT・UPDATE・DELETEや制約を検証する。

- E2Eテスト：ブラウザ操作を通じて、ログインからユーザー登録などの一連の操作を検証する。

テスト実行基準：コード変更時に関連する単体テストを実行し、リリース前には全テストを実行する。