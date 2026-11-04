import pytest
from werkzeug.security import check_password_hash
from models import session, User

pytestmark = pytest.mark.integration


@pytest.mark.parametrize('path', ['/top/', '/record/', '/project/', '/update/', '/detail/', '/estimate/', '/admin/', '/logout/'])
def test_protected_routes_require_login(client, path):
    assert client.get(path).status_code == 401


def test_registration_login_logout(client):
    response = client.post('/register/', data={'username': 'new-user', 'password': 'secret', 'confirmation': 'secret'})
    assert response.status_code == 302
    assert response.location.endswith('/login/')
    user = session.query(User).filter_by(username='new-user').one()
    assert user.password != 'secret'
    assert check_password_hash(user.password, 'secret')
    response = client.post('/login/', data={'username': 'new-user', 'password': 'secret'}, follow_redirects=True)
    assert response.status_code == 200
    assert 'トップページ' in response.text
    response = client.get('/logout/', follow_redirects=True)
    assert response.status_code == 200
    assert client.get('/top/').status_code == 401


@pytest.mark.parametrize(('data', 'message'), [
    ({}, '名前を入力してください'),
    ({'username': 'new'}, 'パスワードを入力してください'),
    ({'username': 'new', 'password': 'a'}, 'パスワードをもう一度入手してください'),
    ({'username': 'new', 'password': 'a', 'confirmation': 'b'}, '入力されたパスワードが一致しません'),
])
def test_invalid_registration_is_not_persisted(client, data, message):
    response = client.post('/register/', data=data)
    assert response.status_code == 200
    assert message in response.text
    assert session.query(User).count() == 0


@pytest.mark.parametrize(('username', 'password', 'message'), [
    ('', 'password', '名前を入力してください'),
    ('tester', '', 'パスワードを入力してください'),
    ('tester', 'incorrect', 'パスワードが違います'),
    ('unknown', 'password', None),
])
def test_invalid_login_does_not_authenticate(client, seed, username, password, message):
    response = client.post('/login/', data={'username': username, 'password': password})
    assert response.status_code == 200
    if message:
        assert message in response.text
    assert client.get('/top/').status_code == 401
