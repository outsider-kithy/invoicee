from flask import Flask,redirect,render_template,request,url_for,flash,Blueprint
from flask_login import login_required

from models import session,Job,Client,Agency,Project,Tool,Account

record = Blueprint(
    "record",
    __name__,
    template_folder="templates",
)

@record.route("/",methods=("GET","POST"))
@login_required
def index():
    if request.method=='GET':
        projects=session.query(Project).all()
        tools=session.query(Tool).all()
        clients=session.query(Client).all()
        agencys=session.query(Agency).all()
        accounts=session.query(Account).all()
        return render_template("record/index.html",projects=projects,tools=tools,clients=clients,agencys=agencys,accounts=accounts)

    elif request.method=='POST':
        title=request.form['title']
        project=request.form['project']
        tool=request.form['tool']
        error=None
        
        if not title:
            error="タイトルが入力されていません"
        if not project:
            error="プロジェクト名が選択されていません"
        if not tool:
            error="ツール名が選択されていません"
        if error is not None:
            flash(error)
        else:
            clientId=None
            agencyId=None
            accountId=None
            projectId=None
            price=0

            #ツール名からtool_idを取得
            t=session.query(Tool).filter(Tool.tool_type==tool)
            for i in t:
                toolId=i.id

                #ツールidから価格を判定
                p=0
                p=session.query(Tool).filter(Tool.id==toolId)
                for j in p:
                    price=j.price

            #プロジェクト名からproject_idを取得
            pj=session.query(Project).filter(Project.project_name==project)
            for n in pj:
                projectId=n.id
                clientId = n.client_id
                agencyId = n.agency_id
                accountId = n.account_id

                #ジョブテーブルに新たなジョブを登録
                session.add(Job(
                    title=title,
                    tool_type_id=toolId,
                    client_id=clientId,
                    agency_id=agencyId,
                    account_id=accountId,
                    project_id=projectId,
                    price=price,
                    estimated=0,
                    invoiced=0
                ))
                session.commit()

            return redirect(url_for('top.index'))
    