from flask import render_template,request,Blueprint
from flask_login import login_required
from models import session,Job,Client,Agency,Project,Tool,Account,Work,Content,Tax

from helper import writeExcel

estimate = Blueprint(
    "estimate",
    __name__,
    template_folder="templates",
)

@estimate.route("/",methods = ("GET","POST"))
@login_required
def index():
    if request.method == 'GET':
        #未見積もりのjobをhtmlに渡す
        jobs = session.query(Job).join(Client).join(Agency).join(Project).filter(Job.estimated == 0).all()
       
        if not jobs:
            error = "ジョブは0件です。"
            return render_template("estimate/index.html",jobs = [], error = error)
        
        return render_template("estimate/index.html",jobs = jobs, error = "")
    
    elif request.method == 'POST':
        estimateJobIds = request.form.getlist('job')

        exportJobList=[]
        for i in estimateJobIds:
            exportJob = session.query(Job).join(Tool).filter(Job.id == int(i)).all()

            for j in exportJob:
                #jobがweb・LP・htmlメールであれば、作業内容を記載
                if j.tool_type_id == 1 or j.tool_type_id==2 or j.tool_type_id==3 or j.tool_type_id==4:
                    #まずjobそのもののタイトルと金額を記載
                    exportJobTitle = j.title
                    exportJobPrice = j.price
                    
                    exportContents = None
                    exportContentsPrice = None
                    exportContentsCreated = None
                    exportContentsTaxRate = 0.0
                    contents = session.query(Content).join(Work).join(Tax).filter(Content.job_id == int(i)).all()

                    if not contents:
                        exportJobList.append([
                            j.title,
                            None,
                            j.price,
                            j.created,
                            exportContentsTaxRate
                        ])

                    for k in contents:
                        exportContents = k.work_content
                        exportContentsPrice = k.work.price
                        exportContentsCreated = k.created
                        #税率
                        exportContentsTaxRate = k.work.tax_rate.rate
                      
                        exportJobList.append([
							exportJobTitle,
							exportContents,
							exportContentsPrice,
							exportContentsCreated,
							exportContentsTaxRate
						])
                
                #jobが紙媒体であればjobタイトルのみを記載
                else:
                    exportJobTitle = j.title
                    exportJobPrice = j.price
                    exportJobCreated = j.created

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
                j.estimated = 1

            #見積書の宛先を検索・入力
            exportAgencyName = (
				session.query(Agency.agency_name)
				.join(Job, Job.agency_id == Agency.id)
				.filter(Job.id == int(i))
				.scalar()
			)

            #担当者を検索・入力
            exportAccountName = (
				session.query(Account.account_name)
				.join(Job, Job.account_id == Account.id)
				.filter(Job.id == int(i))
				.scalar()
			)

            #プロジェクト名を検索・入力
            exportProjectName = (
				session.query(Project.project_name)
				.join(Job, Job.project_id == Project.id)
				.filter(Job.id == int(i))
				.scalar()
			)
			
            session.commit()
            exportFile = writeExcel(exportJobList,exportAgencyName,exportAccountName,exportProjectName)
            session.close()
            exportJobList = []
            return exportFile

        
