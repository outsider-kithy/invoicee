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

    login_manager.init_app(app)

    from top import views as top_views
    app.register_blueprint(top_views.top, url_prefix="/top")

    from record import views as record_views
    app.register_blueprint(record_views.record, url_prefix="/record")

    from update import views as update_views
    app.register_blueprint(update_views.update, url_prefix="/update")

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

    return app