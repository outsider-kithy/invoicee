
import re
import uuid

from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, text


# ============================================================
# AUTH-E2E-001
# ログイン成功
# ============================================================

def test_login_success(auth_page: Page, e2e_server):
    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )


# ============================================================
# AUTH-E2E-002
# ログイン失敗
# ============================================================

def test_login_wrong_password(
    page: Page, e2e_server, e2e_config
):
    page.goto(f"{e2e_server}/login/")

    page.locator('[name="username"]').fill(
        e2e_config["TEST_USERNAME"]
    )

    page.locator('[name="password"]').fill(
        "incorrect-e2e-password"
    )

    page.locator(
        'button[type="submit"], input[type="submit"]'
    ).first.click()

    expect(page).to_have_url(
        f"{e2e_server}/login/"
    )

    page.goto(f"{e2e_server}/top/")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )


# ============================================================
# AUTH-E2E-003
# 未ログイン時のアクセス制限
# ============================================================

def test_protected_page_redirects_when_logged_out(
    page: Page, e2e_server
):
    page.goto(f"{e2e_server}/top/")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )


# ============================================================
# AUTH-E2E-004
# ログアウト
# ============================================================

def test_logout(auth_page: Page, e2e_server):
    auth_page.goto(f"{e2e_server}/logout/")
    auth_page.goto(f"{e2e_server}/top/")

    expect(auth_page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )


# ============================================================
# AUTH-E2E-005
# セッション維持
# ============================================================

def test_session_survives_reload(
    auth_page: Page, e2e_server
):
    auth_page.reload()

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    expect(
        auth_page.locator("body")
    ).not_to_be_empty()


# ============================================================
# AUTH-E2E-006
# 新規ユーザー登録
# ============================================================

def test_register_and_login(
    page: Page, e2e_server, e2e_config
):
    username = "e2e_" + uuid.uuid4().hex[:16]
    password = "E2eTestPassword_2026!"

    engine = create_engine(
        e2e_config["DATABASE_URL"]
    )

    try:
        page.goto(f"{e2e_server}/register/")

        page.locator('[name="username"]').fill(username)
        page.locator('[name="password"]').fill(password)
        page.locator('[name="confirmation"]').fill(password)

        page.locator(
            'button[type="submit"], input[type="submit"]'
        ).first.click()

        # 登録したユーザーでログインできることを確認
        page.goto(f"{e2e_server}/logout/")
        page.goto(f"{e2e_server}/login/")

        page.locator('[name="username"]').fill(username)
        page.locator('[name="password"]').fill(password)

        page.locator(
            'button[type="submit"], input[type="submit"]'
        ).first.click()

        expect(page).to_have_url(
            f"{e2e_server}/top/"
        )

    finally:
        # このテストで作成したユーザーのみ削除
        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM users "
                    "WHERE username = :username"
                ),
                {"username": username},
            )

        engine.dispose()
