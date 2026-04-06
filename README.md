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

### 開発用
プロジェクト直下に`.env.development`を作成し、以下を設定
```.env.development
DATABASE_URL='PostgreSQLデータベースのURL'
TEMPLATE_FILE = 'estimate_template.xlsxまでのパス'
OUTPUT_DIR = '請求書のエクセルデータを書き出すディレクトリ'
```

### 本番用
プロジェクト直下に`.env.production`を作成し、`.env.development`と同様の3つの環境変数を定義

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