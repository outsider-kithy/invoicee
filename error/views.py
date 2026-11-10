from sqlalchemy.exc import SQLAlchemyError
from flask import render_template, Blueprint, current_app, request

from models import session

error = Blueprint(
    "error",
    __name__,
    url_prefix="/error",
    template_folder="templates",
)

@error.route("/",methods = ("GET","POST"))
def index():
    if request.method == 'GET':
        return render_template(
            "error/index.html",
            error_message="データベースエラーが発生しました。"
        ), 500
    elif request.method == 'POST':
        return render_template(
			"error/index.html",
			error_message="データベースエラーが発生しました。"
		), 500


@error.app_errorhandler(SQLAlchemyError)
def handle_database_error(e):

    try:
        session.rollback()
    except Exception:
        current_app.logger.exception("Database rollback failed")

    current_app.logger.error(
        "Database Error",
        exc_info=(type(e), e, e.__traceback__)
    )

    return render_template(
        "error/index.html",
        error_message="データベースエラーが発生しました。"
    ), 500