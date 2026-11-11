"""Desktop UI E2E checks for invoicee.

Run: python -m pytest tests/e2e/test_ui_e2e.py -v
Uses existing e2e_server and auth_page fixtures.
"""
import re

from playwright.sync_api import Page, expect

VIEWPORT = {"width": 1440, "height": 900}
NAV_LABELS = [
    "トップ", "プロジェクトを登録", "ジョブを登録", "ジョブを更新",
    "見積もり", "管理画面", "ログアウト",
]
HEADERS = ["ジョブタイトル", "プロジェクト名", "受注日", "クライアント", "代理店", "価格", "見積書"]


def open_top(page: Page, base_url: str):
    page.set_viewport_size(VIEWPORT)
    response = page.goto(f"{base_url}/top/", wait_until="load")
    assert response is not None and response.status == 200
    return response


def test_ui_001_top_display(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    expect(auth_page.get_by_role("heading", name="トップページ", exact=True)).to_be_visible()


def test_ui_002_title(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    expect(auth_page).to_have_title("トップページ - invoicee")


def test_ui_003_html_metadata(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    expect(auth_page.locator("html")).to_have_attribute("lang", "ja")
    expect(auth_page.locator('meta[charset]')).to_have_attribute("charset", re.compile("utf-8", re.I))
    expect(auth_page.locator('meta[name="robots"]')).to_have_attribute("content", "noindex,nofollow")


def test_ui_004_logo(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    logo = auth_page.locator("nav h1 a img")
    expect(logo).to_be_visible()
    expect(logo).to_have_attribute("alt", "invoicee")
    assert logo.evaluate("img => img.complete && img.naturalWidth > 0"), "ロゴ画像が読み込まれていません"
    expect(auth_page.locator("nav h1 a")).to_have_attribute("href", "/top/")


def test_ui_005_authenticated_menu(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    menu = auth_page.locator("nav #menu")
    expect(menu.locator("li")).to_have_count(7)
    assert menu.locator("li a").all_text_contents() == NAV_LABELS


def test_ui_006_menu_links(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    menu = auth_page.locator("nav #menu")
    expected_paths = ["/top/", "/project/", "/record/", "/update/", "/estimate/", "/admin/", "/logout/"]
    # Check that links point to the application's expected route paths.
    for label, path in zip(NAV_LABELS, expected_paths):
        expect(menu.get_by_role("link", name=label, exact=True)).to_have_attribute("href", path)
    # Actual navigation without logging out.
    auth_page.locator('nav #menu a[href="/estimate/"]').click()
    expect(auth_page).to_have_url(f"{e2e_server}/estimate/")


def test_ui_007_unauthenticated_menu(page: Page, e2e_server):
    page.set_viewport_size(VIEWPORT)
    page.goto(f"{e2e_server}/login/", wait_until="load")
    menu = page.locator("nav #menu")
    expect(menu.get_by_role("link", name="ユーザーを登録")).to_be_attached()
    expect(menu.get_by_role("link", name="ログイン")).to_be_attached()
    expect(menu.get_by_role("link", name="ログアウト")).to_have_count(0)


def test_ui_008_table_headers(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    assert [s.strip() for s in auth_page.locator("table thead th").all_text_contents()] == HEADERS


def test_ui_009_job_rows(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    rows = auth_page.locator("table tr.jobs")
    for i in range(rows.count()):
        expect(rows.nth(i).locator("td")).to_have_count(7)
        expect(rows.nth(i).locator("td").nth(5)).to_contain_text("¥")


def test_ui_010_estimate_status(auth_page: Page, e2e_server):
    open_top(auth_page, e2e_server)
    cells = auth_page.locator("table tr.jobs td:last-child")
    for i in range(cells.count()):
        cell = cells.nth(i)