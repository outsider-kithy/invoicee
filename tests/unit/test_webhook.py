from unittest.mock import Mock

import pytest
from sqlalchemy.exc import SQLAlchemyError
import webhook.views as views

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(('payload', 'message'), [
    ({}, 'Payload is empty'),
    ({'commits': []}, 'Repository information not found'),
    ({'repository': {'name': 'repo'}}, 'Repository full_name not found'),
])
def test_invalid_payload_does_not_access_database(client, monkeypatch, payload, message):
    database = Mock()
    monkeypatch.setattr(views, 'session', database)
    response = client.post('/webhook/', json=payload)
    assert response.status_code == 400
    assert response.json == {'error': message}
    database.query.assert_not_called()
    database.commit.assert_not_called()


@pytest.mark.parametrize(('exception', 'message'), [
    (SQLAlchemyError('failure'), 'Database update failed'),
    (RuntimeError('failure'), 'Internal Server Error'),
])
def test_database_failure_rolls_back(client, monkeypatch, exception, message):
    database = Mock()
    database.query.side_effect = exception
    monkeypatch.setattr(views, 'session', database)
    response = client.post('/webhook/', json={'repository': {'full_name': 'example/repo'}})
    assert response.status_code == 500
    assert response.json == {'error': message}
    database.rollback.assert_called_once_with()
    database.commit.assert_not_called()
