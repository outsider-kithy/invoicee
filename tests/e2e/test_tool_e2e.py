
import re
import uuid
from decimal import Decimal

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, select, func, delete
from sqlalchemy.orm import Session

from models import Tool, Tax


ADMIN_PATH = "/admin/"
TEST_PRICE = 12000


# ============================================================
# 共通fixture
# ============================================================

@pytest.fixture
def tool_name():
    """テストごとに一意のツール名を生成する。"""
    return "E2E_Tool_" + uuid.uuid4().hex[:12]


@pytest.fixture
def tool_db(e2e_config):
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
def test_tax(tool_db):
    """
    テスト用の税率を取得する。
    既存の税率がない場合は作成し、
    テスト終了後に削除する。
    """
    created_tax_id = None

    with Session(tool_db) as db:
        tax = db.execute(
            select(Tax).order_by(Tax.id)
        ).scalars().first()

        if tax is None:
            tax = Tax(rate=Decimal("0.10"))
            db.add(tax)
            db.commit()
            db.refresh(tax)

            created_tax_id = tax.id

        tax_data = {
            "id": tax.id,
            "rate": str(tax.rate),
        }

    try:
        yield tax_data

    finally:
        if created_tax_id is not None:
            with Session(tool_db) as db:
                db.execute(
                    delete(Tax).where(
                        Tax.id == created_tax_id
                    )
                )
                db.commit()


@pytest.fixture
def cleanup_tool(tool_db, tool_name):
    """テスト終了後、作成したツールのみ削除する。"""
    yield

    with Session(tool_db) as db:
        db.execute(
            delete(Tool).where(
                Tool.tool_type == tool_name
            )
        )
        db.commit()


# ============================================================
# 共通関数
# ============================================================

def register_tool(
    page,
    base_url,
    tool_name,
    price,
    tax_rate=None
):
    page.goto(f"{base_url}{ADMIN_PATH}")

    page.locator("#tool").fill(tool_name)
    page.locator("#price").fill(str(price))

    if tax_rate is not None:
        page.locator(
            'select[name="tax"]'
        ).select_option(value=str(tax_rate))

    # 選択された税率を確認
    selected_tax = page.locator(
        'select[name="tax"]'
    ).input_value()

    print("Selected tax:", selected_tax)

    page.locator(
        "form.record input[type='submit']"
    ).click()

    # 送信後のURLを確認
    print("Current URL:", page.url)

    # エラーメッセージを確認
    print("Page text:", page.locator("body").inner_text())


def get_tool(db_engine, tool_name):
    """DBから指定したツールを取得する。"""
    with Session(db_engine) as db:
        return db.execute(
            select(Tool).where(
                Tool.tool_type == tool_name
            )
        ).scalar_one_or_none()


def count_tools(db_engine):
    """DBに登録されているツール数を取得する。"""
    with Session(db_engine) as db:
        return db.scalar(
            select(func.count()).select_from(Tool)
        )


# ============================================================
# TOOL-E2E-001
# ツール登録フォームの表示
# ============================================================

def test_tool_page_display(
    auth_page: Page,
    e2e_server
):
    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    expect(
        auth_page.locator("#tool")
    ).to_be_visible()

    expect(
        auth_page.locator("#price")
    ).to_be_visible()

    expect(
        auth_page.locator('select[name="tax"]')
    ).to_be_visible()

    expect(
        auth_page.locator(
            "form.record input[type='submit']"
        )
    ).to_be_visible()


# ============================================================
# TOOL-E2E-002
# ツールの新規登録
# ============================================================

def test_tool_registration(
    auth_page: Page,
    e2e_server,
    tool_db,
    tool_name,
    test_tax,
    cleanup_tool
):
    register_tool(
        auth_page,
        e2e_server,
        tool_name,
        TEST_PRICE,
        test_tax["rate"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    tool = get_tool(tool_db, tool_name)

    assert tool is not None
    assert tool.tool_type == tool_name
    assert tool.id is not None


# ============================================================
# TOOL-E2E-003
# 価格の保存
# ============================================================

def test_tool_price(
    auth_page: Page,
    e2e_server,
    tool_db,
    tool_name,
    test_tax,
    cleanup_tool
):
    register_tool(
        auth_page,
        e2e_server,
        tool_name,
        TEST_PRICE,
        test_tax["rate"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    tool = get_tool(tool_db, tool_name)

    assert tool is not None
    assert Decimal(str(tool.price)) == Decimal(TEST_PRICE)


# ============================================================
# TOOL-E2E-004
# 税率との紐づけ
# ============================================================

def test_tool_tax_relationship(
    auth_page: Page,
    e2e_server,
    tool_db,
    tool_name,
    test_tax,
    cleanup_tool
):
    register_tool(
        auth_page,
        e2e_server,
        tool_name,
        TEST_PRICE,
        test_tax["rate"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    tool = get_tool(tool_db, tool_name)

    assert tool is not None
    assert tool.tax_rate_id == test_tax["id"]


# ============================================================
# TOOL-E2E-005
# 登録後のリダイレクト
# ============================================================

def test_tool_registration_redirect(
    auth_page: Page,
    e2e_server,
    tool_name,
    test_tax,
    cleanup_tool
):
    register_tool(
        auth_page,
        e2e_server,
        tool_name,
        TEST_PRICE,
        test_tax["rate"]
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/")


# ============================================================
# TOOL-E2E-006
# 税率未選択時のエラー
# ============================================================

def test_tool_without_tax(
    auth_page: Page,
    e2e_server,
    tool_db,
    tool_name
):
    before_count = count_tools(tool_db)

    register_tool(
        auth_page,
        e2e_server,
        tool_name,
        TEST_PRICE
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    after_count = count_tools(tool_db)

    assert after_count == before_count
    assert get_tool(tool_db, tool_name) is None


# ============================================================
# TOOL-E2E-007
# 全項目未入力時のエラー
# ============================================================

def test_tool_empty_submission(
    auth_page: Page,
    e2e_server,
    tool_db
):
    before_count = count_tools(tool_db)

    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    auth_page.locator(
        "form.record input[type='submit']"
    ).click()

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    after_count = count_tools(tool_db)

    assert after_count == before_count


# ============================================================
# TOOL-E2E-008
# 未ログイン時のアクセス制限
# ============================================================

def test_tool_page_requires_login(
    page: Page,
    e2e_server
):
    page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )
