from flask import *
from markupsafe import escape

app = Flask(__name__)
app.secret_key = "_5y#2LF4Q8z\n4xec]/"


@app.route("/")
def home():
    return render_template("home.html",title="Bienvenue")

@app.route("/equipe")
def equipe():
    return render_template("equipe.html", title="Équipe")

@app.route("/equipe/prix")
def prix():
    return render_template("prix.html", title="Prix")

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
            flash("Tout les champs doivent être remplis.", "error")
        else:
            flash("Votre message a bien été envoyé, merci !", "success")
            print(f"Nouveau message de {nom} ({email}): {message}")
            return redirect(url_for("formulaire"))
    return render_template("formulaire.html", title="Contact")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title="Page Introuvable"), 404

if __name__ == "__main__":
    app.run()
