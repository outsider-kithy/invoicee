from io import BytesIO

import openpyxl
import pytest
from playwright.sync_api import expect

pytestmark = pytest.mark.e2e


def test_registration_to_estimate_download(page, live_url):
    page.goto(f'{live_url}/register/')
    page.get_by_label('名前', exact=True).fill('browser-user')
    page.get_by_label('パスワード', exact=True).fill('browser-password')
    page.get_by_label('パスワード（確認用）', exact=True).fill('browser-password')
    page.get_by_role('button', name='登録', exact=True).click()
    expect(page).to_have_url(f'{live_url}/login/')
    page.get_by_label('名前', exact=True).fill('browser-user')
    page.get_by_label('パスワード', exact=True).fill('browser-password')
    page.get_by_role('button', name='ログイン', exact=True).click()
    expect(page).to_have_url(f'{live_url}/top/')

    page.goto(f'{live_url}/record/')
    page.get_by_label('ジョブタイトル').fill('Browser Print Job')
    page.locator('#project').select_option(label='Test Project')
    page.locator('#tool').select_option(label='Print')
    page.locator('[name=github_repository]').fill('example/browser')
    page.get_by_role('button', name='ジョブを登録', exact=True).click()
    expect(page.get_by_role('cell', name='Browser Print Job', exact=True)).to_be_visible()

    page.goto(f'{live_url}/estimate/')
    row = page.get_by_role('row').filter(has_text='Browser Print Job')
    row.get_by_role('radio').check()
    with page.expect_download() as download_info:
        page.get_by_role('button', name='見積もりを出力', exact=True).click()
    download = download_info.value
    assert download.failure() is None
    assert download.suggested_filename.endswith('-estimate.xlsx')
    book = openpyxl.load_workbook(BytesIO(download.path().read_bytes()))
    sheet = book['シート1']
    assert sheet['A12'].value == 'Browser Print Job'
    assert sheet['E12'].value == 20000
    book.close()
    page.goto(f'{live_url}/estimate/')
    expect(page.get_by_role('cell', name='Browser Print Job', exact=True)).to_have_count(0)
    page.goto(f'{live_url}/logout/')
    expect(page).to_have_url(f'{live_url}/login/')
    page.goto(f'{live_url}/top/')
    expect(page.get_by_role('heading', name='Unauthorized')).to_be_visible()


def test_wrong_password_shows_error(page, live_url):
    page.goto(f'{live_url}/login/')
    page.get_by_label('名前', exact=True).fill('tester')
    page.get_by_label('パスワード', exact=True).fill('wrong')
    page.get_by_role('button', name='ログイン', exact=True).click()
    expect(page.locator('.error')).to_have_text('パスワードが違います')
    expect(page).to_have_url(f'{live_url}/login/')
