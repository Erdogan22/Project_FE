from flask import Blueprint, flash, render_template, request, redirect, abort, url_for, current_app
from flask_login import login_required, current_user
from flask_wtf import CSRFProtect
from models import db, User, Project
from functools import wraps
from werkzeug.utils import secure_filename
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


# Gestion des utilisateurs
@admin.route('/admin/users')
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
@admin.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    return render_template('admin/dashboard.html')

# Creer un utilisateur
@admin.route('/admin/create-user', methods=['GET', 'POST'])
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

        #user.set_password(request.form['password'])

        password = secrets.token_hex(12)  # Generate a random 16-character password
        user.set_password(password)

        user.must_change_password = True

        db.session.add(user)
        db.session.commit()

        
        from app import send_account_email
        send_account_email(user, password, action="create")
        
        flash("✅ Utilisateur créé et email envoyé avec succès.")
        return redirect(url_for('admin.dashboard'))

    return render_template(
        'admin/creation_utilisateurs.html',
        managers=managers,
        projects=projects
    )

# Suprimer un utilisateur
@admin.route('/admin/delete-user/<int:user_id>', methods=['POST'])
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
@admin.route('/admin/reset-password/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def reset_password(user_id):
    user = User.query.get_or_404(user_id)

    new_password = secrets.token_hex(12)  # Generate a random 12-character password
    temp_password = new_password[:12]  # Ensure it's 12 characters long
    user.set_password(temp_password)
    user.must_change_password = True

    db.session.commit()

    from app import send_account_email
    send_account_email(user, temp_password, action="reset")

    flash(f"✅ Mot de passe réinitialisé et email envoyé avec succès. Nouveau mot de passe: {temp_password}")
    return redirect(url_for('admin.dashboard'))
