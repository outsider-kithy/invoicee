from io import BytesIO

import openpyxl
import pytest
from sqlalchemy.exc import SQLAlchemyError

from models import session, Project, Job, Content, Client

pytestmark = pytest.mark.integration


def test_create_project_and_job(authenticated_client):
    client = authenticated_client
    response = client.post('/project/', data={'project': 'New Project', 'projectClientName': 'Test Client',
        'projectAgencyId': '1', 'projectAccountName': 'Test Account'})
    assert response.status_code == 302
    project = session.query(Project).filter_by(project_name='New Project').one()
    assert (project.client_id, project.agency_id, project.account_id, project.isfinished) == (1, 1, 1, 0)
    project_id = project.id
    response = client.post('/record/', data={'title': 'New Job', 'project': 'New Project',
        'tool': 'Print', 'github_repository': 'example/new'})
    assert response.status_code == 302
    job = session.query(Job).filter_by(title='New Job').one()
    assert (job.project_id, job.price, job.estimated, job.invoiced) == (project_id, 20000, 0, 0)
    assert job.github_repository == 'example/new'
    assert 'New Job' in client.get('/top/').text


def test_detail_adds_valid_work_and_skips_empty_or_unknown(authenticated_client):
    response = authenticated_client.post('/detail/', data={'update_job_id': '1',
        'new_work[]': ['Design', 'Design', 'Unknown'],
        'new_content[]': ['  New design  ', '   ', 'Ignored']})
    assert response.status_code == 302
    content = session.query(Content).one()
    assert (content.job_id, content.work_id, content.work_content) == (1, 2, 'New design')
    page = authenticated_client.get('/detail/?selectedJobId=1')
    assert page.status_code == 200
    assert 'New design' in page.text
    assert '¥3,000' in page.text
    assert '¥3,000' in authenticated_client.get('/top/').text


@pytest.mark.parametrize('tool_id', [1, 5])
def test_estimate_download_and_status(authenticated_client, tool_id):
    job = session.query(Job).get(1)
    job.tool_type_id = tool_id
    session.add(Content(job_id=1, work_id=2, work_content='Design task'))
    session.commit()
    response = authenticated_client.post('/estimate/', data={'job': '1'})
    assert response.status_code == 200
    assert 'attachment;' in response.headers['Content-Disposition']
    book = openpyxl.load_workbook(BytesIO(response.data))
    sheet = book['シート1']
    assert sheet['A3'].value == 'Test Agency'
    assert sheet['A4'].value == 'Test Account'
    assert sheet['A11'].value == 'Test Project'
    row = 13 if tool_id == 1 else 12
    assert sheet[f'A{row}'].value == ('Design task' if tool_id == 1 else 'Test Job')
    assert sheet[f'E{row}'].value == (3000 if tool_id == 1 else 10000)
    book.close()
    assert session.query(Job).get(1).estimated == 1
    assert 'Test Job' not in authenticated_client.get('/estimate/').text


def test_finished_project_is_hidden_from_record_form(authenticated_client):
    response = authenticated_client.post('/admin/', data={'finished_project': 'Test Project'})
    assert response.status_code == 302
    assert session.query(Project).get(1).isfinished == 1
    assert 'Test Project' not in authenticated_client.get('/record/').text


def test_database_error_rolls_back_pending_insert(authenticated_client, monkeypatch):
    import admin.views as views
    real_commit = session.commit
    def fail_commit():
        session.flush()
        raise SQLAlchemyError('simulated failure after INSERT')
    monkeypatch.setattr(views.session, 'commit', fail_commit)
    response = authenticated_client.post('/admin/', data={'client': 'Must roll back'})
    assert response.status_code == 500
    assert 'データベースエラーが発生しました。' in response.text
    monkeypatch.setattr(views.session, 'commit', real_commit)
    assert session.query(Client).filter_by(client_name='Must roll back').count() == 0
    assert authenticated_client.get('/top/').status_code == 200


def test_error_and_notfound_pages(authenticated_client):
    assert authenticated_client.get('/error/').status_code == 500
    response = authenticated_client.get('/404/')
    assert response.status_code == 404
    assert '指定のページは見つかりませんでした。' in response.text
    assert authenticated_client.get('/does-not-exist').status_code == 404


@pytest.mark.parametrize('path', ['/top/', '/record/', '/project/', '/update/', '/estimate/', '/admin/'])
def test_authenticated_pages_render(authenticated_client, path):
    assert authenticated_client.get(path).status_code == 200


def test_record_form_excludes_finished_projects(authenticated_client):
    session.add(Project(project_name='Finished Project', client_id=1, agency_id=1,
                        account_id=1, isfinished=1))
    session.commit()
    page = authenticated_client.get('/record/')
    assert 'Test Project' in page.text
    assert 'Finished Project' not in page.text
