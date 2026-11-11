
import re
import uuid

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session

from models import Project, Client, Agency, Account


ADMIN_PATH = "/admin/"


# ============================================================
# 共通fixture
# ============================================================

@pytest.fixture
def project_db(e2e_config):
    """E2Eテスト専用DBへの接続を提供する。"""
    engine = create_engine(e2e_config["DATABASE_URL"])

    if engine.url.database != "invoicee_test":
        engine.dispose()
        pytest.fail(
            "テストDB以外への接続は禁止されています。"
        )

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def project_name():
    """テストごとに一意のプロジェクト名を生成する。"""
    return "E2E_Project_" + uuid.uuid4().hex[:12]


def create_test_project(
    db_engine,
    name,
    dependencies,
    isfinished=0
):
    """外部キーを設定してテスト用Projectを作成する。"""
    with Session(db_engine) as db:
        project = Project(
            project_name=name,
            client_id=dependencies["client_id"],
            agency_id=dependencies["agency_id"],
            account_id=dependencies["account_id"],
            isfinished=isfinished
        )

        db.add(project)
        db.commit()
        db.refresh(project)

        return project.id

@pytest.fixture
def test_project(
    project_db,
    project_name,
    project_dependencies
):
    project_id = create_test_project(
        project_db,
        project_name,
        project_dependencies,
        isfinished=0
    )

    try:
        yield {
            "id": project_id,
            "name": project_name,
        }

    finally:
        with Session(project_db) as db:
            db.execute(
                delete(Project).where(
                    Project.id == project_id
                )
            )
            db.commit()

@pytest.fixture
def two_test_projects(
    project_db,
    project_dependencies
):
    name_a = "E2E_Project_A_" + uuid.uuid4().hex[:12]
    name_b = "E2E_Project_B_" + uuid.uuid4().hex[:12]

    project_ids = []

    try:
        id_a = create_test_project(
            project_db,
            name_a,
            project_dependencies
        )
        project_ids.append(id_a)

        id_b = create_test_project(
            project_db,
            name_b,
            project_dependencies
        )
        project_ids.append(id_b)

        yield {
            "a": {"id": id_a, "name": name_a},
            "b": {"id": id_b, "name": name_b},
        }

    finally:
        with Session(project_db) as db:
            if project_ids:
                db.execute(
                    delete(Project).where(
                        Project.id.in_(project_ids)
                    )
                )
                db.commit()

@pytest.fixture
def project_dependencies(project_db):
    """
    Projectの外部キーに必要な
    Client、Agency、Accountを作成する。
    """
    unique_id = uuid.uuid4().hex[:12]

    with Session(project_db) as db:
        client = Client(
            client_name=f"E2E_Client_{unique_id}"
        )

        agency = Agency(
            agency_name=f"E2E_Agency_{unique_id}"
        )

        db.add_all([client, agency])
        db.flush()

        account = Account(
            account_name=f"E2E_Account_{unique_id}",
            agency_id=agency.id
        )

        db.add(account)
        db.flush()

        data = {
            "client_id": client.id,
            "agency_id": agency.id,
            "account_id": account.id,
        }

        db.commit()

    try:
        yield data

    finally:
        with Session(project_db) as db:
            # Projectの削除後に関連レコードを削除
            db.execute(
                delete(Account).where(
                    Account.id == data["account_id"]
                )
            )
            db.execute(
                delete(Agency).where(
                    Agency.id == data["agency_id"]
                )
            )
            db.execute(
                delete(Client).where(
                    Client.id == data["client_id"]
                )
            )
            db.commit()

			
# ============================================================
# 共通関数
# ============================================================

def finish_project(page, base_url, project_name):
    page.goto(f"{base_url}{ADMIN_PATH}")

    page.locator(
        'input[name="finished_project"]'
        f'[value="{project_name}"]'
    ).check()

    page.locator(
        "form.record input[type='submit']"
    ).click()


