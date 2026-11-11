
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest
from dotenv import dotenv_values
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from models import Base, User


ROOT = Path(__file__).resolve().parents[2]
TEST_ENV_FILE = ROOT / ".env.test"

BASE_URL = "http://127.0.0.1:5011"


# ============================================================
# .env.test の読み込み
# ============================================================

@pytest.fixture(scope="session")
def e2e_config():
    if not TEST_ENV_FILE.is_file():
        pytest.fail(
            f"Test environment file missing: {TEST_ENV_FILE}"
        )

    values = dotenv_values(TEST_ENV_FILE)

    required = (
        "DATABASE_URL",
        "TEST_USERNAME",
        "TEST_PASSWORD",
    )

    missing = [
        key for key in required
        if not values.get(key)
    ]

    if missing:
        pytest.fail(
            f"Missing keys in .env.test: {', '.join(missing)}"
        )

    production = (
        dotenv_values(ROOT / ".env")
        if (ROOT / ".env").exists()
        else {}
    )

    if production.get("DATABASE_URL") == values["DATABASE_URL"]:
        pytest.fail(
            "DATABASE_URL in .env.test matches .env"
        )

    return values


# ============================================================
# テストDBの初期化
# ============================================================

@pytest.fixture(scope="session")
def init_test_database(e2e_config):
    database_url = e2e_config["DATABASE_URL"]
    username = e2e_config["TEST_USERNAME"]
    password = e2e_config["TEST_PASSWORD"]

    test_engine = create_engine(database_url)

    try:
        if test_engine.url.database != "invoicee_test":
            pytest.fail(
                "テスト用DB以外への操作は禁止されています。"
            )

        Base.metadata.create_all(bind=test_engine)

        with Session(test_engine) as db:
            user = db.execute(
                select(User).where(
                    User.username == username
                )
            ).scalar_one_or_none()

            if user is None:
                user = User(
                    username=username,
                    password=generate_password_hash(password)
                )
                db.add(user)
            else:
                user.password = generate_password_hash(password)

            db.commit()

        print("E2Eテスト用DBの初期化が完了しました。")

    finally:
        test_engine.dispose()


# ============================================================
# Flaskテストサーバー
# ============================================================

@pytest.fixture(scope="session")
def e2e_server(e2e_config, init_test_database):
    env = os.environ.copy()

    env.update({
        k: str(v)
        for k, v in e2e_config.items()
        if v is not None
    })

    env["DATABASE_URL"] = str(e2e_config["DATABASE_URL"])
    env["FLASK_DEBUG"] = "0"
    env["FLASK_ENV"] = "production"

    with tempfile.TemporaryFile(mode="w+t") as log:
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "flask",
                "--app",
                "app:create_app",
                "run",
                "--host",
                "127.0.0.1",
                "--port",
                "5011",
                "--no-reload",
            ],
            cwd=ROOT,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
        )

        try:
            deadline = time.monotonic() + 20

            while time.monotonic() < deadline:
                if process.poll() is not None:
                    log.seek(0)
                    pytest.fail(
                        "Flask test server exited:\n"
                        + log.read()[-4000:]
                    )

                try:
                    with urlopen(
                        BASE_URL + "/login/",
                        timeout=0.5
                    ):
                        break
                except (URLError, TimeoutError):
                    time.sleep(0.2)
            else:
                pytest.fail(
                    "Flask test server did not start within 20 seconds"
                )

            yield BASE_URL

        finally:
            process.terminate()

            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


# ============================================================
# 共通ログイン関数
# ============================================================

def login(page, base_url, username, password):
    page.goto(f"{base_url}/login/")

    page.locator(
        'input[name="username"]'
    ).fill(username)

    page.locator(
        'input[name="password"]'
    ).fill(password)

    page.locator(
        'button[type="submit"], input[type="submit"]'
    ).first.click()

    expect(page).to_have_url(
        f"{base_url}/top/"
    )


# ============================================================
# 認証済みブラウザ
# ============================================================

@pytest.fixture
def auth_page(page: Page, e2e_server, e2e_config):
    login(
        page,
        e2e_server,
        e2e_config["TEST_USERNAME"],
        e2e_config["TEST_PASSWORD"]
    )

    return page
