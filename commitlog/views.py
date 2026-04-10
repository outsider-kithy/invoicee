import os
import datetime
from zoneinfo import ZoneInfo
import requests
from flask import render_template, request, Blueprint
from models import session,Job
from dotenv import load_dotenv

jst = ZoneInfo("Asia/Tokyo")

commitlog = Blueprint(
    "commitlog",
    __name__,
    template_folder="templates",
)

@commitlog.route("/")
def index():
    selected_job_id = request.args.get("selectedJobId", type=int)

    # Job取得
    job = (
        session.query(Job)
        .filter(Job.id == selected_job_id)
        .first()
    )
    # print(f'ジョブ作成日:{job.created}')
    #print(job.created)

    if not job:
        return "Job not found", 404

    if not job.github_repository:
        return "GitHub repository is not set", 400

    # "username/repository_name" を分割
    owner, repo = job.github_repository.split("/")

    headers = {
        "Accept": "application/vnd.github+json"
    }

    # 非公開リポジトリの場合は Personal Access Token を付与
    load_dotenv('.env')
    token = os.getenv("GITHUB_TOKEN")
    headers["Authorization"] = f"Bearer {token}"

    since = str(job.created) + "T00:00:00Z"
    #print(since)

    url = f"https://api.github.com/repos/{owner}/{repo}/commits?since={since}&per_page=100"

    response = requests.get(
        url,
        headers=headers
    )
    print(response.url)

    if response.status_code != 200:
        return f"GitHub API Error: {response.status_code}", 500

    commit_data = response.json()

    commits = []

    for commit in commit_data:
        commits.append({
            "message": commit["commit"]["message"],
            "date": commit["commit"]["author"]["date"],
        })
    #print(commits)

    return render_template(
        "commitlog/index.html",
        job=job,
        commits=commits
    )