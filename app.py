from flask import Flask, render_template, request, redirect
from flask_wtf import CSRFProtect
from models import db, Timesheet, User, Project
from datetime import date
from flask import flash
from werkzeug.security import generate_password_hash
from flask_mail import Mail, Message


import os
from flask_login import LoginManager
from routes.auth import auth
from routes.user import user_bp
from routes.admin import admin


UPLOAD_FOLDER = 'static/profile_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

'''------ Pour upload d image de profil ---------'''
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2 MB limit

app.secret_key = "super-secret-key"
csrf = CSRFProtect(app)

'''-----------------'''
csrft = CSRFProtect(app)

app.secret_key = "super-secret-key"
db.init_app(app)




'''----------Configuration de l'email--------'''
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'admin@example.com'
app.config['MAIL_PASSWORD'] = 'yourpassword' # Replace with your email password
app.config['MAIL_DEFAULT_SENDER'] = 'admin@example.com'

mail = Mail(app)


def send_account_email(user, password, action="create"):
    if action == "create":
        subject = "Votre compte a été créé"
        body = f"""
Bonjour {user.prenom},

Votre compte a été créé par l'administrateur.

Email : {user.email}
Mot de passe provisoire : {password}

Veuillez changer votre mot de passe après connexion.

Cordialement,
Administration
"""
    else:
        subject = "Réinitialisation de votre mot de passe"
        body = f"""
Bonjour {user.prenom},

Votre mot de passe a été réinitialisé.

Nouveau mot de passe provisoire : {password}

Veuillez le changer après connexion.

Cordialement,
Administration
"""

    msg = Message(subject, recipients=[user.email], body=body)
    mail.send(msg)

'''-----------------------------------------'''

# added by Mamadou
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "auth.login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth)
app.register_blueprint(admin)
app.register_blueprint(user_bp)

'''-----------------'''



@app.route("/feuille-de-temps", methods=["GET", "POST"])
def timesheet():
    if request.method == "POST":

        for day in range(1, 32):

            for entry_type in ["work", "absence1", "absence2"]:
                value = request.form.get(f"{entry_type}_{day}")

                if value and float(value) > 0:
                    ts = Timesheet(
                        user="Mahmoud",
                        date=date(2026, 1, day),
                        type=entry_type,
                        value=float(value),
                        project="Projet 1"
                    )
                    db.session.add(ts)

        db.session.commit()
        flash("✅ Feuille de temps enregistrée avec succès.")

        return redirect("/feuille-de-temps")

    return render_template("timesheet.html")

@app.route("/", methods=["GET"])
def accueil():
    return render_template("accueil.html")

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # 🔐 Creation d admin par default s'il nexiste pas
        admin = User.query.filter_by(email="admin@admin.com").first()
        if not admin:
            admin = User(
                nom="Admin",
                prenom="System",
                email="admin@admin.com",
                role="admin",
                profile_image=None,
                must_change_password=False
            )
            admin.password_hash = generate_password_hash("admin123")
            db.session.add(admin)
            db.session.commit()

    app.run(debug=True) 
# Note: Ensure that the database and templates folder are properly set up for this code to run successfully.

