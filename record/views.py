from flask import redirect,render_template,request,url_for,flash,Blueprint
from flask_login import login_required
from models import session,Job,Project,Tool

record = Blueprint(
    "record",
    __name__,
    template_folder="templates",
)

@record.route("/",methods=("GET","POST"))
@login_required
def index():
    if request.method == 'GET':
        projects = session.query(Project).filter(Project.isfinished == 0).all()
        tools = session.query(Tool).all()
        return render_template("record/index.html",projects = projects,tools = tools)

    elif request.method == 'POST':
        title = request.form['title']
        project = request.form['project']
        tool = request.form['tool']
        github_repository = request.form['github_repository']
        error = None
        
        if not title:
            error = "タイトルが入力されていません"
        if not project:
            error = "プロジェクト名が選択されていません"
        if not tool:
            error="ツール名が選択されていません"
        if error is not None:
            flash(error)
            return redirect(url_for("record.index"))
        else:

            #ツール名からtool_idを取得
            tool_record = (
                session.query(Tool)
                .filter(Tool.tool_type == tool)
                .first()
            )
            if tool_record is None:
                flash("指定されたツールが存在しません")
                return redirect(url_for("record.index"))

			# プロジェクト名からproject_idを取得
            project_record = (
                session.query(Project)
                .filter(Project.project_name == project)
                .first()
            )

            if project_record is None:
                flash("指定されたプロジェクトが存在しません")
                return redirect(url_for("record.index"))

			#ジョブテーブルに新たなジョブを登録
            session.add(Job(
				title = title,
				tool_type_id = tool_record.id,
				client_id = project_record.client_id,
				agency_id = project_record.agency_id,
				account_id = project_record.account_id,
				project_id = project_record.id,
				price = tool_record.price,
				estimated = 0,
				invoiced = 0,
				github_repository = github_repository
			))
            
            session.commit()

        return redirect(url_for('top.index'))
    