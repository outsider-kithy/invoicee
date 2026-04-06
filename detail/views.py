from flask import render_template,request,Blueprint
from flask_login import login_required
from models import session,Job,Client,Agency,Project,Tool,Account,Work,Content,Tax

from helper import writeExcel

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
        #print(selectedJob)

        contents = (
            session.query(Content)
            .filter(Content.job_id == selectedJobId)
            .all()
        )
        #print(contents)

        return render_template("detail/index.html", selectedJob=selectedJob, contents=contents)
    elif request.method == "POST":
        return render_template("detail/index.html", selectedJobId=selectedJobId)