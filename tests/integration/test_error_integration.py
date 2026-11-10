import pytest
from unittest.mock import patch

from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError

from models import session, Client


ERROR_URL = "/error/"


# Clientの件数を取得する共通関数
def count_clients():
    return session.scalar(
        select(func.count()).select_from(Client)
    )


# ERR-INT-001
def test_error_page_get(client):
    """
    エラーページへGETでアクセスできること。
    """
    response = client.get(ERROR_URL)

    assert response.status_code == 500
    assert response.data


# ERR-INT-002
def test_error_page_post(client):
    """
    エラーページへPOSTでアクセスできること。
    """
    response = client.post(ERROR_URL)

    assert response.status_code == 500
    assert response.data


# ERR-INT-003
def test_error_page_status(client):
    """
    エラーページのContent-Typeが
    HTMLであることを確認する。
    """
    response = client.get(ERROR_URL)

    assert response.status_code == 500
    assert response.mimetype == "text/html"


# ERR-INT-004
def test_integrity_error_rollback(app, seed):
    """
    主キー重複でIntegrityErrorが発生した場合、
    rollbackにより既存データが維持されること。
    """
    original = session.get(Client, 1)

    assert original is not None
    original_name = original.client_name

    # 同一Session内でのIdentity Map警告を防止
    session.remove()

    duplicate = Client(
        id=1,
        client_name="Duplicate Client"
    )

    session.add(duplicate)

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()
    session.remove()

    saved = session.get(Client, 1)

    assert saved is not None
    assert saved.client_name == original_name


# ERR-INT-005
def test_session_recovery_after_error(app, seed):
    """
    IntegrityError後にrollbackすると、
    新規レコードを正常に登録できること。
    """
    session.remove()

    duplicate = Client(
        id=1,
        client_name="Duplicate Client"
    )

    session.add(duplicate)

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()

    # エラー後に新規登録
    new_client = Client(
        client_name="Recovered Client"
    )

    session.add(new_client)
    session.commit()

    new_id = new_client.id

    session.remove()

    saved = session.get(Client, new_id)

    assert saved is not None
    assert saved.client_name == "Recovered Client"


# ERR-INT-006
def test_transaction_atomicity(app, seed):
    """
    同じトランザクションで正常なINSERTと
    不正なINSERTを行った場合、
    全体がロールバックされること。
    """
    before_count = count_clients()

    session.remove()

    valid = Client(
        client_name="Should Rollback"
    )

    invalid = Client(
        id=1,
        client_name="Duplicate Client"
    )

    session.add_all([valid, invalid])

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()
    session.remove()

    after_count = count_clients()

    assert after_count == before_count

    saved = session.scalar(
        select(Client).where(
            Client.client_name == "Should Rollback"
        )
    )

    assert saved is None


# ERR-INT-007
def test_error_handler_rollback(app, seed):
    """
    DBエラーをFlask経由で発生させ、
    エラーハンドリング後もDBが利用できること。

    テスト専用ルートでIntegrityErrorを発生させる。
    """
    from flask import current_app

    # このテスト専用のルート
    @app.route("/_test/db-error", methods=["POST"])
    def trigger_db_error():
        session.remove()

        duplicate = Client(
            id=1,
            client_name="Duplicate Client"
        )

        session.add(duplicate)

        # IntegrityErrorを発生させる
        session.commit()

        return "OK"

    # 例外をFlaskのエラーハンドラに渡す
    app.config["PROPAGATE_EXCEPTIONS"] = False

    with app.test_client() as test_client:
        response = test_client.post(
            "/_test/db-error"
        )

    assert response.status_code == 500

    # リクエスト終了後のSessionを破棄
    session.remove()

    # DBが正常に利用できることを確認
    saved = session.get(Client, 1)

    assert saved is not None


# ERR-INT-008
def test_error_page_after_db_failure(
    client, app, seed
):
    """
    DBエラー発生後も、
    エラーページが正常に表示されること。
    """
    session.remove()

    duplicate = Client(
        id=1,
        client_name="Duplicate Client"
    )

    session.add(duplicate)

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()

    response = client.get(ERROR_URL)

    assert response.status_code == 500
    assert response.data

    session.remove()

    saved = session.get(Client, 1)
    assert saved is not None

# ERR-INT-009
def test_sqlalchemy_error_handler(
    app, seed
):
    """
    実DBでIntegrityErrorを発生させ、
    SQLAlchemyErrorハンドラが呼び出されることを確認する。
    """

    # テスト専用ルートを作成
    @app.route("/_test/sqlalchemy-error", methods=["POST"])
    def trigger_sqlalchemy_error():
        session.remove()

        duplicate = Client(
            id=1,
            client_name="Duplicate Client"
        )

        session.add(duplicate)

        # IntegrityErrorが発生
        session.commit()

        return "OK"

    # TESTING=Trueでも例外をハンドラへ渡す
    app.config["PROPAGATE_EXCEPTIONS"] = False

    with app.test_client() as test_client:
        response = test_client.post(
            "/_test/sqlalchemy-error"
        )

    # 独自ハンドラが返すHTTPステータス
    assert response.status_code == 500

    # 独自ハンドラが表示するメッセージ
    assert (
        "データベースエラーが発生しました。"
        in response.get_data(as_text=True)
    )

    # エラー後のSessionが正常に使用できること
    session.remove()

    saved = session.get(Client, 1)

    assert saved is not None
    assert saved.client_name == "Test Client"


# ERR-INT-010
def test_sqlalchemy_error_handler_rollback(
    app, seed
):
    """
    SQLAlchemyErrorハンドラが
    session.rollback()を実行することを確認する。
    """

    @app.route("/_test/rollback-error", methods=["POST"])
    def trigger_rollback_error():
        session.remove()

        duplicate = Client(
            id=1,
            client_name="Duplicate Client"
        )

        session.add(duplicate)
        session.commit()

        return "OK"

    app.config["PROPAGATE_EXCEPTIONS"] = False

    with patch.object(
        session,
        "rollback",
        wraps=session.rollback
    ) as mock_rollback:

        with app.test_client() as test_client:
            response = test_client.post(
                "/_test/rollback-error"
            )

        assert response.status_code == 500
        mock_rollback.assert_called_once()