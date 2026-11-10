import os
from pathlib import Path
import sys
from threading import Thread
from uuid import uuid4
from dotenv import dotenv_values
import pytest
from flask import Flask
from flask_login import LoginManager
from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateSchema, DropSchema
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server

from app import create_app
import models

from login.views import login
from register.views import register
from logout.views import logout
from top.views import top
from update.views import update
from detail.views import detail
from record.views import record
from project.views import project
from admin.views import admin
from estimate.views import estimate
from error.views import error
from notfound.views import notfound

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# テスト用のデータベースに接続
TEST_DATABASE_URL = dotenv_values(ROOT / '.env.test').get('DATABASE_URL')
if not TEST_DATABASE_URL:
    raise pytest.UsageError('.env.testにDATABASE_URLが定義されていません。')
from sqlalchemy.engine import make_url
if make_url(TEST_DATABASE_URL).get_backend_name() != 'postgresql':
    raise pytest.UsageError('テスト用DBはPostgreSQLである必要があります。')
os.environ['DATABASE_URL'] = TEST_DATABASE_URL
os.environ['TEMPLATE_FILE'] = str(ROOT / 'estimate_template.xlsx')

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test-secret-key",
    )

    login_manager = LoginManager()
    
    login_manager.login_view = "login.index"

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return None

    app.register_blueprint(login, url_prefix="/login")
    app.register_blueprint(register, url_prefix="/register")
    app.register_blueprint(logout, url_prefix="/logout")
    app.register_blueprint(top, url_prefix="/top")
    app.register_blueprint(update, url_prefix="/update")
    app.register_blueprint(detail, url_prefix="/detail")
    app.register_blueprint(record, url_prefix="/record")
    app.register_blueprint(project, url_prefix="/project")
    app.register_blueprint(admin, url_prefix="/admin")
    app.register_blueprint(estimate, url_prefix="/estimate")
    app.register_blueprint(error, url_prefix="/error")
    app.register_blueprint(notfound, url_prefix="/404")

    return app


@pytest.fixture
def app(monkeypatch):
    # 既存のDBではなく、テスト用のDBを用いてテストする
    schema = f'pytest_{uuid4().hex}'
    engine = create_engine(TEST_DATABASE_URL,
                           connect_args={'options': f'-csearch_path={schema}'})
    try:
        with engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        models.session.remove()
        models.session.configure(bind=engine)
        models.Base.metadata.create_all(engine)
        import helper
        monkeypatch.setattr(helper, 'TEMPLATE_FILE', str(ROOT / 'estimate_template.xlsx'))
        application = create_app()
        application.config.update(TESTING=True, SECRET_KEY='pytest-only-secret')
        yield application
    finally:
        models.session.remove()
        try:
            with engine.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True, if_exists=True))
        finally:
            models.session.configure(bind=models.engine)
            engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()

# テスト用のレコードを追加
@pytest.fixture
def seed(app):
    tax = models.Tax(id=1, rate='0.10')
    client = models.Client(id=1, client_name='Test Client')
    agency = models.Agency(id=1, agency_name='Test Agency')
    models.session.add_all([tax, client, agency])
    models.session.flush()
    models.session.add_all([
        models.User(id=1, username='tester', password=generate_password_hash('test-password')),
        models.Account(id=1, account_name='Test Account', agency_id=1),
        models.Tool(id=1, tool_type='Web', price=10000, tax_rate_id=1),
        models.Tool(id=5, tool_type='Print', price=20000, tax_rate_id=1),
        models.Work(id=1, work_type='Default', price=1000, tax_rate_id=1),
        models.Work(id=2, work_type='Design', price=3000, tax_rate_id=1),
    ])
    models.session.flush()
    models.session.add(models.Project(id=1, project_name='Test Project', client_id=1,
                                      agency_id=1, account_id=1, isfinished=0))
    models.session.flush()
    models.session.add(models.Job(id=1, title='Test Job', tool_type_id=1, client_id=1,
        agency_id=1, account_id=1, project_id=1, price=10000, estimated=0,
        invoiced=0, github_repository='example/repo'))
    models.session.flush()
    
    for table in models.Base.metadata.sorted_tables:
        models.session.execute(text(
            f"SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), "
            f'COALESCE(MAX(id), 1), MAX(id) IS NOT NULL) FROM "{table.name}"'
        ))
    models.session.commit()
    return {'job_id': 1, 'project_id': 1}


@pytest.fixture
def authenticated_client(client, seed):
    response = client.post('/login/', data={'username': 'tester', 'password': 'test-password'})
    assert response.status_code == 302
    return client


@pytest.fixture
def live_url(app, seed):
    server = make_server('127.0.0.1', 0, app)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f'http://127.0.0.1:{server.server_port}'
    finally:
        server.shutdown()
        thread.join(timeout=5)
        server.server_close()


@pytest.fixture(autouse=True)
def block_external_http(monkeypatch):
    import requests
    def unexpected_request(*args, **kwargs):
        raise AssertionError('テストでは外部HTTPが無効になっているため、サービスクライアントをモックします。')
    monkeypatch.setattr(requests.sessions.Session, 'request', unexpected_request)



