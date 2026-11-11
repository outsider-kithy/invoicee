
import uuid

from playwright.sync_api import Page, expect


ERROR_PATH = "/error/"
NOTFOUND_PATH = "/404/"

DATABASE_ERROR_MESSAGE = "データベースエラーが発生しました。"
NOTFOUND_MESSAGE = "指定のページは見つかりませんでした。"
METHOD_ERROR_MESSAGE = "このHTTPメソッドは許可されていません。"


# ============================================================
# ERROR-E2E-001
# /error/ にGETアクセス
# ============================================================

def test_error_page_get(
    page: Page,
    e2e_server
):
    response = page.goto(
        f"{e2e_server}{ERROR_PATH}"
    )

    assert response is not None
    assert response.status == 500

    expect(page).to_have_url(
        f"{e2e_server}{ERROR_PATH}"
    )

    expect(
        page.get_by_role(
            "heading",
            name="データベースエラー"
        )
    ).to_be_visible()


# ============================================================
# ERROR-E2E-002
# /error/ にPOSTアクセス
# ============================================================

def test_error_page_post(
    page: Page,
    e2e_server
):
    response = page.request.post(
        f"{e2e_server}{ERROR_PATH}"
    )

    assert response.status == 500


# ============================================================
# ERROR-E2E-003
# DBエラーメッセージの表示
# ============================================================

def test_error_message_display(
    page: Page,
    e2e_server
):
    response = page.goto(
        f"{e2e_server}{ERROR_PATH}"
    )

    assert response.status == 500

    expect(
        page.locator("p.error")
    ).to_have_text(DATABASE_ERROR_MESSAGE)


# ============================================================
# ERROR-E2E-004
# /404/ にGETアクセス
# ============================================================

def test_notfound_page_get(
    page: Page,
    e2e_server
):
    response = page.goto(
        f"{e2e_server}{NOTFOUND_PATH}"
    )

    assert response is not None
    assert response.status == 404

    expect(page).to_have_url(
        f"{e2e_server}{NOTFOUND_PATH}"
    )

    expect(
        page.get_by_role(
            "heading",
            name="404エラー"
        )
    ).to_be_visible()


# ============================================================
# ERROR-E2E-005
# /404/ にPOSTアクセス
# ============================================================

def test_notfound_page_post(
    page: Page,
    e2e_server
):
    response = page.request.post(
        f"{e2e_server}{NOTFOUND_PATH}"
    )

    assert response.status == 404

    assert NOTFOUND_MESSAGE in response.text()


# ============================================================
# ERROR-E2E-006
# 存在しないURLへのアクセス
# ============================================================

def test_unknown_url_notfound(
    page: Page,
    e2e_server
):
    unknown_path = (
        "/unknown-page-" + uuid.uuid4().hex
    )

    response = page.goto(
        f"{e2e_server}{unknown_path}"
    )

    assert response is not None
    assert response.status == 404

    expect(
        page.locator("p.error")
    ).to_have_text(NOTFOUND_MESSAGE)

    expect(
        page.get_by_role(
            "heading",
            name="404エラー"
        )
    ).to_be_visible()


# ============================================================
# ERROR-E2E-007
# 404エラー時のURL維持
# ============================================================

def test_notfound_url_preserved(
    page: Page,
    e2e_server
):
    unknown_path = (
        "/not-existing-" + uuid.uuid4().hex
    )

    response = page.goto(
        f"{e2e_server}{unknown_path}"
    )

    assert response.status == 404

    # /404/ へリダイレクトされず、
    # 元のURLが維持される
    expect(page).to_have_url(
        f"{e2e_server}{unknown_path}"
    )


# ============================================================
# ERROR-E2E-008
# 405 Method Not Allowed
# ============================================================

def test_method_not_allowed(
    page: Page,
    e2e_server
):
    # /error/ はGET・POSTのみ許可
    response = page.request.put(
        f"{e2e_server}{ERROR_PATH}"
    )

    assert response.status == 405


# ============================================================
# ERROR-E2E-009
# 405エラーメッセージ
# ============================================================

def test_method_not_allowed_message(
    page: Page,
    e2e_server
):
    response = page.request.put(
        f"{e2e_server}{ERROR_PATH}"
    )

    assert response.status == 405

    assert METHOD_ERROR_MESSAGE in response.text()


# ============================================================
# ERROR-E2E-010
# Allowヘッダーの検証
# ============================================================

def test_method_not_allowed_allow_header(
    page: Page,
    e2e_server
):
    response = page.request.put(
        f"{e2e_server}{ERROR_PATH}"
    )

    assert response.status == 405

    allow_header = response.headers.get("allow", "")

    allowed_methods = {
        method.strip()
        for method in allow_header.split(",")
    }

    assert "GET" in allowed_methods
    assert "POST" in allowed_methods


# ============================================================
# ERROR-E2E-011
# エラー発生後の復旧
# ============================================================

def test_recovery_after_error(
    auth_page: Page,
    e2e_server
):
    # 500エラーページへアクセス
    response = auth_page.goto(
        f"{e2e_server}{ERROR_PATH}"
    )

    assert response.status == 500

    # 正常なトップページに戻れるか確認
    response = auth_page.goto(
        f"{e2e_server}/top/"
    )

    assert response is not None
    assert response.status == 200

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

def test_database_exception_handler(
    page: Page,
    e2e_server
):
    response = page.goto(
        f"{e2e_server}/__test__/database-error"
    )

    assert response.status == 500

    expect(
        page.locator("p.error")
    ).to_have_text(
        "データベースエラーが発生しました。"
    )