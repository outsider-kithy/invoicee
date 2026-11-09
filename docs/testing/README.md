# pytest テスト

`.env.test` の `DATABASE_URL` に記載したPostgreSQLデータベースを使用します。
シェルの環境変数や `.env` の接続先より、この設定を優先します。

```dotenv
DATABASE_URL=postgresql://localhost/invoicee_test
```

PostgreSQLを起動し、接続先DBを事前に作成してください。接続ユーザーには、
このDBへの接続とスキーマ作成権限が必要です。
各テストは固有の `pytest_<UUID>` スキーマにテーブルとデータを作成し、
終了時にそのスキーマだけを削除します。既存のpublicスキーマのデータは変更しません。
アプリケーションのcommit・rollbackと、E2Eサーバーの別接続も実DBで検証します。
テストプロセスを強制終了した場合はテストスキーマが残ることがあります。
DB初期化スクリプトや手動でのFlask起動は不要です。GitHub APIはモックします。

```sh
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium

# 全テスト（E2Eを含む）
python -m pytest -v

# ブラウザ不要の単体・結合テスト
python -m pytest -m 'not e2e' -v

# 種別ごとの実行
python -m pytest -m unit -v
python -m pytest -m integration -v
python -m pytest -m e2e -v --browser chromium

# アプリケーションのカバレッジ
python -m pytest -m 'not e2e' --cov=app --cov=models --cov=helper \
  --cov=login --cov=register --cov=logout --cov=project --cov=record \
  --cov=detail --cov=estimate --cov=admin --cov=webhook --cov=commitlog \
  --cov=top --cov=error --cov=notfound --cov=update --cov-report=term-missing
```

- `unit/`: Excelセル・税率・数式、Webhook入力検証とロールバック、GitHub API連携。
- `integration/`: 認証・入力検証、プロジェクト／ジョブ／作業登録、見積書と見積済フラグ、
  プロジェクト終了、実際のINSERT後のロールバック、Webhook保存、エラーページ。
- `e2e/`: Chromiumでユーザー登録→ログイン→ジョブ作成→見積書ダウンロード→
  ログアウト、およびパスワード誤りの表示。HTTPサーバーは空きポートで自動起動します。

Excel数式は式そのものを検証し、Excelによる再計算結果は検証しません。
