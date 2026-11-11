
import datetime
import re
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from openpyxl import load_workbook
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, select, delete
from sqlalchemy.orm import Session

from models import (
    Client,
    Agency,
    Account,
    Project,
    Tool,
    Tax,
    Job,
    Work,
    Content
)


ESTIMATE_PATH = "/estimate/"
TEST_PRICE = 12000
TEST_TAX_RATE = Decimal("0.10")


# ============================================================
# 共通fixture
# ============================================================

@pytest.fixture
def export_db(e2e_config):
    """テスト専用DBへの接続。"""
    engine = create_engine(e2e_config["DATABASE_URL"])

    if engine.url.database != "invoicee_test":
        engine.dispose()
        pytest.fail("テストDB以外への接続は禁止されています。")

    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def export_dependencies(export_db):
    """
    見積書出力用の関連レコードを作成する。

    Tax / Client / Agency / Account /
    Project / Tool

    Toolは紙媒体向けの分岐を使用する。
    """
    uid = uuid.uuid4().hex[:12]

    with Session(export_db) as db:
        tax = Tax(rate=TEST_TAX_RATE)

        client = Client(
            client_name=f"E2E_Client_{uid}"
        )

        agency = Agency(
            agency_name=f"E2E_Agency_{uid}"
        )

        db.add_all([tax, client, agency])
        db.flush()

        account = Account(
            account_name=f"E2E_Account_{uid}",
            agency_id=agency.id
        )

        db.add(account)
        db.flush()

        project = Project(
            project_name=f"E2E_Project_{uid}",
            client_id=client.id,
            agency_id=agency.id,
            account_id=account.id,
            isfinished=0
        )

        tool = Tool(
            tool_type=f"E2E_Tool_{uid}",
            price=TEST_PRICE,
            tax_rate_id=tax.id
        )

        db.add_all([project, tool])
        db.flush()

        data = {
            "tax_id": tax.id,
            "client_id": client.id,
            "client_name": client.client_name,
            "agency_id": agency.id,
            "agency_name": agency.agency_name,
            "account_id": account.id,
            "account_name": account.account_name,
            "project_id": project.id,
            "project_name": project.project_name,
            "tool_id": tool.id,
        }

        db.commit()

    # views.pyではTool ID 1〜4が特別扱いされる
    if data["tool_id"] in (1, 2, 3, 4):
        with Session(export_db) as db:
            db.execute(
                delete(Tool).where(Tool.id == data["tool_id"])
            )
            db.commit()
        pytest.fail(
            "紙媒体向けテストにはTool ID 5以上が必要です。"
        )

    try:
        yield data
    finally:
        with Session(export_db) as db:
            db.execute(
                delete(Job).where(
                    Job.project_id == data["project_id"]
                )
            )

            db.execute(
                delete(Project).where(
                    Project.id == data["project_id"]
                )
            )

            db.execute(
                delete(Tool).where(
                    Tool.id == data["tool_id"]
                )
            )

            db.execute(
                delete(Account).where(
                    Account.id == data["account_id"]
                )
            )

            db.execute(
                delete(Agency).where(
                    Agency.id == data["agency_id"]
                )
            )

            db.execute(
                delete(Client).where(
                    Client.id == data["client_id"]
                )
            )

            db.execute(
                delete(Tax).where(
                    Tax.id == data["tax_id"]
                )
            )

            db.commit()


@pytest.fixture
def export_job(export_db, export_dependencies):
    """未見積もりのJobを1件作成する。"""
    uid = uuid.uuid4().hex[:12]

    with Session(export_db) as db:
        job = Job(
            title=f"E2E_Export_Job_{uid}",
            created=datetime.date.today(),
            tool_type_id=export_dependencies["tool_id"],
            client_id=export_dependencies["client_id"],
            agency_id=export_dependencies["agency_id"],
            account_id=export_dependencies["account_id"],
            project_id=export_dependencies["project_id"],
            price=TEST_PRICE,
            estimated=0,
            invoiced=0,
            github_repository=""
        )

        db.add(job)
        db.flush()

        data = {
            "id": job.id,
            "title": job.title,
            "price": job.price,
            "created": job.created,
        }

        db.commit()

    yield data

    # Jobの削除はexport_dependenciesのteardownで実施
    

