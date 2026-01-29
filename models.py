from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50))
    date = db.Column(db.Date)
    type = db.Column(db.String(20))  # work, absence1, absence2
    value = db.Column(db.Float)
    project = db.Column(db.String(50))
