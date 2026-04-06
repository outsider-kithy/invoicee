from flask import redirect,render_template,request,url_for,flash,Blueprint
from flask_login import login_required

from models import session,Client,Agency,Account,Tool,Tax

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
        return render_template("admin/index.html",clients=clients,agencys=agencys,accounts=accounts,taxes=taxes)
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

        if client:
            #現在のclientの件数を求めて+1した値を新しいデータのidとする
            clientId=session.query(Client).count()
            session.add(Client(id=clientId+1,
                               client_name=client
                               ))
        elif agency:
            #現在のagencyの件数を求めて+1した値を新しいデータのidとする
            agencyId=session.query(Agency).count()
            session.add(Agency(id=agencyId+1,
                               agency_name=agency
                               ))
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
        else:
            error='何も入力されていません'
            flash(error)
            return render_template('admin/index.html',error=error)
        
        session.commit()

        return redirect(url_for('top.index'))