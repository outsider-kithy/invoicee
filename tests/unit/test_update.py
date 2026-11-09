
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse, parse_qs


# 認証済みユーザーを作成
def authenticated_user():
    user = MagicMock()
    user.is_authenticated = True
    return user


# GET：更新画面の表示
def test_update_get(client):
    mock_job = MagicMock()
    mock_job.id = 1

    mock_work = MagicMock()
    mock_work.id = 1

    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("update.views.session") as mock_session, \
         patch("update.views.render_template") as mock_render:

        mock_get_user.return_value = authenticated_user()

        mock_jobs_query = MagicMock()
        mock_works_query = MagicMock()

        mock_session.query.side_effect = [
            mock_jobs_query,
            mock_works_query
        ]

        mock_jobs_query.join.return_value.join.return_value \
            .join.return_value.filter.return_value \
            .all.return_value = [mock_job]

        mock_works_query.all.return_value = [mock_work]

        mock_render.return_value = "UPDATE PAGE"

        response = client.get("/update/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["jobs"] == [mock_job]
        assert kwargs["works"] == [mock_work]


# GET：ジョブが0件の場合
def test_update_get_empty(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("update.views.session") as mock_session, \
         patch("update.views.render_template") as mock_render:

        mock_get_user.return_value = authenticated_user()

        mock_jobs_query = MagicMock()
        mock_works_query = MagicMock()

        mock_session.query.side_effect = [
            mock_jobs_query,
            mock_works_query
        ]

        mock_jobs_query.join.return_value.join.return_value \
            .join.return_value.filter.return_value \
            .all.return_value = []

        mock_works_query.all.return_value = []

        mock_render.return_value = "UPDATE PAGE"

        response = client.get("/update/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["jobs"] == []
        assert kwargs["works"] == []


# POST：ジョブ選択成功
def test_update_post_success(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("update.views.session") as mock_session:

        mock_get_user.return_value = authenticated_user()

        response = client.post("/update/", data={
            "jobId": "123"
        })

        assert response.status_code == 302

        parsed_url = urlparse(response.location)

        assert parsed_url.path == "/detail/"
        assert parse_qs(parsed_url.query)["selectedJobId"] == ["123"]

        mock_session.close.assert_called_once()


# POST：ジョブが未選択
def test_update_post_empty_job(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("update.views.session") as mock_session, \
         patch("update.views.flash") as mock_flash:

        mock_get_user.return_value = authenticated_user()

        response = client.post("/update/", data={
            "jobId": ""
        })

        mock_flash.assert_called_once_with(
            "ジョブが選択されていません"
        )

        assert response.status_code == 302
        assert urlparse(response.location).path == "/update/"


# POST：セッションが閉じられることを確認
def test_update_session_close(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("update.views.session") as mock_session:

        mock_get_user.return_value = authenticated_user()

        response = client.post("/update/", data={
            "jobId": "123"
        })

        assert response.status_code == 302
        mock_session.close.assert_called_once()


# GET：未ログインユーザーのアクセス
def test_update_login_required(client):
    with patch("update.views.session") as mock_session:

        response = client.get("/update/")

        assert response.status_code == 302

        parsed_url = urlparse(response.location)
        assert parsed_url.path == "/login/"

        mock_session.query.assert_not_called()
