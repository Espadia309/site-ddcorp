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
    return render_template("projet.html", title="Projet")

@app.route("/robot")
def robot():
    return render_template("robot.html", title="Robot Game")

if __name__ == "__main__":
    app.run()
