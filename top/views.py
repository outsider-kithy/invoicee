from flask import render_template, Blueprint
from flask_login import login_required
from models import session,Job,Client,Agency,Project,Content,Work
from sqlalchemy import func

top = Blueprint(
    "top",
    __name__,
    template_folder="templates",
)

@top.route("/")
@login_required
def index():
    #クライアント名と代理店名をjobに紐付ける
    jobs = (
    session.query(Job)
    .join(Client)
    .join(Agency)
    .join(Project)
    .filter(Job.estimated == 0)
    .all()
    )

    job_list = []
    monthly_total_price = 0

    for job in jobs:
        total_price = (
            session.query(func.coalesce(func.sum(Work.price), 0))
            .join(Content, Content.work_id == Work.id)
            .filter(Content.job_id == job.id)
            .scalar()
        )

        monthly_total_price += total_price

        job_list.append({
            "job": job,
            "current_price": total_price,
        })

        # print(job_list)

    return render_template("top/index.html",job_list=job_list, monthly_total_price=monthly_total_price)