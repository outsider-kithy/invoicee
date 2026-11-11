
from unittest.mock import MagicMock, patch
from werkzeug.security import check_password_hash


# GET：ユーザー登録画面
def test_register_get(client):
    response = client.get("/register/")

    assert response.status_code == 200


# POST：ユーザー名が空
def test_register_empty_username(client):
    with patch("register.views.session") as mock_session, \
         patch("register.views.flash") as mock_flash:

        response = client.post("/register/", data={
            "username": "",
            "password": "password123",
            "confirmation": "password123"
        })

        assert response.status_code == 200
        mock_flash.assert_called_once_with(
            "名前を入力してください"
        )
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：パスワードが空
def test_register_empty_password(client):
    with patch("register.views.session") as mock_session, \
         patch("register.views.flash") as mock_flash:

        response = client.post("/register/", data={
            "username": "testuser",
            "password": "",
            "confirmation": "password123"
        })

        assert response.status_code == 200
        mock_flash.assert_called_once_with(
            "パスワードを入力してください"
        )
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：確認用パスワードが空
def test_register_empty_confirmation(client):
    with patch("register.views.session") as mock_session, \
         patch("register.views.flash") as mock_flash:

        response = client.post("/register/", data={
            "username": "testuser",
            "password": "password123",
            "confirmation": ""
        })

        assert response.status_code == 200
        mock_flash.assert_called_once_with(
            "パスワードをもう一度入力してください"
        )
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：パスワードが一致しない
def test_register_password_mismatch(client):
    with patch("register.views.session") as mock_session, \
         patch("register.views.flash") as mock_flash:

        response = client.post("/register/", data={
            "username": "testuser",
            "password": "password123",
            "confirmation": "different_password"
        })

        assert response.status_code == 200
        mock_flash.assert_called_once_with(
            "入力されたパスワードが一致しません"
        )
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()



# POST：ユーザー登録成功
def test_register_success(client):
    with patch("register.views.session") as mock_session:

        # ユーザー名の重複チェック
        # 既存ユーザーが存在しない状態を再現
        mock_session.query.return_value \
            .filter.return_value \
            .first.return_value = None

        response = client.post("/register/", data={
            "username": "testuser",
            "password": "password123",
            "confirmation": "password123"
        })

        # ログインページへリダイレクト
        assert response.status_code == 302
        assert response.location == "/login/"

        # データベースへの登録処理
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        # 登録されたユーザーを取得
        added_user = mock_session.add.call_args.args[0]

        assert added_user.username == "testuser"




# POST：パスワードがハッシュ化されている
def test_register_password_hashed(client):
    with patch("register.views.session") as mock_session:

        # ユーザー名が重複していない状態
        mock_session.query.return_value \
            .filter.return_value \
            .first.return_value = None

        response = client.post("/register/", data={
            "username": "testuser",
            "password": "password123",
            "confirmation": "password123"
        })

        assert response.status_code == 302

        # session.add() に渡されたUserオブジェクト
        added_user = mock_session.add.call_args.args[0]

        # 平文のパスワードが保存されていないこと
        assert added_user.password != "password123"

        # ハッシュ化されたパスワードが検証できること
        assert check_password_hash(
            added_user.password,
            "password123"
        )

        mock_session.commit.assert_called_once()


def test_register_duplicate_username(client):
    with patch("register.views.session") as mock_session, \
         patch("register.views.flash") as mock_flash:

        # 既存ユーザーを再現
        existing_user = MagicMock()
        existing_user.username = "testuser"

        mock_session.query.return_value \
            .filter.return_value \
            .first.return_value = existing_user

        response = client.post("/register/", data={
            "username": "testuser",
            "password": "password123",
            "confirmation": "password123"
        })

        assert response.status_code == 200

        mock_flash.assert_called_once_with(
            "このユーザー名は既に使用されています"
        )

        # DBに新しいユーザーを登録しない
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()