import pytest
from sqlalchemy.exc import IntegrityError
from models import Client, session


def test_insert_and_rollback():

    client_id = 999999

    try:
        # 1件目のINSERT
        session.add(Client(
            id=client_id,
            client_name="テストクライアントA"
        ))
        session.commit()

        # 同じIDでINSERTして重複エラーを発生させる
        session.add(Client(
            id=client_id,
            client_name="テストクライアントB"
        ))

        with pytest.raises(IntegrityError):
            session.commit()

        # エラー発生後にROLLBACK
        session.rollback()

        # 再度DB操作できることを確認
        result = session.get(Client, client_id)

        assert result is not None
        assert result.client_name == "テストクライアントA"

    finally:
        session.rollback()

        # テストデータを削除
        session.query(Client).filter(
            Client.id == client_id
        ).delete()

        session.commit()
        session.remove()
