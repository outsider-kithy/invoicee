from datetime import date
from decimal import Decimal
from io import BytesIO

import openpyxl
import pytest

from helper import writeExcel, currentJPY

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(('content', 'row'), [(None, 12), ('Design task', 13)])
@pytest.mark.parametrize('rate', ['0', '0.08', '0.10'])
def test_excel_download_cells_and_formulas(app, content, row, rate):
    with app.test_request_context():
        response = writeExcel([['Job title', content, 12000, date(2026, 1, 2), Decimal(rate)]],
                              'Agency', 'Account', 'Project')
    assert response.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    assert 'attachment;' in response.headers['Content-Disposition']
    workbook = openpyxl.load_workbook(BytesIO(response.data))
    sheet = workbook['シート1']
    assert sheet['A3'].value == 'Agency'
    assert sheet['A4'].value == 'Account'
    assert sheet['A11'].value == 'Project'
    assert sheet['E3'].value == str(date.today())
    assert sheet[f'A{row}'].value == (content or 'Job title')
    assert sheet[f'D{row}'].value == f'{int(Decimal(rate) * 100)}%'
    assert sheet[f'E{row}'].value == 12000
    assert sheet[f'E{row}'].number_format == currentJPY
    for cell, formula in {'E40': '=SUM(E12:E39)', 'B41': '=SUMIF(D12:D39,"8%",E12:E39)',
                          'B42': '=SUMIF(D12:D39,"10%",E12:E39)',
                          'B43': '=SUMIF(D12:D39,"0%",E12:E39)',
                          'E42': '=SUM(E40:E41)', 'B7': '=SUM(E40:E41)'}.items():
        assert sheet[cell].value == formula
    workbook.close()
