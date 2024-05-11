import os
from flask import Flask

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
#from sqlalchemy.ext.declarative import declarative_base

from flask_login import LoginManager,login_manager

from models import session, User

#データベース関係の設定
#開発用データベース
DATABASE_URL='postgresql://localhost/invoicee-new'
#本番用データベース
# DATABASE_URL = 'postgresql://{user}:{password}@{host}/{name}'.format(**{
#     'user': 'postgres',
#     'password': 'postgres',
#     'host': '0.0.0.0',
#     'name': 'invoicee'
# })

# Engine の作成
Engine = create_engine(DATABASE_URL)
Base = declarative_base()

# Sessionの作成
session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=Engine, info={"in_transaction": False}))

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return session.query(User).get(int(user_id))

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY']='secret_key'
    app.config['SQLALCHEMY_DATABASE_URI']=DATABASE_URL

    login_manager.init_app(app)

    #register
    from register import views as register_views
    app.register_blueprint(register_views.register, url_prefix="/register")

    #login
    from login import views as login_views
    app.register_blueprint(login_views.login, url_prefix="/login")

    #top
    from top import views as top_views
    app.register_blueprint(top_views.top, url_prefix="/top")

    #create
    from create import views as create_views
    app.register_blueprint(create_views.create, url_prefix="/create")

    #update
    from update import views as update_views
    app.register_blueprint(update_views.update, url_prefix="/update")

    #invoice
    from invoice import views as invoice_views
    app.register_blueprint(invoice_views.invoice, url_prefix="/invoice")

    #admin
    from admin import views as admin_views
    app.register_blueprint(admin_views.admin, url_prefix="/admin")

    #logout
    from logout import views as logout_views
    app.register_blueprint(logout_views.logout, url_prefix="/logout")

    return app