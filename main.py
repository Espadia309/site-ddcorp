from flask import *
from markupsafe import escape

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html",title="Bienvenue")

@app.route("/equipe")
def equipe():
    return render_template("equipe.html", title="Équipe")

@app.route("/projet")
def projet():
    return render_template("projet.html", title="Projets")

@app.route("/robot")
def robot():
    return render_template("robot.html", title="Robot Game")

@app.route("/projet/vestige")
def vestige():
    return render_template("vestige.html", title="Vestige")

@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html", title="Page Introuvable"), 404

if __name__ == "__main__":
    app.run()
