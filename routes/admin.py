from flask import Blueprint, flash, render_template, request, redirect, abort, url_for, current_app, send_from_directory
from flask_login import login_required, current_user
from flask_wtf import CSRFProtect
from models import Timesheet, db, User, Project, MonthlyReport, Payroll, VacationRequest, VacationBalance
from functools import wraps
from werkzeug.utils import secure_filename
from sqlalchemy import extract, func
from datetime import datetime, date
import os
import secrets

admin = Blueprint('admin', __name__)
# csrf = CSRFProtect(admin)

# Allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Decorator to check for admin role
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


# Function to generate monthly report for a user
def generate_monthly_report(user_id, month, year):
    entries = Timesheet.query.filter(
        Timesheet.user_id == user_id,
        extract('month', Timesheet.date) == month,
        extract('year', Timesheet.date) == year
    ).all()

    total_work = 0
    total_absence = 0
    work_days = set()
    absence_days = set()

    for e in entries:
        if e.type == "work":
            total_work += e.value
            work_days.add(e.date.day)

        elif e.type in ["absence1", "absence2"]:
            total_absence += e.value
            absence_days.add(e.date.day)

    # business rules
    overtime = max(0, total_work - 160)   # 160h/month standard
    base_salary = 3000                    # example
    hourly_rate = base_salary / 160
    bonus = overtime * hourly_rate * 1.5
    salary_total = base_salary + bonus

    report = MonthlyReport.query.filter_by(
        user_id=user_id,
        month=month,
        year=year
    ).first()

    if not report:
        report = MonthlyReport(
            user_id=user_id,
            month=month,
            year=year
        )

    report.total_work_hours = total_work
    report.total_absence_hours = total_absence
    report.work_days = len(work_days)
    report.absence_days = len(absence_days)
    report.overtime_hours = overtime
    report.salary_base = base_salary
    report.salary_bonus = bonus
    report.salary_total = salary_total
    report.vacation_days_used = len(absence_days)

    db.session.add(report)
    db.session.commit()

    return report


# Utility function to calculate number of days between two dates for vacation calculation
def calculate_days(start, end):
    delta = end - start
    return delta.days + 1  # Include both start and end dates

