from flask import render_template, Blueprint, request

notfound = Blueprint(
    "notfound",
    __name__,
    template_folder="templates",
)

# 404ページへの直接アクセス
@notfound.route("/", methods=("GET", "POST"))
def index():
    return render_template(
        "notfound/index.html",
        error_message="指定のページは見つかりませんでした。"
    ), 404


# 存在しないURLへのアクセスを処理
@notfound.app_errorhandler(404)
def handle_not_found(e):
    return render_template(
        "notfound/index.html",
        error_message="指定のページは見つかりませんでした。"
    ), 404

# 405 Method Not Allowed
@notfound.app_errorhandler(405)
def handle_method_not_allowed(e):
    response = render_template(
        "notfound/index.html",
        error_message="このHTTPメソッドは許可されていません。"
    )

    return response, 405, {
        "Allow": ", ".join(e.valid_methods or [])
    }