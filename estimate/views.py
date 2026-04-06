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
        return render_template("estimate/index.html",jobs=jobs)
    
    elif request.method=='POST':
        estimateJobIds=request.form.getlist('job')
        exportJobList=[]
        for i in estimateJobIds:
            exportJob=session.query(Job).join(Tool).filter(Job.id==i).all()

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

                    for k in contents:
                        exportContents=k.work_content
                        exportContentsPrice=k.work.price
                        exportContentsCreated=k.created
                        #税率
                        exportContentTaxRate = k.tax_rate.rate
                      
                        exportJobList.append([
                            exportJobTitle,
                            exportContents,
                            exportContentsPrice,
                            exportContentsCreated,
                            exportContentTaxRate
                            ])
                
                #jobが紙媒体であればjobタイトルのみを記載
                else:
                    exportJobTitle=j.title
                    exportJobPrice=j.price
                    exportJobCreated=j.created

                    #税率
                    exportJobTaxRate = None
                    tool = session.query(Tool).filter(Tool.id == j.tool_type_id).first()
                    exportJobTaxRate = tool.tax_rate.rate

                    exportJobList.append([
                        exportJobTitle,
                        None,
                        exportJobPrice,
                        exportJobCreated,
                        exportJobTaxRate
                        ])

                #出力したjobを見積済に
                j.estimated=1
                session.commit()

            #見積書の宛先を検索・入力
            exportAgencyName=None
            agency=session.query(Job).join(Agency).filter(Job.id==i).all()
            for m in agency:
                agencyId=m.agency_id
                agencyName=session.query(Agency).filter(Agency.id==agencyId)
                for n in agencyName:
                    exportAgencyName=n.agency_name
            
            #担当者を検索・入力
            exportAccountName=None
            account=session.query(Job).join(Account).filter(Job.id==i).all()
            for o in account:
                accountId=o.account_id
                accountName=session.query(Account).filter(Account.id==accountId)
                for p in accountName:
                    exportAccountName=p.account_name

            #プロジェクト名を検索・入力
            exportProjectName=None
            project=session.query(Job).join(Project).filter(Job.id==i).all()
            for q in project:
                projectId=q.project_id
                projectName=session.query(Project).filter(Project.id==projectId)
                for r in projectName:
                    exportProjectName=r.project_name

                exportFile=writeExcel(exportJobList,exportAgencyName,exportAccountName,exportProjectName)
                session.close()
                exportJobList=[]
                return exportFile

        
