from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Timesheet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
   # user = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    date = db.Column(db.Date)
    type = db.Column(db.String(50))  # work, absence1, absence2
    type = db.Column(db.String(20))  # work, absence1, absence2
    value = db.Column(db.Float)
    project = db.Column(db.String(50))

    created_by = db.Column(db.Integer)  # qui a créé l'entrée (utile pour admin)
    validated = db.Column(db.Boolean, default=False)  # validation par admin



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
    

# Rapport mensuel pour chaque utilisateur (calculé par admin)
class MonthlyReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    month = db.Column(db.Integer, nullable=False)   # 1-12
    year = db.Column(db.Integer, nullable=False)

    total_work_hours = db.Column(db.Float, default=0)
    total_absence_hours = db.Column(db.Float, default=0)

    work_days = db.Column(db.Integer, default=0)
    absence_days = db.Column(db.Integer, default=0)

    overtime_hours = db.Column(db.Float, default=0)

    salary_base = db.Column(db.Float, default=0)
    salary_bonus = db.Column(db.Float, default=0)
    salary_total = db.Column(db.Float, default=0)

    vacation_days_used = db.Column(db.Integer, default=0)

    generated_at = db.Column(db.DateTime, default=datetime.utcnow)    


# Fiche de paie mensuelle (calculée par admin)
class Payroll(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    base_salary = db.Column(db.Float, nullable=False)
    overtime_pay = db.Column(db.Float, default=0)
    bonus = db.Column(db.Float, default=0)

    deductions = db.Column(db.Float, default=0)   # absences, penalties, taxes
    taxes = db.Column(db.Float, default=0)
    social_security = db.Column(db.Float, default=0)

    net_salary = db.Column(db.Float, nullable=False)

    status = db.Column(db.String(20), default="generated")
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)    

# Solde de congés pour chaque utilisateur (calculé par admin)
class VacationBalance(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    year = db.Column(db.Integer, nullable=False)

    total_days = db.Column(db.Integer, default=20)   # legal quota
    used_days = db.Column(db.Integer, default=0)
    remaining_days = db.Column(db.Integer, default=20)    


# Demande de congé faite par l'utilisateur (traitée par admin)
class VacationRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    days = db.Column(db.Integer, nullable=False)

    type = db.Column(db.String(20), default="paid")  
    # paid | unpaid | sick | exceptional

    status = db.Column(db.String(20), default="pending")
    # pending | approved | rejected

    reason = db.Column(db.String(255))
    justificatif = db.Column(db.String(255), nullable=True)  # File path for sick leave certificate
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  
    