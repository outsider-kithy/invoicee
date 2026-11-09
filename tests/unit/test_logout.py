
from unittest.mock import patch
from urllib.parse import urlparse


# GET：ログイン済みユーザーのログアウト
def test_logout_success(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("logout.views.logout_user") as mock_logout:

        # ログイン済みユーザーを再現
        mock_get_user.return_value.is_authenticated = True

        response = client.get("/logout/")

        assert response.status_code == 302
        mock_logout.assert_called_once()


# GET：ログアウト後のリダイレクト先
def test_logout_redirect(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("logout.views.logout_user") as mock_logout:

        mock_get_user.return_value.is_authenticated = True

        response = client.get("/logout/")

        assert response.status_code == 302
        assert response.location == "/login"
        mock_logout.assert_called_once()


# GET：未ログインユーザーのアクセス
def test_logout_required(client):
    with patch("logout.views.logout_user") as mock_logout:

        response = client.get("/logout/")

        assert response.status_code == 302

        # リダイレクト先を確認
        parsed_url = urlparse(response.location)
        assert parsed_url.path == "/login/"

        # ログアウト処理は実行されない
        mock_logout.assert_not_called()


# GET：logout_user()が1回だけ呼ばれる
def test_logout_user_called_once(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("logout.views.logout_user") as mock_logout:

        mock_get_user.return_value.is_authenticated = True

        response = client.get("/logout/")

        assert response.status_code == 302
        mock_logout.assert_called_once()
