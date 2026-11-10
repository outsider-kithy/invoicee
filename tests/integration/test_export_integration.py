
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import pytest
from openpyxl import Workbook, load_workbook

import helper
from models import session, Job

from sqlalchemy import select
from models import Content, Work, Tool, Job, session


# Excelテンプレートと出力先をテスト用に設定
@pytest.fixture
def excel_env(tmp_path, monkeypatch):
    template = tmp_path / "template.xlsx"
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = "シート1"
    workbook.save(template)
    workbook.close()

    monkeypatch.setattr(
        helper, "TEMPLATE_FILE", str(template)
    )
    monkeypatch.setattr(
        helper, "OUTPUT_DIR", str(output_dir),
        raising=False
    )

    return {
        "template": template,
        "output_dir": output_dir
    }


# 見積書を生成する共通関数
def export_estimate(client, job_id=1):
    return client.post(
        "/estimate/",
        data={"job": [str(job_id)]},
        follow_redirects=False
    )


# ExcelレスポンスをWorkbookとして読み込む
def load_excel_response(response):
    return load_workbook(
        BytesIO(response.data),
        data_only=False
    )


# EXP-INT-001
def test_export_success(
    authenticated_client, seed, excel_env
):
    """
    見積書生成が成功し、
    Excelファイルが返されることを確認する。
    """
    response = export_estimate(
        authenticated_client,
        job_id=seed["job_id"]
    )

    assert response.status_code == 200
    assert response.data

    assert (
        "attachment"
        in response.headers["Content-Disposition"]
    )

    assert ".xlsx" in (
        response.headers["Content-Disposition"]
    )


# EXP-INT-002
def test_export_valid_excel(
    authenticated_client, seed, excel_env
):
    """
    生成されたファイルをopenpyxlで
    正常に読み込めることを確認する。
    """
    response = export_estimate(
        authenticated_client,
        job_id=seed["job_id"]
    )

    assert response.status_code == 200

    workbook = load_excel_response(response)

    assert "シート1" in workbook.sheetnames

    workbook.close()


# EXP-INT-003
def test_export_recipient(
    authenticated_client, seed, excel_env
):
    """
    見積書の宛先情報が
    Excelに反映されることを確認する。
    """
    response = export_estimate(
        authenticated_client,
        job_id=seed["job_id"]
    )

    assert response.status_code == 200

    workbook = load_excel_response(response)
    worksheet = workbook["シート1"]

    # 既存のwriteExcel()のセル配置に合わせて確認
    assert worksheet["E3"].value is not None
    assert worksheet["A3"].value is not None
    assert worksheet["A4"].value is not None

    workbook.close()


# EXP-INT-004
def test_export_job_detail(
    authenticated_client, seed, excel_env
):
    """
    Jobの情報が見積書の明細に
    反映されることを確認する。
    """
    job_id = seed["job_id"]

    job = session.get(Job, job_id)
    assert job is not None

    expected_title = job.title

    response = export_estimate(
        authenticated_client,
        job_id=job_id
    )

    assert response.status_code == 200

    workbook = load_excel_response(response)
    worksheet = workbook["シート1"]

    # 明細は12行目から出力される
    titles = [
        worksheet.cell(row=row, column=1).value
        for row in range(12, 40)
    ]

    assert expected_title in titles

    workbook.close()


# EXP-INT-005
def test_export_amount_and_tax(
    authenticated_client, seed, excel_env
):
    """
    見積書の集計セルに数式が
    設定されていることを確認する。
    """
    response = export_estimate(
        authenticated_client,
        job_id=seed["job_id"]
    )

    assert response.status_code == 200

    workbook = load_excel_response(response)
    worksheet = workbook["シート1"]

    # 集計欄の数式を確認
    for cell in ("E40", "E41", "E42"):
        value = worksheet[cell].value

        assert value is not None
        assert (
            isinstance(value, str)
            and value.startswith("=")
        )

    workbook.close()


# EXP-INT-006
def test_export_updates_estimated(
    authenticated_client, seed, excel_env
):
    """
    見積書生成後、Job.estimatedが
    1に更新されることを確認する。
    """
    job_id = seed["job_id"]

    job = session.get(Job, job_id)
    assert job is not None

    job.estimated = 0
    session.commit()

    response = export_estimate(
        authenticated_client,
        job_id=job_id
    )

    assert response.status_code == 200

    # DBから再取得
    session.remove()

    updated_job = session.get(Job, job_id)

    assert updated_job is not None
    assert updated_job.estimated == 1


