from unittest.mock import Mock

import pytest
import commitlog.views as views

pytestmark = pytest.mark.unit


def test_missing_job_returns_404(client, monkeypatch):
    database = Mock()
    database.query.return_value.filter.return_value.first.return_value = None
    monkeypatch.setattr(views, 'session', database)
    get = Mock()
    monkeypatch.setattr(views.requests, 'get', get)
    assert client.get('/commitlog/?selectedJobId=999').status_code == 404
    get.assert_not_called()


def test_missing_repository_returns_400(client, monkeypatch):
    database = Mock()
    database.query.return_value.filter.return_value.first.return_value = Mock(github_repository=None)
    monkeypatch.setattr(views, 'session', database)
    assert client.get('/commitlog/?selectedJobId=1').status_code == 400


@pytest.mark.parametrize('status', [200, 403])
def test_github_api_response(client, monkeypatch, status):
    from datetime import date
    database = Mock()
    job = Mock(github_repository='example/repo', created=date(2026, 1, 2), title='Job')
    database.query.return_value.filter.return_value.first.return_value = job
    monkeypatch.setattr(views, 'session', database)
    monkeypatch.setattr(views, 'load_dotenv', lambda *a, **kw: None)
    monkeypatch.setenv('GITHUB_TOKEN', 'fake-test-token')
    response = Mock(status_code=status)
    response.json.return_value = [{'commit': {'message': 'Fix header', 'author': {'date': '2026-01-03T00:00:00Z'}}}]
    get = Mock(return_value=response)
    monkeypatch.setattr(views.requests, 'get', get)
    result = client.get('/commitlog/?selectedJobId=1')
    assert result.status_code == (200 if status == 200 else 500)
    if status == 200:
        assert 'Fix header' in result.text
    else:
        assert 'GitHub API Error: 403' in result.text
    get.assert_called_once_with(
        'https://api.github.com/repos/example/repo/commits?since=2026-01-02T00:00:00Z&per_page=100',
        headers={'Accept': 'application/vnd.github+json', 'Authorization': 'Bearer fake-test-token'})
