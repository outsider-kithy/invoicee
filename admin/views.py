from flask import redirect,render_template,request,url_for,flash,Blueprint
from flask_login import login_required

from models import session,Client,Agency,Account,Tool,Tax,Project

admin = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
)

@admin.route("/",methods=("GET","POST"))
@login_required
def index():
    if request.method=='GET':
        clients=session.query(Client).all()
        agencys=session.query(Agency).all()
        accounts=session.query(Account).all()
        taxes=session.query(Tax).all()
        projects=session.query(Project).filter(Project.isfinished == 0).all()
        return render_template("admin/index.html",clients=clients,agencys=agencys,accounts=accounts,taxes=taxes,projects=projects)
    elif request.method=='POST':
        #クライアント名が送られてきたら
        client=request.form.get('client')
        #代理店名が送られてきたら
        agency=request.form.get('agency')
        #担当者名が送られてきたら
        account=request.form.get('account')
        agencyName=request.form.get('agencyName')
        #ツール名が送られてきたら
        tool=request.form.get('tool')
        price=request.form.get('price')
        tax=request.form.get('tax')
        error=None
        #終了するプロジェクトが送られてきたら
        finished_project=request.form.get('finished_project')

        if client:
            #現在のclientの件数を求めて+1した値を新しいデータのidとする
            clientId=session.query(Client).count()
            session.add(Client(id=clientId+1,
                               client_name=client
                               ))
            session.commit()

        elif agency:
            #現在のagencyの件数を求めて+1した値を新しいデータのidとする
            agencyId=session.query(Agency).count()
            session.add(Agency(id=agencyId+1,
                               agency_name=agency
                               ))
            session.commit()

        elif account:
            #POSTされてきたagencyNameからagency_idを検索
            a=session.query(Agency).filter(Agency.agency_name==agencyName)
            for i in a:
                accountAgencyId=i.id
            #現在のaccountの件数を求めて+1した値を新しいデータのidとする
            accountId=session.query(Account).count()
            session.add(Account(id=accountId+1,
                                account_name=account,
                                agency_id=accountAgencyId
                                ))
            session.commit()

        elif tool:
            toolId=session.query(Tool).count()
            t = session.query(Tax).filter(Tax.rate==tax)
            for u in t:
                taxId = u.id
            session.add(Tool(id=toolId+1,
                             tool_type=tool,
                             price=price,
                             tax_rate_id = taxId
                             ))
            session.commit()
            
        # 選択したプロジェクトを終了にする
        elif finished_project:
            project=session.query(Project).filter(Project.project_name == finished_project).first()
            project.isfinished = 1
            session.commit()

        else:
            error='何も入力されていません'
            flash(error)
            return render_template('admin/index.html',error=error)
        
        session.commit()

        return redirect(url_for('top.index'))