
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest

from models import Client, Agency, Account, Tool, Project


# 認証済みユーザーを再現
@pytest.fixture
def authenticated():
    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value.is_authenticated = True
        yield mock_user


# GETのクエリをモック化
def setup_get_queries(
    mock_session,
    clients,
    agencys,
    accounts,
    taxes,
    projects
):
    queries = [MagicMock() for _ in range(5)]

    mock_session.query.side_effect = queries

    queries[0].all.return_value = clients
    queries[1].all.return_value = agencys
    queries[2].all.return_value = accounts
    queries[3].all.return_value = taxes

    queries[4].filter.return_value.all.return_value = projects


# POSTでfilter().first()をモック化
def setup_post_query(mock_session, record):
    query = MagicMock()
    query.filter.return_value.first.return_value = record

    mock_session.query.return_value = query


# POST成功時の共通検証
def assert_post_success(response, mock_session):
    assert response.status_code == 302
    assert urlparse(response.location).path == "/top/"

    mock_session.commit.assert_called_once()


# GET：管理画面の表示
def test_admin_get(client, authenticated):
    mock_client = MagicMock()
    mock_agency = MagicMock()
    mock_account = MagicMock()
    mock_tax = MagicMock()
    mock_project = MagicMock()

    with patch("admin.views.session") as mock_session, \
         patch("admin.views.render_template") as mock_render:

        setup_get_queries(
            mock_session,
            [mock_client],
            [mock_agency],
            [mock_account],
            [mock_tax],
            [mock_project]
        )

        mock_render.return_value = "ADMIN PAGE"

        response = client.get("/admin/")

        assert response.status_code == 200

        mock_render.assert_called_once_with(
            "admin/index.html",
            clients=[mock_client],
            agencys=[mock_agency],
            accounts=[mock_account],
            taxes=[mock_tax],
            projects=[mock_project]
        )

        assert mock_session.query.call_count == 5


# GET：各テーブルが0件
def test_admin_get_empty(client, authenticated):
    with patch("admin.views.session") as mock_session, \
         patch("admin.views.render_template") as mock_render:

        setup_get_queries(
            mock_session, [], [], [], [], []
        )

        mock_render.return_value = "ADMIN PAGE"

        response = client.get("/admin/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["clients"] == []
        assert kwargs["agencys"] == []
        assert kwargs["accounts"] == []
        assert kwargs["taxes"] == []
        assert kwargs["projects"] == []


# POST：Clientの新規登録
def test_admin_post_client(client, authenticated):
    with patch("admin.views.session") as mock_session:

        response = client.post("/admin/", data={
            "client": "テストクライアント"
        })

        assert_post_success(response, mock_session)

        mock_session.add.assert_called_once()
        mock_session.query.assert_not_called()

        added = mock_session.add.call_args.args[0]

        assert isinstance(added, Client)
        assert added.client_name == "テストクライアント"


# POST：Agencyの新規登録
def test_admin_post_agency(client, authenticated):
    with patch("admin.views.session") as mock_session:

        response = client.post("/admin/", data={
            "agency": "テスト代理店"
        })

        assert_post_success(response, mock_session)

        mock_session.add.assert_called_once()
        mock_session.query.assert_not_called()

        added = mock_session.add.call_args.args[0]

        assert isinstance(added, Agency)
        assert added.agency_name == "テスト代理店"


# POST：Accountの新規登録
def test_admin_post_account(client, authenticated):
    agency = MagicMock()
    agency.id = 10

    with patch("admin.views.session") as mock_session:

        setup_post_query(mock_session, agency)

        response = client.post("/admin/", data={
            "account": "テスト担当者",
            "agencyName": "テスト代理店"
        })

        assert_post_success(response, mock_session)

        mock_session.query.assert_called_once_with(Agency)
        mock_session.add.assert_called_once()

        added = mock_session.add.call_args.args[0]

        assert isinstance(added, Account)
        assert added.account_name == "テスト担当者"
        assert added.agency_id == 10


# POST：Toolの新規登録
def test_admin_post_tool(client, authenticated):
    tax = MagicMock()
    tax.id = 3

    with patch("admin.views.session") as mock_session:

        setup_post_query(mock_session, tax)

        response = client.post("/admin/", data={
            "tool": "HTML",
            "price": "10000",
            "tax": "10"
        })

        assert_post_success(response, mock_session)

        mock_session.add.assert_called_once()

        added = mock_session.add.call_args.args[0]

        assert isinstance(added, Tool)
        assert added.tool_type == "HTML"
        assert str(added.price) == "10000"
        assert added.tax_rate_id == 3


# POST：Projectの終了処理
def test_admin_post_finish_project(client, authenticated):
    project = MagicMock()
    project.id = 5
    project.isfinished = 0

    with patch("admin.views.session") as mock_session:

        setup_post_query(mock_session, project)

        response = client.post("/admin/", data={
            "finished_project": "テストプロジェクト"
        })

        assert_post_success(response, mock_session)

        assert project.isfinished == 1

        # 既存レコードの更新なのでadd()は不要
        mock_session.add.assert_not_called()
        mock_session.query.assert_called_once_with(Project)


# POST：入力項目がすべて空欄
def test_admin_post_empty(client, authenticated):
    with patch("admin.views.session") as mock_session, \
         patch("admin.views.flash") as mock_flash, \
         patch("admin.views.render_template") as mock_render:

        mock_render.return_value = "ADMIN ERROR PAGE"

        response = client.post("/admin/", data={})

        assert response.status_code == 302
        assert urlparse(response.location).path == "/admin/"
        mock_flash.assert_called_once_with("何も入力されていません")

        mock_session.query.assert_not_called()
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：複数項目の優先順位
def test_admin_post_priority(client, authenticated):
    with patch("admin.views.session") as mock_session:

        response = client.post("/admin/", data={
            "client": "テストクライアント",
            "agency": "テスト代理店",
            "account": "テスト担当者",
            "tool": "HTML",
            "finished_project": "テストプロジェクト"
        })

        assert_post_success(response, mock_session)

        # if / elifなのでClientだけ登録される
        mock_session.add.assert_called_once()

        added = mock_session.add.call_args.args[0]

        assert isinstance(added, Client)
        assert added.client_name == "テストクライアント"

        mock_session.query.assert_not_called()


# POST：登録後のリダイレクト
def test_admin_post_redirect(client, authenticated):
    with patch("admin.views.session") as mock_session:

        response = client.post("/admin/", data={
            "client": "テストクライアント"
        })

        assert response.status_code == 302
        assert urlparse(response.location).path == "/top/"

        assert mock_session.commit.call_count == 1


# GET：未認証アクセス
def test_admin_login_required_get(client):
    with patch("admin.views.session") as mock_session:

        response = client.get("/admin/")

        assert response.status_code == 302
        assert urlparse(response.location).path == "/login/"

        mock_session.query.assert_not_called()


# POST：未認証アクセス
def test_admin_login_required_post(client):
    with patch("admin.views.session") as mock_session:

        response = client.post("/admin/", data={
            "client": "不正登録テスト"
        })

        assert response.status_code == 302
        assert urlparse(response.location).path == "/login/"

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
