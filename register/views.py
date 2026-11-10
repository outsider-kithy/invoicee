
from flask import (
    redirect,
    render_template,
    request,
    url_for,
    flash,
    Blueprint,
    current_app
)
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import IntegrityError
from models import session, User

register = Blueprint(
    "register",
    __name__,
    template_folder="templates",
)


@register.route("/", methods=("GET", "POST"))
def index():

    if request.method == "GET":
        return render_template("register/index.html")

    elif request.method == "POST":

        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        confirmation = request.form.get("confirmation", "")

        error = None

        # ユーザー名が未入力
        if not username:
            error = "名前を入力してください"

        # パスワードが未入力
        elif not password:
            error = "パスワードを入力してください"

        # パスワード確認が未入力
        elif not confirmation:
            error = "パスワードをもう一度入力してください"

        # パスワードが一致しない
        elif password != confirmation:
            error = "入力されたパスワードが一致しません"

        else:
            # ユーザー名の重複チェック
            existing_user = (
                session.query(User)
                .filter(User.username == username)
                .first()
            )

            if existing_user is not None:
                error = "このユーザー名は既に使用されています"

            else:
                # パスワードをハッシュ化
                hashed = generate_password_hash(password)

                try:
                    # 新規ユーザーを登録
                    session.add(
                        User(
                            username=username,
                            password=hashed
                        )
                    )
                    session.commit()

                except IntegrityError:
                    # UNIQUE制約違反などの場合
                    session.rollback()

                    error = "このユーザー名は既に使用されています"

                except Exception:
                    # その他のDB登録エラー
                    session.rollback()

                    current_app.logger.exception(
                        "User registration failed"
                    )

                    error = "ユーザー登録中にエラーが発生しました"

                else:
                    # 登録成功
                    return redirect(url_for("login.index"))

        # エラーメッセージを表示
        if error:
            flash(error)

        return render_template(
            "register/index.html",
            error=error
        )
