
import re
import uuid

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, select, func, delete
from sqlalchemy.orm import Session

from models import Agency, Account


ADMIN_PATH = "/admin/"


# ============================================================
# 共通fixture
# ============================================================

@pytest.fixture
def account_name():
    """テストごとに一意の担当者名を生成する。"""
    return "E2E_Account_" + uuid.uuid4().hex[:12]


@pytest.fixture
def account_db(e2e_config):
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
def test_agency(account_db):
    """
    担当者登録テスト用の代理店を作成する。

    テスト終了後に、担当者と代理店を削除する。
    """
    agency_name = "E2E_Agency_" + uuid.uuid4().hex[:12]

    with Session(account_db) as db:
        agency = Agency(agency_name=agency_name)
        db.add(agency)
        db.commit()
        db.refresh(agency)

        agency_id = agency.id

    try:
        yield {
            "id": agency_id,
            "name": agency_name,
        }

    finally:
        with Session(account_db) as db:
            # この代理店に紐づく担当者を先に削除
            db.execute(
                delete(Account).where(
                    Account.agency_id == agency_id
                )
            )

            # その後、代理店を削除
            db.execute(
                delete(Agency).where(
                    Agency.id == agency_id
                )
            )

            db.commit()


@pytest.fixture
def cleanup_account(account_db, account_name):
    """
    テスト終了後に作成した担当者を削除する。
    """
    yield

    with Session(account_db) as db:
        db.execute(
            delete(Account).where(
                Account.account_name == account_name
            )
        )
        db.commit()


# ============================================================
# 共通関数
# ============================================================

def register_account(
    page,
    base_url,
    account_name,
    agency_name=None
):
    """管理画面から担当者を登録する。"""
    page.goto(f"{base_url}{ADMIN_PATH}")

    page.locator("#account").fill(account_name)

    if agency_name is not None:
        page.locator("#agencyName").select_option(
            label=agency_name
        )

    page.locator(
        "form.record input[type='submit']"
    ).click()


def get_account(db_engine, account_name):
    """DBから指定した担当者を取得する。"""
    with Session(db_engine) as db:
        return db.execute(
            select(Account).where(
                Account.account_name == account_name
            )
        ).scalar_one_or_none()


def count_accounts(db_engine):
    """DBに登録されている担当者数を取得する。"""
    with Session(db_engine) as db:
        return db.scalar(
            select(func.count()).select_from(Account)
        )


# ============================================================
# ACCOUNT-E2E-001
# 担当者登録フォームの表示
# ============================================================

def test_account_page_display(
    auth_page: Page,
    e2e_server
):
    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    expect(
        auth_page.locator("#account")
    ).to_be_visible()

    expect(
        auth_page.locator("#agencyName")
    ).to_be_visible()

    expect(
        auth_page.locator(
            "form.record input[type='submit']"
        )
    ).to_be_visible()


# ============================================================
# ACCOUNT-E2E-002
# 担当者の新規登録
# ============================================================

def test_account_registration(
    auth_page: Page,
    e2e_server,
    account_db,
    account_name,
    test_agency,
    cleanup_account
):
    register_account(
        auth_page,
        e2e_server,
        account_name,
        test_agency["name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    account = get_account(
        account_db,
        account_name
    )

    assert account is not None
    assert account.account_name == account_name
    assert account.id is not None


# ============================================================
# ACCOUNT-E2E-003
# 代理店との紐づけ
# ============================================================

def test_account_agency_relationship(
    auth_page: Page,
    e2e_server,
    account_db,
    account_name,
    test_agency,
    cleanup_account
):
    register_account(
        auth_page,
        e2e_server,
        account_name,
        test_agency["name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    account = get_account(
        account_db,
        account_name
    )

    assert account is not None

    # 登録した担当者が正しい代理店に紐づいている
    assert account.agency_id == test_agency["id"]


# ============================================================
# ACCOUNT-E2E-004
# 登録後のリダイレクト
# ============================================================

def test_account_registration_redirect(
    auth_page: Page,
    e2e_server,
    account_name,
    test_agency,
    cleanup_account
):
    register_account(
        auth_page,
        e2e_server,
        account_name,
        test_agency["name"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )


# ============================================================
# ACCOUNT-E2E-005
# 代理店未選択時のエラー
# ============================================================

def test_account_without_agency(
    auth_page: Page,
    e2e_server,
    account_db,
    account_name
):
    before_count = count_accounts(account_db)

    # 代理店を選択せずに担当者名だけを送信
    register_account(
        auth_page,
        e2e_server,
        account_name
    )

    # 管理画面に戻る
    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    # 担当者は追加されていない
    after_count = count_accounts(account_db)

    assert after_count == before_count

    assert get_account(
        account_db,
        account_name
    ) is None


# ============================================================
# ACCOUNT-E2E-006
# 未入力時のエラー
# ============================================================

def test_account_empty_submission(
    auth_page: Page,
    e2e_server,
    account_db
):
    before_count = count_accounts(account_db)

    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    # 全入力欄を空のまま送信
    auth_page.locator(
        "form.record input[type='submit']"
    ).click()

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    after_count = count_accounts(account_db)

    assert after_count == before_count


# ============================================================
# ACCOUNT-E2E-007
# 未ログイン時のアクセス制限
# ============================================================

def test_account_page_requires_login(
    page: Page,
    e2e_server
):
    page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )
