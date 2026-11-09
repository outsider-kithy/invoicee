from flask import redirect,render_template,request,url_for,flash,Blueprint
from flask_login import login_required
from models import session,Client,Agency,Account,Tool,Tax,Project

admin = Blueprint(
    "admin",
    __name__,
    template_folder="templates",
)

@admin.route("/",methods = ("GET","POST"))
@login_required
def index():
    if request.method == 'GET':
        clients = session.query(Client).all()
        agencys = session.query(Agency).all()
        accounts = session.query(Account).all()
        taxes = session.query(Tax).all()
        projects = session.query(Project).filter(Project.isfinished == 0).all()
        return render_template("admin/index.html",clients = clients,agencys = agencys,accounts = accounts,taxes = taxes,projects = projects)
    elif request.method == 'POST':
        #クライアント名が送られてきたら
        client = request.form.get('client')
        #代理店名が送られてきたら
        agency = request.form.get('agency')
        #担当者名が送られてきたら
        account = request.form.get('account')
        agencyName = request.form.get('agencyName')
        #ツール名が送られてきたら
        tool = request.form.get('tool')
        price = request.form.get('price')
        tax = request.form.get('tax')
        error = None
        #終了するプロジェクトが送られてきたら
        finished_project = request.form.get('finished_project')

        if client:
            session.add(Client(client_name=client))
                
        elif agency:
            session.add(Agency(agency_name=agency))

        elif account:
            #POSTされてきたagencyNameからagency_idを検索
            accountAgency = session.query(Agency).filter(Agency.agency_name == agencyName).first()

            if accountAgency is None:
                flash("指定された代理店が存在しません")
                return redirect(url_for("admin.index"))

            session.add(Account(account_name = account, agency_id = accountAgency.id))

        elif tool:
            tax_rate = session.query(Tax).filter(Tax.rate == tax).first()
            
            if tax_rate is None:
                flash("指定された税率が存在しません")
                return redirect(url_for("admin.index"))
            
            session.add(Tool(tool_type = tool, price = price, tax_rate_id = tax_rate.id))
            
        # 選択したプロジェクトを終了にする
        elif finished_project:
            project = session.query(Project).filter(Project.project_name == finished_project).first()
            
            if project is None:
                flash("指定されたプロジェクトが存在しません")
                return redirect(url_for("admin.index"))
            
            project.isfinished = 1

        else:
            error = '何も入力されていません'
            flash(error)
            return redirect(url_for("admin.index"))
        
        session.commit()

        return redirect(url_for('top.index'))