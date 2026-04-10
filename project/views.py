from flask import Flask,redirect,render_template,request,url_for,flash,Blueprint
from flask_login import login_required
from sqlalchemy import func

from models import session,Client,Agency,Account,Project

project = Blueprint(
    "project",
    __name__,
    template_folder="templates",
)

@project.route("/",methods=("GET","POST"))
@login_required
def index():
    if request.method=='GET':
        clients=session.query(Client).all()
        agencys=session.query(Agency).all()
        accounts=session.query(Account).all()
        return render_template("project/index.html",clients=clients,agencys=agencys,accounts=accounts)

    elif request.method=='POST':
        project=request.form['project']
        projectClientName=request.form['projectClientName']
        projectAgencyId=request.form['projectAgencyId']
        projectAgencyName = session.query(Agency).filter(Agency.id == projectAgencyId).first()
        projectAccountName=request.form['projectAccountName']
        error=None
        
        if not project:
            error="プロジェクト名が入力されていません"
        if not projectClientName:
            error="クライアント名が選択されていません"
        if not projectAgencyName:
            error="代理店名が入力されていません"
        if not projectAccountName:
            error="担当者名が入力されていません"
        if error is not None:
            flash(error)
        else:
            projectClientId=None
            projectAccountId=None
            c=session.query(Client).filter(Client.client_name==projectClientName)
            for j in c:
                projectClientId=j.id
        
            aci=session.query(Account).filter(Account.account_name==projectAccountName)
            for l in aci:
                projectAccountId=l.id
            
                max_id = session.query(func.max(Project.id)).scalar()
                new_id = max_id + 1 if max_id else 1

                session.add(Project(
                    id=new_id,
                    project_name=project, 
                    client_id=projectClientId, 
                    agency_id=projectAgencyId, 
                    account_id=projectAccountId,
                    isfinished=0
                ))
                session.commit()

            return redirect(url_for('top.index'))