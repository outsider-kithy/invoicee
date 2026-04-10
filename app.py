import os
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import session
from sqlalchemy.ext.declarative import declarative_base
from flask_login import LoginManager,login_manager
from dotenv import load_dotenv
from models import session,User

# データベース
ENV_MODE = os.getenv("ENV_MODE", "development")
DOTENV_FILE = f".env.{ENV_MODE}"
load_dotenv(dotenv_path=DOTENV_FILE)
DATABASE_URL = os.getenv("DATABASE_URL")

engine=create_engine(DATABASE_URL,isolation_level='AUTOCOMMIT')
Base=declarative_base()
db_uri = os.environ.get(DATABASE_URL)

login_manager=LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY']='secret_key'
    app.config['SQLALCHEMY_DATABASE_URI']=DATABASE_URL
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
        "pool_recycle": 300
    }

    login_manager.init_app(app)

    from top import views as top_views
    app.register_blueprint(top_views.top, url_prefix="/top")

    from record import views as record_views
    app.register_blueprint(record_views.record, url_prefix="/record")

    from update import views as update_views
    app.register_blueprint(update_views.update, url_prefix="/update")

    from detail import views as detail_views
    app.register_blueprint(detail_views.detail, url_prefix="/detail")

    from commitlog import views as commitlog_views
    app.register_blueprint(commitlog_views.commitlog, url_prefix="/commitlog")

    from webhook import views as webhook_views
    app.register_blueprint(webhook_views.webhook, url_prefix="/webhook")

    from estimate import views as estimate_views
    app.register_blueprint(estimate_views.estimate, url_prefix="/estimate")

    from admin import views as admin_views
    app.register_blueprint(admin_views.admin, url_prefix="/admin")

    from project import views as project_views
    app.register_blueprint(project_views.project, url_prefix="/project")

    from login import views as login_views
    app.register_blueprint(login_views.login, url_prefix="/login")

    from register import views as register_views
    app.register_blueprint(register_views.register, url_prefix="/register")

    from logout import views as logout_views
    app.register_blueprint(logout_views.logout, url_prefix="/logout")

    @app.teardown_request
    def shutdown_session(exception=None):
        if exception:
            session.rollback()
        session.remove()

    return app