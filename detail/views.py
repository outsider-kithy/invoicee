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

            # Contentテーブルを更新
            content_record.work_id = work_record.id
            content_record.work_content = work_content

            #session.commit()

        # 新しい作業内容を登録
        new_works = request.form.getlist("new_work[]")
        new_contents = request.form.getlist("new_content[]")

        print(new_works)
        print(new_contents)

        if new_works and new_contents:

            for work_type, work_content in zip(new_works, new_contents):

                # 作業内容が空欄ならスキップ
                if not work_content.strip():
                    continue

                # 選択された work_type に対応する Work レコードを取得
                work_record = (
                    session.query(Work)
                    .filter(Work.work_type == work_type)
                    .first()
                )

                # work_type が見つからない場合はスキップ
                if not work_record:
                    continue

                # Contentテーブルに新しいレコードを追加
                new_content = Content(
                    job_id=update_job_id,
                    work_id=work_record.id,
                    work_content=work_content.strip()
                )

                session.add(new_content)

            session.commit()

        return redirect(url_for('update.index'))