
from unittest.mock import patch

import pytest
from sqlalchemy.exc import SQLAlchemyError

from error.views import handle_database_error


# ERR-001
def test_error_get_status_code(client):
    """
    GET /error/ がHTTP 500を返すことを確認する。
    """
    with patch("error.views.render_template") as mock_render:
        mock_render.return_value = "ERROR PAGE"

        response = client.get("/error/")

        assert response.status_code == 500
        assert response.get_data(as_text=True) == "ERROR PAGE"


# ERR-002
def test_error_get_template(client):
    """
    正しいテンプレートとエラーメッセージが
    渡されることを確認する。
    """
    with patch("error.views.render_template") as mock_render:
        mock_render.return_value = "ERROR PAGE"

        response = client.get("/error/")

        assert response.status_code == 500

        mock_render.assert_called_once_with(
            "error/index.html",
            error_message="データベースエラーが発生しました。"
        )


# ERR-003
def test_error_post_not_allowed(client):
    """
    /error/ はGET専用であり、
    POSTアクセスが405になることを確認する。
    """
    with patch("error.views.render_template") as mock_render:
        response = client.post("/error/")

        assert response.status_code == 405
        mock_render.assert_not_called()


# ERR-004
def test_database_error_rollback(app):
    """
    SQLAlchemyError発生時に
    session.rollback() が実行されることを確認する。
    """
    error = SQLAlchemyError("DB connection failed")

    with app.app_context():
        with patch("error.views.session") as mock_session, \
             patch("error.views.render_template") as mock_render, \
             patch.object(app.logger, "error"):

            mock_render.return_value = "ERROR PAGE"

            handle_database_error(error)

            mock_session.rollback.assert_called_once()


# ERR-005
def test_database_error_response(app):
    """
    SQLAlchemyError発生時に
    HTTP 500とエラーページを返すことを確認する。
    """
    error = SQLAlchemyError("DB connection failed")

    with app.app_context():
        with patch("error.views.session") as mock_session, \
             patch("error.views.render_template") as mock_render, \
             patch.object(app.logger, "error"):

            mock_render.return_value = "ERROR PAGE"

            response, status_code = handle_database_error(error)

            assert status_code == 500
            assert response == "ERROR PAGE"

            mock_render.assert_called_once_with(
                "error/index.html",
                error_message="データベースエラーが発生しました。"
            )


# ERR-006
def test_database_error_logging(app):
    """
    SQLAlchemyError発生時に
    エラーログが記録されることを確認する。
    """
    try:
        raise SQLAlchemyError("Test database error")
    except SQLAlchemyError as error:
        db_error = error

    with app.app_context():
        with patch("error.views.session") as mock_session, \
             patch("error.views.render_template") as mock_render, \
             patch.object(app.logger, "error") as mock_log_error:

            mock_render.return_value = "ERROR PAGE"

            handle_database_error(db_error)

            mock_log_error.assert_called_once_with(
                "Database Error",
                exc_info=(
                    type(db_error),
                    db_error,
                    db_error.__traceback__
                )
            )


# ERR-007
def test_database_error_rollback_failure(app):
    """
    rollback()自体が失敗しても
    HTTP 500を返し、ログを記録することを確認する。
    """
    error = SQLAlchemyError("Original DB error")

    with app.app_context():
        with patch("error.views.session") as mock_session, \
             patch("error.views.render_template") as mock_render, \
             patch.object(app.logger, "error") as mock_log_error, \
             patch.object(app.logger, "exception") as mock_log_exception:

            mock_session.rollback.side_effect = RuntimeError(
                "Rollback failed"
            )

            mock_render.return_value = "ERROR PAGE"

            response, status_code = handle_database_error(error)

            assert status_code == 500
            assert response == "ERROR PAGE"

            mock_session.rollback.assert_called_once()

            mock_log_exception.assert_called_once_with(
                "Database rollback failed"
            )

            mock_log_error.assert_called_once_with(
                "Database Error",
                exc_info=(
                    type(error),
                    error,
                    error.__traceback__
                )
            )
