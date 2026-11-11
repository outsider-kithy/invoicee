"""Invoicee workflow E2E: login -> admin -> record -> estimate -> logout.

Run: python -m pytest tests/e2e/test_workflow_e2e.py -v

Requires existing fixtures e2e_config, e2e_server, and a PostgreSQL invoicee_test
schema with at least one non-Web Tool (id >= 5). Project is prepared directly
in the TEST database because its registration form was not provided.
"""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from openpyxl import load_workbook
from playwright.sync_api import Page, expect
from sqlalchemy import create_engine, text


@pytest.fixture
def workflow_engine(e2e_config):
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.fail("DATABASE_URL is missing from .env.test")
    engine = create_engine(url)
    if engine.url.database != "invoicee_test":
        engine.dispose()
        pytest.fail("Workflow tests may run only against invoicee_test")
    try:
        yield engine
    finally:
        engine.dispose()


def _find_id(conn, table, column, value):
    # Only constant, internally specified table/column names are used here.
    return conn.execute(
        text(f"SELECT id FROM {table} WHERE {column} = :value ORDER BY id DESC LIMIT 1"),
        {"value": value},
    ).scalar_one_or_none()


def test_workflow_login_to_logout(page: Page, e2e_server, e2e_config,
                                  workflow_engine, tmp_path: Path):
    """WORKFLOW-E2E-001: complete user journey with DB cleanup."""
    page.set_viewport_size({"width": 1440, "height": 900})
    suffix = uuid4().hex[:10]
    client_name = f"E2E_CLIENT_{suffix}"
    agency_name = f"E2E_AGENCY_{suffix}"
    account_name = f"E2E_ACCOUNT_{suffix}"
    project_name = f"E2E_PROJECT_{suffix}"
    job_title = f"E2E_JOB_{suffix}"
    ids = {"client": None, "agency": None, "account": None,
           "project": None, "job": None}

    try:
        # 1. Log in using the real login screen (not the pre-authenticated fixture).
        page.goto(f"{e2e_server}/login/")
        page.locator('input[name="username"]').fill(e2e_config["TEST_USERNAME"])
        page.locator('input[name="password"]').fill(e2e_config["TEST_PASSWORD"])
        page.locator('form input[type="submit"], form button[type="submit"]').first.click()
        expect(page).to_have_url(f"{e2e_server}/top/")

        # 2. Create a Client and Agency using the actual admin form.
        page.goto(f"{e2e_server}/admin/")
        page.locator("#client").fill(client_name)
        page.locator('form.record input[type="submit"]').click()
        with workflow_engine.connect() as conn:
            ids["client"] = _find_id(conn, "clients", "client_name", client_name)
        assert ids["client"] is not None, "Client registration failed"

        page.goto(f"{e2e_server}/admin/")
        page.locator("#agency").fill(agency_name)
        page.locator('form.record input[type="submit"]').click()
        with workflow_engine.connect() as conn:
            ids["agency"] = _find_id(conn, "agencys", "agency_name", agency_name)
        assert ids["agency"] is not None, "Agency registration failed"

        # Account requires agencyName; the agency should now be in the options.
        page.goto(f"{e2e_server}/admin/")
        page.locator("#account").fill(account_name)
        page.locator("#agencyName").select_option(label=agency_name)
        page.locator('form.record input[type="submit"]').click()
        with workflow_engine.connect() as conn:
            ids["account"] = _find_id(conn, "accounts", "account_name", account_name)
        assert ids["account"] is not None, "Account registration failed"

        # 3. Prepare a Project in the TEST DB. Replace with /project/ UI
        # interaction once its HTML and view logic are available.
        with workflow_engine.begin() as conn:
            tool = conn.execute(text(
                "SELECT id, tool_type FROM tools WHERE id >= 5 ORDER BY id LIMIT 1"
            )).mappings().first()
            assert tool is not None, "Seed a non-Web Tool (id >= 5) in invoicee_test"
            ids["project"] = conn.execute(text("""
                INSERT INTO projects
                    (project_name, client_id, agency_id, account_id, created, isfinished)
                VALUES (:name, :client, :agency, :account, CURRENT_DATE, 0)
                RETURNING id
            """), {
                "name": project_name, "client": ids["client"],
                "agency": ids["agency"], "account": ids["account"],
            }).scalar_one()

        # 4. Register a Job using the actual record form.
        page.goto(f"{e2e_server}/record/")
        page.locator("#title").fill(job_title)
        page.locator("#project").select_option(label=project_name)
        page.locator("#tool").select_option(label=tool["tool_type"])
        page.locator('form.record input[type="submit"]').click()
        with workflow_engine.connect() as conn:
            ids["job"] = _find_id(conn, "jobs", "title", job_title)
        assert ids["job"] is not None, "Job registration failed"

        # 5. Confirm job is visible in the top page.
        page.goto(f"{e2e_server}/top/")
        expect(page.locator("tr.jobs").filter(has_text=job_title)).to_be_visible()

        # 6. Download estimate and verify the DB status.
        page.goto(f"{e2e_server}/estimate/")
        radio = page.locator(f'input[type="radio"][name="job"][value="{ids["job"]}"]')
        expect(radio).to_be_visible()
        radio.check()
        with page.expect_download() as download_info:
            page.locator('form.estimate input[type="submit"]').click()
        output = tmp_path / f"workflow-{suffix}.xlsx"
        download_info.value.save_as(output)
        workbook = load_workbook(output, read_only=True, data_only=False)
        try:
            sheet = workbook["シート1"]
            assert sheet["A12"].value == job_title
        finally:
            workbook.close()
        with workflow_engine.connect() as conn:
            estimated = conn.execute(
                text("SELECT estimated FROM jobs WHERE id = :id"),
                {"id": ids["job"]},
            ).scalar_one()
        assert estimated == 1

        # 7. Log out and confirm protected page redirects to login.
        page.goto(f"{e2e_server}/top/")
        page.locator('nav a:has-text("ログアウト")').click()
        expect(page).to_have_url(f"{e2e_server}/login/")
        page.goto(f"{e2e_server}/top/")
        expect(page).not_to_have_url(f"{e2e_server}/top/")

    finally:
        # Clean only this run's records, in reverse FK dependency order.
        with workflow_engine.begin() as conn:
            if ids["job"] is not None:
                conn.execute(text("DELETE FROM contents WHERE job_id = :id"),
                             {"id": ids["job"]})
                conn.execute(text("DELETE FROM jobs WHERE id = :id"),
                             {"id": ids["job"]})
            if ids["project"] is not None:
                conn.execute(text("DELETE FROM projects WHERE id = :id"),
                             {"id": ids["project"]})
            if ids["account"] is not None:
                conn.execute(text("DELETE FROM accounts WHERE id = :id"),
                             {"id": ids["account"]})
            if ids["agency"] is not None:
                conn.execute(text("DELETE FROM agencys WHERE id = :id"),
                             {"id": ids["agency"]})
            if ids["client"] is not None:
                conn.execute(text("DELETE FROM clients WHERE id = :id"),
                             {"id": ids["client"]})
