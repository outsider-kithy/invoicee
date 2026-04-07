from flask import redirect,render_template,request,url_for,flash,Blueprint
from flask_login import login_required

from models import session,Job,Client,Agency,Project,Work

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
        works=session.query(Work).all()
        return render_template("update/index.html",jobs=jobs,works=works)

    elif request.method=='POST':
        error=None
        selectedJobId=request.form['jobId']

        if not selectedJobId:
            error="ジョブが選択されていません"
            flash(error)
        
        session.close()

    # /detailルートに遷移
    return redirect(url_for('detail.index', selectedJobId=selectedJobId))