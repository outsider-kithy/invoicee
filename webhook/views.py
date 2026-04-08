from flask import request,Blueprint
from models import session, Job, Content, Work
import logging
from sqlalchemy.exc import SQLAlchemyError

webhook = Blueprint(
    "webhook",
    __name__,
    template_folder="templates",
)

# ログ設定
logging.basicConfig(level=logging.INFO)

@webhook.route("/", methods=["GET", "POST"])
def index():
    try:
        payload = request.json

        # payloadが空の場合
        if not payload:
            logging.error("Payloadが空です")
            return {"error": "Payload is empty"}, 400

        repository = payload.get("repository")
        if not repository:
            logging.error("リポジトリが見つかりません")
            return {"error": "Repository information not found"}, 400

        repository_name = repository.get("full_name")
        if not repository_name:
            logging.error("リポジトリのフルネームが取得できません")
            return {"error": "Repository full_name not found"}, 400

        job = (
            session.query(Job)
            .filter(Job.github_repository == repository_name)
            .first()
        )

        if not job:
            logging.warning(f"合致するジョブがありません: {repository_name}")
            return {"error": "Matching Job not found"}, 404

        commits = payload.get("commits", [])

        # commits自体が空なら一応ログを出して正常終了
        if not commits:
            logging.info(f"コミットが空です: {repository_name}")
            return {"message": "No commits found"}, 200

        for commit in commits:
            try:
                message = commit.get("message", "").split("\n")[0].strip()

                if not message:
                    logging.warning("コミットメッセージが空です")
                    continue

                work_id = 1
                work_content = message

                if ":" in message:
                    work_type, content_text = message.split(":", 1)

                    work_type = work_type.strip()
                    content_text = content_text.strip()

                    work = (
                        session.query(Work)
                        .filter(Work.work_type == work_type)
                        .first()
                    )

                    if work:
                        work_id = work.id
                        work_content = content_text

                new_content = Content(
                    job_id=job.id,
                    work_id=work_id,
                    work_content=work_content
                )

                session.add(new_content)

            except Exception as commit_error:
                logging.exception(
                    f"コミットに失敗しました: {commit_error}"
                )
                continue

        session.commit()

        logging.info(
            f"Webhookプロセスに成功しました: {repository_name}"
        )

        return {"message": "OK"}, 200

    except SQLAlchemyError as db_error:
        session.rollback()
        logging.exception(f"データベースエラー: {db_error}")
        return {"error": "Database update failed"}, 500

    except Exception as e:
        session.rollback()
        logging.exception(f"Unexpected error: {e}")
        return {"error": "Internal Server Error"}, 500