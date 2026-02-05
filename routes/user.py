from flask import Blueprint, flash, render_template, request, redirect, url_for, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from flask_wtf import CSRFProtect
from models import db
import os

user_bp = Blueprint('user', __name__)

# csrf = CSRFProtect(user_bp)

@user_bp.route('/user', methods=['GET'])
@login_required
def user_page():
    if current_user.role == 'admin':
        abort(403)
    return render_template('page_utilisateur.html')   
 
    
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
        return redirect(url_for('user.user_page'))
    
    return render_template('changer_password.html')

# profile d'utilistaeur
@user_bp.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
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