
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

import pytest

from models import Job, Project, Tool


# ログイン済みユーザーを再現
@pytest.fixture
def authenticated():
    with patch("flask_login.utils._get_user") as mock_user:
        mock_user.return_value.is_authenticated = True
        yield mock_user


# POSTで使用するフォームデータ
@pytest.fixture
def valid_form():
    return {
        "title": "コーポレートサイト制作",
        "project": "テストプロジェクト",
        "tool": "HTML",
        "github_repository": "https://github.com/example/test"
    }



def setup_post_queries(mock_session, tool, project):
    # 1回目：ツール名からToolを取得
    tool_query = MagicMock()
    tool_query.filter.return_value.first.return_value = tool

    # 2回目：プロジェクト名からProjectを取得
    project_query = MagicMock()
    project_query.filter.return_value.first.return_value = project

    mock_session.query.side_effect = [
        tool_query,
        project_query
    ]

# テスト用ToolとProjectを作成
def create_mock_records():
    tool = MagicMock(spec=Tool)
    tool.id = 2
    tool.price = 10000

    project = MagicMock(spec=Project)
    project.id = 5
    project.client_id = 10
    project.agency_id = 20
    project.account_id = 30

    return tool, project


# GET：登録画面の表示
def test_record_get(client, authenticated):
    project = MagicMock(spec=Project)
    tool = MagicMock(spec=Tool)

    with patch("record.views.session") as mock_session, \
         patch("record.views.render_template") as mock_render:

        project_query = MagicMock()
        tool_query = MagicMock()

        mock_session.query.side_effect = [
            project_query,
            tool_query
        ]

        project_query.filter.return_value.all.return_value = [
            project
        ]
        tool_query.all.return_value = [tool]

        mock_render.return_value = "RECORD PAGE"

        response = client.get("/record/")

        assert response.status_code == 200

        mock_render.assert_called_once_with(
            "record/index.html",
            projects=[project],
            tools=[tool]
        )

        assert mock_session.query.call_count == 2


# GET：プロジェクト・ツールが0件
def test_record_get_empty(client, authenticated):
    with patch("record.views.session") as mock_session, \
         patch("record.views.render_template") as mock_render:

        project_query = MagicMock()
        tool_query = MagicMock()

        mock_session.query.side_effect = [
            project_query,
            tool_query
        ]

        project_query.filter.return_value.all.return_value = []
        tool_query.all.return_value = []

        mock_render.return_value = "RECORD PAGE"

        response = client.get("/record/")

        assert response.status_code == 200

        kwargs = mock_render.call_args.kwargs

        assert kwargs["projects"] == []
        assert kwargs["tools"] == []


# POST：Jobの正常登録
def test_record_post_success(client, authenticated, valid_form):
    tool, project = create_mock_records()

    with patch("record.views.session") as mock_session:

        setup_post_queries(
            mock_session,
            tool,
            project
        )

        response = client.post(
            "/record/",
            data=valid_form
        )

        assert response.status_code == 302
        assert urlparse(response.location).path == "/top/"

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        added_job = mock_session.add.call_args.args[0]

        assert isinstance(added_job, Job)

        assert added_job.title == "コーポレートサイト制作"
        assert added_job.tool_type_id == 2
        assert added_job.client_id == 10
        assert added_job.agency_id == 20
        assert added_job.account_id == 30
        assert added_job.project_id == 5
        assert added_job.price == 10000
        assert added_job.estimated == 0
        assert added_job.invoiced == 0
        assert added_job.github_repository == (
            "https://github.com/example/test"
        )


# POST：タイトル未入力
def test_record_post_empty_title(
    client, authenticated, valid_form
):
    valid_form["title"] = ""

    with patch("record.views.session") as mock_session, \
         patch("record.views.flash") as mock_flash:

        response = client.post(
            "/record/",
            data=valid_form
        )

        assert response.status_code == 302
        assert urlparse(response.location).path == "/record/"

        mock_flash.assert_called_once_with(
            "タイトルが入力されていません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.query.assert_not_called()


# POST：プロジェクト未選択
def test_record_post_empty_project(
    client, authenticated, valid_form
):
    valid_form["project"] = ""

    with patch("record.views.session") as mock_session, \
         patch("record.views.flash") as mock_flash:

        response = client.post(
            "/record/",
            data=valid_form
        )

        assert response.status_code == 302
        assert urlparse(response.location).path == "/record/"

        mock_flash.assert_called_once_with(
            "プロジェクト名が選択されていません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：ツール未選択
def test_record_post_empty_tool(
    client, authenticated, valid_form
):
    valid_form["tool"] = ""

    with patch("record.views.session") as mock_session, \
         patch("record.views.flash") as mock_flash:

        response = client.post(
            "/record/",
            data=valid_form
        )

        assert response.status_code == 302
        assert urlparse(response.location).path == "/record/"

        mock_flash.assert_called_once_with(
            "ツール名が選択されていません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()


# POST：GitHub URLが空欄でも登録できる
def test_record_post_optional_github(
    client, authenticated, valid_form
):
    valid_form["github_repository"] = ""

    tool, project = create_mock_records()

    with patch("record.views.session") as mock_session:

        setup_post_queries(
            mock_session,
            tool,
            project
        )

        response = client.post(
            "/record/",
            data=valid_form
        )

        assert response.status_code == 302

        added_job = mock_session.add.call_args.args[0]

        assert added_job.github_repository == ""
        mock_session.commit.assert_called_once()


# POST：同名プロジェクトが複数ある場合
def test_record_post_multiple_projects(
    client, authenticated, valid_form
):
    tool, project1 = create_mock_records()

    with patch("record.views.session") as mock_session:

        setup_post_queries(
            mock_session,
            tool,
            project1
        )

        response = client.post(
            "/record/",
            data=valid_form
        )

        assert response.status_code == 302

        # Jobは1件だけ登録される
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        added_job = mock_session.add.call_args.args[0]

        assert added_job.project_id == project1.id

# Toolが存在しない場合
def test_record_post_unknown_tool(
    client, authenticated, valid_form
):
    with patch("record.views.session") as mock_session, \
         patch("record.views.flash") as mock_flash:

        setup_post_queries(
            mock_session,
            None,
            None
        )

        response = client.post(
            "/record/",
            data=valid_form
        )

        assert response.status_code == 302
        assert urlparse(response.location).path == "/record/"

        mock_flash.assert_called_once_with(
            "指定されたツールが存在しません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        assert mock_session.query.call_count == 1

# Projectが存在しない場合
def test_record_post_unknown_project(
    client, authenticated, valid_form
):
    tool, _ = create_mock_records()

    with patch("record.views.session") as mock_session, \
         patch("record.views.flash") as mock_flash:

        setup_post_queries(
            mock_session,
            tool,
            None
        )

        response = client.post(
            "/record/",
            data=valid_form
        )

        assert response.status_code == 302
        assert urlparse(response.location).path == "/record/"

        mock_flash.assert_called_once_with(
            "指定されたプロジェクトが存在しません"
        )

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        assert mock_session.query.call_count == 2

# GET：未ログインユーザーのアクセス
def test_record_login_required(client):
    with patch("record.views.session") as mock_session:

        response = client.get("/record/")

        assert response.status_code == 302

        parsed_url = urlparse(response.location)
        assert parsed_url.path == "/login/"

        mock_session.query.assert_not_called()