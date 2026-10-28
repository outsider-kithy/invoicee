import pytest
from sqlalchemy import text
from models import session, engine, Client


def test_database_error_integration(logged_in_client, mocker):

    # テスト用クライアント名
    test_name = "結合テスト用クライアント"

    # PostgreSQLのシーケンス名
    #sequence_name = "public.clients_id_seq"

    # テスト用DBの最大IDを取得
    max_id = session.query(Client.id).order_by(
        Client.id.desc()
    ).first()

    max_id = max_id[0] if max_id else 0

    try:
        # ① 正常なINSERT
        response1 = logged_in_client.post(
            "/admin/",
            data={"client": test_name}
        )

        assert response1.status_code in [200, 302]

        # INSERTされたレコードを確認
        new_client = session.query(Client).filter_by(
            client_name=test_name
        ).order_by(Client.id.desc()).first()

        assert new_client is not None

        duplicate_id = new_client.id

        # ② シーケンスを既存IDに変更
        with engine.begin() as conn:
            conn.execute(
                text(
                    "SELECT setval("
                    "'public.clients_id_seq', "
                    ":duplicate_id, false)"
                ),
                {"duplicate_id": duplicate_id}
            )

        # ③ 再度POSTして主キー重複を発生させる
        rollback_spy = mocker.spy(session, "rollback")

        response2 = logged_in_client.post(
            "/admin/",
            data={"client": "結合テスト用クライアント2"}
        )

        # ④ HTTP 500を確認
        assert response2.status_code == 500

        # ⑤ エラー画面を確認
        assert "データベースエラー" in response2.get_data(
            as_text=True
        )

        # ⑥ エラー後もDB操作できるか確認
        result = session.query(Client).filter_by(
            id=duplicate_id
        ).first()

        assert result is not None

    finally:
        # ⑦ シーケンスを正常な状態に戻す
        session.rollback()

        with engine.begin() as conn:
            conn.execute(
                text("""
                    SELECT setval(
                        'public.clients_id_seq',
                        COALESCE(
                            (SELECT MAX(id) FROM public.clients),
                            0
                        ) + 1,
                        false
                    )
                """)
            )

        response3 = logged_in_client.post(
        "/admin/",
        data={"client": "エラー復旧後のクライアント"}
        )

        assert response3.status_code in [200, 302]

        # テストデータを削除
        session.query(Client).filter(
            Client.client_name.in_([
                test_name,
                "結合テスト用クライアント2"
            ])
        ).delete(synchronize_session=False)

        session.commit()
        session.remove()