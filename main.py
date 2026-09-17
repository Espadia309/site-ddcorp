from flask import *
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from dotenv import load_dotenv
from markupsafe import escape
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import Increment
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")
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
def admin():
    return render_template("admin.html", title="Dashboard Admin")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title="Page Introuvable"), 404

@app.context_processor
def inject_views():
    return {"views": get_views()}

if __name__ == "__main__":
    app.run()
