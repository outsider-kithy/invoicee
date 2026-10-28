from playwright.sync_api import expect


def test_admin_page(logged_in_page):

    logged_in_page.goto(
        "http://127.0.0.1:5000/admin/"
    )

    expect(logged_in_page).to_have_title("管理画面")