@pytest.fixture
def web_export_job(export_db, export_dependencies):
    """Web系ジョブと作業内容を作成する。"""

    uid = uuid.uuid4().hex[:12]

    with Session(export_db) as db:

        # Web系Tool（ID 1〜4）を取得
        tool = db.execute(
            select(Tool).where(Tool.id.in_([1, 2, 3, 4]))
        ).scalars().first()

        tool = db.get(Tool, 1)

        assert tool is not None, (
            "E2Eテスト用のWeb系Toolが初期化されていません"
)
        # 作業内容に適用する税率
        tax = db.get(Tax, export_dependencies["tax_id"])

        # Job
        job = Job(
            title=f"E2E_Web_Job_{uid}",
            created=datetime.date.today(),
            tool_type_id=tool.id,
            client_id=export_dependencies["client_id"],
            agency_id=export_dependencies["agency_id"],
            account_id=export_dependencies["account_id"],
            project_id=export_dependencies["project_id"],
            price=tool.price,
            estimated=0,
            invoiced=0,
            github_repository=""
        )

        db.add(job)
        db.flush()

        # Work
        work1 = Work(
            price=8000,
            tax_rate_id=tax.id
        )

        work2 = Work(
            price=5000,
            tax_rate_id=tax.id
        )

        db.add_all([work1, work2])
        db.flush()

        # Content
        content1 = Content(
            job_id=job.id,
            work_id=work1.id,
            work_content=f"E2E_HTML_Coding_{uid}",
            created=datetime.date.today()
        )

        content2 = Content(
            job_id=job.id,
            work_id=work2.id,
            work_content=f"E2E_Responsive_{uid}",
            created=datetime.date.today()
        )

        db.add_all([content1, content2])
        db.flush()

        data = {
            "job_id": job.id,
            "job_title": job.title,
            "tool_id": tool.id,
            "content_ids": [content1.id, content2.id],
            "work_ids": [work1.id, work2.id],
            "contents": [
                {
                    "text": content1.work_content,
                    "price": work1.price,
                    "created": content1.created,
                    "tax_rate": "10%",
                },
                {
                    "text": content2.work_content,
                    "price": work2.price,
                    "created": content2.created,
                    "tax_rate": "10%",
                }
            ]
        }

        db.commit()

    try:
        yield data

    finally:
        with Session(export_db) as db:

            db.execute(
                delete(Content).where(
                    Content.id.in_(data["content_ids"])
                )
            )

            db.execute(
                delete(Work).where(
                    Work.id.in_(data["work_ids"])
                )
            )

            db.execute(
                delete(Job).where(
                    Job.id == data["job_id"]
                )
            )

            db.commit()

@pytest.fixture
def web_exported_excel(
    auth_page,
    e2e_server,
    web_export_job,
    tmp_path
):
    return download_estimate(
        auth_page,
        e2e_server,
        web_export_job["job_id"],
        tmp_path
    )


@pytest.fixture
def web_exported_sheet(web_exported_excel):
    workbook = load_workbook(
        web_exported_excel,
        data_only=False
    )

    try:
        yield workbook["シート1"]
    finally:
        workbook.close()

# ============================================================
# 共通関数
# ============================================================

def get_estimated(db_engine, job_id):
    """Jobの見積もりステータスを取得する。"""
    with Session(db_engine) as db:
        return db.execute(
            select(Job.estimated).where(Job.id == job_id)
        ).scalar_one()


def job_radio(page, job_id):
    """対象Jobのラジオボタンを取得する。"""
    return page.locator(
        f'input[name="job"][value="{job_id}"]'
    )


