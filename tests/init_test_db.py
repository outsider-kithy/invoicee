from models import Base, engine

Base.metadata.create_all(bind=engine)

print("テスト用テーブルを作成しました")