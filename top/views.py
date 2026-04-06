from flask import render_template, Blueprint
from flask_login import login_required

from models import session,Job,Client,Agency,Project

top = Blueprint(
    "top",
    __name__,
    template_folder="templates",
)

@top.route("/")
@login_required
def index():
    #クライアント名と代理店名をjobに紐付ける
    jobs=session.query(Job).join(Client).join(Agency).join(Project).filter(Job.estimated==0).all()
    return render_template("top/index.html",jobs=jobs)