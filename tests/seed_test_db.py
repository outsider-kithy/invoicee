import os
from werkzeug.security import generate_password_hash
from models import session, User, engine


def check_test_database():
    if engine.url.database != "invoicee_test":
        raise RuntimeError(
            "テスト用DB以外への操作は禁止されています。"
        )

def seed_test_db():

    username = os.environ["TEST_USERNAME"]
    password = os.environ["TEST_PASSWORD"]
    hashed = generate_password_hash(password)

    try:
        # すでに存在するか確認
        user = session.query(User).filter_by(
            username=username
        ).first()

        if user is None:
            user = User(
                username=username,
                password=hashed
            )

            session.add(user)
            session.commit()

            print("テストユーザーを登録しました。")

        else:
            print("テストユーザーは登録済みです。")

    except Exception:
        session.rollback()
        raise

    finally:
        session.remove()


if __name__ == "__main__":
    seed_test_db()