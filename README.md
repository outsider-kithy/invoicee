# 請求書発行アプリ「invoicee」

## 環境構築

### 仮想環境の構築
```sh
python3 -m venv .venv
source .venv/bin/activate
```

### PostgreSQLのダウンロード
省略

## 環境変数の設定

プロジェクト直下に`.env`を作成し、以下を設定
```.env
DATABASE_URL='PostgreSQLデータベースのURL'
TEMPLATE_FILE = 'estimate_template.xlsxまでのパス'
OUTPUT_DIR = '請求書のエクセルデータを書き出すディレクトリ'
```

## パッケージインストール
```sh
pip install -r requirements.txt
```

## 起動
```sh
flask run
```

`http://http://127.0.0.1:5000/login`にアクセス


## 停止
```sh
deactivate
```

## テスト

pytestを使った単体・結合・ブラウザE2Eテストを `tests/` に用意しています。
`.env.test` のPostgreSQLデータベースを使用します（DBは事前に作成してください）。
テスト用スキーマとHTTPサーバーは自動で作成・破棄されます。

```sh
python -m playwright install chromium
python -m pytest -v
```

ブラウザ不要のテストは `python -m pytest -m 'not e2e' -v` で実行できます。
詳しい構成・実行方法は [tests/README.md](tests/README.md) を参照してください。
