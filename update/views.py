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
        selectedJobId = request.form.get("jobId", "")

    if not selectedJobId:
        flash("ジョブが選択されていません")
        return redirect(url_for("update.index"))

    session.close()

    return redirect(
        url_for("detail.index", selectedJobId=selectedJobId)
    )