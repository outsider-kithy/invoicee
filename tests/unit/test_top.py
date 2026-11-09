
from unittest.mock import MagicMock, patch, call
from urllib.parse import urlparse


# ログイン済みユーザーとしてアクセスするためのヘルパー
def authenticated_user():
    user = MagicMock()
    user.is_authenticated = True
    return user


# GET：トップページの表示
def test_top_get(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("top.views.session") as mock_session, \
         patch("top.views.render_template") as mock_render:

        mock_get_user.return_value = authenticated_user()

        # 案件0件
        mock_session.query.return_value.join.return_value \
            .join.return_value.join.return_value \
            .filter.return_value.all.return_value = []

        mock_render.return_value = "TOP PAGE"

        response = client.get("/top/")

        assert response.status_code == 200
        assert response.get_data(as_text=True) == "TOP PAGE"

        mock_render.assert_called_once_with(
            "top/index.html",
            job_list=[],
            monthly_total_price=0
        )


# GET：案件が0件
def test_top_empty_jobs(client):
    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("top.views.session") as mock_session, \
         patch("top.views.render_template") as mock_render:

        mock_get_user.return_value = authenticated_user()

        mock_session.query.return_value.join.return_value \
            .join.return_value.join.return_value \
            .filter.return_value.all.return_value = []

        mock_render.return_value = "TOP PAGE"

        response = client.get("/top/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["job_list"] == []
        assert kwargs["monthly_total_price"] == 0


# GET：案件が1件
def test_top_single_job(client):
    mock_job = MagicMock()
    mock_job.id = 1

    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("top.views.session") as mock_session, \
         patch("top.views.render_template") as mock_render:

        mock_get_user.return_value = authenticated_user()

        # Job取得と金額集計を区別
        mock_jobs_query = MagicMock()
        mock_price_query = MagicMock()

        mock_session.query.side_effect = [
            mock_jobs_query,
            mock_price_query
        ]

        mock_jobs_query.join.return_value.join.return_value \
            .join.return_value.filter.return_value \
            .all.return_value = [mock_job]

        mock_price_query.join.return_value.filter.return_value \
            .scalar.return_value = 10000

        mock_render.return_value = "TOP PAGE"

        response = client.get("/top/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["monthly_total_price"] == 10000
        assert len(kwargs["job_list"]) == 1
        assert kwargs["job_list"][0]["job"] is mock_job
        assert kwargs["job_list"][0]["current_price"] == 10000


# GET：複数案件の金額集計
def test_top_multiple_jobs(client):
    job1 = MagicMock()
    job1.id = 1

    job2 = MagicMock()
    job2.id = 2

    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("top.views.session") as mock_session, \
         patch("top.views.render_template") as mock_render:

        mock_get_user.return_value = authenticated_user()

        mock_jobs_query = MagicMock()
        mock_price_query1 = MagicMock()
        mock_price_query2 = MagicMock()

        mock_session.query.side_effect = [
            mock_jobs_query,
            mock_price_query1,
            mock_price_query2
        ]

        mock_jobs_query.join.return_value.join.return_value \
            .join.return_value.filter.return_value \
            .all.return_value = [job1, job2]

        mock_price_query1.join.return_value.filter.return_value \
            .scalar.return_value = 10000

        mock_price_query2.join.return_value.filter.return_value \
            .scalar.return_value = 20000

        mock_render.return_value = "TOP PAGE"

        response = client.get("/top/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["monthly_total_price"] == 30000
        assert len(kwargs["job_list"]) == 2

        assert kwargs["job_list"][0]["current_price"] == 10000
        assert kwargs["job_list"][1]["current_price"] == 20000


# GET：金額が0円の案件
def test_top_zero_price(client):
    mock_job = MagicMock()
    mock_job.id = 1

    with patch("flask_login.utils._get_user") as mock_get_user, \
         patch("top.views.session") as mock_session, \
         patch("top.views.render_template") as mock_render:

        mock_get_user.return_value = authenticated_user()

        mock_jobs_query = MagicMock()
        mock_price_query = MagicMock()

        mock_session.query.side_effect = [
            mock_jobs_query,
            mock_price_query
        ]

        mock_jobs_query.join.return_value.join.return_value \
            .join.return_value.filter.return_value \
            .all.return_value = [mock_job]

        mock_price_query.join.return_value.filter.return_value \
            .scalar.return_value = 0

        mock_render.return_value = "TOP PAGE"

        response = client.get("/top/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["monthly_total_price"] == 0
        assert kwargs["job_list"][0]["current_price"] == 0


# GET：未ログインユーザーのアクセス
def test_top_login_required(client):
    with patch("top.views.session") as mock_session:
        response = client.get("/top/")

        assert response.status_code == 302

        parsed_url = urlparse(response.location)
        assert parsed_url.path == "/login/"

        # 未認証ユーザーはDBアクセスできない
        mock_session.query.assert_not_called()
