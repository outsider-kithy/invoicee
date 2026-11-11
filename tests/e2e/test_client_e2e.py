
import re
import uuid

import pytest
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, select, func, delete
from sqlalchemy.orm import Session

from models import Client


ADMIN_PATH = "/admin/"


# ============================================================
# 共通fixture
# ============================================================

@pytest.fixture
def client_name():
    """テストごとに一意のクライアント名を生成する。"""
    return "E2E_Client_" + uuid.uuid4().hex[:12]


@pytest.fixture
def client_db(e2e_config):
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
def cleanup_client(client_db, client_name):
    """
    テスト終了後に、作成したクライアントだけを削除する。
    """
    yield

    with Session(client_db) as db:
        db.execute(
            delete(Client).where(
                Client.client_name == client_name
            )
        )
        db.commit()


# ============================================================
# 共通関数
# ============================================================

def register_client(page, base_url, client_name):
    """管理画面からクライアントを登録する。"""
    page.goto(f"{base_url}{ADMIN_PATH}")

    page.locator("#client").fill(client_name)

    page.locator(
        "form.record input[type='submit']"
    ).click()


def get_client(db_engine, client_name):
    """DBから指定したクライアントを取得する。"""
    with Session(db_engine) as db:
        return db.execute(
            select(Client).where(
                Client.client_name == client_name
            )
        ).scalar_one_or_none()


def count_clients(db_engine):
    """DBに登録されているクライアント数を取得する。"""
    with Session(db_engine) as db:
        return db.scalar(
            select(func.count()).select_from(Client)
        )


# ============================================================
# CLIENT-E2E-001
# 管理画面の表示
# ============================================================

def test_client_page_display(
    auth_page: Page,
    e2e_server
):
    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    expect(
        auth_page.locator("#client")
    ).to_be_visible()

    expect(
        auth_page.locator(
            "form.record input[type='submit']"
        )
    ).to_be_visible()


# ============================================================
# CLIENT-E2E-002
# クライアントの新規登録
# ============================================================

def test_client_registration(
    auth_page: Page,
    e2e_server,
    client_db,
    client_name,
    cleanup_client
):
    register_client(
        auth_page,
        e2e_server,
        client_name
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )

    client = get_client(
        client_db,
        client_name
    )

    assert client is not None
    assert client.client_name == client_name
    assert client.id is not None


# ============================================================
# CLIENT-E2E-003
# 登録後のリダイレクト
# ============================================================

def test_client_registration_redirect(
    auth_page: Page,
    e2e_server,
    client_name,
    cleanup_client
):
    register_client(
        auth_page,
        e2e_server,
        client_name
    )

    expect(auth_page).to_have_url(
        f"{e2e_server}/top/"
    )


# ============================================================
# CLIENT-E2E-004
# 未入力時のエラー
# ============================================================

def test_client_empty_submission(
    auth_page: Page,
    e2e_server,
    client_db
):
    before_count = count_clients(client_db)

    auth_page.goto(f"{e2e_server}{ADMIN_PATH}")

    # 全入力欄を空のまま送信
    auth_page.locator(
        "form.record input[type='submit']"
    ).click()

    # admin.indexに戻る
    expect(auth_page).to_have_url(
        f"{e2e_server}{ADMIN_PATH}"
    )

    after_count = count_clients(client_db)

    # クライアントは追加されていない
    assert after_count == before_count


# ============================================================
# CLIENT-E2E-005
# 未ログイン時のアクセス制限
# ============================================================

def test_client_page_requires_login(
    page: Page,
    e2e_server
):
    page.goto(f"{e2e_server}{ADMIN_PATH}")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )
