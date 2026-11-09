
from unittest.mock import MagicMock, patch
from werkzeug.security import generate_password_hash


# GET：ログイン画面
def test_login_get(client):
    response = client.get("/login/")

    assert response.status_code == 200


# POST：ユーザー名が空
def test_login_empty_username(client):
    with patch("login.views.session") as mock_session:
        response = client.post("/login/", data={
            "username": "",
            "password": "password123"
        })

        assert response.status_code == 200
        assert b"login" not in response.headers.get(
            "Location", ""
        ).encode()

        mock_session.query.assert_not_called()
        mock_session.close.assert_called_once()


# POST：パスワードが空
def test_login_empty_password(client):
    with patch("login.views.session") as mock_session:
        response = client.post("/login/", data={
            "username": "testuser",
            "password": ""
        })

        assert response.status_code == 200
        mock_session.query.assert_not_called()
        mock_session.close.assert_called_once()


# POST：パスワードが間違っている
def test_login_wrong_password(client):
    mock_user = MagicMock()
    mock_user.username = "testuser"
    mock_user.password = generate_password_hash(
        "correct_password"
    )

    with patch("login.views.session") as mock_session, \
         patch("login.views.login_user") as mock_login:

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_user
        ]

        response = client.post("/login/", data={
            "username": "testuser",
            "password": "wrong_password"
        })

        assert response.status_code == 200
        mock_login.assert_not_called()
        mock_session.close.assert_called_once()


# POST：ログイン成功
def test_login_success(client):
    mock_user = MagicMock()
    mock_user.username = "testuser"
    mock_user.password = generate_password_hash(
        "correct_password"
    )

    with patch("login.views.session") as mock_session, \
         patch("login.views.login_user") as mock_login:

        mock_session.query.return_value.filter.return_value.all.return_value = [
            mock_user
        ]

        response = client.post("/login/", data={
            "username": "testuser",
            "password": "correct_password"
        })

        assert response.status_code == 302
        assert response.location.endswith("/top/")
        mock_login.assert_called_once_with(mock_user)


# POST：存在しないユーザー
def test_login_unknown_user(client):
    with patch("login.views.session") as mock_session, \
         patch("login.views.login_user") as mock_login:

        mock_session.query.return_value.filter.return_value.all.return_value = []

        response = client.post("/login/", data={
            "username": "unknown",
            "password": "password123"
        })

        assert response.status_code == 200
        mock_login.assert_not_called()
        mock_session.close.assert_called_once()
