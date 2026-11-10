
from unittest.mock import patch
from urllib.parse import urlparse

import pytest


@pytest.fixture
def authenticated():
    """
    Flask-Loginの認証済みユーザーをモック化する。
    """
    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value.is_authenticated = True
        yield mock_user


# NFD-001
def test_notfound_get_status_code(client, authenticated):
    """
    GET /notfound/ がHTTP 404を返すことを確認する。
    """
    with patch("notfound.views.render_template") as mock_render:
        mock_render.return_value = "NOT FOUND PAGE"

        response = client.get("/404/")

        assert response.status_code == 404
        assert response.get_data(as_text=True) == "NOT FOUND PAGE"


# NFD-002
def test_notfound_get_template(client, authenticated):
    """
    GET時に正しいテンプレートとエラーメッセージが
    渡されることを確認する。
    """
    with patch("notfound.views.render_template") as mock_render:
        mock_render.return_value = "NOT FOUND PAGE"

        response = client.get("/404/")

        assert response.status_code == 404

        mock_render.assert_called_once_with(
            "notfound/index.html",
            error_message="指定のページは見つかりませんでした。"
        )


# NFD-003
def test_notfound_post_status_code(client, authenticated):
    """
    POST /notfound/ がHTTP 404を返すことを確認する。
    """
    with patch("notfound.views.render_template") as mock_render:
        mock_render.return_value = "NOT FOUND PAGE"

        response = client.post("/404/")

        assert response.status_code == 404
        assert response.get_data(as_text=True) == "NOT FOUND PAGE"


# NFD-004
def test_notfound_post_template(client, authenticated):
    """
    POST時に正しいテンプレートとエラーメッセージが
    渡されることを確認する。
    """
    with patch("notfound.views.render_template") as mock_render:
        mock_render.return_value = "NOT FOUND PAGE"

        response = client.post("/404/")

        assert response.status_code == 404

        mock_render.assert_called_once_with(
            "notfound/index.html",
            error_message="指定のページは見つかりませんでした。"
        )


# NFD-005
def test_notfound_login_required_get(client):
    """
    未ログイン状態でGETアクセスすると
    ログイン画面へリダイレクトされることを確認する。
    """
    with patch("notfound.views.render_template") as mock_render:
        response = client.get("/404/")

        assert response.status_code == 302
        assert urlparse(response.location).path == "/login/"

        mock_render.assert_not_called()


# NFD-006
def test_notfound_login_required_post(client):
    """
    未ログイン状態でPOSTアクセスすると
    ログイン画面へリダイレクトされることを確認する。
    """
    with patch("notfound.views.render_template") as mock_render:
        response = client.post("/404/")

        assert response.status_code == 302
        assert urlparse(response.location).path == "/login/"

        mock_render.assert_not_called()
