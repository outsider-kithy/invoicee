"""Real application, isolated PostgreSQL schemas, and local HTTP fixtures."""
import os
from pathlib import Path
import sys
from threading import Thread
from uuid import uuid4

from dotenv import dotenv_values

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Read this file explicitly, so a shell or .env production URL cannot win.
TEST_DATABASE_URL = dotenv_values(ROOT / '.env.test').get('DATABASE_URL')
if not TEST_DATABASE_URL:
    raise pytest.UsageError('.env.test must define DATABASE_URL')
from sqlalchemy.engine import make_url
if make_url(TEST_DATABASE_URL).get_backend_name() != 'postgresql':
    raise pytest.UsageError('.env.test DATABASE_URL must use PostgreSQL')
os.environ['DATABASE_URL'] = TEST_DATABASE_URL
os.environ['TEMPLATE_FILE'] = str(ROOT / 'estimate_template.xlsx')

from app import create_app
import models
from sqlalchemy import create_engine, text
from sqlalchemy.schema import CreateSchema, DropSchema
from werkzeug.security import generate_password_hash
from werkzeug.serving import make_server


@pytest.fixture
def app(monkeypatch):
    # Separate schemas preserve existing tables, allow real commits/rollbacks,
    # and are visible to the E2E server's independent database connections.
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
    # Explicit fixture IDs do not advance PostgreSQL SERIAL sequences.
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
    """External services must be mocked; browser localhost traffic is unaffected."""
    import requests
    def unexpected_request(*args, **kwargs):
        raise AssertionError('External HTTP is disabled in tests; mock the service client')
    monkeypatch.setattr(requests.sessions.Session, 'request', unexpected_request)
