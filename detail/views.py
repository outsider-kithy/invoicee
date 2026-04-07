from flask import render_template,request,Blueprint,redirect,url_for
from flask_login import login_required
from models import session,Job,Work,Content
from sqlalchemy import func

detail = Blueprint(
    "detail",
    __name__,
    template_folder="templates",
)

@detail.route("/",methods=("GET","POST"))
@login_required
def index():
    if request.method == "GET":
        selectedJobId = request.args.get("selectedJobId")
        selectedJob = (
            session.query(Job)
                .filter(Job.id == selectedJobId)
                .first()
            )

        contents = (
            session.query(Content)
            .filter(Content.job_id == selectedJobId)
            .all()
        )
        
        works = session.query(Work).all()

        total_price = (
            session.query(func.sum(Work.price))
            .join(Content, Content.work_id == Work.id)
            .filter(Content.job_id == selectedJobId)
            .scalar()
)
        return render_template(
            "detail/index.html", 
            selectedJob=selectedJob, 
            contents=contents, 
            works=works,
            total_price = total_price
        )
    
    elif request.method == "POST":
        update_job_id = request.form['update_job_id']
        update_works = request.form.getlist("update_work[]")
        update_contents = request.form.getlist("update_content[]")

        # Jobに紐づく既存のContent一覧を取得
        contents = (
            session.query(Content)
            .filter(Content.job_id == update_job_id)
            .order_by(Content.id)
            .all()
        )

        for content_record, work_type, work_content in zip(
            contents,
            update_works,
            update_contents,
        ):
            # 選択されたwork_typeに対応するWorkレコードを取得
            work_record = (
                session.query(Work)
                .filter(Work.work_type == work_type)
                .first()
            )

            # Contentテーブル更新
            content_record.work_id = work_record.id
            content_record.work_content = work_content

            session.commit()

        return redirect(url_for('update.index'))