def download_estimate(page, base_url, job_id, tmp_path):
    """見積書をダウンロードしてファイルパスを返す。"""
    page.goto(f"{base_url}{ESTIMATE_PATH}")

    job_radio(page, job_id).check()

    with page.expect_download() as download_info:
        page.locator(
            'form.estimate input[type="submit"]'
        ).click()

    download = download_info.value

    output_path = tmp_path / download.suggested_filename
    download.save_as(output_path)

    return output_path


@pytest.fixture
def exported_excel(
    auth_page,
    e2e_server,
    export_job,
    tmp_path
):
    """Excelを出力し、保存先を返す。"""
    return download_estimate(
        auth_page,
        e2e_server,
        export_job["id"],
        tmp_path
    )


@pytest.fixture
def exported_sheet(exported_excel):
    """ダウンロードしたExcelのワークシート。"""
    workbook = load_workbook(
        exported_excel,
        data_only=False
    )

    try:
        yield workbook["シート1"]
    finally:
        workbook.close()


# ============================================================
# EXPORT-E2E-001
# 見積書出力画面の表示
# ============================================================

def test_estimate_page_display(
    auth_page: Page,
    e2e_server
):
    auth_page.goto(f"{e2e_server}{ESTIMATE_PATH}")

    expect(auth_page).to_have_url(
        f"{e2e_server}{ESTIMATE_PATH}"
    )

    expect(
        auth_page.locator("form.estimate")
    ).to_be_visible()

    expect(
        auth_page.locator(
            'form.estimate input[type="submit"]'
        )
    ).to_be_visible()


# ============================================================
# EXPORT-E2E-002
# 未見積もりJobの一覧表示
# ============================================================

def test_unestimated_job_display(
    auth_page: Page,
    e2e_server,
    export_job
):
    auth_page.goto(f"{e2e_server}{ESTIMATE_PATH}")

    expect(
        job_radio(auth_page, export_job["id"])
    ).to_be_visible()

    expect(
        auth_page.locator("tr.jobs").filter(
            has_text=export_job["title"]
        )
    ).to_have_count(1)


# ============================================================
# EXPORT-E2E-003
# Excelのダウンロード
# ============================================================

def test_excel_download(exported_excel):
    assert exported_excel.exists()
    assert exported_excel.stat().st_size > 0
    assert exported_excel.suffix == ".xlsx"


# ============================================================
# EXPORT-E2E-004
# Excelファイルの正常性
# ============================================================

def test_excel_file_valid(exported_excel):
    workbook = load_workbook(exported_excel)

    try:
        assert "シート1" in workbook.sheetnames
        assert workbook["シート1"] is not None
    finally:
        workbook.close()


# ============================================================
# EXPORT-E2E-005
# 代理店・担当者・プロジェクト名
# ============================================================

def test_excel_customer_information(
    exported_sheet,
    export_dependencies
):
    assert exported_sheet["A3"].value == (
        export_dependencies["agency_name"]
    )

    assert exported_sheet["A4"].value == (
        export_dependencies["account_name"]
    )

    assert exported_sheet["A11"].value == (
        export_dependencies["project_name"]
    )


# ============================================================
# EXPORT-E2E-006
# Jobタイトル・価格・日付
# ============================================================

def test_excel_job_information(
    exported_sheet,
    export_job
):
    assert exported_sheet["A12"].value == (
        export_job["title"]
    )

    assert exported_sheet["E12"].value == (
        export_job["price"]
    )

    assert exported_sheet["B12"].value.date() == (
        export_job["created"]
    )

    assert exported_sheet["E3"].value == (
        str(datetime.date.today())
    )


# ============================================================
# EXPORT-E2E-007
# 税率とExcel計算式
# ============================================================

def test_excel_tax_and_formulas(exported_sheet):
    assert exported_sheet["D12"].value == "10%"

    assert exported_sheet["E40"].value == (
        "=SUM(E12:E39)"
    )

    assert exported_sheet["B42"].value == (
        '=SUMIF(D12:D39,"10%",E12:E39)'
    )

    assert exported_sheet["C42"].value == (
        "=B42*0.10"
    )

    assert exported_sheet["E41"].value == (
        "=SUM(C41:C43)"
    )

    assert exported_sheet["E42"].value == (
        "=SUM(E40:E41)"
    )

    assert exported_sheet["B7"].value == (
        "=SUM(E40:E41)"
    )


