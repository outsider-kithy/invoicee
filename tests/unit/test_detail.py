
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest

from models import Content


# 認証済みユーザーを再現
@pytest.fixture
def authenticated():
    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value.is_authenticated = True
        yield mock_user


# GETのDBクエリをモック化
def setup_get_queries(mock_session, job, contents, works, total):
    job_query = MagicMock()
    content_query = MagicMock()
    work_query = MagicMock()
    price_query = MagicMock()

    mock_session.query.side_effect = [
        job_query,
        content_query,
        work_query,
        price_query
    ]

    job_query.filter.return_value.first.return_value = job
    content_query.filter.return_value.all.return_value = contents
    work_query.all.return_value = works

    price_query.join.return_value.filter.return_value \
        .scalar.return_value = total


# POSTのDBクエリをモック化
def setup_post_queries(mock_session, contents, work_records):
    content_query = MagicMock()

    content_query.filter.return_value.order_by.return_value \
        .all.return_value = contents

    queries = [content_query]

    for work_record in work_records:
        work_query = MagicMock()
        work_query.filter.return_value.first.return_value = work_record
        queries.append(work_query)

    mock_session.query.side_effect = queries


# GET：ジョブ詳細画面
def test_detail_get(client, authenticated):
    job = MagicMock(id=1)
    content = MagicMock(id=10)
    work = MagicMock(id=20)

    with patch("detail.views.session") as mock_session, \
         patch("detail.views.render_template") as mock_render:

        setup_get_queries(
            mock_session,
            job,
            [content],
            [work],
            10000
        )

        mock_render.return_value = "DETAIL PAGE"

        response = client.get(
            "/detail/?selectedJobId=1"
        )

        assert response.status_code == 200

        mock_render.assert_called_once_with(
            "detail/index.html",
            selectedJob=job,
            contents=[content],
            works=[work],
            total_price=10000,
            error=None
        )

        assert mock_session.query.call_count == 4


# GET：Contentが0件
def test_detail_get_empty(client, authenticated):
    job = MagicMock(id=1)

    with patch("detail.views.session") as mock_session, \
         patch("detail.views.render_template") as mock_render:

        setup_get_queries(
            mock_session,
            job,
            [],
            [],
            None
        )

        mock_render.return_value = "DETAIL PAGE"

        response = client.get(
            "/detail/?selectedJobId=1"
        )

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["contents"] == []
        assert kwargs["works"] == []
        assert kwargs["total_price"] is None


# GET：合計金額
def test_detail_get_total_price(client, authenticated):
    job = MagicMock(id=1)

    with patch("detail.views.session") as mock_session, \
         patch("detail.views.render_template") as mock_render:

        setup_get_queries(
            mock_session,
            job,
            [MagicMock(), MagicMock()],
            [MagicMock()],
            30000
        )

        mock_render.return_value = "DETAIL PAGE"

        response = client.get(
            "/detail/?selectedJobId=1"
        )

        assert response.status_code == 200
        assert mock_render.call_args.kwargs[
            "total_price"
        ] == 30000


# POST：既存Contentの更新
def test_detail_post_update(client, authenticated):
    content = MagicMock()
    content.id = 10
    content.work_id = 1
    content.work_content = "変更前"

    work = MagicMock()
    work.id = 2

    with patch("detail.views.session") as mock_session:

        setup_post_queries(
            mock_session,
            [content],
            [work]
        )

        response = client.post("/detail/", data={
            "update_job_id": "1",
            "update_work[]": ["coding"],
            "update_content[]": ["変更後"]
        })

        assert response.status_code == 302

        assert content.work_id == 2
        assert content.work_content == "変更後"

        mock_session.add.assert_not_called()

        # 既存Contentの更新でもcommitが1回実行される
        mock_session.commit.assert_called_once()

# POST：新しいContentの追加
def test_detail_post_add(client, authenticated):
    work = MagicMock()
    work.id = 5

    with patch("detail.views.session") as mock_session:

        setup_post_queries(
            mock_session,
            [],
            [work]
        )

        response = client.post("/detail/", data={
            "update_job_id": "1",
            "new_work[]": ["design"],
            "new_content[]": ["デザイン制作"]
        })

        assert response.status_code == 302

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        added_content = mock_session.add.call_args.args[0]

        assert isinstance(added_content, Content)
        assert str(added_content.job_id) == "1"
        assert added_content.work_id == 5
        assert added_content.work_content == "デザイン制作"


# POST：空欄の作業内容をスキップ
def test_detail_post_empty_content(client, authenticated):
    with patch("detail.views.session") as mock_session:

        setup_post_queries(mock_session, [], [])

        response = client.post("/detail/", data={
            "update_job_id": "1",
            "new_work[]": ["design"],
            "new_content[]": ["   "]
        })

        assert response.status_code == 302

        mock_session.add.assert_not_called()
        # 現在のコードではcommit自体は実行される
        mock_session.commit.assert_called_once()


# POST：存在しない作業種別をスキップ
def test_detail_post_unknown_work(client, authenticated):
    with patch("detail.views.session") as mock_session:

        setup_post_queries(
            mock_session,
            [],
            [None]
        )

        response = client.post("/detail/", data={
            "update_job_id": "1",
            "new_work[]": ["unknown"],
            "new_content[]": ["テスト作業"]
        })

        assert response.status_code == 302

        mock_session.add.assert_not_called()
        mock_session.commit.assert_called_once()


# POST：更新画面へリダイレクト
def test_detail_post_redirect(client, authenticated):
    with patch("detail.views.session") as mock_session:

        setup_post_queries(mock_session, [], [])

        response = client.post("/detail/", data={
            "update_job_id": "1"
        })

        assert response.status_code == 302

        parsed_url = urlparse(response.location)
        assert parsed_url.path == "/update/"


# GET：未認証アクセス
def test_detail_login_required(client):
    with patch("detail.views.session") as mock_session:

        response = client.get(
            "/detail/?selectedJobId=1"
        )

        assert response.status_code == 302

        parsed_url = urlparse(response.location)
        assert parsed_url.path == "/login/"

        mock_session.query.assert_not_called()
