
import re
import uuid

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session

from models import (
    Client,
    Agency,
    Account,
    Project,
    Tool,
    Tax,
    Job,
)


RECORD_PATH = "/record/"
TEST_PRICE = 12000


# ============================================================
# 共通fixture
# ============================================================

@pytest.fixture
def job_db(e2e_config):
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
def job_title():
    """テストごとに一意のジョブタイトルを生成する。"""
    return "E2E_Job_" + uuid.uuid4().hex[:12]


@pytest.fixture
def job_dependencies(job_db):
    """
    Job登録に必要な関連データを作成する。

    Client
    Agency
    Account
    Project
    Tool
    Tax

    テスト終了後に関連データを削除する。
    """
    unique_id = uuid.uuid4().hex[:12]

    created_tax_id = None
    data = None

    with Session(job_db) as db:

        # 税率を取得。存在しなければ作成
        tax = db.execute(
            select(Tax).order_by(Tax.id)
        ).scalars().first()

        if tax is None:
            tax = Tax(rate="0.10")
            db.add(tax)
            db.flush()
            created_tax_id = tax.id

        # 顧客と代理店
        client = Client(
            client_name=f"E2E_Client_{unique_id}"
        )

        agency = Agency(
            agency_name=f"E2E_Agency_{unique_id}"
        )

        db.add_all([client, agency])
        db.flush()

        # 担当者
        account = Account(
            account_name=f"E2E_Account_{unique_id}",
            agency_id=agency.id
        )

        db.add(account)
        db.flush()

        # プロジェクト
        project = Project(
            project_name=f"E2E_Project_{unique_id}",
            client_id=client.id,
            agency_id=agency.id,
            account_id=account.id,
            isfinished=0
        )

        # ツール
        tool = Tool(
            tool_type=f"E2E_Tool_{unique_id}",
            price=TEST_PRICE,
            tax_rate_id=tax.id
        )

        db.add_all([project, tool])
        db.flush()

        data = {
            "client_id": client.id,
            "agency_id": agency.id,
            "account_id": account.id,
            "project_id": project.id,
            "project_name": project.project_name,
            "tool_id": tool.id,
            "tool_name": tool.tool_type,
            "tool_price": tool.price,
            "tax_id": tax.id,
        }

        db.commit()

    try:
        yield data

    finally:
        with Session(job_db) as db:

            # 外部キーの参照元から順に削除
            db.execute(
                delete(Job).where(
                    Job.project_id == data["project_id"]
                )
            )

            db.execute(
                delete(Project).where(
                    Project.id == data["project_id"]
                )
            )

            db.execute(
                delete(Tool).where(
                    Tool.id == data["tool_id"]
                )
            )

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

            if created_tax_id is not None:
                db.execute(
                    delete(Tax).where(
                        Tax.id == created_tax_id
                    )
                )

            db.commit()


# ============================================================
# 共通関数
# ============================================================

def register_job(
    page,
    base_url,
    title,
    project_name=None,
    tool_name=None,
    github_repository=""
):
    """ブラウザからジョブを登録する。"""
    page.goto(f"{base_url}{RECORD_PATH}")

    page.locator("#title").fill(title)

    if project_name is not None:
        page.locator("#project").select_option(
            value=project_name
        )

    if tool_name is not None:
        page.locator("#tool").select_option(
            value=tool_name
        )

    page.locator(
        'input[name="github_repository"]'
    ).fill(github_repository)

    page.locator(
        "form.record input[type='submit']"
    ).click()


def get_job(db_engine, title):
    """タイトルを指定してJobを取得する。"""
    with Session(db_engine) as db:
        return db.execute(
            select(Job).where(
                Job.title == title
            )
        ).scalar_one_or_none()


def count_jobs_by_title(db_engine, title):
    """指定したタイトルのJob件数を取得する。"""
    with Session(db_engine) as db:
        return len(
            db.execute(
                select(Job.id).where(
                    Job.title == title
                )
            ).all()
        )


# ============================================================
# JOB-E2E-001
# 登録画面の表示
# ============================================================

def test_job_page_display(
    auth_page: Page,
    e2e_server
):
    auth_page.goto(f"{e2e_server}{RECORD_PATH}")

    expect(auth_page).to_have_url(
        f"{e2e_server}{RECORD_PATH}"
    )

    expect(
        auth_page.locator("#title")
    ).to_be_visible()

    expect(
        auth_page.locator("#project")
    ).to_be_visible()

    expect(
        auth_page.locator("#tool")
    ).to_be_visible()

    expect(
        auth_page.locator(
            'input[name="github_repository"]'
        )
    ).to_be_visible()


# ============================================================
# JOB-E2E-002
# ジョブの新規登録
# ============================================================

def test_job_registration(
    auth_page: Page,
    e2e_server,
    job_db,
    job_title,
    job_dependencies
):
    register_job(
        auth_page,
        e2e_server,
        job_title,
        job_dependencies["project_name"],
        job_dependencies["tool_name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    job = get_job(job_db, job_title)

    assert job is not None
    assert job.id is not None
    assert job.title == job_title


# ============================================================
# JOB-E2E-003
# プロジェクトとの紐づけ
# ============================================================

def test_job_project_relationship(
    auth_page: Page,
    e2e_server,
    job_db,
    job_title,
    job_dependencies
):
    register_job(
        auth_page,
        e2e_server,
        job_title,
        job_dependencies["project_name"],
        job_dependencies["tool_name"]
    )

    job = get_job(job_db, job_title)

    assert job is not None
    assert job.project_id == job_dependencies["project_id"]


# ============================================================
# JOB-E2E-004
# 顧客・代理店・担当者との紐づけ
# ============================================================

def test_job_related_entities(
    auth_page: Page,
    e2e_server,
    job_db,
    job_title,
    job_dependencies
):
    register_job(
        auth_page,
        e2e_server,
        job_title,
        job_dependencies["project_name"],
        job_dependencies["tool_name"]
    )

    job = get_job(job_db, job_title)

    assert job is not None

    assert job.client_id == job_dependencies["client_id"]
    assert job.agency_id == job_dependencies["agency_id"]
    assert job.account_id == job_dependencies["account_id"]


# ============================================================
# JOB-E2E-005
# ツールと価格の引き継ぎ
# ============================================================

def test_job_tool_and_price(
    auth_page: Page,
    e2e_server,
    job_db,
    job_title,
    job_dependencies
):
    register_job(
        auth_page,
        e2e_server,
        job_title,
        job_dependencies["project_name"],
        job_dependencies["tool_name"]
    )

    job = get_job(job_db, job_title)

    assert job is not None

    assert job.tool_type_id == job_dependencies["tool_id"]
    assert job.price == job_dependencies["tool_price"]


# ============================================================
# JOB-E2E-006
# ステータスの初期値
# ============================================================

def test_job_initial_status(
    auth_page: Page,
    e2e_server,
    job_db,
    job_title,
    job_dependencies
):
    register_job(
        auth_page,
        e2e_server,
        job_title,
        job_dependencies["project_name"],
        job_dependencies["tool_name"]
    )

    job = get_job(job_db, job_title)

    assert job is not None
    assert job.estimated == 0
    assert job.invoiced == 0


# ============================================================
# JOB-E2E-007
# GitHubリポジトリの保存
# ============================================================

def test_job_github_repository(
    auth_page: Page,
    e2e_server,
    job_db,
    job_title,
    job_dependencies
):
    repository = "outsider-kithy/e2e-test-repository"

    register_job(
        auth_page,
        e2e_server,
        job_title,
        job_dependencies["project_name"],
        job_dependencies["tool_name"],
        github_repository=repository
    )

    job = get_job(job_db, job_title)

    assert job is not None
    assert job.github_repository == repository


# ============================================================
# JOB-E2E-008
# 登録後のリダイレクト
# ============================================================

def test_job_registration_redirect(
    auth_page: Page,
    e2e_server,
    job_title,
    job_dependencies
):
    register_job(
        auth_page,
        e2e_server,
        job_title,
        job_dependencies["project_name"],
        job_dependencies["tool_name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )


# ============================================================
# JOB-E2E-009
# プロジェクト未選択
# ============================================================

def test_job_without_project(
    auth_page: Page,
    e2e_server,
    job_db,
    job_title,
    job_dependencies
):
    register_job(
        auth_page,
        e2e_server,
        job_title,
        project_name=None,
        tool_name=job_dependencies["tool_name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}{RECORD_PATH}"
    )

    assert count_jobs_by_title(job_db, job_title) == 0


# ============================================================
# JOB-E2E-010
# ツール未選択
# ============================================================

def test_job_without_tool(
    auth_page: Page,
    e2e_server,
    job_db,
    job_title,
    job_dependencies
):
    register_job(
        auth_page,
        e2e_server,
        job_title,
        project_name=job_dependencies["project_name"],
        tool_name=None
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}{RECORD_PATH}"
    )

    assert count_jobs_by_title(job_db, job_title) == 0


# ============================================================
# JOB-E2E-011
# 終了済みプロジェクトの非表示
# ============================================================

def test_finished_project_not_selectable(
    auth_page: Page,
    e2e_server,
    job_db,
    job_dependencies
):
    project_id = job_dependencies["project_id"]

    # テスト用プロジェクトを終了状態にする
    with Session(job_db) as db:
        project = db.get(Project, project_id)
        project.isfinished = 1
        db.commit()

    auth_page.goto(f"{e2e_server}{RECORD_PATH}")

    expect(
        auth_page.locator(
            "#project option"
        ).filter(
            has_text=job_dependencies["project_name"]
        )
    ).to_have_count(0)


# ============================================================
# JOB-E2E-012
# 未ログイン時のアクセス制限
# ============================================================

def test_job_page_requires_login(
    page: Page,
    e2e_server
):
    page.goto(f"{e2e_server}{RECORD_PATH}")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )


# ============================================================
# JOB-E2E-013
# タイトル未入力時のブラウザ検証
# ============================================================

def test_job_title_required(
    auth_page: Page,
    e2e_server,
    job_dependencies
):
    auth_page.goto(f"{e2e_server}{RECORD_PATH}")

    auth_page.locator("#project").select_option(
        value=job_dependencies["project_name"]
    )

    auth_page.locator("#tool").select_option(
        value=job_dependencies["tool_name"]
    )

    auth_page.locator(
        "form.record input[type='submit']"
    ).click()

    # HTML required属性によって送信がブロックされる
    expect(auth_page).to_have_url(
        f"{e2e_server}{RECORD_PATH}"
    )

    assert auth_page.locator("#title").evaluate(
        "(element) => element.validity.valueMissing"
    ) is True
