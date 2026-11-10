
import pytest

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from models import (
    session,
    Client,
    Job,
)


# DB-INT-001
def test_client_insert(app):
    """
    Clientを新規登録し、
    PostgreSQLに保存されることを確認する。
    """
    client = Client(client_name="New Client")

    session.add(client)
    session.commit()

    assert client.id is not None

    # セッションを切り替えてDBから再取得
    client_id = client.id
    session.remove()

    saved_client = session.get(Client, client_id)

    assert saved_client is not None
    assert saved_client.client_name == "New Client"


# DB-INT-002
def test_client_update(app, seed):
    """
    Clientの情報を更新し、
    DBに変更が反映されることを確認する。
    """
    client = session.get(Client, 1)

    assert client is not None

    client.client_name = "Updated Client"
    session.commit()

    session.remove()

    updated_client = session.get(Client, 1)

    assert updated_client.client_name == "Updated Client"


# DB-INT-003
def test_client_auto_increment(app, seed):
    """
    Clientを連続登録したとき、
    主キーが自動採番されることを確認する。
    """
    client = Client(client_name="New Client")

    session.add(client)
    session.commit()

    assert client.id > 1


# DB-INT-004
def test_client_duplicate_primary_key(app):
    """
    同じ主キーを持つClientを登録すると、
    IntegrityErrorが発生することを確認する。
    """

    # 1件目を登録
    client1 = Client(
        id=100,
        client_name="Client A"
    )

    session.add(client1)
    session.commit()

    # Sessionを切り替えてIdentity Mapをクリア
    session.remove()

    # 同じ主キーで2件目を登録
    client2 = Client(
        id=100,
        client_name="Client B"
    )

    session.add(client2)

    # PostgreSQLの主キー制約違反を確認
    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()

    # 元のレコードが維持されていることを確認
    saved_client = session.get(Client, 100)

    assert saved_client is not None
    assert saved_client.client_name == "Client A"



# DB-INT-005
def test_job_insert(app, seed):
    """
    Jobを新規登録し、
    PostgreSQLに保存されることを確認する。
    """
    job = Job(
        title="New Job",
        tool_type_id=1,
        client_id=1,
        agency_id=1,
        account_id=1,
        project_id=1,
        price=15000,
        estimated=0,
        invoiced=0,
        github_repository="example/new-job"
    )

    session.add(job)
    session.commit()

    job_id = job.id

    assert job_id is not None

    session.remove()

    saved_job = session.get(Job, job_id)

    assert saved_job is not None
    assert saved_job.title == "New Job"
    assert saved_job.price == 15000
    assert saved_job.estimated == 0
    assert saved_job.invoiced == 0


# DB-INT-006
def test_job_update(app, seed):
    """
    Jobのタイトル・価格・見積済みフラグを更新し、
    DBに反映されることを確認する。
    """
    job = session.get(Job, 1)

    assert job is not None

    job.title = "Updated Job"
    job.price = 30000
    job.estimated = 1

    session.commit()
    session.remove()

    updated_job = session.get(Job, 1)

    assert updated_job.title == "Updated Job"
    assert updated_job.price == 30000
    assert updated_job.estimated == 1


# DB-INT-007
def test_job_relationships(app, seed):
    """
    Jobと関連テーブルのリレーションが
    正しく取得できることを確認する。
    """
    job = session.get(Job, 1)

    assert job is not None

    assert job.client.client_name == "Test Client"
    assert job.agency.agency_name == "Test Agency"
    assert job.account.account_name == "Test Account"
    assert job.project.project_name == "Test Project"
    assert job.tool_type.tool_type == "Web"


# DB-INT-008
def test_job_auto_increment(app, seed):
    """
    Jobを連続登録したとき、
    主キーが自動採番されることを確認する。
    """
    job1 = Job(
        title="Auto Job A",
        tool_type_id=1,
        client_id=1,
        agency_id=1,
        account_id=1,
        project_id=1,
        price=10000,
        estimated=0,
        invoiced=0
    )

    job2 = Job(
        title="Auto Job B",
        tool_type_id=1,
        client_id=1,
        agency_id=1,
        account_id=1,
        project_id=1,
        price=20000,
        estimated=0,
        invoiced=0
    )

    session.add_all([job1, job2])
    session.commit()

    assert job1.id is not None
    assert job2.id is not None
    assert job1.id != job2.id
    assert job2.id > job1.id


# DB-INT-009
def test_job_invalid_foreign_key(app, seed):
    """
    存在しないClient IDを指定したJobが
    DBの外部キー制約によって拒否されることを確認する。
    """
    job = Job(
        title="Invalid Job",
        tool_type_id=1,
        client_id=99999,
        agency_id=1,
        account_id=1,
        project_id=1,
        price=10000,
        estimated=0,
        invoiced=0
    )

    session.add(job)

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()

    # 不正なJobが保存されていない
    saved_job = session.scalar(
        select(Job).where(Job.title == "Invalid Job")
    )

    assert saved_job is None


# DB-INT-010
def test_job_delete(app, seed):
    """
    Jobを削除すると、
    DBからレコードが削除されることを確認する。
    """
    job = session.get(Job, 1)

    assert job is not None

    session.delete(job)
    session.commit()
    session.remove()

    deleted_job = session.get(Job, 1)

    assert deleted_job is None


# DB-INT-011
def test_transaction_rollback(app, seed):
    """
    commit前にrollbackすると、
    新規登録が取り消されることを確認する。
    """
    client = Client(client_name="Rollback Client")

    session.add(client)
    session.flush()

    client_id = client.id

    session.rollback()
    session.remove()

    saved_client = session.get(Client, client_id)

    assert saved_client is None


# DB-INT-012
def test_session_recovery_after_integrity_error(app, seed):
    """
    IntegrityError発生後にrollbackすることで、
    DB操作を再開できることを確認する。
    """
    duplicate_client = Client(
        id=1,
        client_name="Duplicate Client"
    )

    session.add(duplicate_client)

    with pytest.raises(IntegrityError):
        session.commit()

    session.rollback()

    # rollback後に正常な登録を行う
    new_client = Client(
        client_name="Recovered Client"
    )

    session.add(new_client)
    session.commit()

    assert new_client.id is not None

    session.remove()

    saved_client = session.get(Client, new_client.id)

    assert saved_client is not None
    assert saved_client.client_name == "Recovered Client"
