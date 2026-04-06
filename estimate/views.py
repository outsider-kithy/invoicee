from flask import render_template,request,Blueprint
from flask_login import login_required
from models import session,Job,Client,Agency,Project,Tool,Account,Work,Content,Tax

from helper import writeExcel

estimate = Blueprint(
    "estimate",
    __name__,
    template_folder="templates",
)

@estimate.route("/",methods=("GET","POST"))
@login_required
def index():
    if request.method=='GET':
        #未見積もりのjobをhtmlに渡す
        jobs=session.query(Job).join(Client).join(Agency).join(Project).filter(Job.estimated==0).all()
        #session.close()
        return render_template("estimate/index.html",jobs=jobs)
    
    elif request.method=='POST':
        estimateJobIds=request.form.getlist('job')
        exportJobList=[]
        for i in estimateJobIds:
            #print(i)
            exportJob=session.query(Job).join(Tool).filter(Job.id==i).all()
            #session.close()

            for j in exportJob:
                #jobがweb・LP・htmlメールであれば、作業内容を記載
                if j.tool_type_id==1 or j.tool_type_id==2 or j.tool_type_id==3 or j.tool_type_id==4:
                    #まずjobそのもののタイトルと金額を記載
                    exportJobTitle=j.title
                    exportJobPrice=j.price
                    
                    exportContents=None
                    exportContentsPrice=None
                    exportContentsCreated=None
                    exportContentTaxRate = None
                    contents=session.query(Content).join(Work).join(Tax).filter(Content.job_id==i).all()
                    #session.close()
                    for k in contents:
                        exportContents=k.work_content
                        #print(exportContents)
                        exportContentsPrice=k.work.price
                        #print(exportContentsPrice)
                        exportContentsCreated=k.created
                        #print(exportContentsCreated)
                        #税率
                        exportContentTaxRate = k.tax_rate.rate
                        #session.close()
                      
                        exportJobList.append([exportContents,exportContentsPrice,exportContentsCreated,exportContentTaxRate])
                
                #jobが紙媒体であればjobタイトルのみを記載
                else:
                    exportJobTitle=j.title
                    exportJobPrice=j.price
                    exportJobList.append([exportJobTitle,exportJobPrice,None])

                #出力したjobを見積済に
                j.estimated=1
                session.commit()

            #見積書の宛先を検索・入力
            exportAgencyName=None
            agency=session.query(Job).join(Agency).filter(Job.id==i).all()
            #session.close()
            for m in agency:
                agencyId=m.agency_id
                agencyName=session.query(Agency).filter(Agency.id==agencyId)
                #session.close()
                for n in agencyName:
                    exportAgencyName=n.agency_name
                    #print(exportAgencyName)
            
            #担当者を検索・入力
            exportAccountName=None
            account=session.query(Job).join(Account).filter(Job.id==i).all()
            #session.close()
            for o in account:
                accountId=o.account_id
                accountName=session.query(Account).filter(Account.id==accountId)
                #session.close()
                for p in accountName:
                    exportAccountName=p.account_name
                    #print(exportAccountName)

            #プロジェクト名を検索・入力
            exportProjectName=None
            project=session.query(Job).join(Project).filter(Job.id==i).all()
            #session.close()
            for q in project:
                projectId=q.project_id
                projectName=session.query(Project).filter(Project.id==projectId)
                #session.close()
                for r in projectName:
                    exportProjectName=r.project_name
                    #print(exportProjectName)
            
                exportFile=writeExcel(exportJobList,exportAgencyName,exportAccountName,exportProjectName)
                session.close()
                exportJobList=[]
                return exportFile

        #return redirect(url_for('top.index'))
        
