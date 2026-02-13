from flask import Blueprint, flash, render_template, request, redirect, url_for, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf import CSRFProtect
from models import Payroll, Timesheet, MonthlyReport, VacationRequest, VacationBalance, db
from datetime import datetime
from sqlalchemy import func, extract
import os

user_bp = Blueprint('user', __name__)

# csrf = CSRFProtect(user_bp)

@user_bp.route('/', methods=['GET'])
@login_required
def user_page():
    if current_user.role == 'admin':
        abort(403)
    return redirect(url_for('user.user_profile'))
    
    
    return render_template('page_utilisateur.html')

@user_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    if current_user.role == 'admin':
        abort(403)

    if request.method == 'POST':
        new_password = request.form['password']
        current_user.set_password(new_password)
        current_user.must_change_password = False
        db.session.commit()
        flash("✅ Mot de passe changé avec succès.")
        return redirect(url_for('user.user_profile'))
    
    return render_template('changer_password.html')

# profile d'utilistaeur
@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if current_user.role == 'admin':
        abort(403)
        
    if request.method == 'POST':
        file = request.files.get('profile_image')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            current_user.profile_image = filename
            db.session.commit()
            flash("✅ Image de profil mise à jour avec succès.")
    return render_template('page_utilisateur.html')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Dashboard utilisateur
@user_bp.route("/dashboard")
@login_required
def user_dashboard():
    if current_user.role == "admin":
        return redirect("/admin/dashboard")

    now = datetime.now()
    month = now.month
    year = now.year

    # Total hours
    total_hours = db.session.query(func.sum(Timesheet.value)).filter(
        Timesheet.user_id == current_user.id,
        Timesheet.type == "work",
        extract('month', Timesheet.date) == month,
        extract('year', Timesheet.date) == year
    ).scalar() or 0

    # Absences
    absences = db.session.query(func.sum(Timesheet.value)).filter(
        Timesheet.user_id == current_user.id,
        Timesheet.type != "work",
        extract('month', Timesheet.date) == month,
        extract('year', Timesheet.date) == year
    ).scalar() or 0

    # Vacation days (example logic)
    vacation_used = absences
    vacation_total = 30
    vacation_left = vacation_total - vacation_used

    # Salary logic (example)
    hourly_rate = current_user.hourly_rate if hasattr(current_user, "hourly_rate") else 10
    estimated_salary = total_hours * hourly_rate

    timesheets = Timesheet.query.filter_by(user_id=current_user.id)\
        .order_by(Timesheet.date.desc()).limit(10).all()

    return render_template(
        "user/dashboard.html",
        total_hours=total_hours,
        absences=absences,
        vacation_left=vacation_left,
        estimated_salary=estimated_salary,
        timesheets=timesheets,
        month=now.strftime("%B %Y")
    )    

# Route pour que les utilisateurs puissent voir leurs rapports mensuels
@user_bp.route('/reports')
@login_required
def user_reports():
    reports = MonthlyReport.query.filter_by(
        user_id=current_user.id
    ).order_by(MonthlyReport.year.desc(), MonthlyReport.month.desc()).all()

    return render_template('user/reports.html', reports=reports)



# Route pour que les utilisateurs puissent voir leurs fiches de paie
@user_bp.route('/payroll')
@login_required
def user_payroll():
    payrolls = Payroll.query.filter_by(
        user_id=current_user.id
    ).order_by(Payroll.year.desc(), Payroll.month.desc()).all()

    return render_template('user/payroll.html', payrolls=payrolls)


# Route pour que les utilisateurs puissent voir leur solde de congés et faire des demandes de congé
@user_bp.route('/vaccation')
@login_required
def user_vacation():
    balance = VacationBalance.query.filter_by(
        user_id=current_user.id,
        year=datetime.now().year
    ).first()

    requests = VacationRequest.query.filter_by(
        user_id=current_user.id
    ).order_by(VacationRequest.created_at.desc()).all()

    return render_template(
        'user/vaccation.html',
        balance=balance,
        requests=requests
    )

@user_bp.route('/payslips/')
@login_required
def user_payslips():
    payslips = Payroll.query.filter_by(
        user_id=current_user.id).all()
    return render_template('user/payslips.html', payslips=payslips)