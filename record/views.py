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
        client=request.form['client']
        agency=request.form['agency']
        account=request.form['account']
        error=None
        
        if not title:
            error="タイトルが入力されていません"
        if not project:
            error="プロジェクト名が選択されていません"
        if not tool:
            error="ツール名が選択されていません"
        if not client:
            error="クライアント名が選択されていません"
        if not agency:
            error="代理店名が選択されていません"
        if not account:
            error="担当者名が選択されていません"
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
            #session.close()
            for i in t:
                toolId=i.id
                #print(toolId)

                #ツールidから価格を判定
                p=0
                p=session.query(Tool).filter(Tool.id==toolId)
                #session.close()
                for j in p:
                    price=j.price
                    #print(price)

            #プロジェクト名からproject_idを取得
            pj=session.query(Project).filter(Project.project_name==project)
            #session.close()
            for n in pj:
                projectId=n.id
                #projectName=n.project_name
                #print(projectName)


            #クライアント名からclient_idを取得
            c=session.query(Client).filter(Client.client_name==client)
            #session.close()
            for k in c:
                clientId=k.id
                #clientName=k.client_name
                #print(clientName)

            #エージェンシー名からagency_idを取得
            a=session.query(Agency).filter(Agency.agency_name==agency)
            #session.close()
            for l in a:
                agencyId=l.id
                #agencyName=l.agency_name
                #print(agencyName)
            
            #担当者名からaccount_idを取得
            ac=session.query(Account).filter(Account.account_name==account)
            #session.close()
            for m in ac:
                accountId=m.id
                #accountName=m.account_name
                #print(accountName)

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
    