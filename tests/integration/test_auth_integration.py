
from urllib.parse import urlparse

import pytest
from werkzeug.security import check_password_hash

from models import User, session

from sqlalchemy import select, func


# テスト用の認証情報
TEST_USERNAME = "tester"
TEST_PASSWORD = "test-password"

def get_user_by_username(username):
    """ユーザー名からUserを1件取得する。"""
    return session.scalar(
        select(User).where(User.username == username)
    )


def count_users_by_username(username):
    """指定したユーザー名の登録件数を取得する。"""
    return session.scalar(
        select(func.count())
        .select_from(User)
        .where(User.username == username)
    )

def login(client, username=TEST_USERNAME, password=TEST_PASSWORD):
    """
    Flaskのテストクライアントからログインする。
    """
    return client.post(
        "/login/",
        data={
            "username": username,
            "password": password
        },
        follow_redirects=False
    )


# AUTH-INT-001
def test_login_success(client, seed):
    """
    正しい認証情報でログインできることを確認する。
    """
    response = login(client)

    assert response.status_code == 302
    assert urlparse(response.location).path == "/top/"


# AUTH-INT-002
def test_login_wrong_password(client, seed):
    """
    パスワードが間違っている場合、
    ログインできないことを確認する。
    """
    response = login(
        client,
        password="wrong-password"
    )

    # 認証失敗後も保護ルートにアクセスできない
    protected_response = client.get("/top/")

    assert protected_response.status_code == 302
    assert urlparse(protected_response.location).path == "/login/"


# AUTH-INT-003
def test_login_unknown_user(client, seed):
    """
    存在しないユーザーでログインできないことを確認する。
    """
    response = login(
        client,
        username="unknown-user",
        password="unknown-password"
    )

    protected_response = client.get("/top/")

    assert protected_response.status_code == 302
    assert urlparse(protected_response.location).path == "/login/"


# AUTH-INT-004
@pytest.mark.parametrize(
    "username,password",
    [
        ("", "test-password"),
        ("tester", ""),
        ("", "")
    ]
)
def test_login_empty_fields(
    client, seed, username, password
):
    """
    認証情報が未入力の場合、
    ログインできないことを確認する。
    """
    login(client, username, password)

    response = client.get("/top/")

    assert response.status_code == 302
    assert urlparse(response.location).path == "/login/"


# AUTH-INT-005
def test_protected_route_without_login(client, seed):
    """
    未認証ユーザーが保護ルートにアクセスすると、
    ログイン画面へリダイレクトされる。
    """
    response = client.get("/top/")

    assert response.status_code == 302
    assert urlparse(response.location).path == "/login/"


# AUTH-INT-006
def test_protected_route_after_login(client, seed):
    """
    ログイン後に保護ルートへアクセスできる。
    """
    login_response = login(client)

    assert login_response.status_code == 302

    response = client.get("/top/")

    assert response.status_code == 200


# AUTH-INT-007
def test_login_session_persistence(client, seed):
    """
    複数リクエスト間でログイン状態が
    維持されることを確認する。
    """
    login(client)

    response1 = client.get("/top/")
    response2 = client.get("/top/")

    assert response1.status_code == 200
    assert response2.status_code == 200


# AUTH-INT-008
def test_login_password_hash(client, seed):
    """
    DBに保存されたパスワードハッシュが
    認証に利用できることを確認する。
    """
    user = session.scalar(
		select(User).where(User.username == TEST_USERNAME)
	)

    assert user is not None

    # 平文パスワードが保存されていない
    assert user.password != TEST_PASSWORD

    # ハッシュの照合が成功する
    assert check_password_hash(
        user.password,
        TEST_PASSWORD
    )

    # 実際のログイン処理も成功する
    response = login(client)

    assert response.status_code == 302
    assert urlparse(response.location).path == "/top/"


# 新規登録用ヘルパー関数
def register(client, username, password, password_confirm=None):
    """
    Flaskのテストクライアントから新規登録する。
    """
    if password_confirm is None:
        password_confirm = password

    return client.post(
        "/register/",
        data={
            "username": username,
            "password": password,
            "confirmation": password_confirm
        },
        follow_redirects=False
    )


# AUTH-INT-009
def test_logout_success(client, seed):
    """
    ログイン後にログアウトすると、
    認証状態が解除されることを確認する。
    """
    login_response = login(client)

    assert login_response.status_code == 302
    assert urlparse(login_response.location).path == "/top/"

    # ログアウト
    logout_response = client.get("/logout/")

    # ログアウト後に保護ルートへアクセス
    response = client.get("/top/")

    assert response.status_code == 302
    assert urlparse(response.location).path == "/login/"


# AUTH-INT-010
def test_logout_without_login(client, seed):
    """
    未ログイン状態でログアウトルートにアクセスしても、
    認証状態が作成されないことを確認する。
    """
    logout_response = client.get("/logout/")

    response = client.get("/top/")

    assert response.status_code == 302
    assert urlparse(response.location).path == "/login/"


# AUTH-INT-011
def test_register_success(client, app):
    """
    新規登録したユーザーが実際のDBに
    保存されることを確認する。
    """
    username = "new-user"
    password = "new-password"

    response = register(client, username, password)

    user = get_user_by_username(username)

    assert response.status_code == 302
    assert user is not None
    assert user.username == username


# AUTH-INT-012
def test_register_password_hash(client, app):
    """
    新規登録したパスワードが、
    平文ではなくハッシュ化されて保存されることを確認する。
    """
    username = "hash-test-user"
    password = "secure-password"

    register(
        client,
        username=username,
        password=password
    )

    user = session.scalar(
        select(User).where(User.username == username)
    )

    assert user is not None

    # 平文で保存されていない
    assert user.password != password

    # ハッシュを照合できる
    assert check_password_hash(
        user.password,
        password
    )


# AUTH-INT-013
def test_register_and_login(client, app):
    """
    新規登録したユーザーで実際にログインし、
    保護ルートへアクセスできることを確認する。
    """
	
    username = "register-login-user"
    password = "register-login-password"

    register(
        client,
        username=username,
        password=password
    )

    # 登録されたユーザーでログイン
    login_response = login(
        client,
        username=username,
        password=password
    )

    assert login_response.status_code == 302
    assert urlparse(login_response.location).path == "/top/"

    # 保護ルートへアクセス
    response = client.get("/top/")

    assert response.status_code == 200


# AUTH-INT-014
def test_register_duplicate_username(client, seed):

    username = "tester"

    before_count = count_users_by_username(username)

    response = register(
        client,
        username=username,
        password="another-password"
    )

    after_count = count_users_by_username(username)

    assert response.status_code == 200
    assert before_count == 1
    assert after_count == 1

    # 重複登録時のメッセージを確認
    assert "このユーザー名は既に使用されています" in (
        response.get_data(as_text=True)
    )

def test_register_after_duplicate(client, seed):

    # 既存ユーザー名で登録を試みる
    response1 = register(
        client,
        username="tester",
        password="another-password"
    )

    assert response1.status_code == 200

    # 別のユーザー名で登録
    response2 = register(
        client,
        username="new-tester",
        password="new-password"
    )

    assert response2.status_code == 302

    # DBに正常に保存されていることを確認
    user = (
        session.query(User)
        .filter(User.username == "new-tester")
        .first()
    )

    assert user is not None