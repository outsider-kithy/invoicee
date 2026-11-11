
import re
import uuid

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, select, func, delete
from sqlalchemy.orm import Session

from models import Agency


ADMIN_PATH = "/admin/"


# ============================================================
# 共通fixture
# ============================================================

@pytest.fixture
def agency_name():
    """テストごとに一意の代理店名を生成する。"""
    return "E2E_Agency_" + uuid.uuid4().hex[:12]


@pytest.fixture
def agency_db(e2e_config):
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
def cleanup_agency(agency_db, agency_name):
    """
    テスト終了後に、作成した代理店だけを削除する。
    """
    yield

    with Session(agency_db) as db:
        db.execute(
            delete(Agency).where(
                Agency.agency_name == agency_name
            )
        )
        db.commit()


# ============================================================
# 共通関数
# ============================================================

def register_agency(page, base_url, agency_name):
    """管理画面から代理店を登録する。"""
    page.goto(f"{base_url}{ADMIN_PATH}")

    page.locator("#agency").fill(agency_name)

    page.locator(
        "form.record input[type='submit']"
    ).click()


def get_agency(db_engine, agency_name):
    """DBから指定した代理店を取得する。"""
    with Session(db_engine) as db:
        return db.execute(
            select(Agency).where(
                Agency.agency_name == agency_name
            )
        ).scalar_one_or_none()


def count_agencies(db_engine):
    """DBに登録されている代理店数を取得する。"""
    with Session(db_engine) as db:
        return db.scalar(
            select(func.count()).select_from(Agency)
        )


# ============================================================
# AGENCY-E2E-001
# 管理画面の表示
# ============================================================

def test_agency_page_display(
    auth_page: Page,
    e2e_server
):
    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    expect(
        auth_page.locator("#agency")
    ).to_be_visible()

    expect(
        auth_page.locator(
            "form.record input[type='submit']"
        )
    ).to_be_visible()


# ============================================================
# AGENCY-E2E-002
# 代理店の新規登録
# ============================================================

def test_agency_registration(
    auth_page: Page,
    e2e_server,
    agency_db,
    agency_name,
    cleanup_agency
):
    register_agency(
        auth_page,
        e2e_server,
        agency_name
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    agency = get_agency(
        agency_db,
        agency_name
    )

    assert agency is not None
    assert agency.agency_name == agency_name
    assert agency.id is not None


# ============================================================
# AGENCY-E2E-003
# 登録後のリダイレクト
# ============================================================

def test_agency_registration_redirect(
    auth_page: Page,
    e2e_server,
    agency_name,
    cleanup_agency
):
    register_agency(
        auth_page,
        e2e_server,
        agency_name
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )


# ============================================================
# AGENCY-E2E-004
# 未入力時のエラー
# ============================================================

def test_agency_empty_submission(
    auth_page: Page,
    e2e_server,
    agency_db
):
    before_count = count_agencies(agency_db)

    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    # 全入力欄を空のまま送信
    auth_page.locator(
        "form.record input[type='submit']"
    ).click()

    # admin.indexに戻る
    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    after_count = count_agencies(agency_db)

    # 代理店は追加されていない
    assert after_count == before_count


# ============================================================
# AGENCY-E2E-005
# 未ログイン時のアクセス制限
# ============================================================

def test_agency_page_requires_login(
    page: Page,
    e2e_server
):
    page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )


# ============================================================
# AGENCY-E2E-006
# 登録した代理店がプルダウンに表示される
# ============================================================

def test_agency_appears_in_select(
    auth_page: Page,
    e2e_server,
    agency_name,
    cleanup_agency
):
    # 代理店を登録
    register_agency(
        auth_page,
        e2e_server,
        agency_name
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    # 管理画面を再表示
    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    # 代理店の選択肢に追加されていることを確認
    expect(
        auth_page.locator(
            f'#agencyName option[value="{agency_name}"]'
        )
    ).to_have_count(1)
