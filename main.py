from flask import *
from flask_mail import Mail, Message
from dotenv import load_dotenv
from markupsafe import escape
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY")

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = os.environ.get("MAIL_USERNAME")
app.config["MAIL_PASSWORD"] = os.environ.get("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = os.environ.get("MAIL_USERNAME")

mail = Mail(app)

@app.route("/")
def home():
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

@app.route("/contact", methods=["GET", "POST"])
def formulaire():
    if request.method == "POST":
        nom = request.form.get("nom", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()
        if not nom or not email or not message:
            flash("Tous les champs doivent être remplis.", "error")
        else:
            try:
                msg = Message(
                    subject=f"Nouveau message de {nom} (site ddcorp)",
                    recipients=[os.environ.get("MAIL_RECIPIENT")],
                    body=f"Nom: {nom}\nEmail: {email}\n\nMessage:\n{message}",
                    reply_to=email
                )
                mail.send(msg)
                flash("Votre message a bien été envoyé, merci !", "success")
            except Exception as e:
                print(f"Erreur d'envoi d'email {e}")
                flash("Une erreur est survenue, veuillez réessayer plus tard.", "error")

            return redirect(url_for("formulaire"))
    return render_template("formulaire.html", title="Contact")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title="Page Introuvable"), 404

if __name__ == "__main__":
    app.run()