# Route pour que les utilisateurs puissent faire une demande de congé
@admin.route('/user/vaccation/request', methods=['GET', 'POST'])
@login_required
def request_vacation():
    if request.method == 'POST':
        start = datetime.strptime(request.form['start'], "%Y-%m-%d").date()
        end = datetime.strptime(request.form['end'], "%Y-%m-%d").date()
        vtype = request.form['type']
        reason = request.form.get('reason')

        days = calculate_days(start, end)

        balance = VacationBalance.query.filter_by(
            user_id=current_user.id,
            year=datetime.now().year
        ).first()

        if not balance:
            balance = VacationBalance(
                user_id=current_user.id,
                year=datetime.now().year,
                total_days=20,
                used_days=0,
                remaining_days=20
            )
            db.session.add(balance)
            db.session.commit()

        if vtype == "paid" and days > balance.remaining_days:
            flash("❌ Solde de congé insuffisant")
            return redirect(url_for('admin.request_vacation'))

        # Handle file upload for sick leave
        justificatif_filename = None
        if vtype == "sick":
            if 'justificatif' not in request.files:
                flash("❌ Justificatif médical requis pour un congé maladie")
                return redirect(url_for('admin.request_vacation'))
            
            file = request.files['justificatif']
            if file and file.filename == '':
                flash("❌ Aucun fichier sélectionné")
                return redirect(url_for('admin.request_vacation'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to make filename unique
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_")
                filename = timestamp + filename
                file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
                justificatif_filename = filename
            else:
                flash("❌ Type de fichier non autorisé")
                return redirect(url_for('admin.request_vacation'))

        req = VacationRequest(
            user_id=current_user.id,
            start_date=start,
            end_date=end,
            days=days,
            type=vtype,
            reason=reason,
            justificatif=justificatif_filename
        )

        db.session.add(req)
        db.session.commit()

        flash("✅ Demande de congé envoyée")
        return redirect(url_for('user.user_vacation'))

    return render_template('user/vaccation_request.html')


# Route pour que les administrateurs puissent gérer les demandes de congé
@admin.route('/vaccations', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_vacations():
    requests = VacationRequest.query.order_by(
        VacationRequest.created_at.desc()
    ).all()

    # Build a mapping of user_id -> User to display names in the template
    user_ids = list({r.user_id for r in requests}) if requests else []
    users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
    users_map = {u.id: u for u in users}

    return render_template('admin/vaccations.html', requests=requests, users_map=users_map)

# Route pour approuver une demande de congé
@admin.route('/vaccation/approve/<int:req_id>')
@login_required
@admin_required
def approve_vacation(req_id):
    req = VacationRequest.query.get_or_404(req_id)

    if req.status != "pending":
        return redirect(url_for('admin.manage_vacations'))

    req.status = "approved"

    if req.type == "paid":
        balance = VacationBalance.query.filter_by(
            user_id=req.user_id,
            year=req.start_date.year
        ).first()

        balance.used_days += req.days
        balance.remaining_days -= req.days

    db.session.commit()
    flash("✅ Congé approuvé")
    return redirect(url_for('admin.manage_vacations'))


# Route pour rejeter une demande de congé
@admin.route('/vaccation/reject/<int:req_id>')
@login_required
@admin_required
def reject_vacation(req_id):
    req = VacationRequest.query.get_or_404(req_id)
    req.status = "rejected"
    db.session.commit()

    flash("❌ Congé refusé")
    return redirect(url_for('admin.manage_vacations'))


# Route to download justificatif file
@admin.route('/vaccation/justificatif/<int:req_id>')
@login_required
@admin_required
def download_justificatif(req_id):
    req = VacationRequest.query.get_or_404(req_id)
    
    if not req.justificatif:
        flash("❌ Aucun justificatif n'a été fourni")
        return redirect(url_for('admin.manage_vacations'))
    
    try:
        return send_from_directory(
            current_app.config['UPLOAD_FOLDER'],
            req.justificatif,
            as_attachment=True
        )
    except FileNotFoundError:
        flash("❌ Fichier justificatif non trouvé")
        return redirect(url_for('admin.manage_vacations'))

# Route pour générer le rapport mensuel d'un utilisateur (accessible par admin)
@admin.route('/generate-report/<int:user_id>')
@login_required
@admin_required
def generate_report(user_id):
    now = datetime.now()
    report = generate_monthly_report(user_id, now.month, now.year)

    flash("📊 Rapport mensuel généré")
    return redirect(url_for('admin.manage_users'))


# # Route pour que les utilisateurs puissent voir leurs rapports mensuels
# @admin.route('/user/reports')
# @login_required
# def user_reports():
#     reports = MonthlyReport.query.filter_by(
#         user_id=current_user.id
#     ).order_by(MonthlyReport.year.desc(), MonthlyReport.month.desc()).all()

#     return render_template('user/reports.html', reports=reports)


# Function to generate payroll for a user based on their monthly report
def generate_payroll(user_id, month, year):
    report = MonthlyReport.query.filter_by(
        user_id=user_id,
        month=month,
        year=year
    ).first()

    if not report:
        raise Exception("Monthly report not generated")

    BASE_SALARY = report.salary_base
    OVERTIME_RATE = 1.5
    TAX_RATE = 0.18          # 18%
    SOCIAL_RATE = 0.07       # 7%
    ABSENCE_PENALTY_PER_DAY = 80  # €
    
    # Calculate deductions for absences due to vacation or unpaid leave
    UNPAID_DAY_PENALTY = BASE_SALARY / 22

    unpaid_days = VacationRequest.query.filter_by(
        user_id=user_id,
        status="approved",
        type="unpaid"
    ).filter(
        extract('month', VacationRequest.start_date) == month,
        extract('year', VacationRequest.start_date) == year
    ).count()


    approved_paid_days = VacationRequest.query.filter_by(
        user_id=user_id,
        status="approved",
        type="paid"
    ).filter(
        extract('month', VacationRequest.start_date) == month,
        extract('year', VacationRequest.start_date) == year
    ).count()
    
    sick_days = VacationRequest.query.filter_by(
        user_id=user_id,
        status="approved",
        type="sick"
    ).filter(
        extract('month', VacationRequest.start_date) == month,
        extract('year', VacationRequest.start_date) == year
    ).count()

    report.vacation_days = approved_paid_days
    report.unpaid_days = unpaid_days
    report.sick_days = sick_days  
    ###############################################################

    overtime_pay = report.overtime_hours * (BASE_SALARY/160) * OVERTIME_RATE
    bonus = report.salary_bonus
    

    deductions = 0
    # Deductions for unpaid leave
    deductions += unpaid_days * UNPAID_DAY_PENALTY

    # Deductions for absences (if you want to penalize paid absences as well)
    deductions += report.absence_days * ABSENCE_PENALTY_PER_DAY

    gross_salary = BASE_SALARY + overtime_pay + bonus - deductions

    taxes = gross_salary * TAX_RATE
    social = gross_salary * SOCIAL_RATE

    net_salary = gross_salary - taxes - social

    payroll = Payroll.query.filter_by(
        user_id=user_id,
        month=month,
        year=year
    ).first()

    if not payroll:
        payroll = Payroll(
            user_id=user_id,
            month=month,
            year=year,
            base_salary=BASE_SALARY,
            overtime_pay=overtime_pay,
            bonus=bonus,
            deductions=deductions,
            taxes=taxes,
            social_security=social,
            net_salary=net_salary
        )
    else:
        payroll.base_salary = BASE_SALARY
        payroll.overtime_pay = overtime_pay
        payroll.bonus = bonus
        payroll.deductions = deductions
        payroll.taxes = taxes
        payroll.social_security = social
        payroll.net_salary = net_salary

    db.session.add(payroll)
    db.session.commit()



# Route pour générer la fiche de paie d'un utilisateur (accessible par admin)
@admin.route('/generate-payroll/<int:user_id>')
@login_required
@admin_required
def generate_payroll_route(user_id):
    now = datetime.now()
    generate_monthly_report(user_id, now.month, now.year)
    generate_payroll(user_id, now.month, now.year)

    flash("💰 Paie générée avec succès")
    return redirect(url_for('admin.manage_users'))



# Gestion des utilisateurs
@admin.route('/users')
@login_required
@admin_required
def manage_users():
    users = User.query.filter(User.role != 'admin').all()
    
    '''Search functionalties'''
    page = request.args.get('page', 1, type=int)
    q = request.args.get('q', '')

    users = User.query.filter(
        User.email.contains(q) | User.nom.contains(q) | User.prenom.contains(q)
    ).paginate(page=page, per_page=5)

    return render_template('admin/gestion_utilisateur.html', users=users, q=q)


# Tableau de bord administrateur
# @admin.route('/admin/dashboard')
# @login_required
# @admin_required
# def dashboard():
#     return render_template('admin/dashboard.html')

@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    now = datetime.now()
    month = now.month
    year = now.year

    total_users = User.query.count()

    total_hours = db.session.query(func.sum(Timesheet.value)).filter(
        Timesheet.type == "work",
        extract('month', Timesheet.date) == month,
        extract('year', Timesheet.date) == year
    ).scalar() or 0

    total_absences = db.session.query(func.sum(Timesheet.value)).filter(
        Timesheet.type != "work",
        extract('month', Timesheet.date) == month,
        extract('year', Timesheet.date) == year
    ).scalar() or 0

    # Example payroll logic
    users = User.query.all()
    total_payroll = 0
    for u in users:
        rate = getattr(u, "hourly_rate", 10)
        user_hours = db.session.query(func.sum(Timesheet.value)).filter(
            Timesheet.user_id == u.id,
            Timesheet.type == "work",
            extract('month', Timesheet.date) == month,
            extract('year', Timesheet.date) == year
        ).scalar() or 0
        total_payroll += user_hours * rate

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_hours=total_hours,
        total_absences=total_absences,
        total_payroll=round(total_payroll, 2),
        month=now.strftime("%B %Y")
    )





# liste des utilisateurs pour la feuille de temps
@admin.route('/timesheet')
@login_required
@admin_required
def admin_timesheet_user():
    users = User.query.filter(User.role != 'admin').all()
    return render_template('admin/timesheet_users.html', users=users)

# Creer un utilisateur
@admin.route('/create-user', methods=['GET', 'POST'])
@login_required
@admin_required
def create_user():
    if current_user.role != 'admin':
        return "Access denied", 403

    managers = User.query.filter_by(role='manager').all()
    projects = Project.query.filter(Project.status == 'active').all()
    
    filename = 'default.png'
    file = request.files.get('profile_image')

    if request.method == 'POST':
        user = User(
            nom=request.form['nom'],
            prenom=request.form['prenom'],
            email=request.form['email'],
            role=request.form['role'],
            manager_id=request.form.get('manager_id'),
            project_id=request.form.get('project_id'),
            # profile_image=request.form.get('profile_image')
            
        )
        ''' Upload profile image '''
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
        user.profile_image = filename

        user.set_password(request.form['password'])

        # password = secrets.token_hex(12)  # Generate a random 16-character password
        # user.set_password(password)

        user.must_change_password = True

        db.session.add(user)
        db.session.commit()

        
        # from app import send_account_email
        # send_account_email(user, password, action="create")
        
        flash("✅ Utilisateur créé et email envoyé avec succès.")
        return redirect(url_for('admin.dashboard'))

    return render_template(
        'admin/creation_utilisateurs.html',
        managers=managers,
        projects=projects
    )

# Voir les détails d'un utilisateur
@admin.route('/user/<int:user_id>')
@login_required
@admin_required
def view_user(user_id):
    user = User.query.get_or_404(user_id)
    return render_template('admin/user_profile.html', user=user)

# Suprimer un utilisateur
@admin.route('/delete-user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        return "Cannot delete admin user", 403
    
    # if current_user.role != 'admin':
    #     return "Access denied", 403

    db.session.delete(user)
    db.session.commit()

    flash("✅ Utilisateur supprimé avec succès.")

    return redirect(url_for('admin.dashboard'))

# Reinitialiser le mot de passe d'un utilisateur par l'administrateur
@admin.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)

    new_password = secrets.token_hex(12)  # Generate a random 12-character password
    temp_password = new_password[:12]  # Ensure it's 12 characters long
    flash(f"🔐 Nouveau mot de passe généré: {temp_password}")  # For demonstration purposes only, remove in production
    user.set_password(temp_password)
    user.must_change_password = True

    db.session.commit()

    # from app import send_account_email
    # send_account_email(user, temp_password, action="reset")

    # flash(f"✅ Mot de passe réinitialisé et email envoyé avec succès. Nouveau mot de passe: {temp_password}")
    return redirect(url_for('admin.dashboard'))


# Route to manage timesheet for a specific user
@admin.route('/timesheet/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_timesheet(user_id):
    user = User.query.get_or_404(user_id)
    now = datetime.now()
    month = now.strftime("%B %Y")
    year = now.year
    month_num = now.month

    if request.method == "POST":
        # Optional: clear old entries for that month (avoid duplicates)
        Timesheet.query.filter(
            Timesheet.user_id == user.id,
            db.extract('month', Timesheet.date) == month_num,
            db.extract('year', Timesheet.date) == year
        ).delete()

        for day in range(1, 32):
            for entry_type in ["work", "absence1", "absence2"]:
                value = request.form.get(f"{entry_type}_{day}")

                if value and value.strip() != "" and float(value) > 0:
                    ts = Timesheet(
                        user_id=user.id,
                        date=date(year, month_num, day),
                        type=entry_type,
                        value=float(value),
                        project="Projet 1",
                        created_by=current_user.id,
                        validated=True   # admin = auto-validated
                    )
                    db.session.add(ts)

        db.session.commit()
        flash("✅ Feuille de temps enregistrée pour l'utilisateur.")
        return redirect(url_for('admin.view_user', user_id=user.id))

    return render_template(
        "timesheet.html",
        user=user,
        month=month
    )