def get_project(db_engine, project_id):
    """DBから指定したプロジェクトを取得する。"""
    with Session(db_engine) as db:
        return db.execute(
            select(Project).where(
                Project.id == project_id
            )
        ).scalar_one_or_none()


def get_project_status(db_engine, project_id):
    """DBからプロジェクトの終了状態を取得する。"""
    project = get_project(db_engine, project_id)

    if project is None:
        return None

    return project.isfinished


def submit_empty_form(page, base_url):
    """管理画面のフォームを未入力で送信する。"""
    page.goto(f"{base_url}{ADMIN_PATH}")

    page.locator(
        "form.record input[type='submit']"
    ).click()


# ============================================================
# FINISH-E2E-001
# 管理画面の表示
# ============================================================

def test_finish_project_page_display(
    auth_page: Page,
    e2e_server,
    test_project
):
    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    expect(
        auth_page.locator(
            'input[name="finished_project"]'
            f'[value="{test_project["name"]}"]'
        )
    ).to_be_visible()


# ============================================================
# FINISH-E2E-002
# プロジェクト終了処理
# ============================================================

def test_finish_project_success(
    auth_page: Page,
    e2e_server,
    project_db,
    test_project
):
    # 終了前は0
    assert get_project_status(
        project_db,
        test_project["id"]
    ) == 0

    finish_project(
        auth_page,
        e2e_server,
        test_project["name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    # 終了後は1
    assert get_project_status(
        project_db,
        test_project["id"]
    ) == 1


# ============================================================
# FINISH-E2E-003
# 終了後のリダイレクト
# ============================================================

def test_finish_project_redirect(
    auth_page: Page,
    e2e_server,
    test_project
):
    finish_project(
        auth_page,
        e2e_server,
        test_project["name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )


# ============================================================
# FINISH-E2E-004
# 終了済みプロジェクトの非表示
# ============================================================

def test_finished_project_not_displayed(
    auth_page: Page,
    e2e_server,
    test_project
):
    finish_project(
        auth_page,
        e2e_server,
        test_project["name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    # 管理画面を再表示
    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(
        auth_page.locator(
            'input[name="finished_project"]'
            f'[value="{test_project["name"]}"]'
        )
    ).to_have_count(0)


# ============================================================
# FINISH-E2E-005
# 複数プロジェクトの独立性
# ============================================================

def test_finish_only_selected_project(
    auth_page: Page,
    e2e_server,
    project_db,
    two_test_projects
):
    project_a = two_test_projects["a"]
    project_b = two_test_projects["b"]

    finish_project(
        auth_page,
        e2e_server,
        project_a["name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    # Aだけ終了している
    assert get_project_status(
        project_db,
        project_a["id"]
    ) == 1

    # Bは未終了のまま
    assert get_project_status(
        project_db,
        project_b["id"]
    ) == 0


# ============================================================
# FINISH-E2E-006
# プロジェクト未選択時のエラー
# ============================================================

def test_finish_project_empty_submission(
    auth_page: Page,
    e2e_server,
    project_db,
    test_project
):
    submit_empty_form(auth_page, e2e_server)

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    assert get_project_status(
        project_db,
        test_project["id"]
    ) == 0


# ============================================================
# FINISH-E2E-007
# 存在しないプロジェクトの指定
# ============================================================

def test_finish_nonexistent_project(
    auth_page: Page,
    e2e_server,
    project_db,
    test_project
):
    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    # 存在しないプロジェクト名をPOSTする
    response = auth_page.request.post(
        f"{e2e_server}{ADMIN_PATH}",
        form={
            "finished_project":
                "E2E_NotFound_" + uuid.uuid4().hex
        },
        max_redirects=0
    )

    assert response.status == 302
    assert response.headers["location"].endswith(
        ADMIN_PATH
    )

    # 既存のプロジェクトは変更されない
    assert get_project_status(
        project_db,
        test_project["id"]
    ) == 0


# ============================================================
# FINISH-E2E-008
# 未ログイン時のアクセス制限
# ============================================================

def test_finish_project_requires_login(
    page: Page,
    e2e_server
):
    page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )
