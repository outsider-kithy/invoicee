
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest

from models import Job, Client, Agency, Project, Tool, Account, Work, Content, Tax


@pytest.fixture
def authenticated():
    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value.is_authenticated = True
        yield mock_user


@pytest.fixture
def job_data():
    job = MagicMock(spec=Job)
    job.id = 1
    job.title = "Webサイト制作"
    job.tool_type_id = 1
    job.price = 100000
    job.created = "2026-11-09"
    job.agency_id = 10
    job.account_id = 20
    job.project_id = 30
    job.estimated = 0
    return job


def make_content(
    text="コーディング",
    price=30000,
    created="2026-11-09",
    tax_rate=10
):
    content = MagicMock(spec=Content)
    content.work_content = text
    content.created = created
    content.work = MagicMock(spec=Work)
    content.work.price = price
    content.work.tax_rate = MagicMock(spec=Tax)
    content.work.tax_rate.rate = tax_rate
    return content


def make_query(records):
    query = MagicMock()
    query.all.return_value = records
    query.filter.return_value.all.return_value = records
    return query


def setup_post_queries(mock_session, job, contents=None, tool=None):
    agency = MagicMock(spec=Agency)
    agency.agency_name = "テスト代理店"

    account = MagicMock(spec=Account)
    account.account_name = "テスト担当者"

    project = MagicMock(spec=Project)
    project.project_name = "テストプロジェクト"

    # 最初のJob検索
    queries = [make_query([job])]

    if job.tool_type_id in (1, 2, 3, 4):
        # Web系：Content検索
        queries.append(make_query(contents or []))
    else:
        # 紙媒体：Tool検索
        tool_query = MagicMock()
        tool_query.filter.return_value.first.return_value = tool
        queries.append(tool_query)

    # Agency検索：Job → Agency
    queries.extend([
        make_query([job]),
        make_query([agency]),
    ])

    # Account検索：Job → Account
    queries.extend([
        make_query([job]),
        make_query([account]),
    ])

    # Project検索：Job → Project
    queries.extend([
        make_query([job]),
        make_query([project]),
    ])

    mock_session.query.side_effect = queries


def test_estimate_get(client, authenticated):
    job = MagicMock(spec=Job)

    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.render_template") as mock_render:

        query = MagicMock()
        mock_session.query.return_value = query
        query.join.return_value = query
        query.filter.return_value.all.return_value = [job]
        mock_render.return_value = "ESTIMATE PAGE"

        response = client.get("/estimate/")

        assert response.status_code == 200
        mock_session.query.assert_called_once_with(Job)
        assert query.join.call_count == 3

        mock_render.assert_called_once_with(
            "estimate/index.html",
            jobs=[job]
        )


def test_estimate_get_empty(client, authenticated):
    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.render_template") as mock_render:

        query = MagicMock()
        mock_session.query.return_value = query
        query.join.return_value = query
        query.filter.return_value.all.return_value = []
        mock_render.return_value = "ESTIMATE PAGE"

        response = client.get("/estimate/")

        assert response.status_code == 200
        assert mock_render.call_args.kwargs["jobs"] == []


def test_estimate_post_web_job(client, authenticated, job_data):
    content = make_content()

    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        setup_post_queries(mock_session, job_data, [content])
        mock_excel.return_value = "EXCEL RESULT"

        response = client.post("/estimate/", data={
            "job": ["1"]
        })

        assert response.status_code == 200
        assert response.get_data(as_text=True) == "EXCEL RESULT"

        mock_excel.assert_called_once_with(
            [
                [
                    "Webサイト制作",
                    "コーディング",
                    30000,
                    "2026-11-09",
                    10
                ]
            ],
            "テスト代理店",
            "テスト担当者",
            "テストプロジェクト"
        )