# ============================================================
# EXPORT-E2E-008
# 見積もりステータスの更新
# ============================================================

def test_job_estimated_status(
    exported_excel,
    export_db,
    export_job
):
    assert get_estimated(
        export_db,
        export_job["id"]
    ) == 1


# ============================================================
# EXPORT-E2E-009
# 出力済みJobが一覧から消える
# ============================================================

def test_exported_job_not_displayed(
    auth_page: Page,
    e2e_server,
    exported_excel,
    export_job
):
    auth_page.goto(f"{e2e_server}{ESTIMATE_PATH}")

    expect(
        job_radio(auth_page, export_job["id"])
    ).to_have_count(0)


# ============================================================
# EXPORT-E2E-010
# 未見積もりJobが0件の場合
# ============================================================

def test_no_unestimated_jobs(
    auth_page: Page,
    e2e_server,
    export_db
):
    # 他のテストデータや既存Jobが残っている場合は
    # DB全体が0件であることを前提にできない
    with Session(export_db) as db:
        remaining = db.execute(
            select(Job.id).where(Job.estimated == 0)
        ).first()

    if remaining is not None:
        pytest.skip(
            "DBに他の未見積もりJobが存在するためスキップ"
        )

    auth_page.goto(f"{e2e_server}{ESTIMATE_PATH}")

    expect(
        auth_page.locator("p.error")
    ).to_have_text("ジョブは0件です。")

    expect(
        auth_page.locator("tr.jobs")
    ).to_have_count(0)


# ============================================================
# EXPORT-E2E-011
# 複数Jobから1件だけを出力
# ============================================================

def test_export_only_selected_job(
    auth_page: Page,
    e2e_server,
    export_db,
    export_job,
    export_dependencies,
    tmp_path
):
    second_title = (
        "E2E_Second_Job_" + uuid.uuid4().hex[:12]
    )

    with Session(export_db) as db:
        second = Job(
            title=second_title,
            created=datetime.date.today(),
            tool_type_id=export_dependencies["tool_id"],
            client_id=export_dependencies["client_id"],
            agency_id=export_dependencies["agency_id"],
            account_id=export_dependencies["account_id"],
            project_id=export_dependencies["project_id"],
            price=15000,
            estimated=0,
            invoiced=0,
            github_repository=""
        )

        db.add(second)
        db.flush()
        second_id = second.id
        db.commit()

    download_estimate(
        auth_page,
        e2e_server,
        export_job["id"],
        tmp_path
    )

    assert get_estimated(
        export_db, export_job["id"]
    ) == 1

    assert get_estimated(
        export_db, second_id
    ) == 0


# ============================================================
# EXPORT-E2E-012
# Job未選択時のブラウザ検証
# ============================================================

def test_export_requires_selection(
    auth_page: Page,
    e2e_server,
    export_job
):
    auth_page.goto(f"{e2e_server}{ESTIMATE_PATH}")

    auth_page.locator(
        'form.estimate input[type="submit"]'
    ).click()

    expect(auth_page).to_have_url(
        f"{e2e_server}{ESTIMATE_PATH}"
    )

    assert job_radio(
        auth_page, export_job["id"]
    ).evaluate(
        "(element) => element.validity.valueMissing"
    ) is True


# ============================================================
# EXPORT-E2E-013
# 未ログイン時のアクセス制限
# ============================================================

def test_estimate_requires_login(
    page: Page,
    e2e_server
):
    page.goto(f"{e2e_server}{ESTIMATE_PATH}")

    expect(page).to_have_url(
        re.compile(r"/login/(?:\?.*)?$")
    )



# ============================================================
# EXPORT-E2E-014
# Web系ジョブのExcelダウンロード
# ============================================================

