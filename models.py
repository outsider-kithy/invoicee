import os
from sqlalchemy import Column,Integer,Numeric,String,ForeignKey,create_engine
from sqlalchemy.orm import relationship,sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import datetime
from sqlalchemy.sql.sqltypes import Date
from flask_login import UserMixin
from dotenv import load_dotenv

# データベース
ENV_MODE = os.getenv("ENV_MODE", "development")
DOTENV_FILE = f".env.{ENV_MODE}"
load_dotenv(dotenv_path=DOTENV_FILE)
DATABASE_URL = os.getenv("DATABASE_URL")

engine=create_engine(DATABASE_URL,isolation_level='AUTOCOMMIT')
Base=declarative_base()
db_uri = os.environ.get(DATABASE_URL)

#セッションの設定
Base.metadata.create_all(engine)
Session=sessionmaker(bind=engine)
session=Session()

#ユーザーテーブル
class User(UserMixin,Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True,autoincrement=True)
    username=Column(String,unique=True)
    password=Column(String)

#ジョブテーブル
class Job(Base):
    __tablename__='jobs'
    id=Column(Integer,primary_key=True,autoincrement=True)
    title=Column(String)
    created=Column(Date,index=True,default=datetime.date.today())
    tool_type_id=Column(Integer,ForeignKey('tools.id'))
    client_id=Column(Integer,ForeignKey('clients.id'))
    agency_id=Column(Integer,ForeignKey('agencys.id'))
    account_id=Column(Integer,ForeignKey('accounts.id'))
    project_id=Column(Integer,ForeignKey(('projects.id')))
    price=Column(Integer)
    estimated=Column(Integer)
    invoiced=Column(Integer)
    github_repository = Column(String)

    tool_type=relationship("Tool")
    client=relationship("Client")
    agency=relationship("Agency")
    account=relationship("Account")
    project=relationship("Project")
    content=relationship("Content")

#ツールテーブル
class Tool(Base):
    __tablename__='tools'
    id=Column(Integer,primary_key=True,autoincrement=True)
    tool_type=Column(String)
    price=Column(Integer)
    tax_rate_id=Column(Integer, ForeignKey("taxes.id"))
    
    job=relationship("Job",back_populates="tool_type")
    tax_rate=relationship("Tax")

#作業テーブル
class Work(Base):
    __tablename__="works"
    id=Column(Integer,primary_key=True,autoincrement=True)
    work_type=Column(String)
    price=Column(Integer)
    tax_rate_id=Column(Integer, ForeignKey("taxes.id"))

    tax_rate=relationship("Tax")

#作業内容テーブル
class Content(Base):
    __tablename__="contents"
    id=Column(Integer,primary_key=True,autoincrement=True)
    created=Column(Date,index=True,default=datetime.date.today())
    job_id=Column(Integer,ForeignKey('jobs.id'))
    work_id=Column(Integer,ForeignKey('works.id'))
    work_content=Column(String)
    tax_rate_id=Column(Integer, ForeignKey("taxes.id"))

    job=relationship("Job",back_populates="content")
    work=relationship("Work")
    tax_rate=relationship("Tax")

#クライアントテーブル
class Client(Base):
    __tablename__='clients'
    id=Column(Integer,primary_key=True,autoincrement=True)
    client_name=Column(String)

    job=relationship("Job",back_populates="client")

#エージェンシーテーブル
class Agency(Base):
    __tablename__='agencys'
    id=Column(Integer,primary_key=True,autoincrement=True)
    agency_name=Column(String)

    job=relationship("Job",back_populates="agency")

#担当者テーブル
class Account(Base):
    __tablename__='accounts'
    id=Column(Integer,primary_key=True,autoincrement=True)
    account_name=Column(String)
    agency_id=Column(Integer,ForeignKey('agencys.id'))

    agency=relationship("Agency")

#プロジェクトテーブル
class Project(Base):
    __tablename__='projects'
    id=Column(Integer,primary_key=True,autoincrement=True)
    created=Column(Date,index=True,default=datetime.date.today())
    project_name=Column(String)
    client_id=Column(Integer,ForeignKey('clients.id'))
    agency_id=Column(Integer,ForeignKey('agencys.id'))
    account_id=Column(Integer,ForeignKey('accounts.id'))
    isfinished=Column(Integer)

    client=relationship("Client")
    agency=relationship("Agency")
    account=relationship("Account")
    job=relationship("Job",back_populates="project")

#税率テーブル
class Tax(Base):
    __tablename__ = "taxes"
    id = Column(Integer, primary_key = True, autoincrement = True)
    rate = Column(Numeric(precision = 4, scale = 2))