def test_estimate_post_print_job(client, authenticated, job_data):
    job_data.title = "パンフレット制作"
    job_data.tool_type_id = 5
    job_data.price = 50000

    tool = MagicMock(spec=Tool)
    tool.tax_rate = MagicMock(spec=Tax)
    tool.tax_rate.rate = 10

    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        setup_post_queries(mock_session, job_data, tool=tool)
        mock_excel.return_value = "EXCEL RESULT"

        response = client.post("/estimate/", data={
            "job": ["1"]
        })

        assert response.status_code == 200

        args = mock_excel.call_args.args

        assert args[0] == [
            [
                "パンフレット制作",
                None,
                50000,
                "2026-11-09",
                10
            ]
        ]

        mock_session.commit.assert_called_once()


def test_estimate_post_multiple_contents(
    client, authenticated, job_data
):
    contents = [
        make_content("デザイン", 20000),
        make_content("コーディング", 30000),
    ]

    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        setup_post_queries(mock_session, job_data, contents)
        mock_excel.return_value = "EXCEL RESULT"

        response = client.post("/estimate/", data={
            "job": ["1"]
        })

        assert response.status_code == 200

        rows = mock_excel.call_args.args[0]

        assert len(rows) == 2
        assert rows[0][1] == "デザイン"
        assert rows[0][2] == 20000
        assert rows[1][1] == "コーディング"
        assert rows[1][2] == 30000


def test_estimate_post_no_contents(
    client, authenticated, job_data
):
    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        setup_post_queries(mock_session, job_data, [])
        mock_excel.return_value = "EXCEL RESULT"

        response = client.post("/estimate/", data={
            "job": ["1"]
        })

        assert response.status_code == 200

        # 現行実装ではContentがないと空リストになる
        assert mock_excel.call_args.args[0] == []


def test_estimate_post_mark_estimated(
    client, authenticated, job_data
):
    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        setup_post_queries(
            mock_session,
            job_data,
            [make_content()]
        )
        mock_excel.return_value = "EXCEL RESULT"

        client.post("/estimate/", data={"job": ["1"]})

        assert job_data.estimated == 1
        mock_session.commit.assert_called_once()


def test_estimate_post_recipient(
    client, authenticated, job_data
):
    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        setup_post_queries(
            mock_session,
            job_data,
            [make_content()]
        )
        mock_excel.return_value = "EXCEL RESULT"

        client.post("/estimate/", data={"job": ["1"]})

        args = mock_excel.call_args.args

        assert args[1] == "テスト代理店"
        assert args[2] == "テスト担当者"
        assert args[3] == "テストプロジェクト"


def test_estimate_post_excel_response(
    client, authenticated, job_data
):
    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        setup_post_queries(
            mock_session,
            job_data,
            [make_content()]
        )

        mock_excel.return_value = "TEST EXCEL RESPONSE"

        response = client.post("/estimate/", data={
            "job": ["1"]
        })

        assert response.get_data(as_text=True) == (
            "TEST EXCEL RESPONSE"
        )

        mock_excel.assert_called_once()
        mock_session.close.assert_called_once()


def test_estimate_post_multiple_jobs_current_behavior(
    client, authenticated, job_data
):
    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        setup_post_queries(
            mock_session,
            job_data,
            [make_content()]
        )
        mock_excel.return_value = "EXCEL RESULT"

        response = client.post("/estimate/", data={
            "job": ["1", "2"]
        })

        assert response.status_code == 200

        # 現行実装では最初のJobでreturnされる
        mock_excel.assert_called_once()
        mock_session.commit.assert_called_once()
        assert mock_session.query.call_count == 8


def test_estimate_login_required_get(client):
    with patch("estimate.views.session") as mock_session:

        response = client.get("/estimate/")

        assert response.status_code == 302
        assert urlparse(response.location).path == "/login/"

        mock_session.query.assert_not_called()


def test_estimate_login_required_post(client):
    with patch("estimate.views.session") as mock_session, \
         patch("estimate.views.writeExcel") as mock_excel:

        response = client.post("/estimate/", data={
            "job": ["1"]
        })

        assert response.status_code == 302
        assert urlparse(response.location).path == "/login/"

        mock_session.query.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_excel.assert_not_called()