# EXP-INT-007
def test_export_requires_login(client, seed):
    """
    未ログインユーザーが見積書生成を
    実行できないことを確認する。
    """
    response = export_estimate(
        client,
        job_id=seed["job_id"]
    )

    assert response.status_code == 302

    assert (
        urlparse(response.location).path
        == "/login/"
    )


# EXP-INT-008
def test_export_twice(
    authenticated_client, seed, excel_env
):
    """
    同じJobの見積書を2回生成しても、
    正常にExcelが返されることを確認する。
    """
    job_id = seed["job_id"]

    response1 = export_estimate(
        authenticated_client,
        job_id=job_id
    )

    response2 = export_estimate(
        authenticated_client,
        job_id=job_id
    )

    assert response1.status_code == 200
    assert response2.status_code == 200

    workbook1 = load_excel_response(response1)
    workbook2 = load_excel_response(response2)

    assert "シート1" in workbook1.sheetnames
    assert "シート1" in workbook2.sheetnames

    workbook1.close()
    workbook2.close()

    session.remove()

    job = session.get(Job, job_id)
    assert job.estimated == 1


# EXP-INT-009
def test_export_multiple_contents(
    authenticated_client, seed, excel_env
):
    job_id = seed["job_id"]

    # 既存のWorkを取得
    works = session.scalars(
        select(Work).order_by(Work.id)
    ).all()

    assert len(works) >= 2

    # Web系Jobであることを確認
    job = session.get(Job, job_id)
    assert job.tool_type_id in (1, 2, 3, 4)

    # 2件の明細を登録
    content1 = Content(
        job_id=job_id,
        work_id=works[0].id,
        work_content="デザイン制作"
    )

    content2 = Content(
        job_id=job_id,
        work_id=works[1].id,
        work_content="コーディング"
    )

    session.add_all([content1, content2])
    session.commit()

    # 見積書を生成
    response = export_estimate(
        authenticated_client,
        job_id=job_id
    )

    assert response.status_code == 200

    workbook = load_excel_response(response)
    worksheet = workbook["シート1"]

    # 明細の内容を取得
    details = [
        worksheet.cell(row=row, column=1).value
        for row in range(12, 40)
    ]

    assert "デザイン制作" in details
    assert "コーディング" in details

    workbook.close()

    session.remove()

    updated_job = session.get(Job, job_id)
    assert updated_job.estimated == 1


# EXP-INT-010
def test_export_print_job(
    authenticated_client, seed, excel_env
):
    job_id = seed["job_id"]

    job = session.get(Job, job_id)
    assert job is not None

    # 紙媒体Jobに変更
    job.title = "パンフレット制作"
    job.tool_type_id = 5
    job.price = 50000
    job.estimated = 0

    session.commit()

    # 見積書を生成
    response = export_estimate(
        authenticated_client,
        job_id=job_id
    )

    assert response.status_code == 200

    workbook = load_excel_response(response)
    worksheet = workbook["シート1"]

    # Jobのタイトルが出力されているか
    titles = [
        worksheet.cell(row=row, column=1).value
        for row in range(12, 40)
    ]

    assert "パンフレット制作" in titles

    # Jobの価格が反映されているか
    amounts = [
        worksheet.cell(row=row, column=5).value
        for row in range(12, 40)
    ]

    assert 50000 in amounts

    workbook.close()

    session.remove()

    updated_job = session.get(Job, job_id)
    assert updated_job.estimated == 1

# EXP-INT-011
def test_export_multiple_jobs(
    authenticated_client, seed, excel_env
):
    first_job_id = seed["job_id"]

    first_job = session.get(Job, first_job_id)
    assert first_job is not None

    # 1件目を未見積状態にする
    first_job.estimated = 0

    # 2件目のJobを作成
    second_job = Job(
        title="Second Job",
        tool_type_id=first_job.tool_type_id,
        client_id=first_job.client_id,
        agency_id=first_job.agency_id,
        account_id=first_job.account_id,
        project_id=first_job.project_id,
        price=25000,
        estimated=0,
        invoiced=0
    )

    session.add(second_job)
    session.commit()

    second_job_id = second_job.id

    # 2件のJobを指定してPOST
    response = authenticated_client.post(
        "/estimate/",
        data={
            "job": [
                str(first_job_id),
                str(second_job_id)
            ]
        },
        follow_redirects=False
    )

    assert response.status_code == 200

    # Excelが正常に生成されていることを確認
    workbook = load_excel_response(response)
    assert "シート1" in workbook.sheetnames
    workbook.close()

    session.remove()

    first_job = session.get(Job, first_job_id)
    second_job = session.get(Job, second_job_id)

    # 現行実装では最初のJobのみ処理される
    assert first_job.estimated == 1
    assert second_job.estimated == 0