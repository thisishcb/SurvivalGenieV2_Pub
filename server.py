# https://community.plotly.com/t/sqlite-in-multi-page-dash-app/71879/18

# import flask
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from flask_migrate import Migrate

server = Flask(__name__)
server.app_context().push()
server.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///survivalgenie2.db"
server.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(server)
migrate = Migrate(server, db)

# # https://www.digitalocean.com/community/tutorials/how-to-use-flask-sqlalchemy-to-interact-with-databases-in-a-flask-application
class task_tb(db.Model):
    __tablename__ = 'task_records'

    ssid = db.Column(db.String(40), nullable=False, primary_key=True)
    analysis_type = db.Column(db.String(40), nullable=False)
    status = db.Column(db.Integer, nullable=False)
    # 0 for DONE; 1 for still in process; 2 for failed; 3 for expired
    start_time = db.Column(db.DateTime(timezone=True),default=func.now())
    update_time = db.Column(db.DateTime(timezone=True),onupdate=func.now())
    visit_freq = db.Column(db.Integer, default=1)

    def __init__(self, ssid, analysis_type, status):
        """a = task_tb('iddddd', 'single_gene', 0)"""
        self.ssid = ssid
        self.analysis_type = analysis_type
        self.status = status
        self.visit_freq = 1
    
    def __repr__(self):
        return f'{self.ssid}-{self.analysis_type} | status {self.status} | {self.start_time} - {self.update_time}'

    def is_finished(self):
        return self.status==0 or self.status==4
    
    def add_visit(self):
        if not self.visit_freq:
            self.visit_freq=0
        self.visit_freq += 1

    def __str__(self):
        status_keys = {0:"Finished",
                1:"Processing",
                2:"Failed",
                3:"Expired",
                4:"Protected"}
        return f'Session {self.ssid} is {status_keys[self.status]}'

db.create_all() # does nothing if the table is there but will update fields