def test_web_excel_download(web_exported_excel):
    assert web_exported_excel.exists()
    assert web_exported_excel.suffix == ".xlsx"
    assert web_exported_excel.stat().st_size > 0


# ============================================================
# EXPORT-E2E-015
# Jobタイトルの出力
# ============================================================

def test_web_excel_job_title(
    web_exported_sheet,
    web_export_job
):
    assert web_exported_sheet["A12"].value == (
        web_export_job["job_title"]
    )


# ============================================================
# EXPORT-E2E-016
# Contentの作業内容
# ============================================================

def test_web_excel_content_text(
    web_exported_sheet,
    web_export_job
):
    actual = {
        web_exported_sheet["A13"].value,
        web_exported_sheet["A14"].value
    }

    expected = {
        item["text"]
        for item in web_export_job["contents"]
    }

    assert actual == expected


# ============================================================
# EXPORT-E2E-017
# Workの価格
# ============================================================

def test_web_excel_work_price(
    web_exported_sheet,
    web_export_job
):
    actual = {
        web_exported_sheet["E13"].value,
        web_exported_sheet["E14"].value
    }

    expected = {
        item["price"]
        for item in web_export_job["contents"]
    }

    assert actual == expected


# ============================================================
# EXPORT-E2E-018
# 作業日・税率
# ============================================================

def test_web_excel_content_date_and_tax(
    web_exported_sheet
):
    for row in (13, 14):
        assert (
            web_exported_sheet[f"B{row}"].value.date()
            == datetime.date.today()
        )

        assert (
            web_exported_sheet[f"D{row}"].value
            == "10%"
        )


# ============================================================
# EXPORT-E2E-019
# 複数Contentの整合性
# ============================================================

def test_web_excel_multiple_contents(
    web_exported_sheet,
    web_export_job
):
    actual = {
        (
            web_exported_sheet[f"A{row}"].value,
            web_exported_sheet[f"E{row}"].value,
            web_exported_sheet[f"D{row}"].value
        )
        for row in (13, 14)
    }

    expected = {
        (
            item["text"],
            item["price"],
            item["tax_rate"]
        )
        for item in web_export_job["contents"]
    }

    assert actual == expected


# ============================================================
# EXPORT-E2E-020
# Contentが0件の場合
# ============================================================

def test_web_excel_without_contents(
    auth_page,
    e2e_server,
    export_db,
    export_dependencies,
    tmp_path
):
    uid = uuid.uuid4().hex[:12]

    with Session(export_db) as db:
        tool = db.execute(
            select(Tool).where(Tool.id.in_([1, 2, 3, 4]))
        ).scalars().first()

        if tool is None:
            pytest.skip("Web系Toolが存在しません")

        job = Job(
            title=f"E2E_Web_Empty_{uid}",
            created=datetime.date.today(),
            tool_type_id=tool.id,
            client_id=export_dependencies["client_id"],
            agency_id=export_dependencies["agency_id"],
            account_id=export_dependencies["account_id"],
            project_id=export_dependencies["project_id"],
            price=tool.price,
            estimated=0,
            invoiced=0,
            github_repository=""
        )

        db.add(job)
        db.flush()
        job_id = job.id
        job_title = job.title
        job_price = job.price
        db.commit()

    output_path = download_estimate(
        auth_page,
        e2e_server,
        job_id,
        tmp_path
    )

    workbook = load_workbook(output_path)

    try:
        sheet = workbook["シート1"]

        assert sheet["A12"].value == job_title
        assert sheet["E12"].value == job_price
        assert sheet["D12"].value == "0%"
    finally:
        workbook.close()

    assert get_estimated(export_db, job_id) == 1


# ============================================================
# EXPORT-E2E-021
# Web系Jobのestimated更新
# ============================================================

def test_web_job_estimated_status(
    web_exported_excel,
    export_db,
    web_export_job
):
    assert get_estimated(
        export_db,
        web_export_job["job_id"]
    ) == 1
