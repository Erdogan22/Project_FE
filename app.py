from flask import Flask, render_template, request, redirect
from models import db, Timesheet
from datetime import date
from flask import flash




app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

app.secret_key = "super-secret-key"
db.init_app(app)

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
    app.run(debug=True) 
# Note: Ensure that the database and templates folder are properly set up for this code to run successfully.

