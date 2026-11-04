import pytest
from models import session, Content

pytestmark = pytest.mark.integration


def test_webhook_persists_commit_types_and_first_line(client, seed):
    response = client.post('/webhook/', json={'repository': {'full_name': 'example/repo'}, 'commits': [
        {'message': 'Design:  Header: revised \nBody ignored'},
        {'message': 'Plain message'}, {'message': 'Unknown: keep full message'}, {'message': '  \nignored'},
    ]})
    assert response.status_code == 200
    assert response.json == {'message': 'OK'}
    rows = session.query(Content).order_by(Content.id).all()
    assert [(row.job_id, row.work_id, row.work_content) for row in rows] == [
        (1, 2, 'Header: revised'), (1, 1, 'Plain message'), (1, 1, 'Unknown: keep full message')]


@pytest.mark.parametrize(('repository', 'commits', 'status', 'body'), [
    ('missing/repo', [], 404, {'error': 'Matching Job not found'}),
    ('example/repo', [], 200, {'message': 'No commits found'}),
])
def test_webhook_without_work_does_not_insert(client, seed, repository, commits, status, body):
    response = client.post('/webhook/', json={'repository': {'full_name': repository}, 'commits': commits})
    assert response.status_code == status
    assert response.json == body
    assert session.query(Content).count() == 0


def test_commit_failure_rolls_back_real_inserts(client, seed, monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError
    def fail_commit():
        session.flush()
        raise SQLAlchemyError('simulated write failure')
    monkeypatch.setattr(session, 'commit', fail_commit)
    response = client.post('/webhook/', json={'repository': {'full_name': 'example/repo'},
        'commits': [{'message': 'Design: Must roll back'}]})
    assert response.status_code == 500
    assert response.json == {'error': 'Database update failed'}
    assert session.query(Content).count() == 0
