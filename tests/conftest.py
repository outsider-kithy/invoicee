import os
import pytest
from pathlib import Path
from flask_login import UserMixin
from app import create_app
from dotenv import load_dotenv
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5000"

# プロジェクトのルートディレクトリ
BASE_DIR = Path(__file__).resolve().parent.parent
# .env.testを読み込む
load_dotenv(BASE_DIR / ".env.test")

class MockUser(UserMixin):
    id = "1"


# Flaskアプリケーションを生成
@pytest.fixture
def app():
    app = create_app()

    app.config.update({
        "TESTING": True,
    })

    yield app


# テスト用クライアントを生成
@pytest.fixture
def client(app):
    return app.test_client()


# ログイン済みクライアントを生成
@pytest.fixture
def logged_in_client(app, client):

    @app.login_manager.user_loader
    def load_test_user(user_id):
        if user_id == "1":
            return MockUser()
        return None

    with client.session_transaction() as sess:
        sess["_user_id"] = "1"
        sess["_fresh"] = True

    return client

@pytest.fixture
def logged_in_page(page: Page):

    page.goto(f"{BASE_URL}/login/")

    page.locator('input[name="username"]').fill(
        os.environ["TEST_USERNAME"]
    )

    page.locator('input[name="password"]').fill(
        os.environ["TEST_PASSWORD"]
    )

    page.get_by_role("button", name="ログイン").click()

    expect(page).to_have_url(f"{BASE_URL}/top/")

    return page