from flask import render_template, Blueprint, request
from flask_login import login_required

notfound = Blueprint(
    "notfound",
    __name__,
    template_folder="templates",
)

@notfound.route("/",methods=("GET","POST"))
@login_required
def index():
    if request.method=='GET':
        return render_template(
            "notfound/index.html",
            error_message="指定のページは見つかりませんでした。"
        ), 404
    
    elif request.method=='POST':
        return render_template(
            "notfound/index.html",
			error_message="指定のページは見つかりませんでした。"
        ), 404

