
import pytest

from urllib.parse import urlparse


# ============================================================
# 共通関数
# ============================================================

def assert_html_response(response):
    """
    HTMLレスポンスが正常に返されていることを確認する。
    """
    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert response.data


def assert_login_redirect(response):
    """
    未ログイン時にログイン画面へリダイレクトされること。
    """
    assert response.status_code == 302
    assert urlparse(response.location).path == "/login/"


# ============================================================
# OTH-INT-001
# ログイン済みトップページ
# ============================================================

def test_top_page_authenticated(
    authenticated_client, seed
):
    response = authenticated_client.get("/top/")

    assert_html_response(response)


# ============================================================
# OTH-INT-002
# 未ログイントップページ
# ============================================================

def test_top_page_requires_login(client):
    response = client.get(
        "/top/",
        follow_redirects=False
    )

    assert_login_redirect(response)


# ============================================================
# OTH-INT-003
# ログイン画面表示
# ============================================================

def test_login_page_display(client):
    response = client.get("/login/")

    assert_html_response(response)


# ============================================================
# OTH-INT-004
# ユーザー登録画面表示
# ============================================================

def test_register_page_display(client):
    response = client.get("/register/")

    assert_html_response(response)


# ============================================================
# OTH-INT-005
# 見積書作成画面表示
# ============================================================

def test_estimate_page_display(
    authenticated_client, seed
):
    response = authenticated_client.get("/estimate/")

    assert_html_response(response)


# ============================================================
# OTH-INT-006
# 未ログイン時の見積書作成画面
# ============================================================

def test_estimate_page_requires_login(client):
    response = client.get(
        "/estimate/",
        follow_redirects=False
    )

    assert_login_redirect(response)


# ============================================================
# OTH-INT-007
# 存在しないURL
# ============================================================

def test_unknown_url_returns_404(client):
    response = client.get(
        "/this-page-does-not-exist/"
    )

    assert response.status_code == 404


# ============================================================
# OTH-INT-008
# 404専用画面
# ============================================================

def test_notfound_page_display(client):
    response = client.get("/404/")

    assert response.status_code in (200, 404)
    assert response.mimetype == "text/html"
    assert response.data


# ============================================================
# OTH-INT-009
# 主要ルートの登録確認
# ============================================================

def test_registered_routes(app):
    """
    Flaskアプリケーションに主要なルートが
    正しく登録されていることを確認する。
    """

    registered_routes = {
        rule.rule
        for rule in app.url_map.iter_rules()
    }

    expected_routes = {
        "/top/",
        "/login/",
        "/register/",
        "/estimate/",
        "/error/",
        "/404/",
    }

    for route in expected_routes:
        assert route in registered_routes


# ============================================================
# OTH-INT-010
# 認証済み画面のHTMLレスポンス
# ============================================================

@pytest.mark.parametrize(
    "url",
    [
        "/top/",
        "/estimate/",
    ]
)
def test_authenticated_pages_return_html(
    authenticated_client, seed, url
):
    response = authenticated_client.get(url)

    assert_html_response(response)

    # HTMLとして最低限の構造を持つこと
    html = response.get_data(as_text=True).lower()

    assert "<html" in html
    assert "</html>" in html

# OTH-INT-011
def test_custom_404_page(client):
    """
    存在しないURLへのアクセス時に、
    独自の404ページが表示されることを確認する。
    """

    response = client.get(
        "/this-page-does-not-exist/"
    )

    assert response.status_code == 404
    assert response.mimetype == "text/html"

    html = response.get_data(as_text=True)

    assert "指定のページは見つかりませんでした。" in html

# OTH-INT-012
def test_custom_404_page_post(client):
    """
    存在しないURLへのPOSTリクエストでも、
    独自の404ページが表示されることを確認する。
    """

    response = client.post(
        "/this-page-does-not-exist/"
    )

    assert response.status_code == 404
    assert response.mimetype == "text/html"

    html = response.get_data(as_text=True)

    assert "指定のページは見つかりませんでした。" in html

# OTH-INT-013
def test_custom_405_page(client):
    """
    許可されていないHTTPメソッドでアクセスした場合、
    独自の405ページが表示されることを確認する。
    """

    response = client.put("/login/")

    assert response.status_code == 405
    assert response.mimetype == "text/html"

    html = response.get_data(as_text=True)

    assert "このHTTPメソッドは許可されていません。" in html

    # 許可されているHTTPメソッドを確認
    allow = response.headers.get("Allow", "")

    assert "GET" in allow
    assert "POST" in allow
    assert "PUT" not in allow