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
```sh
tests
├── conftest.py #単体テスト
├── init_test_db.py #テスト用データベースの作成
├── seed_test_db.py #テスト用ユーザーの作成
├── test_db_integration.py #結合テスト
├── test_e2e.py #e2eテスト
├── test_error.py #エラーページへの遷移テスト
└── test_error_integration.py #エラー時のロールバックテスト
```

### テスト用データベース・テスト用ユーザーの作成
```sh
python -m tests.init_test_db
python -m tests.seed_test_db
```

### Flaskの起動
```sh
flask --app 'app:create_app()' run --port 5000 --no-reload
```

### 結合テスト
```sh
python -m pytest tests/test_db_integration.py -v
```

### エラー時のロールバックテスト
```sh
python -m pytest tests/test_error_integration.py -v
```

### e2eテスト
```sh
python -m pytest tests/test_e2e.py -v
```

### エラーページへの遷移テスト 
```sh
python -m pytest tests/test_error.py -v
```