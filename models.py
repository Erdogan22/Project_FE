from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user = db.Column(db.String(50))
    date = db.Column(db.Date)
    type = db.Column(db.String(20))  # work, absence1, absence2
    value = db.Column(db.Float)
    project = db.Column(db.String(50))



'''Added by Mamadou'''
class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), unique=True, nullable=False)
    status = db.Column(db.String(20))  # actif, termine

# creation d'utilisateurs
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20))  # admin, manager, consultant

    manager_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    manager = db.relationship('User', remote_side=[id])

    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    project = db.relationship('Project')

    must_change_password = db.Column(db.Boolean, default=True)

    profile_image = db.Column(db.String(255), default=None)  # chemin vers l'image de profil

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    