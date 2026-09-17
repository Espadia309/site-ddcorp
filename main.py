from flask import *
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField
from wtforms.validators import DataRequired
from dotenv import load_dotenv
from markupsafe import escape
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Increment
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

# firebase stuff for number of views
cred = credentials.Certificate("firebase_service_account.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def increment_views():
    ref = db.collection("site_stats").document("main")
    ref.set(
        {"views": Increment(1)},
        merge=True
    )

def get_views():
    ref = db.collection("site_stats").document("main")
    doc = ref.get()
    if doc.exists:
        return doc.to_dict().get("views", 0)
    return 0

# login stuff
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class AdminUser(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    if user_id == "admin":
        return AdminUser("admin")
    return None

# login form for the admin page
class LoginForm(FlaskForm):
    password = PasswordField("Mot de passe", validators=[DataRequired()])
    submit = SubmitField("Connexion") 

@app.route("/")
def home():
    increment_views()
    return render_template("home.html",title="Bienvenue")

@app.route("/equipe")
def equipe():
    return render_template("equipe.html", title="Équipe")

@app.route("/récompenses")
def recompenses():
    return render_template("recompenses.html", title="Récompenses")

@app.route("/projet")
def projet():
    return render_template("projet.html", title="Projets")

@app.route("/robot")
def robot():
    return render_template("robot.html", title="Robot Game")

@app.route("/actus")
def actus():
    return render_template("actus.html", title="Actualités")

@app.route("/projet/vestige")
def vestige():
    return render_template("vestige.html", title="Vestige")

@app.route("/projet/hydrache")
def hydrache():
    return render_template("hydrache.html", title="Hydra'che")

@app.route("/contact")
def formulaire():
    return render_template("formulaire.html", title="Contact")

@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html", title="Dashboard Admin")

@app.route("/admin/login", methods=["GET", "POST"])
def login():
    password = None
    form = LoginForm()
    if form.validate_on_submit():
        password = form.password.data
        form.password.data = ""
        if password == os.environ.get("PASSWORD"):
            user = AdminUser("admin")
            login_user(user)
            return redirect(url_for("admin"))

        return render_template("login.html",
                               title="Connexion",
                               form=form,
                               error="Mot de passe incorrect.")

    return render_template("login.html",
                           title = "Connexion",
                           password = password,
                           form = form)

@app.route("/admin/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title="Page Introuvable"), 404

@app.context_processor
def inject_views():
    return {"views": get_views()}

if __name__ == "__main__":
    app.run()
