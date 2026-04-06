from flask import redirect,render_template,request,url_for,flash,Blueprint
from flask_login import login_required

from models import session,Job,Client,Agency,Project,Work,Content,Tax

update = Blueprint(
    "update",
    __name__,
    template_folder="templates",
)

@update.route("/",methods=('GET','POST'))
@login_required
def index():
    if request.method=='GET':
        #未見積もりのwebサイト・LP・htmlメールのみ選択
        jobs=session.query(Job).join(Client).join(Agency).join(Project).filter(Job.estimated==0,Job.tool_type_id.between(1,4)).all()
        #session.close()
        works=session.query(Work).all()
        #session.close()
        return render_template("update/index.html",jobs=jobs,works=works)

    elif request.method=='POST':
        error=None
        selectedJob=request.form['job']
        work_type=request.form['work']
        content=request.form['content']

        if not selectedJob:
            error="ジョブが選択されていません"
            flash(error)
        elif not work_type:
            error="作業の種類が選択されていません"
            flash(error)
        elif not content:
            error="作業内容が入力されていません"
            flash(error)
        
        #選択したjobからjobIdを取得
        #print(selectedJob)
        jobId=None
        job_id=session.query(Job).filter(Job.id==selectedJob)
        for i in job_id:
            jobId=i.id
        session.close()
        
        #選択した作業の種類からwork_typeIdを取得
        #print(work_type)
        workTypeId=None
        work_typeId=session.query(Work).filter(Work.work_type==work_type)
        for j in work_typeId:
            workTypeId=j.id
        session.close()

    #contentsテーブルに新しく作業内容を追加
    session.add(Content(job_id=jobId,work_id=workTypeId,work_content=content,tax_rate_id=3))
    session.commit()

    return redirect(url_for('top.index'))