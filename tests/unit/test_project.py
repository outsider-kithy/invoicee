
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest

from models import Project


# 認証済みユーザーを再現
@pytest.fixture
def authenticated():
    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value.is_authenticated = True
        yield mock_user


# 正常なPOSTフォームデータ
@pytest.fixture
def valid_form():
    return {
        "project": "テストプロジェクト",
        "projectClientName": "テストクライアント",
        "projectAgencyId": "2",
        "projectAccountName": "テスト担当者"
    }


# テスト用レコードを作成
def create_mock_records():
    client = MagicMock()
    client.id = 1

    agency = MagicMock()
    agency.id = 2

    account = MagicMock()
    account.id = 3

    return client, agency, account


# GET用のクエリをモック化
def setup_get_queries(mock_session, clients, agencys, accounts):
    client_query = MagicMock()
    agency_query = MagicMock()
    account_query = MagicMock()

    mock_session.query.side_effect = [
        client_query,
        agency_query,
        account_query
    ]

    client_query.all.return_value = clients
    agency_query.all.return_value = agencys
    account_query.all.return_value = accounts


# POST用のクエリをモック化
def setup_post_queries(mock_session, agency, client=None, account=None):
    agency_query = MagicMock()
    client_query = MagicMock()
    account_query = MagicMock()

    agency_query.filter.return_value.first.return_value = agency
    client_query.filter.return_value.first.return_value = client
    account_query.filter.return_value.first.return_value = account

    mock_session.query.side_effect = [
        agency_query,
        client_query,
        account_query
    ]


# GET：プロジェクト登録画面の表示
def test_project_get(client, authenticated):
    mock_client, mock_agency, mock_account = create_mock_records()

    with patch("project.views.session") as mock_session, \
         patch("project.views.render_template") as mock_render:

        setup_get_queries(
            mock_session,
            [mock_client],
            [mock_agency],
            [mock_account]
        )

        mock_render.return_value = "PROJECT PAGE"

        response = client.get("/project/")

        assert response.status_code == 200

        mock_render.assert_called_once_with(
            "project/index.html",
            clients=[mock_client],
            agencys=[mock_agency],
            accounts=[mock_account]
        )

        assert mock_session.query.call_count == 3


# GET：各テーブルのレコードが0件
def test_project_get_empty(client, authenticated):
    with patch("project.views.session") as mock_session, \
         patch("project.views.render_template") as mock_render:

        setup_get_queries(mock_session, [], [], [])

        mock_render.return_value = "PROJECT PAGE"

        response = client.get("/project/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["clients"] == []
        assert kwargs["agencys"] == []
        assert kwargs["accounts"] == []


# POST：正常なProject登録
def test_project_post_success(client, authenticated, valid_form):
    mock_client, mock_agency, mock_account = create_mock_records()

    with patch("project.views.session") as mock_session:

        setup_post_queries(
            mock_session,
            mock_agency,
            mock_client,
            mock_account
        )

        response = client.post("/project/", data=valid_form)

        assert response.status_code == 302
        assert urlparse(response.location).path == "/top/"

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        added_project = mock_session.add.call_args.args[0]

        assert isinstance(added_project, Project)
        assert added_project.project_name == "テストプロジェクト"
        assert added_project.client_id == 1
        assert str(added_project.agency_id) == "2"
        assert added_project.account_id == 3
        assert added_project.isfinished == 0


# POST：プロジェクト名が未入力
def test_project_post_empty_name(client, authenticated, valid_form):
    valid_form["project"] = ""

    _, mock_agency, _ = create_mock_records()

    with patch("project.views.session") as mock_session, \
         patch("project.views.flash") as mock_flash:

        setup_post_queries(mock_session, mock_agency)

        response = client.post("/project/", data=valid_form)

        assert response.status_code == 302
        assert urlparse(response.location).path == "/project/"

        mock_flash.assert_called_once_with(
            "プロジェクト名が入力されていません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：クライアント名が未選択
def test_project_post_empty_client(client, authenticated, valid_form):
    valid_form["projectClientName"] = ""

    _, mock_agency, _ = create_mock_records()

    with patch("project.views.session") as mock_session, \
         patch("project.views.flash") as mock_flash:

        setup_post_queries(mock_session, mock_agency)

        response = client.post("/project/", data=valid_form)

        assert response.status_code == 302
        assert urlparse(response.location).path == "/project/"

        mock_flash.assert_called_once_with(
            "クライアント名が選択されていません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：代理店が存在しない
def test_project_post_empty_agency(client, authenticated, valid_form):
    with patch("project.views.session") as mock_session, \
         patch("project.views.flash") as mock_flash:

        setup_post_queries(mock_session, None)

        response = client.post("/project/", data=valid_form)

        assert response.status_code == 302
        assert urlparse(response.location).path == "/project/"

        mock_flash.assert_called_once_with(
            "代理店名が入力されていません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：担当者名が未入力
def test_project_post_empty_account(client, authenticated, valid_form):
    valid_form["projectAccountName"] = ""

    _, mock_agency, _ = create_mock_records()

    with patch("project.views.session") as mock_session, \
         patch("project.views.flash") as mock_flash:

        setup_post_queries(mock_session, mock_agency)

        response = client.post("/project/", data=valid_form)

        assert response.status_code == 302
        assert urlparse(response.location).path == "/project/"

        mock_flash.assert_called_once_with(
            "担当者名が入力されていません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：代理店IDが空文字列
def test_project_post_optional_agency_id(
    client, authenticated, valid_form
):
    valid_form["projectAgencyId"] = ""

    with patch("project.views.session") as mock_session, \
         patch("project.views.flash") as mock_flash:

        setup_post_queries(mock_session, None)

        response = client.post("/project/", data=valid_form)

        assert response.status_code == 302
        assert urlparse(response.location).path == "/project/"

        mock_flash.assert_called_once_with(
            "代理店名が入力されていません"
        )

        mock_session.add.assert_not_called()


# POST：登録後のリダイレクト
def test_project_post_redirect(client, authenticated, valid_form):
    mock_client, mock_agency, mock_account = create_mock_records()

    with patch("project.views.session") as mock_session:

        setup_post_queries(
            mock_session,
            mock_agency,
            mock_client,
            mock_account
        )

        response = client.post("/project/", data=valid_form)

        assert response.status_code == 302
        assert urlparse(response.location).path == "/top/"

        mock_session.commit.assert_called_once()


# GET：未認証ユーザーのアクセス
def test_project_login_required(client):
    with patch("project.views.session") as mock_session:

        response = client.get("/project/")

        assert response.status_code == 302
        assert urlparse(response.location).path == "/login/"

        mock_session.query.assert_not_called()
