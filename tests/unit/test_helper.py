
import io
import datetime
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

import openpyxl
import pytest

import helper


@pytest.fixture
def excel_env(tmp_path, monkeypatch):
    """
    テスト用Excelテンプレートと出力先を準備する。
    """

    template_file = tmp_path / "template.xlsx"
    output_dir = tmp_path / "output"

    output_dir.mkdir()

    # テスト用Excelテンプレートを作成
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "シート1"

    workbook.save(template_file)
    workbook.close()

    # helper.pyの設定値をテスト用に差し替え
    monkeypatch.setattr(
        helper,
        "TEMPLATE_FILE",
        str(template_file)
    )

    monkeypatch.setattr(
        helper,
        "OUTPUT_DIR",
        str(output_dir)
    )

    return output_dir


@pytest.fixture
def excel_reader():
    """
    FlaskレスポンスのExcelバイナリをWorkbookとして開く。
    """

    def _read(response):
        return openpyxl.load_workbook(
            io.BytesIO(response.data)
        )

    return _read


@pytest.fixture
def fixed_date():
    """
    発行日を固定する。
    """

    class FakeDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(2026, 11, 10)

    with patch.object(helper.datetime, "date", FakeDate):
        yield


def test_write_excel_basic_info(
    app, excel_env, excel_reader, fixed_date
):
    with app.app_context():
        response = helper.writeExcel(
            [],
            "テスト代理店",
            "テスト担当者",
            "テストプロジェクト"
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    assert sheet["E3"].value == "2026-11-10"
    assert sheet["A3"].value == "テスト代理店"
    assert sheet["A4"].value == "テスト担当者"
    assert sheet["A11"].value == "テストプロジェクト"

    workbook.close()


def test_write_excel_with_content(
    app, excel_env, excel_reader, fixed_date
):
    jobs = [
        [
            "Webサイト制作",
            "コーディング",
            30000,
            "2026-11-09",
            0.1
        ]
    ]

    with app.app_context():
        response = helper.writeExcel(
            jobs, "代理店", "担当者", "プロジェクト"
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    assert sheet["A12"].value == "Webサイト制作"
    assert sheet["A13"].value == "コーディング"
    assert sheet["B13"].value == "2026-11-09"
    assert sheet["D13"].value == "10%"
    assert sheet["E13"].value == 30000

    workbook.close()


def test_write_excel_without_content(
    app, excel_env, excel_reader, fixed_date
):
    jobs = [
        [
            "パンフレット制作",
            None,
            50000,
            "2026-11-09",
            0.1
        ]
    ]

    with app.app_context():
        response = helper.writeExcel(
            jobs, "代理店", "担当者", "プロジェクト"
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    assert sheet["A12"].value == "パンフレット制作"
    assert sheet["B12"].value == "2026-11-09"
    assert sheet["D12"].value == "10%"
    assert sheet["E12"].value == 50000

    workbook.close()


def test_write_excel_multiple_contents(
    app, excel_env, excel_reader, fixed_date
):
    jobs = [
        ["Web制作", "デザイン", 20000, "2026-11-08", 0.1],
        ["Web制作", "コーディング", 30000, "2026-11-09", 0.1],
    ]

    with app.app_context():
        response = helper.writeExcel(
            jobs, "代理店", "担当者", "プロジェクト"
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    assert sheet["A13"].value == "デザイン"
    assert sheet["E13"].value == 20000

    assert sheet["A14"].value == "コーディング"
    assert sheet["E14"].value == 30000

    workbook.close()


def test_write_excel_tax_rates(
    app, excel_env, excel_reader, fixed_date
):
    jobs = [
        ["Job1", None, 10000, "2026-11-09", 0],
        ["Job2", None, 20000, "2026-11-09", Decimal("0.08")],
        ["Job3", None, 30000, "2026-11-09", Decimal("0.10")],
    ]

    with app.app_context():
        response = helper.writeExcel(
            jobs, "代理店", "担当者", "プロジェクト"
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    assert sheet["D12"].value == "0%"
    assert sheet["D13"].value == "8%"
    assert sheet["D14"].value == "10%"

    workbook.close()


def test_write_excel_currency_format(
    app, excel_env, excel_reader, fixed_date
):
    jobs = [
        ["パンフレット制作", None, 50000, "2026-11-09", 0.1]
    ]

    with app.app_context():
        response = helper.writeExcel(
            jobs, "代理店", "担当者", "プロジェクト"
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    assert sheet["E12"].number_format == helper.currentJPY
    assert sheet["E40"].number_format == helper.currentJPY
    assert sheet["E42"].number_format == helper.currentJPY
    assert sheet["B7"].number_format == helper.currentJPY

    print("E12 value:", sheet["E12"].value)
    print("E12 format:", sheet["E12"].number_format)
    print("E13 value:", sheet["E13"].value)
    print("E13 format:", sheet["E13"].number_format)
    print("currentJPY:", helper.currentJPY)

    workbook.close()


def test_write_excel_formulas(
    app, excel_env, excel_reader, fixed_date
):
    with app.app_context():
        response = helper.writeExcel(
            [], "代理店", "担当者", "プロジェクト"
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    expected = {
        "E40": "=SUM(E12:E39)",
        "B41": '=SUMIF(D12:D39,"8%",E12:E39)',
        "C41": "=B41*0.08",
        "B42": '=SUMIF(D12:D39,"10%",E12:E39)',
        "C42": "=B42*0.10",
        "B43": '=SUMIF(D12:D39,"0%",E12:E39)',
        "C43": "=B43*0",
        "C44": "=SUM(C41:C43)",
        "E41": "=SUM(C41:C43)",
        "E42": "=SUM(E40:E41)",
        "B7": "=SUM(E40:E41)",
    }

    for cell, formula in expected.items():
        assert sheet[cell].value == formula

    workbook.close()


def test_write_excel_empty_jobs(
    app, excel_env, excel_reader, fixed_date
):
    with app.app_context():
        response = helper.writeExcel(
            [], "代理店", "担当者", "プロジェクト"
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    assert sheet["A12"].value is None
    assert sheet["E12"].value is None
    assert sheet["E40"].value == "=SUM(E12:E39)"

    workbook.close()


def test_write_excel_response_headers(
    app, excel_env, fixed_date
):
    with app.app_context():
        response = helper.writeExcel(
            [], "代理店", "担当者", "プロジェクト"
        )

    assert response.status_code == 200

    assert response.mimetype == (
        "application/vnd.openxmlformats-officedocument."
        "spreadsheetml.sheet"
    )

    assert response.headers["Content-Disposition"] == (
        "attachment; filename=2026-11-10-estimate.xlsx"
    )


def test_write_excel_response_content(
    app, excel_env, fixed_date
):
    with app.app_context():
        response = helper.writeExcel(
            [], "代理店", "担当者", "プロジェクト"
        )

    assert response.data
    assert response.data[:2] == b"PK"

    workbook = openpyxl.load_workbook(
        io.BytesIO(response.data)
    )

    assert "シート1" in workbook.sheetnames

    workbook.close()


def test_write_excel_temporary_file_removed(
    app, excel_env, fixed_date
):
    with app.app_context():
        helper.writeExcel(
            [], "代理店", "担当者", "プロジェクト"
        )

    output_file = excel_env / "2026-11-10-estimate.xlsx"

    assert not output_file.exists()


def test_write_excel_none_recipient(
    app, excel_env, excel_reader, fixed_date
):
    with app.app_context():
        response = helper.writeExcel(
            [], None, None, None
        )

    workbook = excel_reader(response)
    sheet = workbook["シート1"]

    assert sheet["A3"].value == None
    assert sheet["A4"].value == None
    assert sheet["A11"].value == None

    workbook.close()
