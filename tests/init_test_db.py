from models import Base, engine

def check_test_database():
    if engine.url.database != "invoicee_test":
        raise RuntimeError(
            "テスト用DB以外への操作は禁止されています。"
        )

def init_test_db():
    Base.metadata.create_all(bind=engine)
    print("テスト用テーブルを作成しました。")


if __name__ == "__main__":
    init_test_db()