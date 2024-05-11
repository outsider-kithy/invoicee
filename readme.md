# PythonフレームワークFlaskアプリケーションをデプロイしよう サンプルコード

このリポジトリは、書籍「PythonフレームワークFlaskアプリケーションをデプロイしよう」のサンプルコードです。
※姉妹編「PythonフレームワークFlaskで請求書発行アプリを作ろう」の最終章`chap06`と同じ内容です。

## サンプルコードの環境構築
※このアプリケーションを動かすにはPostgreSQLのがインストールが必要です。

### Macの場合
ターミナルで以下を実行
```shell
#仮想環境「.venv」を作成
$ python3 -m venv .venv
#仮想環境をアクティベート
$ source .venv/bin/activate
#依存関係をインストール
(.venv) $ pip install -r requirements.txt
#Flaskを起動
(.venv) $ flask run
```

### Windowsの場合
PowerShellで以下を実行
```shell
#仮想環境「.venv」を作成
python -m venv .venv
#仮想環境をアクティベート
.venv\Scripts\Activate.ps1
#依存関係をインストール
(.venv)　(略) pip install -r requirements.txt
#Flaskを起動
(.venv)　(略) flask run
```


